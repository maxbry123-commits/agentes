"""maxbry continuous work loop v2 — mount under Wordflow.

LLM access only via injected model adapter (Mock or GatewayModel in VL-02).
No direct OpenAI calls in production path.
"""
__version__ = "2.0.0"

from .models import Task, Goal, State, Event, now, uid
from .engine import Engine
from .model import MockModel

__all__ = [
    "Task",
    "Goal",
    "State",
    "Event",
    "Engine",
    "MockModel",
    "now",
    "uid",
]
