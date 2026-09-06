from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_BASE = Path(__file__).resolve().parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

from apscheduler import AsyncScheduler, Scheduler, TaskDefaults  # noqa: E402


def build_scheduler(*, async_mode: bool = False, **kwargs: Any) -> Scheduler | AsyncScheduler:
    """Create the YAIWES scheduler backend without starting it."""
    scheduler_cls = AsyncScheduler if async_mode else Scheduler
    return scheduler_cls(**kwargs)


def build_task_defaults(**kwargs: Any) -> TaskDefaults:
    """Create validated APScheduler task defaults for the orchestration layer."""
    return TaskDefaults(**kwargs)


def capability() -> dict[str, Any]:
    """Deterministic capability declaration consumed by the YAIWES plugin layer."""
    return {
        "id": "yaiwes.scheduler.apscheduler",
        "classification": "B",
        "sync": True,
        "async": True,
        "side_effect_free_factory": True,
        "activation": "director_gate",
    }
