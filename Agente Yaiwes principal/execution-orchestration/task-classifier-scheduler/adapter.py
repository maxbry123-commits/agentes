from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Any


def _ensure_component_path() -> None:
    """Expose the vendored APScheduler package only when the adapter is invoked."""
    module_file = globals().get("__file__")
    if not module_file:
        return

    base = Path(module_file).resolve().parent
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))


def _symbols() -> tuple[type[Any], type[Any], type[Any]]:
    _ensure_component_path()
    module = import_module("apscheduler")
    return module.Scheduler, module.AsyncScheduler, module.TaskDefaults


def build_scheduler(*, async_mode: bool = False, **kwargs: Any) -> Any:
    """Create the YAIWES scheduler backend without starting it."""
    scheduler, async_scheduler, _ = _symbols()
    scheduler_cls = async_scheduler if async_mode else scheduler
    return scheduler_cls(**kwargs)


def build_task_defaults(**kwargs: Any) -> Any:
    """Create validated APScheduler task defaults for the orchestration layer."""
    _, _, task_defaults = _symbols()
    return task_defaults(**kwargs)


def capability() -> dict[str, Any]:
    """Deterministic capability declaration consumed by the YAIWES plugin layer."""
    return {
        "id": "yaiwes.scheduler.apscheduler",
        "classification": "B",
        "sync": True,
        "async": True,
        "side_effect_free_factory": True,
        "activation": "director_gate",
        "contract_inspection_safe": True,
    }
