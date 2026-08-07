"""Authority Graph."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

CONTROL = ("agent_loop", "mission", "spawn", "scheduler", "orchestrat", "allocate", "terminate")
COGNITIVE = ("generate", "analyze_code", "reason", "review", "plan_edit", "llm", "complete", "chat")
EXECUTION = ("subprocess", "filesystem", "git", "terminal", "browser", "http", "docker", "run_cmd")
STATE = ("memory", "store", "cache", "session", "db", "sqlite")
PRESENTATION = ("ui", "frontend", "render", "dashboard")
DEFAULT_ACTION = {"cognitive": "preserve", "execution": "adapt", "control": "subordinate", "state": "adapt", "presentation": "isolate", "unknown": "adapt"}

@dataclass
class AuthorityEdge:
    component: str
    authority: str
    action: str
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    certainty: str = "CERTAIN"
    def to_dict(self): return asdict(self)

def classify_component(name, calls=None, side_effects=None):
    text = " ".join([name] + list(calls or []) + list(side_effects or [])).lower()
    if any(t in text for t in CONTROL):
        return AuthorityEdge(name, "control", DEFAULT_ACTION["control"], ["control_token"], 0.9, "CERTAIN")
    if any(t in text for t in COGNITIVE):
        return AuthorityEdge(name, "cognitive", DEFAULT_ACTION["cognitive"], ["cognitive_token"], 0.85, "CERTAIN")
    if any(t in text for t in EXECUTION) or any(s in (side_effects or []) for s in ("subprocess", "filesystem", "network")):
        return AuthorityEdge(name, "execution", DEFAULT_ACTION["execution"], ["execution_token"], 0.8, "CERTAIN")
    if any(t in text for t in STATE):
        return AuthorityEdge(name, "state", DEFAULT_ACTION["state"], ["state_token"], 0.75, "CERTAIN")
    if any(t in text for t in PRESENTATION):
        return AuthorityEdge(name, "presentation", DEFAULT_ACTION["presentation"], ["presentation_token"], 0.7, "CERTAIN")
    return AuthorityEdge(name, "unknown", DEFAULT_ACTION["unknown"], ["no_signal"], 0.2, "UNKNOWN")

def build_authority_graph(components):
    return [classify_component(str(c.get("name") or ""), list(c.get("calls") or c.get("methods") or []), list(c.get("side_effects") or [])) for c in components]
