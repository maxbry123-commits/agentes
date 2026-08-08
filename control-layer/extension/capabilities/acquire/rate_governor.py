"""GitHub Rate Governor · minimal.

Reads x-ratelimit-remaining / x-ratelimit-reset.
Backoff on 403/429. Caps concurrency. Configurable limits.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RateState:
    remaining: int = 5000
    limit: int = 5000
    reset_at: float = 0.0  # unix
    last_status: int = 200
    calls: int = 0


@dataclass
class RateGovernor:
    max_concurrent: int = 4
    min_remaining: int = 5  # pause if below
    max_calls: int = 0  # 0 = unlimited for mission
    _inflight: int = 0
    state: RateState = field(default_factory=RateState)

    def observe_headers(self, headers: dict[str, str] | Any, status: int = 200) -> None:
        def g(k: str) -> str | None:
            if hasattr(headers, "get"):
                return headers.get(k) or headers.get(k.lower())
            return None

        rem = g("X-RateLimit-Remaining") or g("x-ratelimit-remaining")
        lim = g("X-RateLimit-Limit") or g("x-ratelimit-limit")
        reset = g("X-RateLimit-Reset") or g("x-ratelimit-reset")
        if rem is not None:
            try:
                self.state.remaining = int(rem)
            except ValueError:
                pass
        if lim is not None:
            try:
                self.state.limit = int(lim)
            except ValueError:
                pass
        if reset is not None:
            try:
                self.state.reset_at = float(reset)
            except ValueError:
                pass
        self.state.last_status = status
        self.state.calls += 1

    def can_call(self) -> tuple[bool, str | None]:
        if self.max_calls and self.state.calls >= self.max_calls:
            return False, "max_api_calls"
        if self._inflight >= self.max_concurrent:
            return False, "max_concurrent"
        if self.state.remaining < self.min_remaining and self.state.reset_at > time.time():
            return False, "rate_limit_wait"
        return True, None

    def wait_if_needed(self, timeout: float = 60.0) -> bool:
        """Block briefly if rate-limited. Return False if still blocked after timeout."""
        ok, reason = self.can_call()
        if ok:
            return True
        if reason == "rate_limit_wait":
            delay = max(0.0, self.state.reset_at - time.time())
            delay = min(delay, timeout)
            if delay > 0:
                time.sleep(min(delay, 5.0))  # phase: cap sleep 5s per check
            return self.can_call()[0]
        if reason == "max_concurrent":
            time.sleep(0.05)
            return self.can_call()[0]
        return False

    def backoff_seconds(self, status: int) -> float:
        if status == 429:
            return min(30.0, 2.0 ** min(self.state.calls % 5, 4))
        if status == 403:
            return min(20.0, 1.5 ** min(self.state.calls % 5, 4))
        return 0.0

    def acquire_slot(self) -> bool:
        ok, _ = self.can_call()
        if not ok:
            if not self.wait_if_needed():
                return False
        self._inflight += 1
        return True

    def release_slot(self) -> None:
        self._inflight = max(0, self._inflight - 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "remaining": self.state.remaining,
            "limit": self.state.limit,
            "reset_at": self.state.reset_at,
            "calls": self.state.calls,
            "inflight": self._inflight,
            "max_concurrent": self.max_concurrent,
        }
