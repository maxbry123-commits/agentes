"""Tests A05 · 5 estados + shadow promotion."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sheriff.estados import SheriffState, evaluate
from sheriff.shadow import ShadowLedger, promote_candidate
from sheriff.gate import run_sheriff


def test_green_normal():
    v = evaluate(
        risk_score=1,
        band="normal",
        elevated=False,
        block_execution=False,
        active_contracts=("C03", "C04"),
        process_plan=("acl_check",),
    )
    assert v.state == SheriffState.GREEN
    assert v.allow_execute is True


def test_red_block():
    v = evaluate(
        risk_score=9,
        band="quarantine",
        elevated=True,
        block_execution=True,
        active_contracts=("C47", "C48"),
        process_plan=("credential_gate",),
    )
    assert v.state == SheriffState.RED
    assert v.allow_execute is False


def test_orange_shadow_and_promote():
    ledger = ShadowLedger()
    decision = {
        "risk_score": 3,
        "band": "normal",
        "elevated": False,
        "block_execution": False,
        "active_contracts": ["C55", "C52", "C53"],
        "process_plan": ["promotion_shadow"],
        "sheriff_required": False,
        "suggested_op_type": "WRITE_LOCAL",
        "set_hash": "sha256:abc",
        "fingerprint_hash": "sha256:def",
    }
    v, rec = run_sheriff(decision, ledger=ledger, shadow_candidate=True)
    assert v.state == SheriffState.ORANGE
    assert v.shadow_only is True
    assert rec is not None
    assert rec.promoted is False

    blocked = promote_candidate(ledger, rec.record_id, provenance_ok=True, test_gate_ok=False, trust_ok=True)
    assert blocked.promoted is False
    assert blocked.promotion_blocked_reason == "test_gate_failed"

    ok = promote_candidate(ledger, rec.record_id, provenance_ok=True, test_gate_ok=True, trust_ok=True)
    assert ok.promoted is True


def test_black_critical():
    v = evaluate(
        risk_score=2,
        band="normal",
        elevated=False,
        block_execution=False,
        active_contracts=(),
        process_plan=(),
        critical_contract_violated=True,
    )
    assert v.state == SheriffState.BLACK
    assert v.allow_execute is False


if __name__ == "__main__":
    test_green_normal()
    test_red_block()
    test_orange_shadow_and_promote()
    test_black_critical()
    print("A05 tests OK")
