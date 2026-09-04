"""Authority Graph · separar capacidad de autoridad de control.

COGNITIVE  → preserve (razonamiento de code agent NO se elimina)
EXECUTION  → adapt
CONTROL    → subordinate (loop/mission global)
STATE      → adapt
PRESENTATION → isolate
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

AUTHORITY_TYPES = ("cognitive", "execution", "control", "state", "presentation", "unknown")

DEFAULT_POLICY: dict[str, str] = {
    "cognitive": "preserve",
    "execution": "adapt",
    "control": "subordinate",
    "state": "adapt",
    "presentation": "isolate",
    "unknown": "adapt",
}

# Señales deterministas (heurística; LLM solo si UNKNOWN)
CONTROL_SIGNALS = (
    "agent_loop", "mission_loop", "spawn_worker", "global_scheduler",
    "allocate_resource", "terminate_all", "free_tool_router",
)
COGNITIVE_SIGNALS = (
    "generate_code", "analyze_code", "reason", "plan_edit", "review_code",
    "llm.generate", "chain_of_thought",
)
EXECUTION_SIGNALS = (
    "subprocess", "filesystem", "git", "terminal", "browser", "http_request",
)


@dataclass
class AuthorityNode:
    component: str
    authority: str
    action: str
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_authority(name: str, side_effects: list[str] | None = None, calls: list[str] | None = None) -> AuthorityNode:
    text = " ".join([name] + list(side_effects or []) + list(calls or [])).lower()
    evidence: list[str] = []
    if any(s in text for s in CONTROL_SIGNALS):
        evidence.append("control_signal")
        return AuthorityNode(name, "control", DEFAULT_POLICY["control"], evidence, 0.9)
    if any(s in text for s in COGNITIVE_SIGNALS):
        evidence.append("cognitive_signal")
        return AuthorityNode(name, "cognitive", DEFAULT_POLICY["cognitive"], evidence, 0.85)
    if any(s in text for s in EXECUTION_SIGNALS):
        evidence.append("execution_signal")
        return AuthorityNode(name, "execution", DEFAULT_POLICY["execution"], evidence, 0.8)
    if "memory" in text or "store" in text:
        evidence.append("state_signal")
        return AuthorityNode(name, "state", DEFAULT_POLICY["state"], evidence, 0.75)
    if "ui" in text or "frontend" in text:
        evidence.append("presentation_signal")
        return AuthorityNode(name, "presentation", DEFAULT_POLICY["presentation"], evidence, 0.7)
    return AuthorityNode(name, "unknown", DEFAULT_POLICY["unknown"], ["no_signal"], 0.2)
