"""Reader · verifica hash chain · no interpreta contenido."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .store import GENESIS, InputBlock, InputStore, _chain_hash, _content_hash


class ChainBrokenError(Exception):
    def __init__(self, seq: int, detail: str):
        self.seq = seq
        super().__init__(f"chain_broken_at_seq_{seq}: {detail}")


@dataclass(frozen=True)
class ChainReport:
    ok: bool
    length: int
    tip_hash: str
    errors: tuple[str, ...]


class InputBlockReader:
    def __init__(self, store: InputStore) -> None:
        self.store = store

    def verify_chain(self) -> ChainReport:
        errors: List[str] = []
        prev = GENESIS
        last_hash = GENESIS
        for block in self.store:
            expected_content = _content_hash(block.content)
            if block.content_hash != expected_content:
                errors.append(f"content_hash_mismatch_seq_{block.seq}")
            if block.prev_hash != prev:
                errors.append(f"prev_hash_mismatch_seq_{block.seq}")
            expected_chain = _chain_hash(block.prev_hash, block.content_hash, block.seq)
            if block.chain_hash != expected_chain:
                errors.append(f"chain_hash_mismatch_seq_{block.seq}")
            prev = block.chain_hash
            last_hash = block.chain_hash
        return ChainReport(
            ok=len(errors) == 0,
            length=len(self.store),
            tip_hash=last_hash,
            errors=tuple(errors),
        )

    def verify_or_raise(self) -> ChainReport:
        report = self.verify_chain()
        if not report.ok:
            raise ChainBrokenError(report.length, "; ".join(report.errors))
        return report

    def read_literal(self, block_id: str) -> str:
        b = self.store.get(block_id)
        if b is None:
            raise KeyError(block_id)
        return b.content  # literal, sin transform

    def read_mission_literals(self, mission_id: str) -> list[str]:
        return [b.content for b in self.store if b.mission_id == mission_id]
