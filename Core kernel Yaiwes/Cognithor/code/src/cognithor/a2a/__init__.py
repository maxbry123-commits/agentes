"""Cognithor · A2A Protocol -- RC v1.0 (Linux Foundation).

Agent-to-agent communication following open standard.
Replaces proprietary JAIP protocol with Linux Foundation-compliant A2A.

Modules:
  types        -- Data types (Task, Message, AgentCard, Parts, Events)
  server       -- JSON-RPC 2.0 server (receives remote tasks)
  client       -- JSON-RPC 2.0 client (sends tasks to remote agents)
  adapter      -- Bridge JAIP<->A2A + gateway integration
  http_handler -- HTTP transport (FastAPI routes)

OPTIONAL: Only active when enabled in config. No import error when disabled.
"""

from __future__ import annotations

# Adapter -- always available
from cognithor.a2a.adapter import A2AAdapter
from cognithor.a2a.client import A2AClient, RemoteAgent

# Server + Client -- always available
from cognithor.a2a.server import A2AServer, A2AServerConfig

# Types -- always available (no external deps)
from cognithor.a2a.types import (
    A2A_CONTENT_TYPE,
    A2A_PROTOCOL_VERSION,
    A2A_VERSION_HEADER,
    VALID_TRANSITIONS,
    A2AAgentCapabilities,
    A2AAgentCard,
    A2AErrorCode,
    A2AInterface,
    A2AProvider,
    A2ASecurityScheme,
    A2ASkill,
    Artifact,
    DataPart,
    FilePart,
    Message,
    MessageRole,
    Part,
    PartType,
    PushNotificationAuth,
    PushNotificationConfig,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
    is_valid_transition,
    part_from_dict,
)

__all__ = [
    # Types
    "A2A_CONTENT_TYPE",
    "A2A_PROTOCOL_VERSION",
    "A2A_VERSION_HEADER",
    "VALID_TRANSITIONS",
    # Adapter
    "A2AAdapter",
    "A2AAgentCapabilities",
    "A2AAgentCard",
    # Client
    "A2AClient",
    "A2AErrorCode",
    "A2AInterface",
    "A2AProvider",
    "A2ASecurityScheme",
    # Server
    "A2AServer",
    "A2AServerConfig",
    "A2ASkill",
    "Artifact",
    "DataPart",
    "FilePart",
    "Message",
    "MessageRole",
    "Part",
    "PartType",
    "PushNotificationAuth",
    "PushNotificationConfig",
    "RemoteAgent",
    "Task",
    "TaskArtifactUpdateEvent",
    "TaskState",
    "TaskStatus",
    "TaskStatusUpdateEvent",
    "TextPart",
    "is_valid_transition",
    "part_from_dict",
]
