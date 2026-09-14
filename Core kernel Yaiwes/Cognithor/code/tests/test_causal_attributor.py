"""Tests for jarvis.learning.causal_attributor — CausalAttributor, CausalFinding."""

from __future__ import annotations

import time
import uuid

from cognithor.learning.causal_attributor import CausalAttributor, CausalFinding
from cognithor.learning.execution_trace import ExecutionTrace, TraceStep

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _step(
    *,
    step_id: str | None = None,
    parent_id: str | None = None,
    tool_name: str = "shell_exec",
    status: str = "success",
    error_detail: str = "",
    duration_ms: int = 100,
) -> TraceStep:
    return TraceStep(
        step_id=step_id or uuid.uuid4().hex[:12],
        parent_id=parent_id,
        tool_name=tool_name,
        input_summary="in",
        output_summary="out",
        status=status,
        error_detail=error_detail,
        duration_ms=duration_ms,
        timestamp=time.time(),
    )


def _trace(steps: list[TraceStep], *, trace_id: str | None = None) -> ExecutionTrace:
    return ExecutionTrace(
        trace_id=trace_id or uuid.uuid4().hex[:12],
        session_id="sess-test",
        goal="test",
        steps=steps,
        created_at=time.time(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAnalyzeTrace:
    """Tests for CausalAttributor.analyze_trace()."""

    def test_analyze_simple_failure(self):
        """Single failed step with no parent chain produces one finding."""
        attr = CausalAttributor()
        s = _step(step_id="s1", status="error", error_detail="timeout exceeded")
        t = _trace([s])

        findings = attr.analyze_trace(t)
        assert len(findings) == 1, "Should produce exactly one finding"
        f = findings[0]
        assert f.trace_id == t.trace_id
        assert f.root_step_id == "s1"
        assert f.failure_category == "timeout"
        assert f.confidence == 0.9, "Single-step failure should have 0.9 confidence"
        assert f.tool_name == "shell_exec"

    def test_analyze_cascade_failure(self):
        """Parent fails, child also fails -> root cause is the parent."""
        attr = CausalAttributor()
        parent = _step(
            step_id="p1",
            parent_id=None,
            tool_name="web_search",
            status="error",
            error_detail="connection refused",
        )
        child = _step(
            step_id="c1",
            parent_id="p1",
            tool_name="read_file",
            status="error",
            error_detail="no data available",
        )
        t = _trace([parent, child])

        findings = attr.analyze_trace(t)
        # The parent is the root cause for both failures; child should be
        # deduplicated (same root). The parent itself is a root cause.
        root_step_ids = {f.root_step_id for f in findings}
        assert "p1" in root_step_ids, "Parent should be identified as root cause"

    def test_no_findings_for_successful_trace(self):
        """All steps succeed -> no findings."""
        attr = CausalAttributor()
        s1 = _step(status="success")
        s2 = _step(status="success")
        t = _trace([s1, s2])

        findings = attr.analyze_trace(t)
        assert findings == [], "Successful trace should produce no findings"


class TestClassifyFailure:
    """Tests for failure classification heuristics."""

    def test_classify_timeout(self):
        attr = CausalAttributor()
        for keyword in ("timeout", "timed out", "deadline exceeded"):
            s = _step(status="error", error_detail=f"Operation {keyword}")
            category = attr.classify_failure(s)
            assert category == "timeout", f"'{keyword}' should classify as timeout"

    def test_classify_permission_denied(self):
        attr = CausalAttributor()
        for keyword in ("blocked", "denied", "gatekeeper rejected"):
            s = _step(status="error", error_detail=f"Action {keyword}")
            category = attr.classify_failure(s)
            assert category == "permission_denied", f"'{keyword}' should be permission_denied"

    def test_classify_bad_parameters(self):
        attr = CausalAttributor()
        for keyword in ("parameter", "missing field", "invalid value", "required field"):
            s = _step(status="error", error_detail=f"Bad {keyword}")
            category = attr.classify_failure(s)
            assert category == "bad_parameters", f"'{keyword}' should be bad_parameters"

    def test_classify_rate_limited(self):
        attr = CausalAttributor()
        for keyword in ("429", "rate limit", "too many requests"):
            s = _step(status="error", error_detail=f"HTTP {keyword}")
            category = attr.classify_failure(s)
            assert category == "rate_limited", f"'{keyword}' should be rate_limited"

    def test_classify_parse_error(self):
        attr = CausalAttributor()
        for keyword in ("json decode", "parse failed", "syntax error"):
            s = _step(status="error", error_detail=f"Error: {keyword}")
            category = attr.classify_failure(s)
            assert category == "parse_error", f"'{keyword}' should be parse_error"

    def test_classify_tool_unavailable(self):
        attr = CausalAttributor()
        s = _step(status="error", error_detail="Tool not found: xyz_tool")
        category = attr.classify_failure(s)
        assert category == "tool_unavailable"

    def test_classify_hallucination(self):
        attr = CausalAttributor()
        s = _step(status="error", error_detail="incorrect output detected")
        category = attr.classify_failure(s)
        assert category == "hallucination"

    def test_classify_cascade_via_step_index(self):
        """When parent also failed, classify as cascade_failure."""
        attr = CausalAttributor()
        parent = _step(step_id="p", status="error", error_detail="some error")
        child = _step(step_id="c", parent_id="p", status="error", error_detail="downstream")
        step_index = {"p": parent, "c": child}

        category = attr.classify_failure(child, step_index=step_index)
        assert category == "cascade_failure"

    def test_classify_wrong_tool_choice(self):
        """Parent is a planner step that succeeded, child fails -> wrong_tool_choice."""
        attr = CausalAttributor()
        parent = _step(step_id="p", tool_name="planner", status="success")
        child = _step(
            step_id="c",
            parent_id="p",
            status="error",
            error_detail="unexpected result",
        )
        step_index = {"p": parent, "c": child}

        category = attr.classify_failure(child, step_index=step_index)
        assert category == "wrong_tool_choice"

    def test_classify_missing_context_fallback(self):
        """Unrecognized error with no structural hints -> missing_context."""
        attr = CausalAttributor()
        s = _step(status="error", error_detail="something completely unrecognized happened")
        category = attr.classify_failure(s)
        assert category == "missing_context"


class TestNormalizeError:
    """Tests for error string normalization."""

    def test_normalize_strips_paths(self):
        attr = CausalAttributor()
        result = attr.normalize_error("Failed at /home/user/project/main.py line 42")
        assert "<PATH>" in result
        assert "line <N>" in result

    def test_normalize_strips_uuids(self):
        attr = CausalAttributor()
        result = attr.normalize_error("Error for 550e8400-e29b-41d4-a716-446655440000")
        assert "<UUID>" in result
        assert "550e8400" not in result

    def test_normalize_strips_timestamps(self):
        attr = CausalAttributor()
        result = attr.normalize_error("Failed at 2025-03-19T14:30:00 with error")
        assert "<TIMESTAMP>" in result

    def test_normalize_collapses_whitespace(self):
        attr = CausalAttributor()
        result = attr.normalize_error("error   with   many    spaces")
        assert "  " not in result


class TestAggregate:
    """Tests for aggregate_findings and get_improvement_targets."""

    def test_aggregate_findings(self):
        attr = CausalAttributor()
        findings = [
            CausalFinding(
                trace_id="t1",
                root_step_id="s1",
                failure_category="timeout",
                tool_name="web_search",
                error_signature="timed out",
                confidence=0.9,
            ),
            CausalFinding(
                trace_id="t2",
                root_step_id="s2",
                failure_category="timeout",
                tool_name="web_search",
                error_signature="timed out",
                confidence=0.8,
            ),
            CausalFinding(
                trace_id="t3",
                root_step_id="s3",
                failure_category="parse_error",
                tool_name="read_file",
                error_signature="json decode",
                confidence=0.7,
            ),
        ]

        aggregated = attr.aggregate_findings(findings)
        assert len(aggregated) == 2, "Should group into 2 distinct groups"

        # Sorted by priority (count * avg_confidence) descending
        top = aggregated[0]
        assert top["failure_category"] == "timeout"
        assert top["count"] == 2
        assert top["avg_confidence"] == 0.85
        assert set(top["trace_ids"]) == {"t1", "t2"}

    def test_get_improvement_targets(self):
        attr = CausalAttributor()
        findings = [
            CausalFinding(
                trace_id=f"t{i}",
                failure_category="timeout",
                tool_name="web_search",
                error_signature="timed out",
                confidence=0.9,
            )
            for i in range(3)
        ] + [
            CausalFinding(
                trace_id="t-single",
                failure_category="parse_error",
                tool_name="read_file",
                error_signature="json",
                confidence=0.3,
            ),
        ]

        targets = attr.get_improvement_targets(findings, min_count=2, min_confidence=0.5)
        assert len(targets) == 1, "Only timeout group meets both thresholds"
        assert targets[0]["failure_category"] == "timeout"

    def test_get_improvement_targets_empty_when_below_thresholds(self):
        attr = CausalAttributor()
        findings = [
            CausalFinding(
                trace_id="t1",
                failure_category="timeout",
                tool_name="web_search",
                error_signature="sig",
                confidence=0.3,
            ),
        ]
        targets = attr.get_improvement_targets(findings, min_count=2, min_confidence=0.5)
        assert targets == [], "Single finding with low confidence should not pass"
