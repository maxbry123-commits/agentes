"""
CODA persistence-only tool surface for transformed AI_Pentest.

Only abstract tool/result/registry primitives are exposed. Network/web/vulnerability
scanners, brute-force functionality and post-exploitation tooling are intentionally
not imported. Original source remains reproducible from `_archives`.
"""
from .base import BaseTool, ToolResult, ToolRegistry

PERSISTENCE_ONLY_MODE = True
QUARANTINED_TOOL_GROUPS = (
    "NetworkScanner",
    "WebScanner",
    "VulnerabilityScanner",
    "BruteForceTool",
    "PostExploitTool",
    "ToolManager",
)

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "PERSISTENCE_ONLY_MODE",
    "QUARANTINED_TOOL_GROUPS",
]
