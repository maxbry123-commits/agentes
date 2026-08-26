# -*- coding: utf-8 -*-
"""HF ResourceIndex — T35. Index only; no download. 0% LLM.

Storage on HF (1TB); GitHub keeps index. fetchable default False until
microkernel + HF compute online (PIPELINE/32).
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any


def make_hf_entry(
    *,
    kind: str,
    hf_id: str,
    name: str | None = None,
    revision: str | None = None,
    fetchable: bool = False,
    size_hint_mb: float | None = None,
    contract_schema: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rid = f"hf_{kind}_{uuid.uuid4().hex[:10]}"
    return {
        "resource_id": rid,
        "kind": kind,
        "hf_id": hf_id,
        "name": name or hf_id,
        "revision": revision,
        "fetchable": bool(fetchable),
        "size_hint_mb": size_hint_mb,
        "contract_schema": contract_schema,
        "meta": dict(meta or {}),
        "source": "huggingface",
    }


class HFResourceIndex:
    """In-memory + optional JSON index. Never downloads blobs."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._by_id: dict[str, dict[str, Any]] = {}
        if self.path and self.path.is_file():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for e in data.get("entries") or []:
                self._by_id[e["resource_id"]] = e

    def register(self, entry: dict[str, Any]) -> dict[str, Any]:
        if not entry.get("resource_id") or not entry.get("hf_id"):
            raise ValueError("resource_id and hf_id required")
        # force safe default until post-Wordflow
        e = dict(entry)
        if e.get("fetchable") is None:
            e["fetchable"] = False
        self._by_id[e["resource_id"]] = e
        return dict(e)

    def get(self, resource_id: str) -> dict[str, Any] | None:
        e = self._by_id.get(resource_id)
        return dict(e) if e else None

    def find(
        self,
        *,
        kind: str | None = None,
        hf_id: str | None = None,
    ) -> list[dict[str, Any]]:
        out = []
        for e in self._by_id.values():
            if kind and e.get("kind") != kind:
                continue
            if hf_id and e.get("hf_id") != hf_id:
                continue
            out.append(dict(e))
        return out

    def request_fetch(self, resource_id: str) -> dict[str, Any]:
        """Plan fetch only — does not download."""
        e = self.get(resource_id)
        if not e:
            return {"ok": False, "reason": "NOT_FOUND"}
        if not e.get("fetchable"):
            return {
                "ok": False,
                "reason": "FETCH_DISABLED",
                "detail": "enable after HF compute + microkernel",
                "hf_id": e.get("hf_id"),
            }
        return {
            "ok": True,
            "action": "FETCH_PLANNED",
            "resource_id": resource_id,
            "hf_id": e["hf_id"],
            "revision": e.get("revision"),
            "note": "executor not attached",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "count": len(self._by_id),
            "entries": [dict(e) for e in self._by_id.values()],
        }
