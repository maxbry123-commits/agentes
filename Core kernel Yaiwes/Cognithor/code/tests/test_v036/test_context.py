"""Tests for Feature 4: Per-Agent Isolated Context Windows."""

from __future__ import annotations

import time

from cognithor.core.context_window import ContextEntry, ContextWindow


class TestIsolation:
    def test_contexts_are_isolated_between_agents(self):
        """Two context windows do not share state."""
        ctx_a = ContextWindow(max_tokens=100)
        ctx_b = ContextWindow(max_tokens=100)

        ctx_a.add(ContextEntry(content="agent A data", tokens=20))
        assert ctx_a.entry_count == 1
        assert ctx_b.entry_count == 0

        ctx_b.add(ContextEntry(content="agent B data", tokens=30))
        assert ctx_a.total_tokens == 20
        assert ctx_b.total_tokens == 30


class TestTrimming:
    def test_time_weighted_trim_removes_oldest_first(self):
        """Oldest entries are removed first due to time decay."""
        ctx = ContextWindow(max_tokens=50, retention_half_life_minutes=1)

        # Add an "old" entry with a timestamp in the past
        old_entry = ContextEntry(content="old", tokens=20, timestamp=time.monotonic() - 120)
        new_entry = ContextEntry(content="new", tokens=20)
        ctx._entries = [old_entry, new_entry]

        # Add one more to exceed budget
        ctx.add(ContextEntry(content="latest", tokens=20))

        # Old entry should be trimmed (lowest weight due to age decay)
        contents = [e.content for e in ctx._entries]
        assert "old" not in contents
        assert "new" in contents
        assert "latest" in contents

    def test_system_messages_never_trimmed(self):
        """System messages (importance=1.0, type=system) survive trimming."""
        ctx = ContextWindow(max_tokens=30)

        sys_entry = ContextEntry(content="system", tokens=15, entry_type="system", importance=1.0)
        normal_entry = ContextEntry(
            content="normal",
            tokens=15,
            importance=0.3,
            timestamp=time.monotonic() - 3600,
        )
        ctx._entries = [sys_entry, normal_entry]

        # Exceed budget
        ctx.add(ContextEntry(content="extra", tokens=15))

        contents = [e.content for e in ctx._entries]
        assert "system" in contents  # Protected
        assert "normal" not in contents  # Trimmed

    def test_tool_results_never_trimmed(self):
        """Tool results are protected from trimming."""
        ctx = ContextWindow(max_tokens=30)

        tool_entry = ContextEntry(
            content="tool output", tokens=15, entry_type="tool_result", importance=1.0
        )
        msg = ContextEntry(
            content="msg",
            tokens=15,
            importance=0.2,
            timestamp=time.monotonic() - 3600,
        )
        ctx._entries = [tool_entry, msg]

        ctx.add(ContextEntry(content="new", tokens=15))

        contents = [e.content for e in ctx._entries]
        assert "tool output" in contents
        assert "msg" not in contents


class TestTokenBudget:
    def test_context_window_respects_max_tokens(self):
        """Total tokens never exceed max_tokens after trim."""
        ctx = ContextWindow(max_tokens=50)
        for i in range(10):
            ctx.add(ContextEntry(content=f"entry-{i}", tokens=15, importance=0.3))

        assert ctx.total_tokens <= 50


class TestSnapshotRestore:
    def test_context_snapshot_and_restore(self):
        """Round-trip: snapshot -> new window -> restore -> same state."""
        ctx = ContextWindow(max_tokens=200, retention_half_life_minutes=45)
        ctx.add(ContextEntry(content="hello", tokens=10, importance=0.8))
        ctx.add(ContextEntry(content="world", tokens=12, entry_type="system"))

        snap = ctx.snapshot()

        ctx2 = ContextWindow()
        ctx2.restore(snap)

        assert ctx2.max_tokens == 200
        assert ctx2.retention_half_life_minutes == 45
        assert ctx2.entry_count == 2
        assert ctx2._entries[0].content == "hello"
        assert ctx2._entries[1].entry_type == "system"
        assert ctx2.total_tokens == 22
