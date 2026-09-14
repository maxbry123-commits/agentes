"""Tests for jarvis.learning.trace_optimizer.

Covers TraceOptimizer, ProposalStore, and OptimizationProposal.
"""

from __future__ import annotations

import time
import uuid
from unittest.mock import MagicMock

from cognithor.learning.trace_optimizer import (
    OptimizationProposal,
    ProposalStore,
    TraceOptimizer,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_proposal(
    *,
    proposal_id: str | None = None,
    finding_id: str = "finding-1",
    optimization_type: str = "tool_param",
    target: str = "web_search.timeout_config",
    description: str = "Increase timeout",
    patch_before: str = "timeout=30",
    patch_after: str = "timeout=60",
    estimated_impact: float = 0.5,
    confidence: float = 0.75,
    failure_category: str = "timeout",
    tool_name: str = "web_search",
    evidence_trace_ids: list[str] | None = None,
    status: str = "proposed",
    applied_at: float = 0.0,
    metrics_before: dict | None = None,
    metrics_after: dict | None = None,
    created_at: float = 0.0,
) -> OptimizationProposal:
    return OptimizationProposal(
        proposal_id=proposal_id or uuid.uuid4().hex[:12],
        finding_id=finding_id,
        optimization_type=optimization_type,
        target=target,
        description=description,
        patch_before=patch_before,
        patch_after=patch_after,
        estimated_impact=estimated_impact,
        confidence=confidence,
        failure_category=failure_category,
        tool_name=tool_name,
        evidence_trace_ids=evidence_trace_ids or ["t1"],
        status=status,
        applied_at=applied_at,
        metrics_before=metrics_before or {},
        metrics_after=metrics_after or {},
        created_at=created_at or time.time(),
    )


def _make_mock_trace_store() -> MagicMock:
    """Create a mock trace store with properly typed return values."""
    from cognithor.learning.execution_trace import ExecutionTrace, TraceStep

    mock_trace = ExecutionTrace(
        trace_id="mock-t1",
        session_id="mock-s1",
        goal="test",
        total_duration_ms=5000,
        success_score=0.3,
        created_at=1.0,
    )
    mock_trace.steps.append(
        TraceStep(
            step_id="mock-st1",
            parent_id=None,
            tool_name="web_search",
            input_summary="query",
            output_summary="",
            status="error",
            error_detail="timeout",
            duration_ms=5000,
            timestamp=1.0,
        )
    )
    mock = MagicMock()
    mock.get_trace.return_value = mock_trace
    mock.get_recent_traces.return_value = [mock_trace]
    return mock


def _make_target(
    *,
    failure_category: str = "timeout",
    tool_name: str = "web_search",
    trace_ids: list[str] | None = None,
    finding_id: str = "f1",
) -> dict:
    return {
        "failure_category": failure_category,
        "tool_name": tool_name,
        "trace_ids": trace_ids or ["t1", "t2"],
        "finding_id": finding_id,
        "error_signature": "error sig",
        "count": 3,
        "avg_confidence": 0.8,
        "priority": 2.4,
        "explanation": "Test explanation",
    }


# ---------------------------------------------------------------------------
# ProposalStore tests
# ---------------------------------------------------------------------------


class TestProposalStoreCRUD:
    """CRUD operations on ProposalStore."""

    def test_save_and_get(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        p = _make_proposal(proposal_id="p-1")
        store.save_proposal(p)

        loaded = store.get_proposal("p-1")
        assert loaded is not None, "Proposal should be retrievable"
        assert loaded.proposal_id == "p-1"
        assert loaded.optimization_type == "tool_param"
        assert loaded.confidence == 0.75
        assert loaded.evidence_trace_ids == ["t1"]
        assert loaded.status == "proposed"

    def test_update_status(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        p = _make_proposal(proposal_id="p-2")
        store.save_proposal(p)

        now = time.time()
        metrics_before = {"success_rate": 0.6}
        store.update_status(
            "p-2",
            "applied",
            applied_at=now,
            metrics_before=metrics_before,
        )

        loaded = store.get_proposal("p-2")
        assert loaded is not None
        assert loaded.status == "applied"
        assert loaded.applied_at == now
        assert loaded.metrics_before == metrics_before

    def test_get_pending(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        p1 = _make_proposal(proposal_id="p-pending", status="proposed")
        p2 = _make_proposal(proposal_id="p-applied", status="applied")
        store.save_proposal(p1)
        store.save_proposal(p2)

        pending = store.get_pending()
        ids = {p.proposal_id for p in pending}
        assert "p-pending" in ids
        assert "p-applied" not in ids

    def test_get_applied(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        p1 = _make_proposal(proposal_id="p-a", status="applied")
        p2 = _make_proposal(proposal_id="p-b", status="proposed")
        store.save_proposal(p1)
        store.save_proposal(p2)

        applied = store.get_applied()
        ids = {p.proposal_id for p in applied}
        assert "p-a" in ids
        assert "p-b" not in ids

    def test_get_by_status(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        for status in ("proposed", "applied", "rejected", "rolled_back"):
            store.save_proposal(_make_proposal(status=status))

        rejected = store.get_by_status("rejected")
        assert len(rejected) == 1
        assert rejected[0].status == "rejected"

    def test_delete_old(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        now = time.time()
        old_rejected = _make_proposal(
            proposal_id="old-rej",
            status="rejected",
            created_at=now - 120 * 86400,
        )
        old_rolled = _make_proposal(
            proposal_id="old-roll",
            status="rolled_back",
            created_at=now - 120 * 86400,
        )
        recent_rejected = _make_proposal(
            proposal_id="new-rej",
            status="rejected",
            created_at=now,
        )
        old_applied = _make_proposal(
            proposal_id="old-applied",
            status="applied",
            created_at=now - 120 * 86400,
        )
        for p in (old_rejected, old_rolled, recent_rejected, old_applied):
            store.save_proposal(p)

        deleted = store.delete_old(older_than_days=90)
        assert deleted == 2, "Should delete only old rejected and rolled_back"

        assert store.get_proposal("old-rej") is None
        assert store.get_proposal("old-roll") is None
        assert store.get_proposal("new-rej") is not None
        assert store.get_proposal("old-applied") is not None, "Applied should not be deleted"

    def test_get_history(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        now = time.time()
        for i in range(5):
            store.save_proposal(_make_proposal(created_at=now - i))

        history = store.get_history(limit=3)
        assert len(history) == 3, "Should respect limit"


# ---------------------------------------------------------------------------
# TraceOptimizer tests
# ---------------------------------------------------------------------------


class TestTraceOptimizer:
    """Tests for TraceOptimizer proposal generation."""

    def test_propose_for_timeout(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        target = _make_target(failure_category="timeout", tool_name="web_search")
        proposals = optimizer.propose_optimizations([target], trace_store)

        assert len(proposals) == 1
        p = proposals[0]
        assert p.optimization_type == "tool_param"
        assert p.failure_category == "timeout"
        assert p.tool_name == "web_search"
        assert "timeout" in p.target.lower()

    def test_propose_for_wrong_tool(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        target = _make_target(failure_category="wrong_tool", tool_name="shell_exec")
        proposals = optimizer.propose_optimizations([target], trace_store)

        assert len(proposals) == 1
        p = proposals[0]
        assert p.optimization_type == "strategy_change"
        assert p.failure_category == "wrong_tool"

    def test_propose_for_hallucination(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        target = _make_target(failure_category="hallucination", tool_name="formulate_response")
        proposals = optimizer.propose_optimizations([target], trace_store)

        assert len(proposals) == 1
        p = proposals[0]
        assert p.optimization_type == "guardrail"
        assert p.failure_category == "hallucination"

    def test_propose_for_missing_context(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        target = _make_target(failure_category="missing_context", tool_name="read_file")
        proposals = optimizer.propose_optimizations([target], trace_store)

        assert len(proposals) == 1
        p = proposals[0]
        assert p.optimization_type == "context_enrichment"
        assert p.failure_category == "missing_context"

    def test_propose_generic_fallback(self, tmp_path):
        """Unknown failure category falls back to _propose_generic."""
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        target = _make_target(failure_category="alien_invasion", tool_name="ufo_detector")
        proposals = optimizer.propose_optimizations([target], trace_store)

        assert len(proposals) == 1
        p = proposals[0]
        assert p.optimization_type == "new_procedure"
        assert p.failure_category == "alien_invasion"

    def test_score_proposal(self, tmp_path):
        """Score is (affected/total) * confidence."""
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        # Mock get_recent to return traces where some match the failure
        mock_trace_ok = MagicMock()
        mock_trace_ok.tool_name = "web_search"
        mock_trace_ok.failure_category = "timeout"
        mock_trace_ok.success = False

        mock_trace_unrelated = MagicMock()
        mock_trace_unrelated.tool_name = "shell_exec"
        mock_trace_unrelated.failure_category = "parse_error"
        mock_trace_unrelated.success = True

        trace_store.get_recent_traces.return_value = [mock_trace_ok, mock_trace_unrelated]

        p = _make_proposal(
            tool_name="web_search",
            failure_category="timeout",
            confidence=0.8,
        )
        score = optimizer.score_proposal(p, trace_store)
        # 1 affected out of 2 total * 0.8 confidence = 0.4
        assert score == 0.4

    def test_score_proposal_no_recent_traces(self, tmp_path):
        """With no recent traces, score should be 0.0."""
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        trace_store.get_recent_traces.return_value = []
        optimizer = TraceOptimizer(store)

        p = _make_proposal(confidence=0.8)
        score = optimizer.score_proposal(p, trace_store)
        assert score == 0.0

    def test_propose_for_bad_params(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        target = _make_target(failure_category="bad_params", tool_name="shell_exec")
        proposals = optimizer.propose_optimizations([target], trace_store)

        assert len(proposals) == 1
        p = proposals[0]
        assert p.optimization_type == "tool_param"
        assert p.failure_category == "bad_params"

    def test_propose_for_cascade(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        target = _make_target(failure_category="cascade_failure", tool_name="web_search")
        proposals = optimizer.propose_optimizations([target], trace_store)

        assert len(proposals) == 1
        p = proposals[0]
        assert p.optimization_type == "strategy_change"

    def test_propose_for_rate_limit(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        target = _make_target(failure_category="rate_limit", tool_name="web_search")
        proposals = optimizer.propose_optimizations([target], trace_store)

        assert len(proposals) == 1
        p = proposals[0]
        assert p.optimization_type == "tool_param"

    def test_propose_for_parse_error(self, tmp_path):
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        target = _make_target(failure_category="parse_error", tool_name="read_file")
        proposals = optimizer.propose_optimizations([target], trace_store)

        assert len(proposals) == 1
        p = proposals[0]
        assert p.optimization_type == "tool_param"

    def test_proposal_saved_to_store(self, tmp_path):
        """Proposals generated by optimizer are persisted to the ProposalStore."""
        store = ProposalStore(tmp_path / "proposals.db")
        trace_store = _make_mock_trace_store()
        optimizer = TraceOptimizer(store)

        target = _make_target(failure_category="timeout", tool_name="web_search")
        proposals = optimizer.propose_optimizations([target], trace_store)

        assert len(proposals) == 1
        # Verify it was saved
        loaded = store.get_proposal(proposals[0].proposal_id)
        assert loaded is not None
        assert loaded.proposal_id == proposals[0].proposal_id
