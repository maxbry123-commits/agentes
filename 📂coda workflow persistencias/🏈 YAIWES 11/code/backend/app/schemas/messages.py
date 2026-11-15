"""WebSocket 消息 Pydantic 模型 — 前后端通信协议。"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    msg_type: str
    content: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class SystemMessage(Message):
    msg_type: str = "system"
    type: str = "info"  # info | warning | success | error


class SolveStepMessage(Message):
    """SolveAgent 每步完成后推送的结构化快照。"""
    msg_type: str = "solve_step"
    step_num: int
    phase: str  # recon | exploit | report
    think: str = ""
    tool_calls: list = Field(default_factory=list)
    tool_names: list = Field(default_factory=list)
    output: str = ""
    analysis: str = ""
    flag_found: bool = False
    flag_value: Optional[str] = None
    stuck_warning: bool = False
    vulnerability: Optional[dict] = None
    token_stats: dict = Field(default_factory=dict)
    cache_stats: dict = Field(default_factory=dict)


class ApprovalMessage(Message):
    """HIL 人工确认消息 — 阻塞 SolveAgent 等待用户决策。"""
    msg_type: str = "approval"
    checkpoint_id: str
    prompt: dict = Field(default_factory=dict)  # {message, type: confirm|choose|prompt_text}
    options: list = Field(default_factory=list)
    timeout: int = 300
