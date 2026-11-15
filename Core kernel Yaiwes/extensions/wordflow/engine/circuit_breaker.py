# -*- coding: utf-8 -*-
"""CircuitBreaker — T19. CLOSED / OPEN / HALF_OPEN. 0% LLM."""
from __future__ import annotations

import time
from typing import Any, Callable


class CircuitOpenError(Exception):
    def __init__(self, name: str, retry_at: float):
        self.name = name
        self.retry_at = retry_at
        super().__init__(f"circuit open: {name}")


class CircuitBreaker:
    """Classic breaker. clock injectable for tests."""

    def __init__(
        self,
        name: str = "default",
        *,
        failure_threshold: int = 3,
        recovery_timeout_s: float = 30.0,
        success_threshold: int = 1,
        clock: Any = None,
    ):
        if failure_threshold < 1:
            raise ValueError("failure_threshold >= 1")
        if recovery_timeout_s <= 0:
            raise ValueError("recovery_timeout_s > 0")
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = float(recovery_timeout_s)
        self.success_threshold = max(1, success_threshold)
        self._clock = clock or time.monotonic
        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        self.opened_at: float | None = None

    def _now(self) -> float:
        return float(self._clock())

    def allow(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            assert self.opened_at is not None
            if self._now() - self.opened_at >= self.recovery_timeout_s:
                self.state = "HALF_OPEN"
                self.success_count = 0
                return True
            return False
        # HALF_OPEN: allow probe
        return True

    def record_success(self) -> None:
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                self.failure_count = 0
                self.opened_at = None
        elif self.state == "CLOSED":
            self.failure_count = 0

    def record_failure(self) -> None:
        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.opened_at = self._now()
            self.failure_count = self.failure_threshold
            self.success_count = 0
            return
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.opened_at = self._now()

    def call(self, fn: Callable[[], Any]) -> Any:
        if not self.allow():
            retry_at = (self.opened_at or 0) + self.recovery_timeout_s
            raise CircuitOpenError(self.name, retry_at)
        try:
            result = fn()
        except Exception:
            self.record_failure()
            raise
        self.record_success()
        return result

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "opened_at": self.opened_at,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_s": self.recovery_timeout_s,
        }
