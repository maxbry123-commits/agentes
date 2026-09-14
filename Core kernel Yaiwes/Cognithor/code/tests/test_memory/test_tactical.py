"""Tests for memory/tactical.py · Tier 3 Tactical Memory."""

from __future__ import annotations

import time

import pytest

from cognithor.memory.tactical import TacticalMemory, ToolEffectiveness, ToolOutcome

# ---------------------------------------------------------------------------
# TestToolOutcome
# ---------------------------------------------------------------------------


class TestToolOutcome:
    def test_create(self):
        now = time.time()
        outcome = ToolOutcome(
            tool_name="web_search",
            params_hash="abc123def456",
            success=True,
            duration_ms=120,
            context_hash="ctx000111222",
            timestamp=now,
        )
        assert outcome.tool_name == "web_search"
        assert outcome.success is True
        assert outcome.duration_ms == 120
        assert outcome.error_snippet is None
        assert outcome.caused_replan is False

    def test_with_error(self):
        now = time.time()
        outcome = ToolOutcome(
            tool_name="shell_exec",
            params_hash="000aaa111bbb",
            success=False,
            duration_ms=500,
            context_hash="ctx999888777",
            timestamp=now,
            error_snippet="Permission denied",
            caused_replan=True,
        )
        assert outcome.success is False
        assert outcome.error_snippet == "Permission denied"
        assert outcome.caused_replan is True


# ---------------------------------------------------------------------------
# TestToolEffectiveness
# ---------------------------------------------------------------------------


class TestToolEffectiveness:
    def test_default_values(self):
        eff = ToolEffectiveness()
        assert eff.total == 0
        assert eff.successes == 0
        assert eff.failures == 0
        assert eff.avg_duration_ms == 0.0
        assert eff.consecutive_failures == 0
        assert eff.last_success_at is None
        assert eff.last_failure_at is None
        assert eff.contexts_succeeded == set()
        assert eff.contexts_failed == set()

    def test_effectiveness_score(self):
        eff = ToolEffectiveness(total=10, successes=7, failures=3)
        assert eff.effectiveness == pytest.approx(0.7)

    def test_effectiveness_zero_total(self):
        eff = ToolEffectiveness()
        assert eff.effectiveness == 0.5


# ---------------------------------------------------------------------------
# TestRecordOutcome
# ---------------------------------------------------------------------------


class TestRecordOutcome:
    def test_record_success(self):
        tm = TacticalMemory()
        tm.record_outcome("tool_a", {}, True, 100, "ctx1")
        assert tm.get_tool_effectiveness("tool_a") == pytest.approx(1.0)

    def test_record_failure(self):
        tm = TacticalMemory()
        tm.record_outcome("tool_b", {}, False, 200, "ctx1", error="timeout")
        assert tm.get_tool_effectiveness("tool_b") == pytest.approx(0.0)

    def test_mixed_outcomes(self):
        tm = TacticalMemory()
        tm.record_outcome("tool_c", {}, True, 100, "ctx1")
        tm.record_outcome("tool_c", {}, True, 100, "ctx2")
        tm.record_outcome("tool_c", {}, False, 150, "ctx3")
        eff = tm.get_tool_effectiveness("tool_c")
        assert eff == pytest.approx(2 / 3)

    def test_unknown_tool(self):
        tm = TacticalMemory()
        assert tm.get_tool_effectiveness("nonexistent_tool") == 0.5

    def test_max_outcomes_respected(self):
        tm = TacticalMemory(max_outcomes=5)
        for i in range(10):
            tm.record_outcome("tool_x", {"i": i}, True, 10, "ctx")
        assert len(tm._outcomes) == 5

    def test_outcome_stored(self):
        tm = TacticalMemory()
        tm.record_outcome("tool_d", {"key": "val"}, True, 75, "some context")
        assert len(tm._outcomes) == 1
        outcome = tm._outcomes[0]
        assert outcome.tool_name == "tool_d"
        assert outcome.success is True
        assert outcome.duration_ms == 75


# ---------------------------------------------------------------------------
# TestAvoidanceRules
# ---------------------------------------------------------------------------


