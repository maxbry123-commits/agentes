"""Store de InputBlocks · literal · SHA-256 chain · TTL purge."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


class Criticality(str, Enum):
    ORDEN = "ORDEN"
    INFO = "INFO"
    CRITICO = "CRITICO"


@dataclass
class InputBlock:
    block_id: str
    seq: int
    content: str
    content_hash: str
    prev_hash: str
    chain_hash: str
    criticality: Criticality
    created_at: float
    expires_at: float
    mission_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["criticality"] = self.criticality.value
        return d

    @staticmethod
    def from_dict(d: MappingLike) -> "InputBlock":
        return InputBlock(
            block_id=str(d["block_id"]),
            seq=int(d["seq"]),
            content=str(d["content"]),
            content_hash=str(d["content_hash"]),
            prev_hash=str(d["prev_hash"]),
            chain_hash=str(d["chain_hash"]),
            criticality=Criticality(str(d["criticality"])),
            created_at=float(d["created_at"]),
            expires_at=float(d["expires_at"]),
            mission_id=d.get("mission_id"),
            meta=dict(d.get("meta") or {}),
        )


# typing alias without importing Mapping for older py
MappingLike = Dict[str, Any]


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _content_hash(content: str) -> str:
    return _sha256(content)


def _chain_hash(prev_hash: str, content_hash: str, seq: int) -> str:
    raw = f"{prev_hash}|{content_hash}|{seq}"
    return _sha256(raw)


GENESIS = "sha256:" + ("0" * 64)


class InputStore:
    """Store en memoria + opcional JSONL en disco."""

    def __init__(self, path: Path | None = None, default_ttl_sec: int = 86400 * 7) -> None:
        self._blocks: Dict[str, InputBlock] = {}
        self._order: List[str] = []
        self._path = path
        self.default_ttl_sec = default_ttl_sec
        self._seq = 0
        if path and path.is_file():
            self._load(path)

    def _load(self, path: Path) -> None:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            b = InputBlock.from_dict(json.loads(line))
            self._blocks[b.block_id] = b
            self._order.append(b.block_id)
            self._seq = max(self._seq, b.seq)

    def _persist(self, block: InputBlock) -> None:
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(block.to_dict(), ensure_ascii=False) + "\n")

    def last_chain_hash(self) -> str:
        if not self._order:
            return GENESIS
        return self._blocks[self._order[-1]].chain_hash

    def append(
        self,
        content: str,
        *,
        criticality: Criticality = Criticality.INFO,
        mission_id: str | None = None,
        ttl_sec: int | None = None,
        meta: dict[str, Any] | None = None,
    ) -> InputBlock:
        """Append literal. Nunca interpreta el contenido."""
        if content is None:
            raise ValueError("content_required")
        # literal: no strip de significado; solo normaliza fin de línea para hash estable
        literal = content if isinstance(content, str) else str(content)
        self._seq += 1
        seq = self._seq
        ch = _content_hash(literal)
        prev = self.last_chain_hash()
        chain = _chain_hash(prev, ch, seq)
        now = time.time()
        ttl = self.default_ttl_sec if ttl_sec is None else int(ttl_sec)
        block_id = f"ib_{seq:08d}_{hashlib.sha256(chain.encode()).hexdigest()[:8]}"
        block = InputBlock(
            block_id=block_id,
            seq=seq,
            content=literal,
            content_hash=ch,
            prev_hash=prev,
            chain_hash=chain,
            criticality=criticality,
            created_at=now,
            expires_at=now + ttl,
            mission_id=mission_id,
            meta=dict(meta or {}),
        )
        self._blocks[block_id] = block
        self._order.append(block_id)
        self._persist(block)
        return block

    def get(self, block_id: str) -> InputBlock | None:
        return self._blocks.get(block_id)

    def list_active(self, now: float | None = None) -> List[InputBlock]:
        t = time.time() if now is None else now
        return [self._blocks[i] for i in self._order if self._blocks[i].expires_at >= t]

    def purge_expired(self, now: float | None = None) -> int:
        t = time.time() if now is None else now
        removed = 0
        keep: List[str] = []
        for i in self._order:
            if self._blocks[i].expires_at < t:
                # no borrar CRITICO por TTL automático
                if self._blocks[i].criticality == Criticality.CRITICO:
                    keep.append(i)
                    continue
                del self._blocks[i]
                removed += 1
            else:
                keep.append(i)
        self._order = keep
        return removed

    def __iter__(self) -> Iterator[InputBlock]:
        for i in self._order:
            yield self._blocks[i]

    def __len__(self) -> int:
        return len(self._order)
