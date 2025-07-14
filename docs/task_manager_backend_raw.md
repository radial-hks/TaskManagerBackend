## 项目结构

```
project_root/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI 入口
│   ├── auth.py                # 用户认证模块
│   ├── models.py              # 数据模型定义
│   ├── storage.py             # JSON 读写封装
│   ├── task_routes.py         # 任务相关路由
│   └── utils.py               # 工具函数，如密码加密、UUID
├── data/
│   ├── users.json             # 用户信息
│   └── tasks.json             # 任务信息
├── recordings/               # 存储音频文件
└── requirements.txt          # 依赖包列表
```

---

## requirements.txt
```
fastapi
uvicorn
python-jose[cryptography]
bcrypt
pydantic
```

---

## models.py
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    username: str
    password_hash: str
    role: str = "user"

class Task(BaseModel):
    id: str
    title: str
    description: str
    priority: str
    owner: str
    category: Optional[str] = "未分类"
    tags: Optional[List[str]] = []
    audio_file: Optional[str] = None
    created_at: str
```

---

## storage.py
```python
import json
from pathlib import Path

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
TASKS_FILE = DATA_DIR / "tasks.json"


def load_users():
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    return []

def save_users(users):
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")


def load_tasks():
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    return []

def save_tasks(tasks):
    TASKS_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
```

---

## utils.py
```python
import bcrypt
import uuid
from datetime import datetime


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())


def generate_id():
    return str(uuid.uuid4())


def now_iso():
    return datetime.utcnow().isoformat()
```

---

## auth.py
```python
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta
from models import User
from storage import load_users, save_users
from utils import hash_password, verify_password

SECRET_KEY = "super-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        users = load_users()
        user = next((u for u in users if u["username"] == username), None)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")


@router.post("/register")
def register(form: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    if any(u["username"] == form.username for u in users):
        raise HTTPException(status_code=400, detail="Username exists")
    user = {
        "username": form.username,
        "password_hash": hash_password(form.password),
        "role": "user"
    }
    users.append(user)
    save_users(users)
    return {"msg": "Registered"}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    user = next((u for u in users if u["username"] == form.username), None)
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user["username"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer"}
```

---

## task_routes.py
```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from models import Task, User
from utils import generate_id, now_iso
from storage import load_tasks, save_tasks
from auth import get_current_user
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
```

---

## main.py
```python
from fastapi import FastAPI
from app import auth, task_routes

app = FastAPI()

app.include_router(auth.router)
app.include_router(task_routes.router)
```
## 示例数据

### data/users.json
```json
[
  {
    "username": "admin",
    "password_hash": "$2b$12$3RCXwqgPIEVdcKyoGDr2tOmLbRHfEj35PBsT8OayWmHLR0Kk4Nz/q",  // 密码为 "admin123"
    "role": "admin"
  },
  {
    "username": "user1",
    "password_hash": "$2b$12$8tLZjtzM3ycbxAeWmDbPSOHptcIo7vIGpO62AThzXtUjGyaMldcxu",  // 密码为 "user123"
    "role": "user"
  }
]
```

### data/tasks.json
```json
[
  {
    "id": "test-uuid-1",
    "title": "会议纪要整理",
    "description": "请将上周的会议音频转成文本。",
    "priority": "high",
    "owner": "user1",
    "category": "会议纪要",
    "tags": ["转录", "会议"],
    "audio_file": "recordings/test-uuid-1.wav",
    "created_at": "2025-07-13T08:00:00"
  },
  {
    "id": "test-uuid-2",
    "title": "客户反馈分析",
    "description": "分析最近客户的音频反馈内容。",
    "priority": "medium",
    "owner": "user1",
    "category": "客户反馈",
    "tags": ["客户", "分析"],
    "audio_file": null,
    "created_at": "2025-07-13T09:30:00"
  }
]
```

---

## Swagger 示例说明

FastAPI 内置 Swagger UI：访问 http://localhost:8000/docs

推荐使用示例请求体测试：

### 创建任务 POST /tasks
```json
{
  "title": "录音转文字",
  "description": "将电话录音文件转为文字文档",
  "priority": "medium",
  "category": "转写",
  "tags": ["语音", "文字"]
}
```


