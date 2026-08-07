"""Loop Lease — ownership temporal in-process · 0% LLM
SOURCE: Fase 4 · base para workers distribuidos
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Lease:
    run_id: str
    owner: str
    expires_at: datetime

    def alive(self, now: datetime | None = None) -> bool:
        return (now or _now()) < self.expires_at


class LeaseManager:
    def __init__(self, default_ttl_seg: int = 30) -> None:
        self.default_ttl = default_ttl_seg
        self._leases: dict[str, Lease] = {}

    def acquire(self, run_id: str, owner: str, ttl_seg: int | None = None) -> Lease | None:
        now = _now()
        existing = self._leases.get(run_id)
        if existing and existing.alive(now) and existing.owner != owner:
            return None  # held by another
        lease = Lease(
            run_id=run_id,
            owner=owner,
            expires_at=now + timedelta(seconds=ttl_seg or self.default_ttl),
        )
        self._leases[run_id] = lease
        return lease

    def renew(self, run_id: str, owner: str, ttl_seg: int | None = None) -> bool:
        lease = self._leases.get(run_id)
        if not lease or lease.owner != owner:
            return False
        if not lease.alive():
            return False
        lease.expires_at = _now() + timedelta(seconds=ttl_seg or self.default_ttl)
        return True

    def release(self, run_id: str, owner: str) -> bool:
        lease = self._leases.get(run_id)
        if not lease or lease.owner != owner:
            return False
        del self._leases[run_id]
        return True

    def expired(self) -> list[str]:
        now = _now()
        return [rid for rid, l in self._leases.items() if not l.alive(now)]

    def reclaim_expired(self) -> list[str]:
        dead = self.expired()
        for rid in dead:
            self._leases.pop(rid, None)
        return dead
