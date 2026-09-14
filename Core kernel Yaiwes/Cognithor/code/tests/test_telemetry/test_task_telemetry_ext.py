"""Extended tests fuer TaskTelemetryCollector -- fehlende Zeilen."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cognithor.telemetry.task_telemetry import TaskTelemetryCollector


class TestToolStats:
    def setup_method(self):
        self.collector = TaskTelemetryCollector()

    def teardown_method(self):
        self.collector.close()

    def test_tool_stats_basic(self):
        self.collector.record_task("s1", True, 100.0, ["read_file", "write_file"])
        self.collector.record_task("s2", False, 200.0, ["read_file", "exec_command"])
        stats = self.collector.get_tool_stats()
        assert "read_file" in stats
        assert stats["read_file"]["total"] == 2
        assert stats["read_file"]["errors"] == 1
        assert stats["write_file"]["total"] == 1
        assert stats["write_file"]["errors"] == 0

    def test_tool_stats_empty(self):
        stats = self.collector.get_tool_stats()
        assert stats == {}


class TestGetUnusedTools:
    def setup_method(self):
        self.collector = TaskTelemetryCollector()

    def teardown_method(self):
        self.collector.close()

    def test_unused_tools_none_since(self):
        result = self.collector.get_unused_tools(since=None)
        assert result == []

    def test_unused_tools_all_recent(self):
        self.collector.record_task("s1", True, 100.0, ["tool_a"])
        since = datetime.now(UTC) - timedelta(hours=1)
        result = self.collector.get_unused_tools(since=since)
        assert result == []

    def test_unused_tools_with_old_data(self):
        # Record a task (will have current timestamp)
        self.collector.record_task("s1", True, 100.0, ["tool_a", "tool_b"])
        # Query with future since (so all are "old")
        future = datetime.now(UTC) + timedelta(hours=1)
        result = self.collector.get_unused_tools(since=future)
        assert "tool_a" in result
        assert "tool_b" in result


class TestToolLatencyProfileExtended:
    def setup_method(self):
        self.collector = TaskTelemetryCollector()

    def teardown_method(self):
        self.collector.close()

    def test_multiple_tools_per_task(self):
        self.collector.record_task("s1", True, 300.0, ["a", "b", "c"])
        profile = self.collector.get_tool_latency_profile()
        assert "a" in profile
        assert "b" in profile
        assert "c" in profile
        # 300 / 3 = 100 per tool
        assert profile["a"]["avg"] == 100.0

    def test_empty_tools_list(self):
        self.collector.record_task("s1", True, 100.0, [])
        profile = self.collector.get_tool_latency_profile()
        assert profile == {}

    def test_p95_p99_with_many_records(self):
        for i in range(20):
            self.collector.record_task(f"s{i}", True, float(i * 10), ["tool_x"])
        profile = self.collector.get_tool_latency_profile()
        assert "tool_x" in profile
        assert "p95" in profile["tool_x"]
        assert "p99" in profile["tool_x"]


class TestHourlyStatsExtended:
    def setup_method(self):
        self.collector = TaskTelemetryCollector()

    def teardown_method(self):
        self.collector.close()

    def test_hourly_stats_multiple_tasks(self):
        for i in range(5):
            self.collector.record_task(f"s{i}", i % 2 == 0, float(i * 50))
        stats = self.collector.get_hourly_stats(hours=1)
        assert len(stats) >= 1
        assert stats[0]["total"] == 5
        assert "success_rate" in stats[0]
        assert "avg_duration_ms" in stats[0]


class TestDbPath:
    def test_file_based_db(self, tmp_path):
        db_file = tmp_path / "test.db"
        collector = TaskTelemetryCollector(db_path=db_file)
        collector.record_task("s1", True, 100.0)
        assert collector.get_total_tasks() == 1
        collector.close()

    def test_close_idempotent(self):
        collector = TaskTelemetryCollector()
        collector.close()
        collector.close()  # Should not crash
