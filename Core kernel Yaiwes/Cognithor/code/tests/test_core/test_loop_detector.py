"""Tests fuer die Tool-Loop-Detection."""

from __future__ import annotations

from cognithor.core.loop_detector import (
    GUARDED_TOOL_NAMES,
    NO_PROGRESS_REPEAT_THRESHOLD,
    PING_PONG_THRESHOLD,
    ToolLoopDetector,
)


class TestToolLoopDetector:
    def test_no_loop_on_first_call(self):
        d = ToolLoopDetector()
        r = d.detect("web_search", {"q": "test"})
        assert not r.stuck

    def test_no_loop_on_unguarded_tool(self):
        d = ToolLoopDetector()
        for _ in range(10):
            d.record("calculator", {"expr": "1+1"}, "2", False)
        r = d.detect("calculator", {"expr": "1+1"})
        assert not r.stuck

    def test_generic_repeat_detected(self):
        d = ToolLoopDetector()
        args = {"q": "same query"}
        for _ in range(NO_PROGRESS_REPEAT_THRESHOLD):
            d.record("web_search", args, "same result", False)
        r = d.detect("web_search", args)
        assert r.stuck
        assert r.detector == "generic_repeat"
        assert r.count == NO_PROGRESS_REPEAT_THRESHOLD + 1

    def test_no_repeat_with_different_results(self):
        d = ToolLoopDetector()
        args = {"q": "query"}
        for i in range(NO_PROGRESS_REPEAT_THRESHOLD):
            d.record("web_search", args, f"result_{i}", False)
        r = d.detect("web_search", args)
        assert not r.stuck

    def test_no_repeat_with_different_args(self):
        d = ToolLoopDetector()
        for i in range(NO_PROGRESS_REPEAT_THRESHOLD):
            d.record("web_search", {"q": f"query_{i}"}, "same", False)
        r = d.detect("web_search", {"q": "query_new"})
        assert not r.stuck

    def test_ping_pong_detected(self):
        d = ToolLoopDetector()
        args_a = {"q": "search A"}
        args_b = {"path": "/file"}
        # generic_repeat threshold is 4, so we stay just below by
        # alternating. With 3 of each, generic_repeat won't fire but
        # ping_pong (threshold 6) will fire at 7 alternations.
        for _ in range(3):
            d.record("web_search", args_a, "result_a", False)
            d.record("fs_read", args_b, "result_b", False)
        d.record("web_search", args_a, "result_a", False)
        # 7 entries alternating: web, fs, web, fs, web, fs, web
        # Next detect for fs_read should trigger ping_pong
        r = d.detect("fs_read", args_b)
        # Either ping_pong or generic_repeat is fine — both indicate stuck
        assert r.stuck

    def test_no_ping_pong_with_progress(self):
        d = ToolLoopDetector()
        args_a = {"q": "search"}
        args_b = {"path": "/file"}
        for i in range(PING_PONG_THRESHOLD // 2):
            d.record("web_search", args_a, f"result_a_{i}", False)
            d.record("fs_read", args_b, f"result_b_{i}", False)
        r = d.detect("web_search", args_a)
        assert not r.stuck  # Results changed each time

    def test_reset_clears_history(self):
        d = ToolLoopDetector()
        args = {"q": "test"}
        for _ in range(NO_PROGRESS_REPEAT_THRESHOLD):
            d.record("web_search", args, "same", False)
        d.reset()
        r = d.detect("web_search", args)
        assert not r.stuck
        assert d.history_size == 0

    def test_sliding_window(self):
        d = ToolLoopDetector()
        # Fill beyond window size
        for i in range(30):
            d.record("web_search", {"q": f"q{i}"}, f"r{i}", False)
        assert d.history_size == 24  # TOOL_CALL_HISTORY_SIZE

    def test_guarded_tools_list(self):
        assert "web_search" in GUARDED_TOOL_NAMES
        assert "shell_exec" in GUARDED_TOOL_NAMES
        assert "calculator" not in GUARDED_TOOL_NAMES

    def test_message_content(self):
        d = ToolLoopDetector()
        args = {"q": "stuck"}
        for _ in range(NO_PROGRESS_REPEAT_THRESHOLD):
            d.record("web_search", args, "same", False)
        r = d.detect("web_search", args)
        assert "web_search" in r.message
        assert "identischen" in r.message or "Tool-Loop" in r.message
