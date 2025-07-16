from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid

class TaskStatus(str, Enum):
    PENDING = "pending"                    # 已创建，待处理
    IN_PROGRESS = "in_progress"            # 处理中
    WAITING_REVIEW = "waiting_review"      # 处理完，等待审核或确认
    APPROVED = "approved"                  # 审核通过 / 确认完成
    REJECTED = "rejected"                  # 审核驳回，需重做
    FAILED = "failed"                      # 处理失败
    COMPLETED = "completed"                # 已完成（最终状态）
    CANCELED = "canceled"                  # 已被取消
    ARCHIVED = "archived"                  # 已归档，不再显示在默认列表中

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    role: str = "user"

class Transcription(BaseModel):
    raw_text: str
    optimized_text: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Task(BaseModel):
    id: str
    title: str
    description: str
    priority: str
    status: TaskStatus = TaskStatus.PENDING
    owner: str
    user_id: Optional[str] = None  # 用户唯一标识，可与用户模型中 UUID 对应
    category: Optional[str] = "未分类"
    tags: Optional[List[str]] = []
    audio_files: Optional[List[str]] = []
    transcription: Optional[Transcription] = None
    created_at: str


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium"
    category: Optional[str] = "未分类"
    tags: Optional[List[str]] = []
    user_id: Optional[str] = None
    audio_files: Optional[List[str]] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[TaskStatus] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    user_id: Optional[str] = None
    transcription: Optional[Transcription] = None
    audio_files: Optional[List[str]] = None