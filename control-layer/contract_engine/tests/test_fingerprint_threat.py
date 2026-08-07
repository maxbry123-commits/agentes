"""Tests A02 · determinismo fingerprint + elevación threat."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contract_engine.fingerprint import build_fingerprint
from contract_engine.threat import analyze_threat


def test_fingerprint_stable_same_input():
    a = build_fingerprint(op_type="WRITE_LOCAL", payload={"path": "/tmp/x"})
    b = build_fingerprint(op_type="WRITE_LOCAL", payload={"path": "/tmp/x"})
    assert a.fingerprint_hash == b.fingerprint_hash
    assert a.to_dict() == b.to_dict()


def test_read_local_low_risk():
    fp = build_fingerprint(op_type="READ_LOCAL", payload={"path": "README.md"})
    t = analyze_threat(fp)
    assert t.band == "normal"
    assert t.risk_score <= 3
    assert t.elevated is False


def test_write_with_api_key_elevates_to_credential_access():
    fp = build_fingerprint(
        op_type="WRITE_LOCAL",
        payload={"content": "api_key=sk-secret-value-here"},
    )
    assert fp.is_secret is True
    assert fp.is_write is True
    t = analyze_threat(fp)
    assert t.suggested_op_type == "CREDENTIAL_ACCESS"
    assert t.elevated is True
    assert t.risk_score >= 8 or t.data_level == "secret"


def test_delete_scores_higher_than_read():
    r = analyze_threat(build_fingerprint(op_type="READ_LOCAL"))
    d = analyze_threat(build_fingerprint(op_type="DELETE_LOCAL"))
    assert d.risk_score > r.risk_score


if __name__ == "__main__":
    test_fingerprint_stable_same_input()
    test_read_local_low_risk()
    test_write_with_api_key_elevates_to_credential_access()
    test_delete_scores_higher_than_read()
    print("A02 tests OK")
