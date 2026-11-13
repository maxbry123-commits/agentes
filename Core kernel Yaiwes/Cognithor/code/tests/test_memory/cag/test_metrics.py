from __future__ import annotations

import pytest

from cognithor.memory.cag.metrics import CAGMetricsCollector


class TestCAGMetricsCollector:
    def test_record_hit(self):
        c = CAGMetricsCollector()
        c.record_hit("hash1")
        m = c.get_metrics()
        assert m.prefix_hits == 1
        assert m.prefix_misses == 0

    def test_record_miss(self):
        c = CAGMetricsCollector()
        c.record_miss("hash2")
        m = c.get_metrics()
        assert m.prefix_misses == 1
        assert m.prefix_hits == 0

    def test_hit_rate(self):
        c = CAGMetricsCollector()
        c.record_hit("h")
        c.record_hit("h")
        c.record_hit("h")
        c.record_miss("h")
        assert c.get_metrics().hit_rate == pytest.approx(0.75)

    def test_record_build(self):
        c = CAGMetricsCollector()
        c.record_build(150.0)
        c.record_build(50.0)
        m = c.get_metrics()
        assert m.total_builds == 2
        assert m.total_build_ms == pytest.approx(200.0)

    def test_prefix_hash_tracking(self):
        c = CAGMetricsCollector()
        c.record_hit("aaa")
        assert c.get_metrics().last_prefix_hash == "aaa"
        c.record_miss("bbb")
        assert c.get_metrics().last_prefix_hash == "bbb"

    def test_reset(self):
        c = CAGMetricsCollector()
        c.record_hit("x")
        c.record_build(100.0)
        c.reset()
        m = c.get_metrics()
        assert m.prefix_hits == 0
        assert m.total_builds == 0
        assert m.total_build_ms == 0.0
        assert m.last_prefix_hash == ""
