# -*- coding: utf-8 -*-
"""RetryPolicy — T21. Deterministic backoff. 0% LLM."""
from __future__ import annotations

from typing import Any, Callable


class RetryExhaustedError(Exception):
    def __init__(self, attempts: int, last_error: Exception | None):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"retry exhausted after {attempts} attempts")


class RetryPolicy:
    """fixed | linear | exponential backoff. No jitter (determinism)."""

    def __init__(
        self,
        *,
        max_attempts: int = 3,
        strategy: str = "exponential",
        base_delay_s: float = 1.0,
        max_delay_s: float = 60.0,
        retry_on: tuple[type[Exception], ...] = (Exception,),
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts >= 1")
        if strategy not in ("fixed", "linear", "exponential"):
            raise ValueError("strategy fixed|linear|exponential")
        self.max_attempts = max_attempts
        self.strategy = strategy
        self.base_delay_s = float(base_delay_s)
        self.max_delay_s = float(max_delay_s)
        self.retry_on = retry_on

    def delay_for_attempt(self, attempt: int) -> float:
        """attempt is 1-based index of the failure that just occurred."""
        if attempt < 1:
            return 0.0
        if self.strategy == "fixed":
            d = self.base_delay_s
        elif self.strategy == "linear":
            d = self.base_delay_s * attempt
        else:
            d = self.base_delay_s * (2 ** (attempt - 1))
        return min(d, self.max_delay_s)

    def run(
        self,
        fn: Callable[[], Any],
        *,
        sleeper: Callable[[float], None] | None = None,
    ) -> Any:
        """Execute fn with retries. sleeper injectable (default no-op for tests)."""
        sleep = sleeper or (lambda _d: None)
        last_err: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return fn()
            except self.retry_on as exc:
                last_err = exc
                if attempt >= self.max_attempts:
                    break
                sleep(self.delay_for_attempt(attempt))
            except Exception:
                raise
        raise RetryExhaustedError(self.max_attempts, last_err)

    def plan(self) -> list[dict[str, Any]]:
        """List of planned delays after each failure before final attempt."""
        return [
            {"after_attempt": i, "delay_s": self.delay_for_attempt(i)}
            for i in range(1, self.max_attempts)
        ]
