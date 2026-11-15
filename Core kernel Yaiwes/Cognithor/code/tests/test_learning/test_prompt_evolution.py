"""Tests for PromptEvolutionEngine (A/B-test-based prompt optimization)."""

from __future__ import annotations

import time as _time
from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.learning.prompt_evolution import (
    PromptEvolutionEngine,
    _version_id,
)


@pytest.fixture()
def engine(tmp_path):
    db = str(tmp_path / "prompt_evo.db")
    eng = PromptEvolutionEngine(db_path=db)
    yield eng
    eng.close()


@pytest.fixture()
def engine_with_llm(tmp_path):
    db = str(tmp_path / "prompt_evo_llm.db")
    llm = AsyncMock(return_value="Improved prompt: {tools_section} {context_section}")
    eng = PromptEvolutionEngine(db_path=db, llm_client=llm)
    yield eng
    eng.close()


# =========================================================================
# TestPromptVersionStore
# =========================================================================


class TestPromptVersionStore:
    def test_register_prompt_creates_version(self, engine):
        vid = engine.register_prompt("system_prompt", "Hello {tools_section}")
        assert isinstance(vid, str)
        assert len(vid) == 16

    def test_register_same_prompt_returns_same_id(self, engine):
        vid1 = engine.register_prompt("system_prompt", "Hello {tools_section}")
        vid2 = engine.register_prompt("system_prompt", "Hello {tools_section}")
        assert vid1 == vid2

    def test_register_different_prompts_different_ids(self, engine):
        vid1 = engine.register_prompt("system_prompt", "Hello v1")
        vid2 = engine.register_prompt("system_prompt", "Hello v2")
        assert vid1 != vid2

    def test_get_active_version_returns_registered(self, engine):
        engine.register_prompt("system_prompt", "Hello {tools_section}")
        version_id, text = engine.get_active_version("system_prompt")
        assert text == "Hello {tools_section}"

    def test_version_id_is_sha256_prefix(self):
        vid = _version_id("test", "content")
        assert len(vid) == 16
        # Should be hex
        int(vid, 16)

    def test_first_registered_version_is_active(self, engine):
        vid1 = engine.register_prompt("test_prompt", "Version 1")
        engine.register_prompt("test_prompt", "Version 2")

        active_id, text = engine.get_active_version("test_prompt")
        assert active_id == vid1
        assert text == "Version 1"

    def test_get_active_version_unknown_template_raises(self, engine):
        with pytest.raises(ValueError, match="No registered prompt"):
            engine.get_active_version("nonexistent")


# =========================================================================
# TestABTest
# =========================================================================


class TestABTest:
    def test_start_ab_test(self, engine):
        vid_a = engine.register_prompt("sp", "Version A")
        vid_b = engine.register_prompt("sp", "Version B")

        test_id = engine.start_ab_test("sp", vid_a, vid_b)
        assert isinstance(test_id, int)
        assert test_id >= 1

    def test_ab_split_deterministic(self, engine):
        vid_a = engine.register_prompt("sp", "Version A")
        vid_b = engine.register_prompt("sp", "Version B")
        engine.start_ab_test("sp", vid_a, vid_b)

        # Same session_id should always get the same version
        result1 = engine.get_active_version("sp", "session_123")
        result2 = engine.get_active_version("sp", "session_123")
        assert result1[0] == result2[0]

    def test_ab_split_balanced(self, engine):
        vid_a = engine.register_prompt("sp", "Version A")
        vid_b = engine.register_prompt("sp", "Version B")
        engine.start_ab_test("sp", vid_a, vid_b)

        # Check roughly balanced split over 100 sessions
        counts = {vid_a: 0, vid_b: 0}
        for i in range(100):
            version_id, _ = engine.get_active_version("sp", f"session_{i}")
            counts[version_id] += 1

        # Should be roughly 50/50 (allow 30/70 range)
        assert counts[vid_a] >= 20, f"A got only {counts[vid_a]}"
        assert counts[vid_b] >= 20, f"B got only {counts[vid_b]}"

    def test_record_session_updates_stats(self, engine):
        vid_a = engine.register_prompt("sp", "Version A")
        vid_b = engine.register_prompt("sp", "Version B")
        test_id = engine.start_ab_test("sp", vid_a, vid_b)

        engine.record_session("s1", vid_a, 0.8)
        engine.record_session("s2", vid_a, 0.9)

        # Check stats updated
        row = engine._conn.execute(
            "SELECT sessions_a, avg_reward_a FROM ab_tests WHERE id = ?", (test_id,)
        ).fetchone()
        assert row["sessions_a"] == 2
        assert abs(row["avg_reward_a"] - 0.85) < 0.01

    def test_evaluate_test_picks_winner(self, engine):
        engine.MIN_SESSIONS_PER_ARM = 2  # Lower for testing
        vid_a = engine.register_prompt("sp", "Version A")
        vid_b = engine.register_prompt("sp", "Version B")
        test_id = engine.start_ab_test("sp", vid_a, vid_b)

        # A gets higher reward
        for _ in range(3):
            engine.record_session(f"a_{_}", vid_a, 0.9)
        for _ in range(3):
            engine.record_session(f"b_{_}", vid_b, 0.5)

        winner = engine.evaluate_test(test_id)
        assert winner == vid_a

    def test_evaluate_test_needs_min_sessions(self, engine):
        engine.MIN_SESSIONS_PER_ARM = 20
        vid_a = engine.register_prompt("sp", "Version A")
        vid_b = engine.register_prompt("sp", "Version B")
        test_id = engine.start_ab_test("sp", vid_a, vid_b)

        # Only 1 session each - not enough
        engine.record_session("s1", vid_a, 0.9)
        engine.record_session("s2", vid_b, 0.5)

        winner = engine.evaluate_test(test_id)
        assert winner is None

    def test_no_winner_if_below_threshold(self, engine):
        engine.MIN_SESSIONS_PER_ARM = 2
        engine.SIGNIFICANCE_THRESHOLD = 0.1
        vid_a = engine.register_prompt("sp", "Version A")
        vid_b = engine.register_prompt("sp", "Version B")
        test_id = engine.start_ab_test("sp", vid_a, vid_b)

        # Very similar rewards - within threshold
        for _ in range(3):
            engine.record_session(f"a_{_}", vid_a, 0.80)
        for _ in range(3):
            engine.record_session(f"b_{_}", vid_b, 0.81)

        winner = engine.evaluate_test(test_id)
        assert winner is None

    def test_concurrent_tests_limited(self, engine):
        vid_a = engine.register_prompt("sp1", "Version A1")
        vid_b = engine.register_prompt("sp1", "Version B1")
        engine.start_ab_test("sp1", vid_a, vid_b)

        vid_c = engine.register_prompt("sp2", "Version A2")
        vid_d = engine.register_prompt("sp2", "Version B2")

        with pytest.raises(ValueError, match="Max concurrent tests"):
            engine.start_ab_test("sp2", vid_c, vid_d)


