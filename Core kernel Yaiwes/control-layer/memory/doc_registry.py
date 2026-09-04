"""Doc registry · Tier 3 parcial · append-only JSONL + chain.

Objetivo: no perder qué documentos se ingerieron entre 100+ docs.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

GENESIS = "sha256:" + ("0" * 64)


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class DocRecord:
    doc_id: str
    name: str
    source: str  # path o file_id
    content_hash: str
    prev_hash: str
    chain_hash: str
    registered_at: float
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "DocRecord":
        return DocRecord(
            doc_id=str(d["doc_id"]),
            name=str(d["name"]),
            source=str(d.get("source") or ""),
            content_hash=str(d["content_hash"]),
            prev_hash=str(d["prev_hash"]),
            chain_hash=str(d["chain_hash"]),
            registered_at=float(d["registered_at"]),
            summary=str(d.get("summary") or ""),
            tags=list(d.get("tags") or []),
            meta=dict(d.get("meta") or {}),
        )


class DocRegistry:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._by_id: Dict[str, DocRecord] = {}
        self._order: List[str] = []
        if self.path.is_file():
            self._load()

    def _load(self) -> None:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = DocRecord.from_dict(json.loads(line))
            self._by_id[rec.doc_id] = rec
            self._order.append(rec.doc_id)

    def tip_hash(self) -> str:
        if not self._order:
            return GENESIS
        return self._by_id[self._order[-1]].chain_hash

    def register(
        self,
        *,
        name: str,
        source: str,
        content: str,
        summary: str = "",
        tags: list[str] | None = None,
        meta: dict[str, Any] | None = None,
        doc_id: str | None = None,
    ) -> DocRecord:
        content_hash = _sha(content)
        # idempotente por content_hash+name
        for existing in self._by_id.values():
            if existing.content_hash == content_hash and existing.name == name:
                return existing

        prev = self.tip_hash()
        seq = len(self._order) + 1
        raw_id = doc_id or f"doc_{seq:04d}_{content_hash[7:15]}"
        chain = _sha(f"{prev}|{content_hash}|{raw_id}")
        rec = DocRecord(
            doc_id=raw_id,
            name=name,
            source=source,
            content_hash=content_hash,
            prev_hash=prev,
            chain_hash=chain,
            registered_at=time.time(),
            summary=summary[:500],
            tags=list(tags or []),
            meta=dict(meta or {}),
        )
        self._by_id[rec.doc_id] = rec
        self._order.append(rec.doc_id)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
        return rec

    def get(self, doc_id: str) -> DocRecord | None:
        return self._by_id.get(doc_id)

    def find_by_name(self, name: str) -> list[DocRecord]:
        return [r for r in self if r.name == name]

    def list_tags(self, tag: str) -> list[DocRecord]:
        return [r for r in self if tag in r.tags]

    def __iter__(self) -> Iterator[DocRecord]:
        for i in self._order:
            yield self._by_id[i]

    def __len__(self) -> int:
        return len(self._order)
