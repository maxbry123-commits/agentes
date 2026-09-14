"""Tests for ImprovementGate (SAFE_DOMAINS safety layer)."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from cognithor.config import ImprovementGovernanceConfig
from cognithor.governance.improvement_gate import (
    CATEGORY_DOMAIN_MAP,
    GateVerdict,
    ImprovementDomain,
    ImprovementGate,
)


@pytest.fixture()
def default_config():
    return ImprovementGovernanceConfig()


@pytest.fixture()
def gate(default_config):
    return ImprovementGate(default_config)


# =========================================================================
# TestImprovementGate
# =========================================================================


class TestImprovementGate:
    def test_auto_domain_returns_allowed(self, gate):
        verdict = gate.check(ImprovementDomain.PROMPT_TUNING)
        assert verdict == GateVerdict.ALLOWED

    def test_auto_domain_tool_parameters_allowed(self, gate):
        verdict = gate.check(ImprovementDomain.TOOL_PARAMETERS)
        assert verdict == GateVerdict.ALLOWED

    def test_auto_domain_workflow_order_allowed(self, gate):
        verdict = gate.check(ImprovementDomain.WORKFLOW_ORDER)
        assert verdict == GateVerdict.ALLOWED

    def test_hitl_domain_returns_needs_approval(self, gate):
        verdict = gate.check(ImprovementDomain.MEMORY_WEIGHTS)
        assert verdict == GateVerdict.NEEDS_APPROVAL

    def test_hitl_model_selection_needs_approval(self, gate):
        verdict = gate.check(ImprovementDomain.MODEL_SELECTION)
        assert verdict == GateVerdict.NEEDS_APPROVAL

    def test_blocked_domain_returns_blocked(self, gate):
        verdict = gate.check(ImprovementDomain.CODE_GENERATION)
        assert verdict == GateVerdict.BLOCKED

    def test_unknown_domain_defaults_to_needs_approval(self, gate):
        """A domain not in auto or blocked -> NEEDS_APPROVAL."""
        # MODEL_SELECTION is in hitl_domains but not in auto_domains
        verdict = gate.check(ImprovementDomain.MODEL_SELECTION)
        assert verdict == GateVerdict.NEEDS_APPROVAL

    def test_cooldown_after_failure(self, gate):
        gate.record_outcome(ImprovementDomain.PROMPT_TUNING, success=False)
        verdict = gate.check(ImprovementDomain.PROMPT_TUNING)
        assert verdict == GateVerdict.COOLDOWN

    def test_cooldown_expires(self):
        config = ImprovementGovernanceConfig(cooldown_minutes=5)
        gate = ImprovementGate(config)

        gate.record_outcome(ImprovementDomain.PROMPT_TUNING, success=False)

        # Simulate cooldown expiry by patching the timestamp
        gate._cooldowns[ImprovementDomain.PROMPT_TUNING] = time.monotonic() - 301  # 5min + 1s ago
        verdict = gate.check(ImprovementDomain.PROMPT_TUNING)
        assert verdict == GateVerdict.ALLOWED

    def test_max_changes_per_hour_enforced(self):
        config = ImprovementGovernanceConfig(max_changes_per_hour=2)
        gate = ImprovementGate(config)

        gate.record_outcome(ImprovementDomain.PROMPT_TUNING, success=True)
        gate.record_outcome(ImprovementDomain.TOOL_PARAMETERS, success=True)

        # Third change should be rate-limited
        verdict = gate.check(ImprovementDomain.WORKFLOW_ORDER)
        assert verdict == GateVerdict.COOLDOWN

    def test_record_outcome_success_no_cooldown(self, gate):
        gate.record_outcome(ImprovementDomain.PROMPT_TUNING, success=True)
        verdict = gate.check(ImprovementDomain.PROMPT_TUNING)
        assert verdict == GateVerdict.ALLOWED

    def test_record_outcome_failure_triggers_cooldown(self, gate):
        gate.record_outcome(ImprovementDomain.PROMPT_TUNING, success=False)
        verdict = gate.check(ImprovementDomain.PROMPT_TUNING)
        assert verdict == GateVerdict.COOLDOWN

    def test_success_clears_cooldown(self, gate):
        gate.record_outcome(ImprovementDomain.PROMPT_TUNING, success=False)
        assert gate.check(ImprovementDomain.PROMPT_TUNING) == GateVerdict.COOLDOWN

        gate.record_outcome(ImprovementDomain.PROMPT_TUNING, success=True)
        assert gate.check(ImprovementDomain.PROMPT_TUNING) == GateVerdict.ALLOWED

    def test_disabled_gate_allows_everything(self):
        config = ImprovementGovernanceConfig(enabled=False)
        gate = ImprovementGate(config)

        assert gate.check(ImprovementDomain.CODE_GENERATION) == GateVerdict.ALLOWED
        assert gate.check(ImprovementDomain.MODEL_SELECTION) == GateVerdict.ALLOWED

    def test_custom_config_domains(self):
        config = ImprovementGovernanceConfig(
            auto_domains=["code_generation"],
            blocked_domains=["prompt_tuning"],
        )
        gate = ImprovementGate(config)

        assert gate.check(ImprovementDomain.CODE_GENERATION) == GateVerdict.ALLOWED
        assert gate.check(ImprovementDomain.PROMPT_TUNING) == GateVerdict.BLOCKED

    def test_category_to_domain_mapping(self):
        assert CATEGORY_DOMAIN_MAP["error_rate"] == ImprovementDomain.TOOL_PARAMETERS
        assert CATEGORY_DOMAIN_MAP["budget"] == ImprovementDomain.MODEL_SELECTION
        assert CATEGORY_DOMAIN_MAP["recurring_error"] == ImprovementDomain.WORKFLOW_ORDER
        assert CATEGORY_DOMAIN_MAP["tool_latency"] == ImprovementDomain.TOOL_PARAMETERS
        assert CATEGORY_DOMAIN_MAP["unused_tool"] == ImprovementDomain.TOOL_PARAMETERS
        assert CATEGORY_DOMAIN_MAP["prompt_evolution"] == ImprovementDomain.PROMPT_TUNING


# =========================================================================
# TestGateIntegration (with GovernanceAgent)
# =========================================================================


class TestGateIntegration:
    def test_governor_approve_checks_gate_allowed(self, tmp_path):
        from cognithor.governance.governor import GovernanceAgent

        config = ImprovementGovernanceConfig()
        gate = ImprovementGate(config)
        db = str(tmp_path / "gov.db")
        gov = GovernanceAgent(db_path=db, improvement_gate=gate)

        # Create a proposal in "error_rate" category -> maps to TOOL_PARAMETERS -> auto allowed
        tel = MagicMock()
        tel.get_tool_stats.return_value = {
            "broken_tool": {"total": 10, "errors": 5},
        }
        gov.task_telemetry = tel
        proposals = gov.analyze()
        assert len(proposals) >= 1

        # Should approve without error
        change = gov.approve_proposal(proposals[0].id)
        assert change.category == "error_rate"
        gov.close()

    def test_governor_approve_checks_gate_blocked(self, tmp_path):
        from cognithor.governance.governor import GovernanceAgent

        config = ImprovementGovernanceConfig(
            blocked_domains=["model_selection"],
        )
        gate = ImprovementGate(config)
        db = str(tmp_path / "gov.db")
        gov = GovernanceAgent(db_path=db, improvement_gate=gate)

        # Create a proposal in "budget" category -> maps to MODEL_SELECTION -> blocked
        ct = MagicMock()
        ct.get_budget_info.return_value = {"limit": 10.0, "used": 9.0}
        gov.cost_tracker = ct
        proposals = gov.analyze()
        assert len(proposals) >= 1

        with pytest.raises(ValueError, match="blocked"):
            gov.approve_proposal(proposals[0].id)
        gov.close()

    def test_governor_approve_checks_gate_cooldown(self, tmp_path):
        from cognithor.governance.governor import GovernanceAgent

        config = ImprovementGovernanceConfig()
        gate = ImprovementGate(config)
        gate.record_outcome(ImprovementDomain.TOOL_PARAMETERS, success=False)

        db = str(tmp_path / "gov.db")
        gov = GovernanceAgent(db_path=db, improvement_gate=gate)

        tel = MagicMock()
        tel.get_tool_stats.return_value = {
            "broken_tool": {"total": 10, "errors": 5},
        }
        gov.task_telemetry = tel
        proposals = gov.analyze()
        assert len(proposals) >= 1

        with pytest.raises(ValueError, match="cooldown"):
            gov.approve_proposal(proposals[0].id)
        gov.close()

    def test_governor_approve_without_gate_works(self, tmp_path):
        from cognithor.governance.governor import GovernanceAgent

        db = str(tmp_path / "gov.db")
        gov = GovernanceAgent(db_path=db)  # No gate

        tel = MagicMock()
        tel.get_tool_stats.return_value = {
            "broken_tool": {"total": 10, "errors": 5},
        }
        gov.task_telemetry = tel
        proposals = gov.analyze()
        assert len(proposals) >= 1

        change = gov.approve_proposal(proposals[0].id)
        assert change is not None
        gov.close()

    def test_governor_approve_needs_approval_passes_through(self, tmp_path):
        from cognithor.governance.governor import GovernanceAgent

        # MODEL_SELECTION is hitl by default, which maps to NEEDS_APPROVAL
        config = ImprovementGovernanceConfig()
        gate = ImprovementGate(config)
        db = str(tmp_path / "gov.db")
        gov = GovernanceAgent(db_path=db, improvement_gate=gate)

        # Budget proposal -> MODEL_SELECTION -> NEEDS_APPROVAL -> should pass through
        ct = MagicMock()
        ct.get_budget_info.return_value = {"limit": 10.0, "used": 9.0}
        gov.cost_tracker = ct
        proposals = gov.analyze()
        assert len(proposals) >= 1

        # NEEDS_APPROVAL should not block the approve_proposal call
        change = gov.approve_proposal(proposals[0].id)
        assert change.category == "budget"
        gov.close()
