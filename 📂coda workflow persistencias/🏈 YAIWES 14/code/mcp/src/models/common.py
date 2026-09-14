from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Execution status for tools and workflows"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExecutionResult(BaseModel):
    """Result from a tool or workflow execution"""
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS and self.exit_code == 0


class ToolOutput(BaseModel):
    """Structured output from security tools"""
    tool_name: str
    raw_output: str
    parsed_data: Optional[Dict[str, Any]] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    execution_result: ExecutionResult


class HealthStatus(BaseModel):
    """Health check status"""
    healthy: bool
    container_running: bool
    tools_available: Dict[str, bool] = Field(default_factory=dict)
    disk_usage: Optional[Dict[str, Any]] = None
    message: str = ""
