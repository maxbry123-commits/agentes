"""
DeepAudit-derived CODA persistence core.

This transformed copy keeps the reusable orchestration primitives (state,
registry, messaging, event flow and collaboration) but deliberately does not
import the original reconnaissance, vulnerability-analysis or verification
agents at package import time.

Runtime workflow for this copy:
    LOAD_STATE -> PLAN -> CHECKPOINT -> SAFE_TASK -> VERIFY -> HANDOFF
"""

from .event_manager import EventManager, AgentEventEmitter
from .core import (
    AgentState,
    AgentStatus,
    AgentRegistry,
    agent_registry,
    AgentMessage,
    MessageType,
    MessagePriority,
    MessageBus,
)
from .tools import (
    ThinkTool,
    ReflectTool,
    CreateSubAgentTool,
    SendMessageTool,
    ViewAgentGraphTool,
    WaitForMessageTool,
    AgentFinishTool,
    RunSubAgentsTool,
    CollectSubAgentResultsTool,
    PERSISTENCE_ONLY_MODE,
    QUARANTINED_CAPABILITY_GROUPS,
)
from .telemetry import Tracer, get_global_tracer, set_global_tracer

TRANSFORMED_ROLE = "CODA_PERSISTENCE_LINK"

__all__ = [
    "EventManager",
    "AgentEventEmitter",
    "AgentState",
    "AgentStatus",
    "AgentRegistry",
    "agent_registry",
    "AgentMessage",
    "MessageType",
    "MessagePriority",
    "MessageBus",
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
    "Tracer",
    "get_global_tracer",
    "set_global_tracer",
    "TRANSFORMED_ROLE",
]