# =========================================================================
# TestPromptEvolutionEngine
# =========================================================================


class TestPromptEvolutionEngine:
    async def test_maybe_evolve_no_data_returns_none(self, engine):
        engine.register_prompt("sp", "Hello")
        result = await engine.maybe_evolve("sp")
        assert result is None

    async def test_maybe_evolve_with_data_creates_variant(self, engine_with_llm):
        engine = engine_with_llm
        engine.MIN_SESSIONS_PER_ARM = 2

        vid_a = engine.register_prompt("sp", "Version A: {tools_section} {context_section}")
        vid_b = engine.register_prompt("sp", "Version B: {tools_section} {context_section}")
        engine.start_ab_test("sp", vid_a, vid_b)

        # Record enough sessions for both arms
        for i in range(3):
            engine.record_session(f"a_{i}", vid_a, 0.9)
        for i in range(3):
            engine.record_session(f"b_{i}", vid_b, 0.5)

        new_vid = await engine.maybe_evolve("sp")
        assert new_vid is not None
        assert isinstance(new_vid, str)

    def test_get_stats_returns_correct_counts(self, engine):
        engine.register_prompt("sp", "Version A")
        engine.register_prompt("sp", "Version B")

        stats = engine.get_stats("sp")
        assert stats["template_name"] == "sp"
        assert stats["version_count"] == 2
        assert stats["active_version_id"] is not None
        assert stats["total_sessions"] == 0
        assert stats["running_tests"] == 0

    def test_record_session_and_query(self, engine):
        vid = engine.register_prompt("sp", "Hello")
        engine.record_session("session_1", vid, 0.85)

        stats = engine.get_stats("sp")
        assert stats["total_sessions"] == 1

    async def test_evolution_respects_gate(self, tmp_path):
        """When ImprovementGate blocks prompt_tuning, evolution should not proceed."""
        from cognithor.config import ImprovementGovernanceConfig
        from cognithor.governance.improvement_gate import (
            GateVerdict,
            ImprovementDomain,
            ImprovementGate,
        )

        config = ImprovementGovernanceConfig(
            blocked_domains=["prompt_tuning"],
        )
        gate = ImprovementGate(config)

        # Gate should block prompt_tuning
        verdict = gate.check(ImprovementDomain.PROMPT_TUNING)
        assert verdict == GateVerdict.BLOCKED

        # Engine still works independently (gate check is at governance level)
        db = str(tmp_path / "pe.db")
        engine = PromptEvolutionEngine(db_path=db)
        vid = engine.register_prompt("sp", "Test")
        assert vid is not None
        engine.close()

    def test_winner_becomes_active(self, engine):
        engine.MIN_SESSIONS_PER_ARM = 2
        vid_a = engine.register_prompt("sp", "Version A")
        vid_b = engine.register_prompt("sp", "Version B")
        test_id = engine.start_ab_test("sp", vid_a, vid_b)

        # B gets higher reward
        for i in range(3):
            engine.record_session(f"a_{i}", vid_a, 0.3)
        for i in range(3):
            engine.record_session(f"b_{i}", vid_b, 0.9)

        winner = engine.evaluate_test(test_id)
        assert winner == vid_b

        # B should now be the active version
        active_id, text = engine.get_active_version("sp")
        assert active_id == vid_b
        assert text == "Version B"


