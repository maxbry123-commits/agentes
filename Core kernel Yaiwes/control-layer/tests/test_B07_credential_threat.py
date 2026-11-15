"""B07 · sim S5 · WRITE con API key → elevación + block."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bootstrap import run_control_pipeline
from contract_engine.fingerprint import build_fingerprint
from contract_engine.threat import analyze_threat
from sheriff.estados import SheriffState


def test_fingerprint_detects_secret():
    fp = build_fingerprint(
        op_type="WRITE_LOCAL",
        payload={"content": "api_key=sk-live-abc"},
    )
    assert fp.is_secret is True
    assert fp.is_write is True


def test_threat_elevates_to_credential_access():
    fp = build_fingerprint(
        op_type="WRITE_LOCAL",
        payload={"content": "token=secret-value"},
    )
    t = analyze_threat(fp)
    assert t.elevated is True
    assert t.suggested_op_type == "CREDENTIAL_ACCESS"
    assert t.data_level == "secret"


def test_pipeline_blocks_credential_write():
    r = run_control_pipeline(
        op_type="WRITE_LOCAL",
        payload={"content": "password=supersecret"},
        mount_mode="dual",
    )
    assert r.blocked is True
    assert r.decision["suggested_op_type"] == "CREDENTIAL_ACCESS"
    assert "C47" in r.decision["active_contracts"]
    assert r.verdict["state"] in (SheriffState.RED.value, SheriffState.BLACK.value)


def test_innocent_write_not_credential():
    r = run_control_pipeline(
        op_type="WRITE_LOCAL",
        payload={"content": "hello world"},
        mount_mode="dual",
    )
    # puede ser YELLOW por risk write, pero no CREDENTIAL_ACCESS
    assert r.decision["suggested_op_type"] != "CREDENTIAL_ACCESS"


if __name__ == "__main__":
    test_fingerprint_detects_secret()
    test_threat_elevates_to_credential_access()
    test_pipeline_blocks_credential_write()
    test_innocent_write_not_credential()
    print("B07 OK")
