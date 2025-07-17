from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Form, Body
from fastapi.responses import FileResponse, JSONResponse
from .models import Task, User, TaskCreate, TaskUpdate, TaskStatus, AudioFile
from .utils import generate_id, now_iso
from .storage import load_tasks, save_tasks
from .auth import get_current_user
from typing import Optional, List, Dict
from pathlib import Path
import shutil
import logging
import uuid
from logging.handlers import RotatingFileHandler
from fastapi.encoders import jsonable_encoder

# 配置日志
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_dir = Path("log")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'app.log'

# 使用 RotatingFileHandler 实现日志分块
file_handler = RotatingFileHandler(log_file, maxBytes=1*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)

# 获取 logger 实例
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(file_handler)

router = APIRouter()
AUDIO_DIR = Path("recordings")
AUDIO_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


async def get_task_for_user(task_id: str, current_user: User = Depends(get_current_user)) -> Dict:
    """
    依赖项：按ID获取任务，并验证当前用户是否有权访问。
    管理员可以访问任何任务，普通用户只能访问自己的任务。
    """
    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)

    if not task:
        logger.warning(f"任务 {task_id} 未找到，访问用户：{current_user.username}。")
        raise HTTPException(status_code=404, detail="Task not found")

    is_owner = task.get("user_id") == current_user.id or task.get("owner") == current_user.username
    if current_user.role != "admin" and not is_owner:
        logger.error(f"用户 {current_user.username} 无权访问任务 {task_id}。")
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    
    return task


@router.get("/tasks", response_model=List[Task])
def get_tasks(current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 100):
    logger.info(f"用户 {current_user.username} 正在获取任务列表，skip={skip}, limit={limit}。")
    tasks = load_tasks()
    if current_user.role == "admin":
        logger.info(f"管理员 {current_user.username} 正在获取所有任务。")
        return [Task(**t) for t in tasks[skip : skip + limit]]
    
    user_tasks = [t for t in tasks if t.get("user_id") == current_user.id or t.get("owner") == current_user.username]
    logger.info(f"用户 {current_user.username} 获取到 {len(user_tasks)} 个任务。")
    return [Task(**t) for t in user_tasks[skip : skip + limit]]


@router.get("/tasks/{task_id}", response_model=Task)
def get_task_by_id(task: dict = Depends(get_task_for_user)):
    """
    通过ID检索单个任务。
    授权由 get_task_for_user 依赖项处理。
    """
    return Task(**task)


@router.post("/tasks", response_model=Task, status_code=201)
def create_task(task_data: TaskCreate, current_user: User = Depends(get_current_user)):
    logger.info(f"用户 {current_user.username} 正在创建新任务。")
    tasks = load_tasks()
    
    task_dict = task_data.dict(exclude_unset=True)  # 使用 exclude_unset=True 避免覆盖默认值
    if not task_dict.get('user_id'):
        task_dict['user_id'] = current_user.id

    new_task = Task(
        id=generate_id(),
        **task_dict,
        owner=current_user.username, 
        created_at=now_iso(),
        status=TaskStatus.PENDING
    )
    
    tasks.append(new_task.dict())
    save_tasks(tasks)
    logger.info(f"任务 {new_task.id} 已由用户 {current_user.username} 成功创建。")
    return new_task


@router.put("/tasks/{task_id}", response_model=Task)
def update_task(update_data: TaskUpdate, task: dict = Depends(get_task_for_user), current_user: User = Depends(get_current_user)):
    task_id = task['id']
    logger.info(f"用户 {current_user.username} 正在更新任务 {task_id}。")

    try:
        tasks = load_tasks()
        task_index = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)

        if task_index is None:
            # 这个检查理论上是多余的，因为 get_task_for_user 已经处理了
            raise HTTPException(status_code=404, detail="Task not found during update process.")

        # 将存储的字典转换为 Pydantic 模型
        task_model = Task(**tasks[task_index])

        # 获取更新数据字典
        update_dict = update_data.dict(exclude_unset=True)

        # 使用 Pydantic 的 copy 方法进行更新
        updated_task_model = task_model.copy(update=update_dict)
        
        # 将更新后的模型转换为可序列化的字典
        tasks[task_index] = jsonable_encoder(updated_task_model)
        
        save_tasks(tasks)
        
        logger.info(f"任务 {task_id} 已由用户 {current_user.username} 成功更新。")
        return updated_task_model
    except Exception as e:
        logger.error(f"更新任务 {task_id} 时发生内部错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error during task update.")


