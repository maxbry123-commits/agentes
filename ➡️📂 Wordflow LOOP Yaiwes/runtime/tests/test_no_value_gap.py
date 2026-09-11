import pytest

from runtime.src.core.no_value_gap import ValueAssessment, decide_value, gap_markdown


def _base(**overrides):
    data = dict(
        component="candidate-x",
        unique_capabilities=1,
        overlap_capabilities=0,
        maintenance_risk=2,
        security_risk=2,
        integration_cost=2,
        reviewer_verdict="APPROVE",
        reviewer_id="reviewer-b",
        reviewer_independent=True,
    )
    data.update(overrides)
    return ValueAssessment(**data)


def test_rejects_duplicate_only_with_independent_reviewer():
    decision = decide_value(_base(unique_capabilities=0, overlap_capabilities=3, reviewer_verdict="REJECT"))
    assert decision.verdict == "NO_VALUE_GAP"
    assert "NO_UNIQUE_CAPABILITY" in decision.reason_codes
    assert decision.execution_authorized is False
    assert decision.deployment_authorized is False


def test_missing_independent_reviewer_fails_closed():
    decision = decide_value(_base(reviewer_independent=False))
    assert decision.verdict == "REVIEW_REQUIRED"
    assert decision.reason_codes == ("INDEPENDENT_REVIEW_REQUIRED",)


def test_rejection_signal_requires_reviewer_reject():
    decision = decide_value(_base(security_risk=9, reviewer_verdict="APPROVE"))
    assert decision.verdict == "REVIEW_REQUIRED"
    assert "REVIEWER_REJECTION_REQUIRED" in decision.reason_codes


def test_no_value_markdown_requires_alternative():
    assessment = _base(unique_capabilities=0, overlap_capabilities=2, reviewer_verdict="REJECT")
    decision = decide_value(assessment)
    with pytest.raises(ValueError):
        gap_markdown(assessment, decision, ())


def test_markdown_contains_reviewer_and_alternative():
    assessment = _base(unique_capabilities=0, overlap_capabilities=2, reviewer_verdict="REJECT")
    decision = decide_value(assessment)
    rendered = gap_markdown(assessment, decision, ("reuse:existing-capability",))
    assert "reviewer-b" in rendered
    assert "reuse:existing-capability" in rendered
    assert "execution_authorized: `false`" in rendered