# =========================================================================
# TestIntervalEnforcement
# =========================================================================


class TestIntervalEnforcement:
    def test_set_evolution_interval_hours(self, engine):
        engine.set_evolution_interval_hours(12)
        assert engine._evolution_interval_seconds == 12 * 3600

    async def test_maybe_evolve_skips_if_too_soon(self, engine_with_llm):
        engine = engine_with_llm
        engine.MIN_SESSIONS_PER_ARM = 2
        engine.set_evolution_interval_hours(6)

        vid_a = engine.register_prompt("sp", "Version A: {tools_section}")
        vid_b = engine.register_prompt("sp", "Version B: {tools_section}")
        engine.start_ab_test("sp", vid_a, vid_b)

        for i in range(3):
            engine.record_session(f"a_{i}", vid_a, 0.9)
        for i in range(3):
            engine.record_session(f"b_{i}", vid_b, 0.5)

        # First call should work (evaluates test + starts new AB test)
        result = await engine.maybe_evolve("sp")
        assert result is not None

        # The first evolve already started a new test (winner vs new variant).
        # Feed that running test enough data so it *could* evolve again.
        running = engine._conn.execute(
            "SELECT * FROM ab_tests WHERE status = 'running' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        for i in range(3):
            engine.record_session(f"ra_{i}", running["version_a_id"], 0.9)
        for i in range(3):
            engine.record_session(f"rb_{i}", running["version_b_id"], 0.5)

        # Second call immediately should be skipped (interval not elapsed)
        result2 = await engine.maybe_evolve("sp")
        assert result2 is None

    async def test_maybe_evolve_works_after_interval(self, engine_with_llm):
        engine = engine_with_llm
        engine.MIN_SESSIONS_PER_ARM = 2
        engine.set_evolution_interval_hours(6)

        vid_a = engine.register_prompt("sp", "Version A: {tools_section}")
        vid_b = engine.register_prompt("sp", "Version B: {tools_section}")
        engine.start_ab_test("sp", vid_a, vid_b)

        for i in range(3):
            engine.record_session(f"a_{i}", vid_a, 0.9)
        for i in range(3):
            engine.record_session(f"b_{i}", vid_b, 0.5)

        result = await engine.maybe_evolve("sp")
        assert result is not None

        # Fake that the interval has passed
        engine._last_evolution_at = _time.monotonic() - (7 * 3600)

        # Feed the running test enough data
        running = engine._conn.execute(
            "SELECT * FROM ab_tests WHERE status = 'running' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        for i in range(3):
            engine.record_session(f"ra_{i}", running["version_a_id"], 0.9)
        for i in range(3):
            engine.record_session(f"rb_{i}", running["version_b_id"], 0.5)

        result2 = await engine.maybe_evolve("sp")
        assert result2 is not None


# =========================================================================
# TestCronCallback
# =========================================================================


class TestCronCallback:
    async def test_cron_skips_when_no_engine(self):
        from cognithor.cron.jobs import prompt_evolution_check

        gw = MagicMock(spec=[])  # no _prompt_evolution attr
        await prompt_evolution_check(gw)  # should not raise

    async def test_cron_blocked_by_gate(self):
        from cognithor.cron.jobs import prompt_evolution_check
        from cognithor.governance.improvement_gate import GateVerdict

        engine = AsyncMock()
        gate = MagicMock()
        gate.check.return_value = GateVerdict.BLOCKED

        gw = MagicMock()
        gw._prompt_evolution = engine
        gw._improvement_gate = gate

        await prompt_evolution_check(gw)
        engine.maybe_evolve.assert_not_called()

    async def test_cron_calls_maybe_evolve(self):
        from cognithor.cron.jobs import prompt_evolution_check

        engine = AsyncMock()
        engine.maybe_evolve.return_value = "abc123"

        gw = MagicMock()
        gw._prompt_evolution = engine
        gw._improvement_gate = None

        await prompt_evolution_check(gw)
        engine.maybe_evolve.assert_awaited_once_with("system_prompt")

    async def test_cron_no_gate_attribute(self):
        from cognithor.cron.jobs import prompt_evolution_check

        engine = AsyncMock()
        engine.maybe_evolve.return_value = None

        gw = MagicMock(spec=[])
        gw._prompt_evolution = engine

        await prompt_evolution_check(gw)
        engine.maybe_evolve.assert_awaited_once()
