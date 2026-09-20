"""CapabilityRequest type · 0% LLM"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal

CapabilityName = Literal[
    "code_generation", "code_review", "debugging", "testing", "validation",
    "web_search", "github_search", "reasoning", "planning", "research",
    "documentation", "image_generation", "database_query", "deploy", "recovery",
]


@dataclass
class CapabilityRequest:
    request_id: str
    run_id: str
    capability: CapabilityName
    issued_at: str
    constraints: dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"
    resolved_by: str | None = None
    status: str = "pending"
