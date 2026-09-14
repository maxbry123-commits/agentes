"""Fixed-size rolling event log for support diagnostics."""

from __future__ import annotations

import threading
import time
from collections import deque

P_MAX_SIZE = 50
p_lock = threading.Lock()
p_buffer: deque[dict] = deque(maxlen=P_MAX_SIZE)


def record(label: str, **meta: str | int | float | None) -> None:
    """Append an entry. Oldest drops when full."""
    with p_lock:
        p_buffer.append({
            "l": label,
            "t": time.time(),
            **{k: v for k, v in meta.items() if v is not None},
        })


def snapshot() -> list[dict]:
    """Return a copy of the current buffer, oldest first."""
    with p_lock:
        return list(p_buffer)


def clear() -> None:
    with p_lock:
        p_buffer.clear()
