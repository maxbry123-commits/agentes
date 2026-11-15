"""SDK type definitions for agents, tools, and hooks.

Pydantic models for declarative agent and tool configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

# ---------------------------------------------------------------------------
# Tool Definition
# ---------------------------------------------------------------------------


@dataclass
class ToolDefinition:
    """A registered SDK tool."""

    name: str
    description: str = ""
    handler: Callable[..., Any] | None = None
    input_schema: dict[str, Any] = field(default_factory=dict)
    risk_level: str = "green"  # green, yellow, orange, red
    requires_network: bool = False
    idempotent: bool = False
    read_only: bool = False
    version: str = "0.1.0"

    def to_mcp_schema(self) -> dict[str, Any]:
        """Convert to MCP-compatible tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
            or {
                "type": "object",
                "properties": {},
            },
            "annotations": {
                "readOnlyHint": self.read_only,
                "destructiveHint": self.risk_level in ("orange", "red"),
                "idempotentHint": self.idempotent,
            },
        }


# ---------------------------------------------------------------------------
# Hook Definition
# ---------------------------------------------------------------------------


class HookEvent(StrEnum):
    """Lifecycle events for agent hooks."""

    ON_MESSAGE = "on_message"
    ON_TOOL_CALL = "on_tool_call"
    ON_TOOL_RESULT = "on_tool_result"
    ON_ERROR = "on_error"
    ON_COMPLETE = "on_complete"
    ON_START = "on_start"
    ON_STOP = "on_stop"


@dataclass
class HookDefinition:
    """A registered lifecycle hook."""

    event: HookEvent
    handler: Callable[..., Any] | None = None
    priority: int = 0
    description: str = ""


# ---------------------------------------------------------------------------
# Agent Definition
# ---------------------------------------------------------------------------


@dataclass
class AgentDefinition:
    """A registered SDK agent."""

    name: str
    description: str = ""
    version: str = "0.1.0"
    tools: list[str] = field(default_factory=list)
    system_prompt: str = ""
    trigger_keywords: list[str] = field(default_factory=list)
    can_delegate_to: list[str] = field(default_factory=list)
    max_iterations: int = 5
    timeout_seconds: int = 300
    cls: type | None = None
    hooks: list[HookDefinition] = field(default_factory=list)

    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert to YAML-serializable dict for agents.yaml."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tools": self.tools,
            "system_prompt": self.system_prompt,
            "trigger_keywords": self.trigger_keywords,
            "can_delegate_to": self.can_delegate_to,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
        }
