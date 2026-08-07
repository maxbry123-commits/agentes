"""Tests A04 · Sentinela activa procesos y bloquea quarantine+secret."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contract_engine.sentinela_router import route


def test_read_local_has_plan():
    d = route(op_type="READ_LOCAL", payload={"path": "x.md"}, strict_reverse=False)
    assert d.band == "normal"
    assert d.block_execution is False
    assert len(d.active_contracts) >= 1
    assert isinstance(d.process_plan, tuple)


def test_secret_write_blocks_and_activates_credential_gate():
    d = route(
        op_type="WRITE_LOCAL",
        payload={"content": "api_key=sk-live"},
        strict_reverse=True,
    )
    assert d.suggested_op_type == "CREDENTIAL_ACCESS"
    assert "C47" in d.active_contracts
    assert "credential_gate" in d.process_plan
    assert d.sheriff_required is True
    assert d.block_execution is True


def test_mount_mode_hint():
    d = route(op_type="EXTENSION_MOUNT", strict_reverse=False, mount_mode="extension")
    assert d.mode_hint == "extension"
    assert "C00" in d.active_contracts or "C82" in d.active_contracts


if __name__ == "__main__":
    test_read_local_has_plan()
    test_secret_write_blocks_and_activates_credential_gate()
    test_mount_mode_hint()
    print("A04 tests OK")
