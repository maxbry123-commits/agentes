"""_safe_call — wraps optional subsystem initialisation with structured failure tracking.

Usage:
    result = _safe_call("hashline_guard", hashline_guard.init, config)

Any exception is caught, logged at WARNING level, and counted in
_FAILURE_REGISTRY. The registry is exposed via ``get_failure_report()``
and surfaced by ``cognithor doctor --health``.
"""

from __future__ import annotations

import logging
import threading
import traceback
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

_FAILURE_REGISTRY: dict[str, list[str]] = {}
_lock = threading.Lock()


def _safe_call(name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any | None:
    """Call *fn*. On exception: log WARNING, record in registry, return None."""
    try:
        return fn(*args, **kwargs)
    except Exception:
        tb = traceback.format_exc()
        logger.warning(
            "Optional subsystem '%s' failed to initialise:\n%s",
            name,
            tb,
        )
        with _lock:
            _FAILURE_REGISTRY.setdefault(name, []).append(tb)
        return None


async def _safe_call_async(
    name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any
) -> Any | None:
    """Async variant of ``_safe_call``."""
    try:
        return await fn(*args, **kwargs)
    except Exception:
        tb = traceback.format_exc()
        logger.warning(
            "Optional subsystem '%s' failed to initialise:\n%s",
            name,
            tb,
        )
        with _lock:
            _FAILURE_REGISTRY.setdefault(name, []).append(tb)
        return None


def get_failure_report() -> dict[str, list[str]]:
    """Return a snapshot of all recorded failures, keyed by subsystem name."""
    with _lock:
        return dict(_FAILURE_REGISTRY)


def has_failures() -> bool:
    """Return True if any subsystem has a non-zero failure count."""
    with _lock:
        return bool(_FAILURE_REGISTRY)


def clear_failures() -> None:
    """Clear all recorded failures (for testing)."""
    with _lock:
        _FAILURE_REGISTRY.clear()