@router.post("/tasks/{task_id}/files/upload", response_model=List[AudioFile])
def upload_audio(
    task: dict = Depends(get_task_for_user),
    files: List[UploadFile] = File(...),
    user_filenames: Optional[List[str]] = Form(None),
    current_user: User = Depends(get_current_user)
):
    task_id = task['id']
    logger.info(f"用户 {current_user.username} 正在为任务 {task_id} 上传文件。")

    if user_filenames and len(user_filenames) != len(files):
        raise HTTPException(status_code=400, detail="The number of filenames does not match the number of files.")

    tasks = load_tasks()
    task_index = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    if task_index is None:
        raise HTTPException(status_code=404, detail="Task not found during upload.")

    task_model = Task(**tasks[task_index])
    newly_added_files = []

    for i, file in enumerate(files):
        # 检查文件大小
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)  # 重置文件指针
        if file_size > MAX_UPLOAD_SIZE:
            logger.warning(
                f"用户 {current_user.username} 尝试上传过大文件: {file.filename}, "
                f"大小: {file_size} 字节, 限制: {MAX_UPLOAD_SIZE} 字节。"
            )
            raise HTTPException(
                status_code=413,
                detail=f"文件 '{file.filename}' 过大，超过了 50MB 的限制。"
            )

        ext = Path(file.filename).suffix
        internal_filename = f"{task_id}_{uuid.uuid4()}{ext}"
        dest_path = AUDIO_DIR / internal_filename

        try:
            with dest_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file {file.filename}.")

        user_filename = user_filenames[i] if user_filenames and user_filenames[i] else file.filename
        
        audio_file_model = AudioFile(
            user_filename=user_filename,
            internal_path=str(dest_path)
        )
        task_model.audio_files.append(audio_file_model)
        newly_added_files.append(audio_file_model)

    tasks[task_index] = jsonable_encoder(task_model)
    save_tasks(tasks)

    logger.info(f"为任务 {task_id} 成功上传 {len(newly_added_files)} 个文件。")
    return newly_added_files


@router.delete("/tasks/{task_id}/files")
def delete_audio_files(
    file_ids: List[str],
    task: dict = Depends(get_task_for_user),
    current_user: User = Depends(get_current_user)
):
    task_id = task['id']
    logger.info(f"用户 {current_user.username} 请求删除任务 {task_id} 的文件：{file_ids}")

    tasks = load_tasks()
    task_index = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    if task_index is None:
        logger.error(f"删除文件时未找到任务 {task_id}")
        raise HTTPException(status_code=404, detail="Task not found.")

    task_model = Task(**tasks[task_index])
    if not task_model.audio_files:
        logger.warning(f"任务 {task_id} 没有音频文件")
        raise HTTPException(status_code=404, detail="Task has no audio files.")

    # 验证所有要删除的文件ID是否存在
    existing_file_ids = {f.id for f in task_model.audio_files}
    invalid_file_ids = set(file_ids) - existing_file_ids
    if invalid_file_ids:
        logger.warning(f"请求删除的文件ID不存在：{invalid_file_ids}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file IDs: {list(invalid_file_ids)}"
        )

    # 准备删除操作
    files_to_delete = [f for f in task_model.audio_files if f.id in file_ids]
    files_to_keep = [f for f in task_model.audio_files if f.id not in file_ids]
    deletion_results = []
    failed_deletions = []

    # 执行文件删除
    for file in files_to_delete:
        try:
            file_path = Path(file.internal_path)
            if file_path.is_file():
                file_path.unlink()
                deletion_results.append({
                    "id": file.id,
                    "filename": file.user_filename,
                    "status": "success"
                })
                logger.info(f"成功删除文件：{file.user_filename} (ID: {file.id})")
            else:
                logger.warning(f"文件不存在于磁盘：{file.internal_path}")
                deletion_results.append({
                    "id": file.id,
                    "filename": file.user_filename,
                    "status": "file_not_found"
                })
        except Exception as e:
            logger.error(f"删除文件 {file.internal_path} 失败: {str(e)}", exc_info=True)
            failed_deletions.append({
                "id": file.id,
                "filename": file.user_filename,
                "error": str(e)
            })

    # 更新任务数据
    task_model.audio_files = files_to_keep
    tasks[task_index] = jsonable_encoder(task_model)
    
    try:
        save_tasks(tasks)
        logger.info(f"已更新任务 {task_id} 的文件列表")
    except Exception as e:
        logger.error(f"保存任务数据时发生错误: {str(e)}", exc_info=True)
        # 如果保存失败，尝试恢复已删除的文件
        for result in deletion_results:
            if result["status"] == "success":
                file_to_restore = next(
                    f for f in files_to_delete if f.id == result["id"]
                )
                logger.warning(f"正在尝试恢复已删除的文件：{file_to_restore.user_filename}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save task data after file deletion."
        )

    response_data = {
        "message": "File deletion completed",
        "results": deletion_results
    }
    
    if failed_deletions:
        response_data["failed"] = failed_deletions
        return JSONResponse(
            status_code=207,
            content=response_data
        )

    return response_data


