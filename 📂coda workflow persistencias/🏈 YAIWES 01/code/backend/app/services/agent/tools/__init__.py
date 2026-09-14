"""
CODA persistence-only tool surface for the transformed DeepAudit copy.

The downloaded upstream implementation is retained for provenance under this
component, but the public tool package intentionally exposes only benign
workflow primitives. Sandbox execution, vulnerability-test payloads, fuzzing,
external security scanners and generic code execution are NOT imported here.

This is a fail-closed transformation: code that expects an offensive tool from
``agent.tools`` must fail instead of silently regaining that capability.
"""

from .base import AgentTool, ToolResult
from .file_tool import FileReadTool, FileSearchTool, ListFilesTool
from .thinking_tool import ThinkTool, ReflectTool
from .agent_tools import (
    CreateSubAgentTool,
    SendMessageTool,
    ViewAgentGraphTool,
    WaitForMessageTool,
    AgentFinishTool,
    RunSubAgentsTool,
    CollectSubAgentResultsTool,
)

PERSISTENCE_ONLY_MODE = True
QUARANTINED_CAPABILITY_GROUPS = (
    "sandbox_execution",
    "http_sandbox",
    "vulnerability_verification",
    "injection_test_tools",
    "fuzzing_harness",
    "generic_code_execution",
    "external_security_scanners",
    "smart_scan",
    "vulnerability_reporting",
)

__all__ = [
    "AgentTool",
    "ToolResult",
    "FileReadTool",
    "FileSearchTool",
    "ListFilesTool",
    "ThinkTool",
    "ReflectTool",
    "CreateSubAgentTool",
    "SendMessageTool",
    "ViewAgentGraphTool",
    "WaitForMessageTool",
    "AgentFinishTool",
    "RunSubAgentsTool",
    "CollectSubAgentResultsTool",
    "PERSISTENCE_ONLY_MODE",
    "QUARANTINED_CAPABILITY_GROUPS",
]
