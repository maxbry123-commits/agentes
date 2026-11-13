import hashlib
import json

import pytest

from source_truth_reconciler import (
    REQUIRED_TRUTHS,
    TruthRecord,
    TruthReconciliationError,
    build_record,
    reconcile,
    validate_reconciliation_plan,
)


def rec(name, checkpoint):
    return TruthRecord(name, checkpoint, "0" * 64)


def full(checkpoint):
    return [rec(name, checkpoint) for name in REQUIRED_TRUTHS]


def test_consistent():
    report = reconcile(full("WFLOOP-CODE-GRAPH-20260911-0010"))
    assert report.status == "CONSISTENT"
    assert report.write_authorized is False


def test_drift_detected():
    records = full("WFLOOP-CODE-GRAPH-20260911-0010")
    records[0] = rec("README", "WFLOOP-CODE-GRAPH-20260911-0009")
    report = reconcile(records)
    assert report.status == "DRIFT_RECONCILE_REQUIRED"
    assert report.drift == ("README",)
    assert validate_reconciliation_plan(
        report, {"README": "WFLOOP-CODE-GRAPH-20260911-0010"}
    )


def test_anchor_conflict_fails_closed():
    records = full("WFLOOP-CODE-GRAPH-20260911-0010")
    records[1] = rec("STATE", "WFLOOP-CODE-GRAPH-20260911-0009")
    report = reconcile(records)
    assert report.status == "FAIL_CLOSED_CONFLICT"
    assert report.canonical_checkpoint is None


def test_missing_truth_fails_closed():
    report = reconcile(full("WFLOOP-CODE-GRAPH-20260911-0010")[:-1])
    assert report.status == "FAIL_CLOSED_MISSING_TRUTH"
    assert "RECOVERY" in report.missing


def test_build_record_json_and_markdown():
    digest = hashlib.sha256(b"x").hexdigest()
    state = build_record(
        "STATE",
        json.dumps({"checkpoint_id": "WFLOOP-CODE-GRAPH-20260911-0010"}),
        digest,
    )
    handoff = build_record(
        "HANDOFF",
        "Checkpoint: `WFLOOP-CODE-GRAPH-20260911-0010`",
        digest,
    )
    assert state.checkpoint_id == handoff.checkpoint_id


def test_historical_truth_uses_explicit_canonical_marker():
    digest = hashlib.sha256(b"history").hexdigest()
    text = """
Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0010`
Histórico: `WFLOOP-CODE-GRAPH-20260911-0008`
Histórico: `WFLOOP-CODE-GRAPH-20260911-0009`
"""
    record = build_record("BITACORA", text, digest)
    assert record.checkpoint_id == "WFLOOP-CODE-GRAPH-20260911-0010"


def test_conflicting_canonical_markers_fail_closed():
    digest = hashlib.sha256(b"conflict").hexdigest()
    text = """
Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0010`
Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0011`
"""
    with pytest.raises(TruthReconciliationError):
        build_record("BITACORA", text, digest)
