"""Lease backends — in-process + optional Redis · 0% LLM
SOURCE: P1 multi-worker ready
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

from loops.lease import Lease


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LeaseBackend(ABC):
    @abstractmethod
    def acquire(self, run_id: str, owner: str, ttl_seg: int) -> Lease | None: ...

    @abstractmethod
    def renew(self, run_id: str, owner: str, ttl_seg: int) -> bool: ...

    @abstractmethod
    def release(self, run_id: str, owner: str) -> bool: ...

    @abstractmethod
    def reclaim_expired(self) -> list[str]: ...


class InProcessLeaseBackend(LeaseBackend):
    def __init__(self) -> None:
        self._leases: dict[str, Lease] = {}

    def acquire(self, run_id: str, owner: str, ttl_seg: int) -> Lease | None:
        now = _now()
        existing = self._leases.get(run_id)
        if existing and existing.alive(now) and existing.owner != owner:
            return None
        lease = Lease(run_id=run_id, owner=owner, expires_at=now + timedelta(seconds=ttl_seg))
        self._leases[run_id] = lease
        return lease

    def renew(self, run_id: str, owner: str, ttl_seg: int) -> bool:
        lease = self._leases.get(run_id)
        if not lease or lease.owner != owner or not lease.alive():
            return False
        lease.expires_at = _now() + timedelta(seconds=ttl_seg)
        return True

    def release(self, run_id: str, owner: str) -> bool:
        lease = self._leases.get(run_id)
        if not lease or lease.owner != owner:
            return False
        del self._leases[run_id]
        return True

    def reclaim_expired(self) -> list[str]:
        now = _now()
        dead = [rid for rid, l in self._leases.items() if not l.alive(now)]
        for rid in dead:
            self._leases.pop(rid, None)
        return dead


class RedisLeaseBackend(LeaseBackend):
    """Opcional: requiere redis-py. Key lease:{run_id} → owner, TTL nativo."""

    def __init__(self, redis_client: Any, prefix: str = "loop:lease:") -> None:
        self.r = redis_client
        self.prefix = prefix

    def _key(self, run_id: str) -> str:
        return f"{self.prefix}{run_id}"

    def acquire(self, run_id: str, owner: str, ttl_seg: int) -> Lease | None:
        key = self._key(run_id)
        ok = self.r.set(key, owner, nx=True, ex=ttl_seg)
        if not ok:
            current = self.r.get(key)
            if current and current.decode() == owner:
                self.r.expire(key, ttl_seg)
            else:
                return None
        return Lease(run_id=run_id, owner=owner, expires_at=_now() + timedelta(seconds=ttl_seg))

    def renew(self, run_id: str, owner: str, ttl_seg: int) -> bool:
        key = self._key(run_id)
        current = self.r.get(key)
        if not current or current.decode() != owner:
            return False
        return bool(self.r.expire(key, ttl_seg))

    def release(self, run_id: str, owner: str) -> bool:
        key = self._key(run_id)
        current = self.r.get(key)
        if not current or current.decode() != owner:
            return False
        self.r.delete(key)
        return True

    def reclaim_expired(self) -> list[str]:
        # Redis TTL auto-expires; nothing to reclaim locally
        return []
