"""REST API 请求模型。"""
from typing import Optional
from pydantic import BaseModel


class SolveRequest(BaseModel):
    problem: str
    mode: str = "ctf"  # ctf | pentest
    auto_mode: bool = True
    export_writeup: bool = False


class TaskConfigRequest(BaseModel):
    llm_config: Optional[dict] = None
    tool_config: Optional[dict] = None
