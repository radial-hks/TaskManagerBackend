from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from .models import Task, User
from .utils import generate_id, now_iso
from .storage import load_tasks, save_tasks
from .auth import get_current_user
from typing import Optional, List
from pathlib import Path
import shutil

router = APIRouter()
AUDIO_DIR = Path("recordings")
AUDIO_DIR.mkdir(exist_ok=True)


@router.get("/tasks")
def get_tasks(current_user: User = Depends(get_current_user)):
    tasks = load_tasks()
    if current_user.role == "admin":
        return tasks
    return [t for t in tasks if t["owner"] == current_user.username]


@router.post("/tasks")
def create_task(task_data: dict, current_user: User = Depends(get_current_user)):
    tasks = load_tasks()
    task = Task(
        id=generate_id(),
        title=task_data["title"],
        description=task_data.get("description", ""),
        priority=task_data.get("priority", "medium"),
        owner=current_user.username,
        category=task_data.get("category", "未分类"),
        tags=task_data.get("tags", []),
        audio_file=None,
        created_at=now_iso()
    )
    tasks.append(task.dict())
    save_tasks(tasks)
    return task


@router.put("/tasks/{task_id}")
def update_task(task_id: str, update_data: dict, current_user: User = Depends(get_current_user)):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            if current_user.role != "admin" and task["owner"] != current_user.username:
                raise HTTPException(status_code=403)
            task.update(update_data)
            save_tasks(tasks)
            return task
    raise HTTPException(status_code=404)


@router.post("/tasks/{task_id}/upload")
def upload_audio(task_id: str, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            if current_user.role != "admin" and task["owner"] != current_user.username:
                raise HTTPException(status_code=403)
            ext = Path(file.filename).suffix
            dest = AUDIO_DIR / f"{task_id}{ext}"
            with dest.open("wb") as f:
                shutil.copyfileobj(file.file, f)
            task["audio_file"] = str(dest)
            save_tasks(tasks)
            return {"msg": "Uploaded", "path": str(dest)}
    raise HTTPException(status_code=404)


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
    return result