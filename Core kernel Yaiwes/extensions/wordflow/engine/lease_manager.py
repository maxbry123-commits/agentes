# -*- coding: utf-8 -*-
"""LeaseManager — T17. TTL leases for tasks/sandboxes. 0% LLM."""
from __future__ import annotations

import time
import uuid
from typing import Any


class LeaseError(Exception):
    pass


class LeaseManager:
    """Issue/renew/expire leases. Uses monotonic clock (injectable for tests)."""

    def __init__(self, default_ttl_s: float = 60.0, *,
                 clock: Any = None):
        if default_ttl_s <= 0:
            raise ValueError("default_ttl_s > 0")
        self.default_ttl_s = float(default_ttl_s)
        self._clock = clock or time.monotonic
        self._leases: dict[str, dict[str, Any]] = {}

    def _now(self) -> float:
        return float(self._clock())

    def issue(
        self,
        *,
        subject_id: str,
        subject_kind: str = "task",
        ttl_s: float | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not subject_id:
            raise LeaseError("subject_id required")
        ttl = float(ttl_s if ttl_s is not None else self.default_ttl_s)
        if ttl <= 0:
            raise LeaseError("ttl_s > 0")
        now = self._now()
        lease = {
            "lease_id": f"lease_{uuid.uuid4().hex[:12]}",
            "subject_id": subject_id,
            "subject_kind": subject_kind,
            "issued_at": now,
            "expires_at": now + ttl,
            "ttl_s": ttl,
            "status": "ACTIVE",
            "meta": dict(meta or {}),
        }
        self._leases[lease["lease_id"]] = lease
        return dict(lease)

    def renew(self, lease_id: str, *,
              ttl_s: float | None = None) -> dict[str, Any]:
        lease = self._require(lease_id)
        self._expire_if_needed(lease)
        if lease["status"] != "ACTIVE":
            raise LeaseError(f"lease not ACTIVE: {lease['status']}")
        ttl = float(ttl_s if ttl_s is not None else lease["ttl_s"])
        now = self._now()
        lease["expires_at"] = now + ttl
        lease["ttl_s"] = ttl
        return dict(lease)

    def is_alive(self, lease_id: str) -> bool:
        lease = self._leases.get(lease_id)
        if lease is None:
            return False
        self._expire_if_needed(lease)
        return lease["status"] == "ACTIVE"

    def release(self, lease_id: str) -> dict[str, Any]:
        lease = self._require(lease_id)
        lease["status"] = "RELEASED"
        return dict(lease)

    def sweep_expired(self) -> list[str]:
        expired: list[str] = []
        for lid, lease in list(self._leases.items()):
            if lease["status"] == "ACTIVE":
                self._expire_if_needed(lease)
                if lease["status"] == "EXPIRED":
                    expired.append(lid)
        return expired

    def get(self, lease_id: str) -> dict[str, Any] | None:
        lease = self._leases.get(lease_id)
        if lease is None:
            return None
        self._expire_if_needed(lease)
        return dict(lease)

    def _expire_if_needed(self, lease: dict[str, Any]) -> None:
        if lease["status"] == "ACTIVE" and self._now() >= lease["expires_at"]:
            lease["status"] = "EXPIRED"

    def _require(self, lease_id: str) -> dict[str, Any]:
        lease = self._leases.get(lease_id)
        if lease is None:
            raise LeaseError(f"unknown lease {lease_id}")
        return lease
