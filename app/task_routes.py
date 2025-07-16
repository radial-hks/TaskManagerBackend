from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from .models import Task, User, TaskCreate, TaskUpdate
from .utils import generate_id, now_iso
from .storage import load_tasks, save_tasks
from .auth import get_current_user
from typing import Optional, List
from pathlib import Path
import shutil
import logging
import uuid
from logging.handlers import RotatingFileHandler

# 配置日志
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_dir = Path("log")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'app.log'

# 使用 RotatingFileHandler 实现日志分块
# 设置每个日志文件最大为 1MB，最多保留 5 个备份
file_handler = RotatingFileHandler(log_file, maxBytes=1*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)

# 获取 logger 实例
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 如果 logger 没有 handler，则添加
if not logger.handlers:
    logger.addHandler(file_handler)

router = APIRouter()
AUDIO_DIR = Path("recordings")
AUDIO_DIR.mkdir(exist_ok=True)


@router.get("/tasks")
def get_tasks(current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 10):
    logger.info(f"User {current_user.username} fetching tasks with skip={skip} and limit={limit}.")
    tasks = load_tasks()
    if current_user.role == "admin":
        logger.info(f"Admin user {current_user.username} fetching all tasks.")
        return tasks[skip : skip + limit]
    user_tasks = [t for t in tasks if t.get("user_id") == current_user.username or t.get("owner") == current_user.username]
    logger.info(f"User {current_user.username} fetched {len(user_tasks)} tasks.")
    return user_tasks[skip : skip + limit]


@router.post("/tasks", response_model=Task)
def create_task(task_data: TaskCreate, current_user: User = Depends(get_current_user)):
    logger.info(f"User {current_user.username} creating a new task.")
    tasks = load_tasks()
    task_dict = task_data.dict()
    if 'user_id' not in task_dict or task_dict['user_id'] is None:
        task_dict['user_id'] = current_user.id

    task = Task(
        id=generate_id(),
        **task_dict,
        owner=current_user.username, # owner 字段保留，用于向后兼容或特定业务逻辑
        created_at=now_iso()
    )
    tasks.append(task.dict())
    save_tasks(tasks)
    logger.info(f"Task {task.id} created successfully by user {current_user.username}.")
    return task


@router.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, update_data: TaskUpdate, current_user: User = Depends(get_current_user)):
    logger.info(f"User {current_user.username} attempting to update task {task_id}.")
    tasks = load_tasks()
    task_index = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)

    if task_index is None:
        logger.warning(f"Task {task_id} not found for update attempt by user {current_user.username}.")
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_index]
    if current_user.role != "admin" and task["owner"] != current_user.username:
        logger.error(f"User {current_user.username} not authorized to update task {task_id}.")
        raise HTTPException(status_code=403, detail="Not authorized to update this task")

    update_data_dict = update_data.dict(exclude_unset=True)
    for key, value in update_data_dict.items():
        task[key] = value

    tasks[task_index] = task
    save_tasks(tasks)
    logger.info(f"Task {task_id} updated successfully by user {current_user.username}.")
    return task


@router.post("/tasks/{task_id}/upload")
def upload_audio(task_id: str, files: List[UploadFile] = File(...), current_user: User = Depends(get_current_user)):
    logger.info(f"User {current_user.username} uploading audio for task {task_id}.")
    tasks = load_tasks()
    task_found = False
    for task in tasks:
        if task["id"] == task_id:
            task_found = True
            if current_user.role != "admin" and task["owner"] != current_user.username:
                logger.error(f"User {current_user.username} not authorized to upload audio for task {task_id}.")
                raise HTTPException(status_code=403)

            uploaded_files = []
            for file in files:
                ext = Path(file.filename).suffix
                unique_filename = f"{uuid.uuid4()}{ext}"
                dest = AUDIO_DIR / unique_filename
                try:
                    with dest.open("wb") as f:
                        shutil.copyfileobj(file.file, f)
                    uploaded_files.append(str(dest))
                except Exception as e:
                    logger.error(f"Error uploading audio for task {task_id}: {e}")
                    raise HTTPException(status_code=500, detail="Audio upload failed.")

            if "audio_files" not in task or not task["audio_files"]:
                task["audio_files"] = []
            task["audio_files"].extend(uploaded_files)
            save_tasks(tasks)
            logger.info(f"Audio for task {task_id} uploaded successfully to {uploaded_files}.")
            return {"msg": "Uploaded", "paths": uploaded_files}

    if not task_found:
        logger.warning(f"Task {task_id} not found for audio upload attempt by user {current_user.username}.")
        raise HTTPException(status_code=404)


@router.delete("/tasks/{task_id}/files")
def delete_audio_files(task_id: str, file_paths: List[str], current_user: User = Depends(get_current_user)):
    logger.info(f"User {current_user.username} requesting to delete files for task {task_id}.")
    tasks = load_tasks()
    task_found = False
    for task in tasks:
        if task["id"] == task_id:
            task_found = True
            if current_user.role != "admin" and task["owner"] != current_user.username:
                logger.error(f"User {current_user.username} not authorized to delete files for task {task_id}.")
                raise HTTPException(status_code=403, detail="Not authorized to delete files for this task.")

            if "audio_files" not in task or not task["audio_files"]:
                raise HTTPException(status_code=404, detail="No audio files associated with this task.")

            deleted_files = []
            not_found_files = []
            
            original_audio_files = list(task["audio_files"])

            for file_path_to_delete in file_paths:
                if file_path_to_delete in original_audio_files:
                    try:
                        Path(file_path_to_delete).unlink(missing_ok=True)
                        task["audio_files"].remove(file_path_to_delete)
                        deleted_files.append(file_path_to_delete)
                        logger.info(f"Deleted file {file_path_to_delete} for task {task_id}.")
                    except Exception as e:
                        logger.error(f"Error deleting file {file_path_to_delete} for task {task_id}: {e}")
                else:
                    not_found_files.append(file_path_to_delete)

            if not deleted_files:
                raise HTTPException(status_code=404, detail="None of the specified files were found for this task.")

            save_tasks(tasks)
            
            response = {"msg": "Deletion process completed.", "deleted": deleted_files}
            if not_found_files:
                response["not_found"] = not_found_files
            
            return response

    if not task_found:
        logger.warning(f"Task {task_id} not found for file deletion attempt by user {current_user.username}.")
        raise HTTPException(status_code=404, detail="Task not found.")


@router.get("/tasks/search")
def search_tasks(
    keyword: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    owner: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} searching tasks with criteria: keyword={keyword}, priority={priority}, category={category}, tags={tags}, owner={owner}, created_after={created_after}, created_before={created_before}")
    tasks = load_tasks()
    result = []
    for task in tasks:
        if current_user.role != "admin" and task["owner"] != current_user.username:
            continue
        if keyword and keyword not in (task["title"] + task["description"]):
            continue
        if priority and task["priority"] != priority:
            continue
        if category and task.get("category") != category:
            continue
        if tags and not all(t in task.get("tags", []) for t in tags):
            continue
        if owner and task["owner"] != owner:
            continue
        if created_after and task["created_at"] < created_after:
            continue
        if created_before and task["created_at"] > created_before:
            continue
        result.append(task)
    logger.info(f"Search by user {current_user.username} found {len(result)} tasks.")
    return result