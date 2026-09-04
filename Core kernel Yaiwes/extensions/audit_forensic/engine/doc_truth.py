# -*- coding: utf-8 -*-
"""DocumentTruthStore — A-AUD-02. Design truth index. 0% LLM."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

REASON = {
    "DOC_NOT_IN_STORE": "DOC_NOT_IN_STORE",
    "SECTION_NOT_FOUND": "SECTION_NOT_FOUND",
    "DOC_SUPERSEDED": "DOC_SUPERSEDED",
    "SEED_MISSING": "SEED_MISSING",
    "YAML_REQUIRED": "YAML_REQUIRED",
}


class DocTruthError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _default_seed_path() -> Path:
    return Path(__file__).resolve().parents[1] / "store" / "document_truth_seed.yaml"


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DocumentTruthStore:
    """Index of project design documents used as law by the auditor."""

    def __init__(self, entries: list[dict[str, Any]] | None = None):
        self._by_id: dict[str, dict[str, Any]] = {}
        if entries:
            for e in entries:
                self.register(e)

    @classmethod
    def from_seed(
        cls,
        seed_path: Path | str | None = None,
        *,
        repo_root: Path | str | None = None,
    ) -> "DocumentTruthStore":
        if yaml is None:
            raise DocTruthError(REASON["YAML_REQUIRED"], "PyYAML not installed")
        path = Path(seed_path) if seed_path else _default_seed_path()
        if not path.is_file():
            raise DocTruthError(REASON["SEED_MISSING"], str(path))
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        docs = data.get("documents") or []
        store = cls()
        root = Path(repo_root) if repo_root else None
        for raw in docs:
            entry = dict(raw)
            entry.setdefault("status", "active")
            entry.setdefault("sections", [])
            entry.setdefault("version", None)
            if not entry.get("content_hash") and root and entry.get("path"):
                fpath = root / entry["path"]
                if fpath.is_file():
                    entry["content_hash"] = _hash_text(fpath.read_text(encoding="utf-8"))
            store.register(entry)
        return store

    def register(self, entry: dict[str, Any]) -> None:
        doc_id = entry.get("doc_id")
        if not doc_id:
            raise DocTruthError(REASON["DOC_NOT_IN_STORE"], "missing doc_id")
        self._by_id[str(doc_id)] = {
            "doc_id": str(doc_id),
            "path": entry.get("path") or "",
            "content_hash": entry.get("content_hash"),
            "version": entry.get("version"),
            "sections": list(entry.get("sections") or []),
            "status": entry.get("status") or "active",
        }

    def get(self, doc_id: str) -> dict[str, Any] | None:
        return self._by_id.get(doc_id)

    def has(self, doc_id: str) -> bool:
        return doc_id in self._by_id

    def active_ids(self) -> list[str]:
        return [k for k, v in self._by_id.items() if v.get("status") == "active"]

    def resolve_anchor(self, anchor: dict[str, Any]) -> dict[str, Any]:
        """Validate a doc_anchor against the store.

        Returns {ok, doc_id, section, status, reason_code?}.
        """
        doc_id = (anchor or {}).get("doc_id")
        if not doc_id or not self.has(doc_id):
            return {
                "ok": False,
                "doc_id": doc_id,
                "reason_code": REASON["DOC_NOT_IN_STORE"],
            }
        entry = self._by_id[doc_id]
        if entry.get("status") == "superseded":
            return {
                "ok": False,
                "doc_id": doc_id,
                "reason_code": REASON["DOC_SUPERSEDED"],
            }
        section = anchor.get("section")
        if section:
            ids = {s.get("id") for s in entry.get("sections") or []}
            if section not in ids:
                return {
                    "ok": False,
                    "doc_id": doc_id,
                    "section": section,
                    "reason_code": REASON["SECTION_NOT_FOUND"],
                }
        return {
            "ok": True,
            "doc_id": doc_id,
            "section": section,
            "path": entry.get("path"),
            "status": entry.get("status"),
            "content_hash": entry.get("content_hash"),
        }

    def resolve_anchors(self, anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.resolve_anchor(a) for a in (anchors or [])]

    def all_entries(self) -> list[dict[str, Any]]:
        return list(self._by_id.values())

    def __len__(self) -> int:
        return len(self._by_id)
