"""Idle Detector — monitors user activity to determine when system is idle."""

from __future__ import annotations

import time

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

__all__ = ["IdleDetector"]


class IdleDetector:
    """Tracks user activity. Reports idle when no activity for threshold seconds."""

    def __init__(self, idle_threshold_seconds: int = 300) -> None:
        self._last_activity = time.time()
        self._threshold = idle_threshold_seconds

    def notify_activity(self) -> None:
        """Called on every user message or interaction."""
        self._last_activity = time.time()

    @property
    def is_idle(self) -> bool:
        """True if no activity for threshold seconds."""
        return (time.time() - self._last_activity) >= self._threshold

    @property
    def idle_seconds(self) -> float:
        """Seconds since last activity."""
        return max(0.0, time.time() - self._last_activity)

    @property
    def last_activity_at(self) -> float:
        """Timestamp of last activity."""
        return self._last_activity
