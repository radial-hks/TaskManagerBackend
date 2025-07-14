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