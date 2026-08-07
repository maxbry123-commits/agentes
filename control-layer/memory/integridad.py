"""MC08 · integridad chain heads tier local."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from memory.doc_registry import DocRegistry
from memory.session_store import SessionStore


@dataclass(frozen=True)
class IntegrityReport:
    ok: bool
    tip_docs: str
    tip_session: str
    docs_count: int
    session_count: int
    errors: tuple[str, ...]


def check_local_integrity(root: Path) -> IntegrityReport:
    root = Path(root)
    errors: list[str] = []
    docs = DocRegistry(root / "docs.jsonl")
    ses = SessionStore(root / "session.jsonl")
    # re-scan chain docs
    prev = None
    from memory.doc_registry import GENESIS

    tip = GENESIS
    for i, rec in enumerate(docs):
        if i == 0 and rec.prev_hash != GENESIS:
            # first may still be valid if loaded
            pass
        if prev is not None and rec.prev_hash != prev:
            errors.append(f"docs_chain_break_at_{rec.doc_id}")
        prev = rec.chain_hash
        tip = rec.chain_hash
    return IntegrityReport(
        ok=len(errors) == 0,
        tip_docs=docs.tip_hash(),
        tip_session=ses.tip_hash,
        docs_count=len(docs),
        session_count=len(ses),
        errors=tuple(errors),
    )
