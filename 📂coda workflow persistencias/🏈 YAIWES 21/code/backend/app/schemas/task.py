"""
任务相关的Pydantic模式定义
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime


class TaskCreate(BaseModel):
    """创建任务请求"""
    target_url: str = Field(..., description="目标URL")
    mode: Literal["ctf", "realworld"] = Field(..., description="测试模式")
    max_rounds: Optional[int] = Field(30, ge=1, le=100, description="最大轮数")
    
    # 🔥 自定义目标
    custom_objective: Optional[str] = Field(None, max_length=1000, description="自定义渗透测试目标")
    
    # CTF模式参数
    flag_submit_url: Optional[str] = Field(None, description="FLAG提交URL")
    flag_submit_method: Optional[Literal["GET", "POST"]] = Field("POST", description="FLAG提交方法")
    token: Optional[str] = Field(None, description="认证Token")
    challenge_code: Optional[str] = Field(None, description="题目代码")
    
    # RealWorld模式参数
    scope_file: Optional[str] = Field(None, description="测试范围文件")
    compliance: Optional[str] = Field("OWASP", description="合规标准")
    stealth: Optional[bool] = Field(False, description="隐蔽模式")
    stealth_profile: Optional[Literal["paranoid", "stealth", "balanced", "aggressive"]] = Field("balanced", description="隐蔽级别")
    
    # 高级配置
    verbose: Optional[bool] = Field(False, description="详细输出")


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    target_url: str
    mode: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    max_rounds: int
    current_round: int
    flags_found: List[str]
    flags: List[str]  # 兼容前端
    vulnerabilities: List[Dict[str, Any]]
    report: Optional[Dict[str, Any]] = None
    task_plan: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class InterventionRequest(BaseModel):
    """人工干预请求"""
    action: Literal["pause", "resume", "inject", "force_stop"]
    instruction: Optional[str] = None  # inject时使用
    priority: Optional[Literal["low", "medium", "high", "critical"]] = Field("high", description="优先级")
