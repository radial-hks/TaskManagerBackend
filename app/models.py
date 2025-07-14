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


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium"
    category: Optional[str] = "未分类"
    tags: Optional[List[str]] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None