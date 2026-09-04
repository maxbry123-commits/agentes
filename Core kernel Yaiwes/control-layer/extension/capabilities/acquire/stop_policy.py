"""STOP_POLICY · budget limits · Phase 0.

If any limit exceeded → BUDGET_EXCEEDED (terminal).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .schema import StopPolicy


@dataclass
class BudgetUsage:
    nodes_used: int = 0
    bytes_downloaded: int = 0
    retries_used: int = 0
    api_calls_used: int = 0
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes_used": self.nodes_used,
            "bytes_downloaded": self.bytes_downloaded,
            "retries_used": self.retries_used,
            "api_calls_used": self.api_calls_used,
            "started_at": self.started_at,
            "elapsed_sec": time.time() - self.started_at,
        }

    @staticmethod
    def from_dict(d: dict[str, Any] | None) -> "BudgetUsage":
        d = d or {}
        u = BudgetUsage(
            nodes_used=int(d.get("nodes_used") or 0),
            bytes_downloaded=int(d.get("bytes_downloaded") or 0),
            retries_used=int(d.get("retries_used") or 0),
            api_calls_used=int(d.get("api_calls_used") or 0),
        )
        if "started_at" in d:
            u.started_at = float(d["started_at"])
        return u


class StopPolicyGuard:
    def __init__(self, policy: StopPolicy | dict[str, Any] | None = None) -> None:
        if isinstance(policy, dict):
            self.policy = StopPolicy.from_dict(policy)
        elif policy is None:
            self.policy = StopPolicy()
        else:
            self.policy = policy

    def exceeded(self, usage: BudgetUsage | dict[str, Any]) -> tuple[bool, str | None]:
        """Return (True, reason) if any limit is exceeded."""
        u = usage if isinstance(usage, BudgetUsage) else BudgetUsage.from_dict(usage)
        p = self.policy

        if p.max_nodes > 0 and u.nodes_used >= p.max_nodes:
            return True, f"max_nodes:{u.nodes_used}>={p.max_nodes}"

        elapsed = time.time() - u.started_at
        if p.max_wall_time_sec > 0 and elapsed >= p.max_wall_time_sec:
            return True, f"max_wall_time_sec:{elapsed:.1f}>={p.max_wall_time_sec}"

        if p.max_bytes_downloaded > 0 and u.bytes_downloaded >= p.max_bytes_downloaded:
            return True, f"max_bytes_downloaded:{u.bytes_downloaded}>={p.max_bytes_downloaded}"

        if p.max_retries_total > 0 and u.retries_used >= p.max_retries_total:
            return True, f"max_retries_total:{u.retries_used}>={p.max_retries_total}"

        if p.max_api_calls > 0 and u.api_calls_used >= p.max_api_calls:
            return True, f"max_api_calls:{u.api_calls_used}>={p.max_api_calls}"

        return False, None

    def remaining(self, usage: BudgetUsage | dict[str, Any]) -> dict[str, Any]:
        u = usage if isinstance(usage, BudgetUsage) else BudgetUsage.from_dict(usage)
        p = self.policy
        elapsed = time.time() - u.started_at
        return {
            "nodes": max(0, p.max_nodes - u.nodes_used) if p.max_nodes else None,
            "wall_time_sec": max(0.0, p.max_wall_time_sec - elapsed) if p.max_wall_time_sec else None,
            "bytes": max(0, p.max_bytes_downloaded - u.bytes_downloaded) if p.max_bytes_downloaded else None,
            "retries": max(0, p.max_retries_total - u.retries_used) if p.max_retries_total else None,
            "api_calls": max(0, p.max_api_calls - u.api_calls_used) if p.max_api_calls else None,
        }
