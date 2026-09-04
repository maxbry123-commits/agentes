from pathlib import Path

from extensions.wordflow.standards.audit_history import AuditHistory


def test_audit_history_is_append_only_and_replayable(tmp_path: Path):
    history = AuditHistory(tmp_path / "audit.jsonl")
    first = history.append(event="FIX", task_id="T09", status="FIXED", revision="r1", evidence={"test": "pass"})
    second = history.append(event="VERIFY", task_id="T09", status="VERIFIED", revision="r2")
    assert second["previous_hash"] == first["event_hash"]
    verified = history.verify()
    assert verified["ok"] is True
    assert verified["count"] == 2
    assert history.replay()[1]["status"] == "VERIFIED"


def test_audit_history_detects_mutation_and_sequence_break(tmp_path: Path):
    history = AuditHistory(tmp_path / "audit.jsonl")
    history.append(event="FIX", task_id="T09", status="FIXED", revision="r1")
    history.append(event="VERIFY", task_id="T09", status="VERIFIED", revision="r2")
    rows = history.replay()
    rows[1]["status"] = "CLOSED"
    history.replace_for_test(rows)
    assert history.verify()["reason"] == "HASH_MISMATCH"
    rows[1]["status"] = "VERIFIED"
    rows[1]["sequence"] = 3
    history.replace_for_test(rows)
    assert history.verify()["reason"] == "SEQUENCE_MISMATCH"
