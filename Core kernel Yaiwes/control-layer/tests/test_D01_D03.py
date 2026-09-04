"""D01-D03 tests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from execution.adapter import LocalExecutionAdapter, RunStatus
from hermes.supervisor import HermesDecision, HermesSupervisor
from research.policy import ResearchCandidate, evaluate_research


def test_local_execution():
    ad = LocalExecutionAdapter()
    ad.register_activity("echo", lambda p: {"ok": True, **p})
    rid = ad.start_workflow("w1", {"x": 1})
    r = ad.run_activity(rid, "echo", {"a": 2})
    assert r.status == RunStatus.SUCCESS
    assert r.output["a"] == 2


def test_hermes_block_missing_goals():
    h = HermesSupervisor()
    rep = h.audit(goals_out={}, output={"result": "x"})
    assert rep.decision == HermesDecision.BLOCK


def test_research_min_20():
    cands = [ResearchCandidate(name=f"r{i}", score=0.1 * i) for i in range(5)]
    rep = evaluate_research(category="memory", candidates=cands)
    assert rep.ok is False
    cands20 = [ResearchCandidate(name=f"r{i}") for i in range(20)]
    rep2 = evaluate_research(category="memory", candidates=cands20)
    assert rep2.ok is True


if __name__ == "__main__":
    test_local_execution()
    test_hermes_block_missing_goals()
    test_research_min_20()
    print("D01-D03 OK")
