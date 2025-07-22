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


class AudioFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_filename: str = Field(..., description="用户自定义的文件名")
    internal_path: str = Field(..., description="服务器内部存储路径")
    uploaded_at: datetime = Field(default_factory=datetime.now)


class TaskBase(BaseModel):
    """
    任务模型的基础部分，包含创建和读取时共有的字段。
    """
    title: str = Field(..., min_length=1, max_length=100, description="任务标题")
    description: Optional[str] = Field(None, max_length=1000, description="任务的详细描述")
    priority: Optional[str] = Field("medium", description="任务优先级")
    category: Optional[str] = Field("未分类", description="任务分类")
    tags: Optional[List[str]] = Field([], description="任务标签列表")
    user_id: Optional[str] = Field(None, description="任务所属用户的ID")


class TaskCreate(TaskBase):
    """
    用于创建任务的模型，继承自 TaskBase。
    创建任务时不应直接提供音频文件，应在创建后上传。
    """
    pass


class Task(TaskBase):
    """
    完整的任务模型，用于从数据库读取或API返回。
    """
    id: str
    owner: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: str
    audio_files: Optional[List[AudioFile]] = []
    transcription: Optional[Transcription] = None
    


class TaskUpdate(BaseModel):
    """
    用于更新任务的模型，所有字段都是可选的。
    """
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[str] = None
    status: Optional[TaskStatus] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    # user_id: Optional[str] = None  # 通常不应允许直接更新，除非有特定权限控制
    transcription: Optional[Transcription] = None