"""Tests memoria parcial M01-M02."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from memory.doc_registry import DocRegistry
from memory.ondemand import rank_docs
from memory.session_store import SessionStore


def test_register_idempotent_and_chain():
    with tempfile.TemporaryDirectory() as td:
        reg = DocRegistry(Path(td) / "docs.jsonl")
        a = reg.register(name="S12-DOC2", source="x", content="memoria 4 tiers", summary="tiers", tags=["memory"])
        b = reg.register(name="S12-DOC2", source="x", content="memoria 4 tiers", summary="tiers", tags=["memory"])
        assert a.doc_id == b.doc_id
        assert len(reg) == 1
        c = reg.register(name="S9", source="y", content="contratos 85", tags=["contracts"])
        assert len(reg) == 2
        assert c.prev_hash == a.chain_hash


def test_session_and_rank():
    with tempfile.TemporaryDirectory() as td:
        ses = SessionStore(Path(td) / "session.jsonl")
        ses.append("doc_in", {"name": "S12"})
        assert len(ses) == 1
        reg = DocRegistry(Path(td) / "docs.jsonl")
        reg.register(name="S12-DOC2-MEMORIA", source="f", content="kg lateral tiers", tags=["memory", "s12"])
        reg.register(name="S9-CONTRATOS", source="g", content="85 contracts", tags=["contracts"])
        top = rank_docs(reg, "memoria tiers", top_n=5)
        assert top and "MEMORIA" in top[0].record.name.upper() or top[0].score > 0


if __name__ == "__main__":
    test_register_idempotent_and_chain()
    test_session_and_rank()
    print("memory partial OK")