class TestAvoidanceRules:
    def test_no_avoidance_on_first(self):
        tm = TacticalMemory(avoidance_consecutive_failures=3)
        tm.record_outcome("tool_e", {}, False, 100, "ctx")
        assert tm.check_avoidance("tool_e", {}) is None

    def test_avoidance_after_n_failures(self):
        tm = TacticalMemory(avoidance_consecutive_failures=3)
        for _ in range(3):
            tm.record_outcome("tool_f", {}, False, 100, "ctx", error="err")
        rule = tm.check_avoidance("tool_f", {})
        assert rule is not None
        assert rule.tool_name == "tool_f"

    def test_success_resets(self):
        tm = TacticalMemory(avoidance_consecutive_failures=3)
        for _ in range(3):
            tm.record_outcome("tool_g", {}, False, 100, "ctx")
        assert tm.check_avoidance("tool_g", {}) is not None
        # A success should clear the rule
        tm.record_outcome("tool_g", {}, True, 100, "ctx")
        assert tm.check_avoidance("tool_g", {}) is None

    def test_rule_expires(self):
        # Use a very short TTL so the rule expires quickly
        tm = TacticalMemory(avoidance_consecutive_failures=3, ttl_hours=0.0001)
        for _ in range(3):
            tm.record_outcome("tool_h", {}, False, 100, "ctx")
        assert tm.check_avoidance("tool_h", {}) is not None
        time.sleep(0.5)
        assert tm.check_avoidance("tool_h", {}) is None

    def test_success_removes_active_rule(self):
        tm = TacticalMemory(avoidance_consecutive_failures=2)
        tm.record_outcome("tool_i", {}, False, 100, "ctx")
        tm.record_outcome("tool_i", {}, False, 100, "ctx")
        assert tm.check_avoidance("tool_i", {}) is not None
        tm.record_outcome("tool_i", {}, True, 100, "ctx")
        active_rules = [r for r in tm._avoidance_rules if r.tool_name == "tool_i"]
        assert len(active_rules) == 0


# ---------------------------------------------------------------------------
# TestInsights
# ---------------------------------------------------------------------------


class TestInsights:
    def test_empty_returns_empty(self):
        tm = TacticalMemory()
        assert tm.get_insights_for_llm("context") == ""

    def test_includes_tool_data(self):
        tm = TacticalMemory()
        tm.record_outcome("web_search", {}, True, 100, "ctx")
        tm.record_outcome("web_search", {}, True, 120, "ctx")
        result = tm.get_insights_for_llm("ctx")
        assert "web_search" in result
        assert "100%" in result

    def test_includes_avoidance_warning(self):
        tm = TacticalMemory(avoidance_consecutive_failures=2)
        tm.record_outcome("bad_tool", {}, False, 100, "ctx")
        tm.record_outcome("bad_tool", {}, False, 100, "ctx")
        result = tm.get_insights_for_llm("ctx")
        assert "WARNUNG" in result
        assert "bad_tool" in result

    def test_respects_max_chars(self):
        tm = TacticalMemory()
        for i in range(20):
            tm.record_outcome(f"tool_{i:02d}", {}, True, 100, "ctx")
        result = tm.get_insights_for_llm("ctx", max_chars=100)
        assert len(result) <= 100


# ---------------------------------------------------------------------------
# TestPersistence
# ---------------------------------------------------------------------------


class TestPersistence:
    def test_flush_and_load(self, tmp_path):
        db = tmp_path / "tactical.db"
        tm = TacticalMemory(db_path=db)
        tm.record_outcome("tool_persist", {}, True, 150, "ctx_p")
        tm.record_outcome("tool_persist", {}, False, 200, "ctx_p", error="oops")
        written = tm.flush_to_db()
        assert written >= 1
        tm.close()

        tm2 = TacticalMemory(db_path=db)
        loaded = tm2.load_from_db()
        assert loaded >= 1
        assert "tool_persist" in tm2._effectiveness
        eff = tm2._effectiveness["tool_persist"]
        assert eff.total == 2
        assert eff.successes == 1
        assert eff.failures == 1

    def test_avoidance_rules_persisted(self, tmp_path):
        db = tmp_path / "tactical_rules.db"
        tm = TacticalMemory(db_path=db, avoidance_consecutive_failures=2)
        tm.record_outcome("bad_tool2", {}, False, 100, "ctx")
        tm.record_outcome("bad_tool2", {}, False, 100, "ctx")
        assert tm.check_avoidance("bad_tool2", {}) is not None
        tm.flush_to_db()
        tm.close()

        tm2 = TacticalMemory(db_path=db)
        tm2.load_from_db()
        assert tm2.check_avoidance("bad_tool2", {}) is not None

    def test_flush_only_high_confidence(self, tmp_path):
        db = tmp_path / "tactical_hc.db"
        tm = TacticalMemory(db_path=db)
        # Record multiple tools; flush should write all effectiveness rows
        for tool in ["alpha", "beta", "gamma"]:
            tm.record_outcome(tool, {}, True, 100, "ctx")
        written = tm.flush_to_db()
        assert written >= 3
        tm.close()


# ---------------------------------------------------------------------------
# TestStats
# ---------------------------------------------------------------------------


class TestStats:
    def test_stats_structure(self):
        tm = TacticalMemory()
        stats = tm.get_stats()
        assert "outcomes_count" in stats
        assert "tools_tracked" in stats
        assert "avoidance_rules_active" in stats

    def test_stats_after_recording(self):
        tm = TacticalMemory(avoidance_consecutive_failures=2)
        tm.record_outcome("tool_s1", {}, True, 100, "ctx")
        tm.record_outcome("tool_s2", {}, False, 100, "ctx")
        tm.record_outcome("tool_s2", {}, False, 100, "ctx")
        stats = tm.get_stats()
        assert stats["outcomes_count"] == 3
        assert stats["tools_tracked"] == 2
        assert stats["avoidance_rules_active"] == 1
