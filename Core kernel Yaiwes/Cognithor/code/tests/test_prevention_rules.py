"""Tests for Self-Correction Engine prevention rules.

Tests:
  - Prevention rule generation for each category
  - Rule storage via ReflexionMemory
  - Adoption on apply_proposal
  - Rejection on rollback_proposal
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from cognithor.learning.trace_optimizer import (
    OptimizationProposal,
    ProposalStore,
    TraceOptimizer,
)

if TYPE_CHECKING:
    from pathlib import Path

# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    return tmp_path / "proposals.db"


@pytest.fixture
def proposal_store(tmp_db: Path) -> ProposalStore:
    return ProposalStore(tmp_db)


@pytest.fixture
def mock_trace_store() -> MagicMock:
    ts = MagicMock()
    ts.get.return_value = None
    ts.get_recent.return_value = []
    return ts


@pytest.fixture
def mock_reflexion_memory() -> MagicMock:
    rm = MagicMock()
    rm.record_error.return_value = MagicMock()
    rm.adopt_rule.return_value = True
    rm.reject_rule.return_value = True
    rm._all_entries = []
    return rm


# ── Prevention Rule Generation ───────────────────────────────────


class TestPreventionRuleGeneration:
    """Test _generate_prevention_rule for each known category."""

    def test_timeout_rule(self) -> None:
        target = {"tool_name": "web_search"}
        rule = TraceOptimizer._generate_prevention_rule(target, "timeout")
        assert "Rate-limit" in rule
        assert "web_search" in rule

    def test_bad_parameters_rule(self) -> None:
        target = {"tool_name": "write_file", "error_param": "path"}
        rule = TraceOptimizer._generate_prevention_rule(target, "bad_parameters")
        assert "Validate" in rule
        assert "path" in rule
        assert "write_file" in rule

    def test_bad_params_rule(self) -> None:
        target = {"tool_name": "write_file", "error_param": "content"}
        rule = TraceOptimizer._generate_prevention_rule(target, "bad_params")
        assert "Validate" in rule
        assert "content" in rule

    def test_hallucination_rule(self) -> None:
        target = {"tool_name": "summarize"}
        rule = TraceOptimizer._generate_prevention_rule(target, "hallucination")
        assert "Cross-reference" in rule
        assert "web_search" in rule

    def test_wrong_tool_choice_rule(self) -> None:
        target = {
            "tool_name": "read_file",
            "suggested_tool": "search_and_read",
            "context": "web queries",
        }
        rule = TraceOptimizer._generate_prevention_rule(target, "wrong_tool_choice")
        assert "search_and_read" in rule
        assert "web queries" in rule

    def test_wrong_tool_rule(self) -> None:
        target = {
            "tool_name": "exec_command",
            "suggested_tool": "run_python",
            "context": "code tasks",
        }
        rule = TraceOptimizer._generate_prevention_rule(target, "wrong_tool")
        assert "run_python" in rule

    def test_missing_context_rule(self) -> None:
        target = {"tool_name": "run_python"}
        rule = TraceOptimizer._generate_prevention_rule(target, "missing_context")
        assert "memory" in rule.lower()
        assert "vault" in rule.lower()
        assert "run_python" in rule

    def test_cascade_failure_rule(self) -> None:
        target = {"tool_name": "document_export", "upstream_tool": "web_fetch"}
        rule = TraceOptimizer._generate_prevention_rule(target, "cascade_failure")
        assert "web_fetch" in rule
        assert "document_export" in rule

    def test_permission_denied_rule(self) -> None:
        target = {"tool_name": "exec_command", "resource": "/etc/passwd"}
        rule = TraceOptimizer._generate_prevention_rule(target, "permission_denied")
        assert "approval" in rule.lower()
        assert "/etc/passwd" in rule

    def test_rate_limited_rule(self) -> None:
        target = {"tool_name": "web_search"}
        rule = TraceOptimizer._generate_prevention_rule(target, "rate_limited")
        assert "backoff" in rule.lower()
        assert "web_search" in rule

    def test_rate_limit_rule(self) -> None:
        target = {"tool_name": "web_search"}
        rule = TraceOptimizer._generate_prevention_rule(target, "rate_limit")
        assert "backoff" in rule.lower()

    def test_parse_error_rule(self) -> None:
        target = {"tool_name": "analyze_code"}
        rule = TraceOptimizer._generate_prevention_rule(target, "parse_error")
        assert "Validate" in rule
        assert "analyze_code" in rule

    def test_unknown_category_returns_empty(self) -> None:
        target = {"tool_name": "some_tool"}
        rule = TraceOptimizer._generate_prevention_rule(target, "nonexistent_category")
        assert rule == ""


# ── Rule Storage via ReflexionMemory ─────────────────────────────


class TestRuleStorageViaReflexion:
    """Prevention rules are stored via ReflexionMemory during propose_optimizations."""

    def test_rule_stored_on_proposal(
        self,
        proposal_store: ProposalStore,
        mock_trace_store: MagicMock,
        mock_reflexion_memory: MagicMock,
    ) -> None:
        optimizer = TraceOptimizer(
            proposal_store=proposal_store,
            reflexion_memory=mock_reflexion_memory,
        )

        targets = [
            {
                "failure_category": "timeout",
                "tool_name": "web_search",
                "finding_id": "f1",
                "trace_ids": [],
            }
        ]

        proposals = optimizer.propose_optimizations(targets, mock_trace_store)

        assert len(proposals) == 1
        # ReflexionMemory.record_error should have been called
        mock_reflexion_memory.record_error.assert_called_once()
        call_kwargs = mock_reflexion_memory.record_error.call_args
        assert call_kwargs[1]["tool_name"] == "web_search"
        assert call_kwargs[1]["error_category"] == "timeout"
        assert "Rate-limit" in call_kwargs[1]["prevention_rule"]

    def test_no_reflexion_memory_no_error(
        self,
        proposal_store: ProposalStore,
        mock_trace_store: MagicMock,
    ) -> None:
        """Without reflexion_memory, proposals still generated without errors."""
        optimizer = TraceOptimizer(
            proposal_store=proposal_store,
            reflexion_memory=None,
        )

        targets = [
            {
                "failure_category": "parse_error",
                "tool_name": "analyze_code",
                "finding_id": "f2",
                "trace_ids": [],
            }
        ]

        proposals = optimizer.propose_optimizations(targets, mock_trace_store)
        assert len(proposals) == 1


# ── Adoption and Rejection via EvolutionOrchestrator ─────────────


class TestAdoptionRejection:
    """Apply marks rules as adopted; rollback marks as rejected."""

    def _make_proposal(self, store: ProposalStore) -> OptimizationProposal:
        proposal = OptimizationProposal(
            proposal_id=str(uuid.uuid4()),
            finding_id="f_test",
            optimization_type="tool_param",
            target="web_search.timeout_config",
            description="Timeout fix",
            patch_before="",
            patch_after="timeout=60",
            estimated_impact=0.5,
            confidence=0.8,
            failure_category="timeout",
            tool_name="web_search",
            evidence_trace_ids=[],
            status="proposed",
            created_at=time.time(),
        )
        store.save_proposal(proposal)
        return proposal

    def test_apply_marks_rule_adopted(
        self,
        proposal_store: ProposalStore,
        mock_trace_store: MagicMock,
        mock_reflexion_memory: MagicMock,
    ) -> None:
        from cognithor.learning.evolution_orchestrator import EvolutionOrchestrator

        proposal = self._make_proposal(proposal_store)

        # Create a reflexion entry linked to this proposal
        entry = MagicMock()
        entry.task_context = f"proposal:{proposal.proposal_id}"
        entry.error_signature = "sig_abc"
        mock_reflexion_memory._all_entries = [entry]

        attributor = MagicMock()
        optimizer = MagicMock()

        orch = EvolutionOrchestrator(
            trace_store=mock_trace_store,
            attributor=attributor,
            optimizer=optimizer,
            proposal_store=proposal_store,
            reflexion_memory=mock_reflexion_memory,
        )

        result = orch.apply_proposal(proposal.proposal_id)

        assert result is True
        mock_reflexion_memory.adopt_rule.assert_called_once_with("sig_abc")

    def test_rollback_marks_rule_rejected(
        self,
        proposal_store: ProposalStore,
        mock_trace_store: MagicMock,
        mock_reflexion_memory: MagicMock,
    ) -> None:
        from cognithor.learning.evolution_orchestrator import EvolutionOrchestrator

        proposal = self._make_proposal(proposal_store)
        # First apply
        proposal_store.update_status(
            proposal.proposal_id,
            "applied",
            applied_at=time.time(),
            metrics_before={"success_rate": 0.8},
        )

        entry = MagicMock()
        entry.task_context = f"proposal:{proposal.proposal_id}"
        entry.error_signature = "sig_xyz"
        mock_reflexion_memory._all_entries = [entry]

        attributor = MagicMock()
        optimizer = MagicMock()

        orch = EvolutionOrchestrator(
            trace_store=mock_trace_store,
            attributor=attributor,
            optimizer=optimizer,
            proposal_store=proposal_store,
            reflexion_memory=mock_reflexion_memory,
        )

        result = orch.rollback_proposal(proposal.proposal_id)

        assert result is True
        mock_reflexion_memory.reject_rule.assert_called_once_with("sig_xyz")
