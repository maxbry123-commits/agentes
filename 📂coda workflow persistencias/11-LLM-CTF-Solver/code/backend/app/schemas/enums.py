"""消息类型、任务状态等枚举定义。"""
from enum import StrEnum


class MessageType(StrEnum):
    SYSTEM = "system"
    SOLVE_STEP = "solve_step"
    APPROVAL = "approval"


class TaskStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    TERMINATED = "terminated"


class ChallengeType(StrEnum):
    CTF = "ctf"
    PENTEST = "pentest"


class PhaseType(StrEnum):
    RECON = "recon"
    EXPLOIT = "exploit"
    REPORT = "report"
