# -*- coding: utf-8 -*-
"""ResourceCatalog + HF index stub — T9. Local only. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

ALLOWED_KINDS = frozenset({"skill", "dataset", "adapter", "model", "tool", "other"})
ALLOWED_SOURCES = frozenset({"local", "github", "hf", "url", "other"})


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _entry_body(e: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": e["schema_version"],
        "resource_id": e["resource_id"],
        "name": e["name"],
        "kind": e["kind"],
        "source": e["source"],
        "ref": e.get("ref"),
        "pin_id": e.get("pin_id"),
        "content_sha256": e.get("content_sha256"),
        "tags": list(e.get("tags") or []),
        "size_hint_bytes": e.get("size_hint_bytes"),
        "fetchable": bool(e.get("fetchable")),
    }


def make_entry(
    *,
    name: str,
    kind: str,
    source: str = "local",
    ref: str | None = None,
    pin_id: str | None = None,
    content_sha256: str | None = None,
    tags: list[str] | None = None,
    size_hint_bytes: int | None = None,
    fetchable: bool = False,
    resource_id: str | None = None,
) -> dict[str, Any]:
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"invalid kind={kind}")
    if source not in ALLOWED_SOURCES:
        raise ValueError(f"invalid source={source}")
    # Policy WAVE-0/2: remote sources not fetchable until post-Wordflow
    if source in ("hf", "github", "url") and fetchable:
        raise ValueError("fetchable=True forbidden for remote sources until post-Wordflow")

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "resource_id": resource_id or f"res_{uuid.uuid4().hex[:12]}",
        "name": name,
        "kind": kind,
        "source": source,
        "ref": ref,
        "pin_id": pin_id,
        "content_sha256": content_sha256,
        "tags": list(tags or []),
        "size_hint_bytes": size_hint_bytes,
        "fetchable": False if source != "local" else bool(fetchable),
    }
    if source == "local":
        body["fetchable"] = bool(fetchable)
    else:
        body["fetchable"] = False
    body["entry_hash"] = _hash(_entry_body(body))
    return body


def verify_entry(entry: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(entry, dict):
        return {"ok": False, "reason": "INVALID_ENTRY"}
    expected = _hash(_entry_body(entry))
    if entry.get("entry_hash") != expected:
        return {"ok": False, "reason": "ENTRY_HASH_MISMATCH"}
    return {"ok": True, "reason": "ENTRY_OK", "resource_id": entry.get("resource_id")}


class ResourceCatalog:
    """In-memory + optional JSON index. No network."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._by_id: dict[str, dict[str, Any]] = {}
        if self.path and self.path.exists():
            self._load()

    def _load(self) -> None:
        assert self.path is not None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        for e in data.get("entries") or []:
            self._by_id[e["resource_id"]] = e

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "entries": list(self._by_id.values()),
        }
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def add(self, entry: dict[str, Any]) -> dict[str, Any]:
        v = verify_entry(entry)
        if not v["ok"]:
            raise ValueError(v["reason"])
        self._by_id[entry["resource_id"]] = entry
        return entry

    def get(self, resource_id: str) -> dict[str, Any] | None:
        return self._by_id.get(resource_id)

    def list(
        self,
        *,
        kind: str | None = None,
        source: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        out = list(self._by_id.values())
        if kind:
            out = [e for e in out if e.get("kind") == kind]
        if source:
            out = [e for e in out if e.get("source") == source]
        if tag:
            out = [e for e in out if tag in (e.get("tags") or [])]
        return out

    def search_name(self, query: str) -> list[dict[str, Any]]:
        q = (query or "").lower()
        return [e for e in self._by_id.values() if q in (e.get("name") or "").lower()]


def seed_hf_index_stub() -> list[dict[str, Any]]:
    """Example HF-oriented index rows — fetchable always False."""
    return [
        make_entry(
            name="example-skill-pack",
            kind="skill",
            source="hf",
            ref="hf://org/example-skill-pack",
            tags=["skill", "stub"],
            fetchable=False,
        ),
        make_entry(
            name="example-dataset",
            kind="dataset",
            source="hf",
            ref="hf://org/example-dataset",
            tags=["dataset", "stub"],
            size_hint_bytes=10_000_000,
            fetchable=False,
        ),
        make_entry(
            name="example-adapter",
            kind="adapter",
            source="hf",
            ref="hf://org/example-adapter",
            tags=["adapter", "stub"],
            fetchable=False,
        ),
    ]
