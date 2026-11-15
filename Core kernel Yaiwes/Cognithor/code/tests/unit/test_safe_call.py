"""Tests for jarvis.core.safe_call."""

from __future__ import annotations

import pytest

from cognithor.core.safe_call import (
    _safe_call,
    _safe_call_async,
    clear_failures,
    get_failure_report,
    has_failures,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure a clean failure registry for every test."""
    clear_failures()
    yield
    clear_failures()


class TestSafeCall:
    def test_success_returns_value(self):
        result = _safe_call("test", lambda: 42)
        assert result == 42

    def test_success_with_args(self):
        result = _safe_call("test", lambda x, y: x + y, 3, 4)
        assert result == 7

    def test_failure_returns_none(self):
        def broken():
            raise RuntimeError("boom")

        result = _safe_call("broken_subsystem", broken)
        assert result is None

    def test_failure_records_in_registry(self):
        def broken():
            raise ValueError("bad config")

        _safe_call("my_subsystem", broken)
        report = get_failure_report()
        assert "my_subsystem" in report
        assert len(report["my_subsystem"]) == 1
        assert "ValueError" in report["my_subsystem"][0]
        assert "bad config" in report["my_subsystem"][0]

    def test_multiple_failures_accumulate(self):
        def broken():
            raise RuntimeError("fail")

        _safe_call("sub_a", broken)
        _safe_call("sub_a", broken)
        _safe_call("sub_b", broken)

        report = get_failure_report()
        assert len(report["sub_a"]) == 2
        assert len(report["sub_b"]) == 1

    def test_has_failures_false_when_clean(self):
        assert has_failures() is False

    def test_has_failures_true_after_failure(self):
        _safe_call("x", lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        assert has_failures() is True

    def test_clear_failures(self):
        _safe_call("x", lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        assert has_failures() is True
        clear_failures()
        assert has_failures() is False
        assert get_failure_report() == {}

    def test_execution_continues_after_failure(self):
        results = []
        _safe_call("a", lambda: (_ for _ in ()).throw(RuntimeError))
        results.append("continued")
        _safe_call("b", lambda: results.append("b_ok"))
        assert results == ["continued", "b_ok"]


class TestSafeCallAsync:
    @pytest.mark.asyncio
    async def test_async_success(self):
        async def ok():
            return 99

        result = await _safe_call_async("async_ok", ok)
        assert result == 99

    @pytest.mark.asyncio
    async def test_async_failure(self):
        async def broken():
            raise RuntimeError("async boom")

        result = await _safe_call_async("async_broken", broken)
        assert result is None
        assert "async_broken" in get_failure_report()
        assert "async boom" in get_failure_report()["async_broken"][0]
