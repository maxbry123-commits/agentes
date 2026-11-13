"""Tests for jarvis.learning.execution_trace — TraceStep, ExecutionTrace, TraceStore."""

from __future__ import annotations

import time
import uuid

from cognithor.learning.execution_trace import ExecutionTrace, TraceStep, TraceStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_step(
    *,
    step_id: str | None = None,
    parent_id: str | None = None,
    tool_name: str = "shell_exec",
    status: str = "success",
    error_detail: str = "",
    duration_ms: int = 100,
    timestamp: float = 0.0,
    input_summary: str = "input",
    output_summary: str = "output",
    metadata: dict | None = None,
) -> TraceStep:
    return TraceStep(
        step_id=step_id or uuid.uuid4().hex[:12],
        parent_id=parent_id,
        tool_name=tool_name,
        input_summary=input_summary,
        output_summary=output_summary,
        status=status,
        error_detail=error_detail,
        duration_ms=duration_ms,
        timestamp=timestamp or time.time(),
        metadata=metadata or {},
    )


def _make_trace(
    *,
    trace_id: str | None = None,
    session_id: str = "sess-1",
    goal: str = "test goal",
    steps: list[TraceStep] | None = None,
    success_score: float = 1.0,
    model_used: str = "qwen3:8b",
    total_duration_ms: int = 500,
    created_at: float = 0.0,
) -> ExecutionTrace:
    return ExecutionTrace(
        trace_id=trace_id or uuid.uuid4().hex[:12],
        session_id=session_id,
        goal=goal,
        steps=steps or [],
        total_duration_ms=total_duration_ms,
        success_score=success_score,
        model_used=model_used,
        created_at=created_at or time.time(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTraceStoreCRUD:
    """CRUD operations on TraceStore."""

    def test_save_and_get_trace(self, tmp_path):
        store = TraceStore(tmp_path / "traces.db")
        try:
            s1 = _make_step(tool_name="web_search", status="success")
            s2 = _make_step(tool_name="read_file", status="error", error_detail="not found")
            trace = _make_trace(
                steps=[s1, s2],
                success_score=0.5,
                session_id="sess-abc",
                goal="find info",
            )

            store.save_trace(trace)
            loaded = store.get_trace(trace.trace_id)

            assert loaded is not None, "Trace should be retrievable after save"
            assert loaded.trace_id == trace.trace_id
            assert loaded.session_id == "sess-abc"
            assert loaded.goal == "find info"
            assert loaded.success_score == 0.5
            assert loaded.model_used == trace.model_used
            assert loaded.total_duration_ms == trace.total_duration_ms
            assert len(loaded.steps) == 2, "Both steps should be persisted"
            assert loaded.steps[0].tool_name == "web_search"
            assert loaded.steps[1].tool_name == "read_file"
            assert loaded.steps[1].status == "error"
            assert loaded.steps[1].error_detail == "not found"
        finally:
            store.close()

    def test_get_traces_by_session(self, tmp_path):
        store = TraceStore(tmp_path / "traces.db")
        try:
            now = time.time()
            t1 = _make_trace(session_id="sess-x", created_at=now - 10)
            t2 = _make_trace(session_id="sess-x", created_at=now - 5)
            t3 = _make_trace(session_id="sess-y", created_at=now)
            for t in (t1, t2, t3):
                store.save_trace(t)

            results = store.get_traces_by_session("sess-x")
            assert len(results) == 2, "Should return only traces for sess-x"
            assert results[0].trace_id == t1.trace_id, "Ordered by created_at ASC"
            assert results[1].trace_id == t2.trace_id

            results_y = store.get_traces_by_session("sess-y")
            assert len(results_y) == 1
        finally:
            store.close()

    def test_get_traces_by_tool(self, tmp_path):
        store = TraceStore(tmp_path / "traces.db")
        try:
            s_web = _make_step(tool_name="web_search")
            s_shell = _make_step(tool_name="shell_exec")
            t1 = _make_trace(steps=[s_web])
            t2 = _make_trace(steps=[s_shell])
            t3 = _make_trace(steps=[_make_step(tool_name="web_search")])
            for t in (t1, t2, t3):
                store.save_trace(t)

            results = store.get_traces_by_tool("web_search")
            trace_ids = {r.trace_id for r in results}
            assert t1.trace_id in trace_ids
            assert t3.trace_id in trace_ids
            assert t2.trace_id not in trace_ids, "shell_exec trace should not appear"
        finally:
            store.close()

    def test_get_failed_traces(self, tmp_path):
        store = TraceStore(tmp_path / "traces.db")
        try:
            now = time.time()
            t_ok = _make_trace(success_score=0.9, created_at=now)
            t_fail = _make_trace(success_score=0.2, created_at=now)
            t_old_fail = _make_trace(success_score=0.1, created_at=now - 2 * 86400)
            for t in (t_ok, t_fail, t_old_fail):
                store.save_trace(t)

            results = store.get_failed_traces(since_hours=24)
            ids = {r.trace_id for r in results}
            assert t_fail.trace_id in ids, "Recent failed trace should appear"
            assert t_ok.trace_id not in ids, "Successful trace should not appear"
            assert t_old_fail.trace_id not in ids, "Old failed trace should not appear"
        finally:
            store.close()

    def test_get_recent_traces(self, tmp_path):
        store = TraceStore(tmp_path / "traces.db")
        try:
            now = time.time()
            traces = []
            for i in range(5):
                t = _make_trace(created_at=now - (4 - i))
                traces.append(t)
                store.save_trace(t)

            results = store.get_recent_traces(limit=3)
            assert len(results) == 3, "Should respect limit"
            # Most recent first (DESC)
            assert results[0].trace_id == traces[4].trace_id
            assert results[1].trace_id == traces[3].trace_id
            assert results[2].trace_id == traces[2].trace_id
        finally:
            store.close()

    def test_get_trace_stats(self, tmp_path):
        store = TraceStore(tmp_path / "traces.db")
        try:
            now = time.time()
            s_ok = _make_step(tool_name="web_search", status="success")
            _make_step(tool_name="shell_exec", status="error", error_detail="fail")
            t1 = _make_trace(
                success_score=0.9,
                total_duration_ms=200,
                steps=[s_ok],
                created_at=now,
            )
            t2 = _make_trace(
                success_score=0.3,
                total_duration_ms=800,
                steps=[_make_step(tool_name="shell_exec", status="error", error_detail="fail")],
                created_at=now,
            )
            for t in (t1, t2):
                store.save_trace(t)

            stats = store.get_trace_stats(since_hours=1)
            assert stats["total"] == 2
            assert stats["success_rate"] == 0.5, "1 of 2 traces has score >= 0.5"
            assert stats["avg_duration_ms"] == 500.0
            assert stats["avg_steps"] == 1.0
            assert len(stats["top_failing_tools"]) >= 1
            failing_tools = {t["tool_name"] for t in stats["top_failing_tools"]}
            assert "shell_exec" in failing_tools
        finally:
            store.close()

    def test_delete_old_traces(self, tmp_path):
        store = TraceStore(tmp_path / "traces.db")
        try:
            now = time.time()
            t_old = _make_trace(created_at=now - 60 * 86400)  # 60 days ago
            t_new = _make_trace(created_at=now)
            for t in (t_old, t_new):
                store.save_trace(t)

            deleted = store.delete_old_traces(older_than_days=30)
            assert deleted == 1, "Should delete only the old trace"

            assert store.get_trace(t_old.trace_id) is None, "Old trace should be gone"
            assert store.get_trace(t_new.trace_id) is not None, "New trace should remain"
        finally:
            store.close()

    def test_get_nonexistent_trace(self, tmp_path):
        store = TraceStore(tmp_path / "traces.db")
        try:
            result = store.get_trace("nonexistent-id")
            assert result is None
        finally:
            store.close()


class TestExecutionTraceModel:
    """Tests for ExecutionTrace data model properties."""

    def test_trace_causal_chain(self):
        root = _make_step(step_id="root", parent_id=None, tool_name="planner")
        mid = _make_step(step_id="mid", parent_id="root", tool_name="web_search")
        leaf = _make_step(step_id="leaf", parent_id="mid", tool_name="read_file")
        trace = _make_trace(steps=[root, mid, leaf])

        chain = trace.get_causal_chain("leaf")
        assert len(chain) == 3, "Chain should walk from root to leaf"
        assert chain[0].step_id == "root"
        assert chain[1].step_id == "mid"
        assert chain[2].step_id == "leaf"

    def test_trace_causal_chain_single_step(self):
        s = _make_step(step_id="only", parent_id=None)
        trace = _make_trace(steps=[s])
        chain = trace.get_causal_chain("only")
        assert len(chain) == 1
        assert chain[0].step_id == "only"

    def test_trace_failed_steps_property(self):
        s1 = _make_step(status="success")
        s2 = _make_step(status="error", error_detail="something broke")
        s3 = _make_step(status="timeout", error_detail="too slow")
        s4 = _make_step(status="skipped")
        trace = _make_trace(steps=[s1, s2, s3, s4])

        failed = trace.failed_steps
        assert len(failed) == 2, "Only error and timeout should be failed"
        statuses = {s.status for s in failed}
        assert statuses == {"error", "timeout"}

    def test_trace_tool_sequence(self):
        s1 = _make_step(tool_name="planner")
        s2 = _make_step(tool_name="web_search")
        s3 = _make_step(tool_name="read_file")
        trace = _make_trace(steps=[s1, s2, s3])

        seq = trace.tool_sequence
        assert seq == ["planner", "web_search", "read_file"]

    def test_get_step_and_get_children(self):
        parent = _make_step(step_id="p1", parent_id=None)
        child1 = _make_step(step_id="c1", parent_id="p1")
        child2 = _make_step(step_id="c2", parent_id="p1")
        other = _make_step(step_id="o1", parent_id=None)
        trace = _make_trace(steps=[parent, child1, child2, other])

        assert trace.get_step("p1") is not None
        assert trace.get_step("nonexistent") is None

        children = trace.get_children("p1")
        assert len(children) == 2
        child_ids = {c.step_id for c in children}
        assert child_ids == {"c1", "c2"}


class TestTraceStoreIdempotency:
    """Test idempotent re-saves and edge cases."""

    def test_resave_trace_updates(self, tmp_path):
        store = TraceStore(tmp_path / "traces.db")
        try:
            trace = _make_trace(
                trace_id="fixed-id",
                success_score=0.5,
                steps=[_make_step(step_id="s1", tool_name="web_search")],
            )
            store.save_trace(trace)

            # Re-save with updated data
            trace.success_score = 0.9
            trace.steps = [
                _make_step(step_id="s2", tool_name="shell_exec"),
                _make_step(step_id="s3", tool_name="read_file"),
            ]
            store.save_trace(trace)

            loaded = store.get_trace("fixed-id")
            assert loaded is not None
            assert loaded.success_score == 0.9, "Score should be updated"
            assert len(loaded.steps) == 2, "Steps should be replaced"
            assert loaded.steps[0].step_id == "s2"
        finally:
            store.close()

    def test_step_metadata_round_trip(self, tmp_path):
        store = TraceStore(tmp_path / "traces.db")
        try:
            meta = {"retries": 3, "source": "planner", "tags": ["important"]}
            s = _make_step(metadata=meta)
            trace = _make_trace(steps=[s])
            store.save_trace(trace)

            loaded = store.get_trace(trace.trace_id)
            assert loaded is not None
            assert loaded.steps[0].metadata == meta, "Metadata should survive JSON round-trip"
        finally:
            store.close()