@router.put("/tasks/{task_id}/files/{file_id}", response_model=AudioFile)
def rename_audio_file(
    file_id: str,
    new_filename: str = Body(..., embed=True, alias="new_filename"),
    task: dict = Depends(get_task_for_user),
    current_user: User = Depends(get_current_user)
):
    task_id = task['id']
    tasks = load_tasks()
    task_index = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    task_model = Task(**tasks[task_index])

    file_to_rename = next((f for f in task_model.audio_files if f.id == file_id), None)
    if not file_to_rename:
        raise HTTPException(status_code=404, detail="File not found.")

    file_to_rename.user_filename = new_filename
    tasks[task_index] = jsonable_encoder(task_model)
    save_tasks(tasks)

    logger.info(f"用户 {current_user.username} 已将任务 {task_id} 的文件 {file_id} 重命名为 {new_filename}。")
    return file_to_rename


@router.get("/tasks/{task_id}/files/{file_identifier}")
def get_audio_file(
    file_identifier: str,
    task: dict = Depends(get_task_for_user)
):
    logger.info(f"正在获取任务 {task['id']} 的文件 {file_identifier}。")
    task_model = Task(**task)
    
    try:
        found_file = next((f for f in task_model.audio_files if f.id == file_identifier or f.user_filename == file_identifier), None)

        if not found_file:
            logger.warning(f"未找到文件 {file_identifier}。")
            raise HTTPException(status_code=404, detail="File not found.")

        file_path = Path(found_file.internal_path)
        if not file_path.is_file():
            logger.error(f"服务器上未找到文件 {found_file.internal_path}。")
            raise HTTPException(status_code=404, detail="File not found on server.")

        logger.info(f"成功找到并返回文件 {found_file.user_filename}。")
        return FileResponse(path=file_path, filename=found_file.user_filename, media_type='application/octet-stream')
    except Exception as e:
        logger.error(f"获取文件时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving file.")


@router.get("/tasks/search/", response_model=List[Task])
def search_tasks(
    keyword: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    owner: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    logger.info(f"用户 {current_user.username} 正在根据条件搜索任务: keyword={keyword}, priority={priority}, status={status}, category={category}, tags={tags}, owner={owner}, created_after={created_after}, created_before={created_before}")
    
    tasks = load_tasks()

    if current_user.role == "admin":
        accessible_tasks = tasks
    else:
        accessible_tasks = [t for t in tasks if t.get("user_id") == current_user.id or t.get("owner") == current_user.username]

    def task_filter(task: dict) -> bool:
        if keyword and keyword.lower() not in (task.get("title", "").lower() + task.get("description", "").lower()):
            return False
        if priority and task.get("priority") != priority:
            return False
        if status and task.get("status") != status:
            return False
        if category and task.get("category") != category:
            return False
        if tags and not set(tags).issubset(set(task.get("tags", []))):
            return False
        if owner and task.get("owner") != owner:
            return False
        if created_after and task.get("created_at") < created_after:
            return False
        if created_before and task.get("created_at") > created_before:
            return False
        return True

    filtered_tasks = list(filter(task_filter, accessible_tasks))
    
    logger.info(f"用户 {current_user.username} 的搜索找到 {len(filtered_tasks)} 个任务。")
    return [Task(**t) for t in filtered_tasks]