"""Tests A11 · CHEF B."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from format.output_chef import chef_b_pipeline, format_output


def test_no_gaps_stops_at_detect():
    facts = {
        "mission_id": "m1",
        "status": "RUNNING",
        "summary": "ok",
        "evidence_hash": "sha256:abc",
    }
    r = chef_b_pipeline(facts)
    assert r.pass_reached == "detect"
    assert r.used_llm is False
    assert r.gaps == ()


def test_gaps_filled_without_llm():
    facts = {"mission_id": "m2", "status": "BLOCKED", "sheriff_state": "RED"}
    r = chef_b_pipeline(facts)
    assert r.pass_reached == "fill"
    assert r.used_llm is False
    assert r.output["summary"]
    assert r.output["evidence_hash"]
    assert r.output.get("blocked_reason")


def test_duplicate_steps_cleaned():
    facts = {
        "mission_id": "m3",
        "status": "RUNNING",
        "summary": "s",
        "evidence_hash": "sha256:x",
        "steps_done": ["a", "b"],
        "steps_pending": ["b", "c"],
    }
    out = format_output(facts)
    assert "b" not in out["steps_pending"]
    assert "c" in out["steps_pending"]


if __name__ == "__main__":
    test_no_gaps_stops_at_detect()
    test_gaps_filled_without_llm()
    test_duplicate_steps_cleaned()
    print("A11 tests OK")
