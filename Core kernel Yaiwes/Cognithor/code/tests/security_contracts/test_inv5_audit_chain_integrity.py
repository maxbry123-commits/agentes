"""INVARIANT 5 — Audit chain is append-only and tamper-evident.

Every tool call, every approval decision, every skill load must append
to the SHA-256 hash chain. The chain is unbroken and earlier entries
cannot be silently rewritten.
"""

from __future__ import annotations

import json

import pytest

from cognithor.models import GateStatus, RiskLevel
from cognithor.security.audit import AuditTrail, _compute_hash

from .conftest import make_audit_entry

pytestmark = pytest.mark.security_contract


# ---------------------------------------------------------------------------
# INV-5.1 — Genesis hash
# ---------------------------------------------------------------------------


def test_chain_genesis_hash(audit_trail: AuditTrail, audit_log_path):
    """First entry must chain from 'genesis'."""
    entry = make_audit_entry()
    audit_trail.record(entry)

    with open(audit_log_path, encoding="utf-8") as f:
        first = json.loads(f.readline())

    assert first["prev_hash"] == "genesis"


# ---------------------------------------------------------------------------
# INV-5.2 — Chain links correctly
# ---------------------------------------------------------------------------


def test_chain_links_correctly(audit_trail: AuditTrail, audit_log_path):
    """N entries must chain: each prev_hash == previous entry's hash."""
    for i in range(5):
        audit_trail.record(make_audit_entry(tool=f"tool_{i}"))

    entries = []
    with open(audit_log_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    assert len(entries) == 5
    assert entries[0]["prev_hash"] == "genesis"
    for i in range(1, len(entries)):
        assert entries[i]["prev_hash"] == entries[i - 1]["hash"], f"Entry {i} prev_hash mismatch"


# ---------------------------------------------------------------------------
# INV-5.3 — Detect modification
# ---------------------------------------------------------------------------


def test_verify_chain_detects_modification(audit_trail: AuditTrail, audit_log_path):
    """Mutating a middle entry must break verification."""
    for i in range(5):
        audit_trail.record(make_audit_entry(tool=f"tool_{i}"))

    lines = audit_log_path.read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[2])
    entry["action_tool"] = "TAMPERED"
    lines[2] = json.dumps(entry, ensure_ascii=False)
    audit_log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    fresh = AuditTrail(log_path=audit_log_path)
    valid, total, broken_at = fresh.verify_chain()
    assert not valid
    assert broken_at == 2


# ---------------------------------------------------------------------------
# INV-5.4 — Detect deletion
# ---------------------------------------------------------------------------


def test_verify_chain_detects_deletion(audit_trail: AuditTrail, audit_log_path):
    """Deleting an entry must break the chain at the next entry."""
    for i in range(5):
        audit_trail.record(make_audit_entry(tool=f"tool_{i}"))

    lines = audit_log_path.read_text(encoding="utf-8").splitlines()
    del lines[2]
    audit_log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    fresh = AuditTrail(log_path=audit_log_path)
    valid, _total, broken_at = fresh.verify_chain()
    assert not valid
    assert broken_at >= 2


# ---------------------------------------------------------------------------
# INV-5.5 — Detect insertion
# ---------------------------------------------------------------------------


def test_verify_chain_detects_insertion(audit_trail: AuditTrail, audit_log_path):
    """Inserting a fake entry must break the chain."""
    for i in range(3):
        audit_trail.record(make_audit_entry(tool=f"tool_{i}"))

    lines = audit_log_path.read_text(encoding="utf-8").splitlines()
    fake = json.dumps(
        {
            "timestamp": "2026-01-01T00:00:00+00:00",
            "session_id": "fake",
            "action_tool": "fake_tool",
            "action_params_hash": "0" * 64,
            "decision_status": "ALLOW",
            "decision_reason": "injected",
            "risk_level": "green",
            "policy_name": "",
            "user_override": False,
            "prev_hash": "fakehash",
            "hash": "fakehash2",
        }
    )
    lines.insert(1, fake)
    audit_log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    fresh = AuditTrail(log_path=audit_log_path)
    valid, _total, broken_at = fresh.verify_chain()
    assert not valid


# ---------------------------------------------------------------------------
# INV-5.6 — Detect reorder
# ---------------------------------------------------------------------------


def test_verify_chain_detects_reorder(audit_trail: AuditTrail, audit_log_path):
    """Swapping two entries must break the chain."""
    for i in range(4):
        audit_trail.record(make_audit_entry(tool=f"tool_{i}"))

    lines = audit_log_path.read_text(encoding="utf-8").splitlines()
    lines[1], lines[2] = lines[2], lines[1]
    audit_log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    fresh = AuditTrail(log_path=audit_log_path)
    valid, _total, broken_at = fresh.verify_chain()
    assert not valid


# ---------------------------------------------------------------------------
# INV-5.7 — Hash excludes meta fields
# ---------------------------------------------------------------------------


def test_hash_excludes_meta_fields(audit_trail: AuditTrail, audit_log_path):
    """prev_hash, hash, hmac, ed25519_sig must not be in the hash input."""
    audit_trail.record(make_audit_entry())

    with open(audit_log_path, encoding="utf-8") as f:
        entry = json.loads(f.readline())

    data_fields = {
        k: v for k, v in entry.items() if k not in ("prev_hash", "hash", "hmac", "ed25519_sig")
    }
    data_str = json.dumps(data_fields, ensure_ascii=False, sort_keys=True)
    expected = _compute_hash(data_str, "genesis")

    assert entry["hash"] == expected


# ---------------------------------------------------------------------------
# INV-5.8 — Empty chain is valid
# ---------------------------------------------------------------------------


def test_empty_chain_is_valid(tmp_path):
    """No entries means the chain is trivially valid."""
    trail = AuditTrail(log_path=tmp_path / "empty.jsonl")
    valid, total, broken_at = trail.verify_chain()
    assert valid
    assert total == 0
    assert broken_at == -1


# ---------------------------------------------------------------------------
# INV-5.9 — Concurrent writes maintain chain
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_writes_maintain_chain(tmp_path):
    """Sequential record() calls must maintain the chain even under rapid fire."""

    trail = AuditTrail(log_path=tmp_path / "concurrent.jsonl")

    async def write_entry(i: int):
        trail.record(make_audit_entry(tool=f"tool_{i}"))

    for i in range(20):
        await write_entry(i)

    valid, total, broken_at = trail.verify_chain()
    assert valid
    assert total == 20
    assert broken_at == -1


# ---------------------------------------------------------------------------
# INV-5.10 — Gatekeeper records every decision
# ---------------------------------------------------------------------------


def test_record_returns_hash_string(audit_trail: AuditTrail):
    """record() must return a hex SHA-256 hash."""
    h = audit_trail.record(make_audit_entry())
    assert isinstance(h, str)
    assert len(h) == 64
    int(h, 16)  # must be valid hex


def test_chain_valid_after_multiple_records(audit_trail: AuditTrail):
    """After N records, verify_chain must confirm the chain is intact."""
    for status in (GateStatus.ALLOW, GateStatus.BLOCK, GateStatus.APPROVE, GateStatus.INFORM):
        audit_trail.record(make_audit_entry(status=status, risk=RiskLevel.ORANGE))

    valid, total, broken_at = audit_trail.verify_chain()
    assert valid
    assert total == 4
    assert broken_at == -1
