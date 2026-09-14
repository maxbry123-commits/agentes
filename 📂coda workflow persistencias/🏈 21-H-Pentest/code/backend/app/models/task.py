"""
数据库模型 - 使用SQLAlchemy 2.0异步模式
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, DateTime, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import enum


class Base(DeclarativeBase):
    """基础模型类"""
    pass


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    STOPPED = "stopped"  # 添加STOPPED状态


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    target_url: Mapped[str] = mapped_column(String(512))
    mode: Mapped[str] = mapped_column(String(20))  # ctf, realworld
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    
    # 配置
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    max_rounds: Mapped[int] = mapped_column(Integer, default=30)
    current_round: Mapped[int] = mapped_column(Integer, default=0)
    
    # 任务计划
    task_plan: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # 结果
    flags_found: Mapped[List[str]] = mapped_column(JSON, default=list)
    vulnerabilities: Mapped[List[Dict]] = mapped_column(JSON, default=list)
    report: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # 时间（使用timezone-aware datetime）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 元数据（重命名为metadata -> task_metadata）
    task_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class Message(Base):
    """消息表 - 存储所有任务相关消息"""
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), index=True)
    
    # 消息类型
    type: Mapped[str] = mapped_column(String(50), index=True)
    # log, progress, llm_thinking, tool_execution, vulnerability, flag, plan, etc.
    
    # 内容
    content: Mapped[str] = mapped_column(Text)
    msg_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default=dict)  # 重命名
    
    # 时间（🔥 使用timezone-aware datetime）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        index=True
    )
    round: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class Conversation(Base):
    """对话历史表 - 用于上下文管理"""
    __tablename__ = "conversations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), index=True)
    
    # 消息内容
    role: Mapped[str] = mapped_column(String(20))  # system, user, assistant, tool
    content: Mapped[str] = mapped_column(Text)
    
    # 上下文管理
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[str] = mapped_column(String(10), default="medium")  # high, medium, low
    pentest_value: Mapped[float] = mapped_column(default=0.5)
    
    # 时间和轮次（使用timezone-aware datetime）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        index=True
    )
    round: Mapped[int] = mapped_column(Integer, default=0)
    
    # 元数据（重命名）
    conv_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
