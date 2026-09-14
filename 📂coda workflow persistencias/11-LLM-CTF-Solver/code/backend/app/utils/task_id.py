"""Task ID 生成 — 仿 MMA 模式。"""
import uuid
from datetime import datetime


def generate_task_id() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"{ts}-{short_uuid}"


def validate_task_id(task_id: str) -> bool:
    """验证 task_id 格式安全性（防路径遍历）。"""
    import re
    return bool(re.match(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$', task_id))
