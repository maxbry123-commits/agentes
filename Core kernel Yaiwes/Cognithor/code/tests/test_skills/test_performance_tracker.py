"""Tests for Adaptive Skill-Performance-Tracking."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from cognithor.skills.performance_tracker import (
    DegradationConfig,
    SkillPerformanceTracker,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cfg(**overrides: object) -> DegradationConfig:
    return DegradationConfig(**overrides)  # type: ignore[arg-type]


def _tracker(tmp_path: Path, **cfg_kw: object) -> SkillPerformanceTracker:
    return SkillPerformanceTracker(
        config=_cfg(**cfg_kw),
        data_path=tmp_path / "perf.json",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRecordExecution:
    """Recording executions and basic metric tracking."""

    @pytest.mark.asyncio
    async def test_record_single_success(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path)
        await tracker.record_execution("s1", success=True, score=0.9, duration_ms=100)
        health = await tracker.get_skill_health("s1")
        assert health.total_executions == 1
        assert health.window_executions == 1
        assert health.failure_rate == 0.0
        assert health.avg_score == 0.9
        assert not health.is_degraded

    @pytest.mark.asyncio
    async def test_record_multiple(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path)
        await tracker.record_execution("s1", success=True, score=0.8, duration_ms=50)
        await tracker.record_execution("s1", success=False, score=0.2, duration_ms=200)
        health = await tracker.get_skill_health("s1")
        assert health.total_executions == 2
        assert health.failure_rate == 0.5
        assert health.avg_score == pytest.approx(0.5, abs=0.01)
        assert health.avg_duration_ms == pytest.approx(125.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_unknown_skill_not_degraded(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path)
        assert not await tracker.is_degraded("nonexistent")


class TestFailureRateThreshold:
    """Failure rate above threshold triggers degradation."""

    @pytest.mark.asyncio
    async def test_high_failure_rate_degrades(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path, min_executions=5, failure_rate_threshold=0.6)
        # 4 failures, 1 success  -> 80% failure rate
        for _ in range(4):
            await tracker.record_execution("s1", success=False, score=0.1)
        await tracker.record_execution("s1", success=True, score=0.8)
        assert await tracker.is_degraded("s1")

    @pytest.mark.asyncio
    async def test_below_threshold_not_degraded(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path, min_executions=5, failure_rate_threshold=0.6)
        # 2 failures, 3 successes -> 40%
        for _ in range(2):
            await tracker.record_execution("s1", success=False, score=0.4)
        for _ in range(3):
            await tracker.record_execution("s1", success=True, score=0.8)
        assert not await tracker.is_degraded("s1")


class TestConsecutiveFailures:
    """max_consecutive_failures triggers instant degradation."""

    @pytest.mark.asyncio
    async def test_consecutive_failures_degrade(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path, max_consecutive_failures=3, min_executions=10)
        # Even below min_executions, 3 consecutive failures should trigger
        for _ in range(3):
            await tracker.record_execution("s1", success=False, score=0.0)
        assert await tracker.is_degraded("s1")

    @pytest.mark.asyncio
    async def test_success_resets_consecutive(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path, max_consecutive_failures=3, min_executions=10)
        await tracker.record_execution("s1", success=False, score=0.0)
        await tracker.record_execution("s1", success=False, score=0.0)
        await tracker.record_execution("s1", success=True, score=0.5)
        await tracker.record_execution("s1", success=False, score=0.0)
        assert not await tracker.is_degraded("s1")


class TestMinExecutionsGuard:
    """Skills should not be judged before min_executions."""

    @pytest.mark.asyncio
    async def test_not_degraded_before_min(self, tmp_path: Path) -> None:
        tracker = _tracker(
            tmp_path,
            min_executions=5,
            failure_rate_threshold=0.5,
            max_consecutive_failures=100,  # disable consecutive rule
        )
        # 4 failures, still below min_executions
        for _ in range(4):
            await tracker.record_execution("s1", success=False, score=0.1)
        assert not await tracker.is_degraded("s1")

    @pytest.mark.asyncio
    async def test_degrades_at_min(self, tmp_path: Path) -> None:
        tracker = _tracker(
            tmp_path,
            min_executions=5,
            failure_rate_threshold=0.5,
            max_consecutive_failures=100,
        )
        for _ in range(5):
            await tracker.record_execution("s1", success=False, score=0.1)
        assert await tracker.is_degraded("s1")


class TestCooldown:
    """Cooldown re-enables a degraded skill."""

    @pytest.mark.asyncio
    async def test_cooldown_reenables(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path, max_consecutive_failures=2, cooldown_seconds=60)
        await tracker.record_execution("s1", success=False, score=0.0)
        await tracker.record_execution("s1", success=False, score=0.0)
        assert await tracker.is_degraded("s1")

        # Simulate time passing
        with patch("cognithor.skills.performance_tracker.time") as mock_time:
            mock_time.time.return_value = time.time() + 61
            assert not await tracker.is_degraded("s1")


class TestSlidingWindow:
    """Old entries fall off the window."""

    @pytest.mark.asyncio
    async def test_window_trims(self, tmp_path: Path) -> None:
        tracker = _tracker(
            tmp_path,
            window_size=5,
            min_executions=5,
            failure_rate_threshold=0.6,
            max_consecutive_failures=100,
        )
        # 5 failures -> degraded
        for _ in range(5):
            await tracker.record_execution("s1", success=False, score=0.1)
        assert await tracker.is_degraded("s1")

        # Reset and then push 5 successes; old failures fall off
        await tracker.reset_skill("s1")
        for _ in range(5):
            await tracker.record_execution("s1", success=True, score=0.9)

        health = await tracker.get_skill_health("s1")
        assert health.window_executions == 5
        # Window should now be all successes
        assert health.failure_rate == 0.0
        assert not health.is_degraded


class TestLowAvgScore:
    """Avg score below threshold triggers degradation."""

    @pytest.mark.asyncio
    async def test_low_score_degrades(self, tmp_path: Path) -> None:
        tracker = _tracker(
            tmp_path,
            min_executions=3,
            min_avg_score=0.3,
            failure_rate_threshold=1.0,  # disable failure-rate rule
            max_consecutive_failures=100,
        )
        for _ in range(3):
            await tracker.record_execution("s1", success=True, score=0.1)
        assert await tracker.is_degraded("s1")


class TestPersistence:
    """Save and reload from disk."""

    @pytest.mark.asyncio
    async def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "perf.json"
        cfg = _cfg(max_consecutive_failures=100)

        tracker1 = SkillPerformanceTracker(config=cfg, data_path=path)
        await tracker1.record_execution("s1", success=True, score=0.7, duration_ms=50)
        await tracker1.record_execution("s1", success=False, score=0.2, duration_ms=100)

        # New tracker loads from same file
        tracker2 = SkillPerformanceTracker(config=cfg, data_path=path)
        health = await tracker2.get_skill_health("s1")
        assert health.total_executions == 2
        assert health.failure_rate == 0.5

    @pytest.mark.asyncio
    async def test_missing_file_ok(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent" / "perf.json"
        tracker = SkillPerformanceTracker(config=_cfg(), data_path=path)
        health = await tracker.get_skill_health("s1")
        assert health.total_executions == 0


class TestGetAllHealth:
    """get_all_health returns data for all tracked skills."""

    @pytest.mark.asyncio
    async def test_multiple_skills(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path)
        await tracker.record_execution("a", success=True, score=0.9)
        await tracker.record_execution("b", success=False, score=0.1)
        all_health = await tracker.get_all_health()
        assert set(all_health.keys()) == {"a", "b"}
        assert all_health["a"].failure_rate == 0.0
        assert all_health["b"].failure_rate == 1.0


class TestGetDegradedSkills:
    """get_degraded_skills returns only degraded names."""

    @pytest.mark.asyncio
    async def test_list_degraded(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path, max_consecutive_failures=2)
        await tracker.record_execution("good", success=True, score=0.9)
        await tracker.record_execution("bad", success=False, score=0.0)
        await tracker.record_execution("bad", success=False, score=0.0)

        degraded = await tracker.get_degraded_skills()
        assert "bad" in degraded
        assert "good" not in degraded


class TestResetSkill:
    """Manual reset clears degradation."""

    @pytest.mark.asyncio
    async def test_reset_clears(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path, max_consecutive_failures=2)
        await tracker.record_execution("s1", success=False, score=0.0)
        await tracker.record_execution("s1", success=False, score=0.0)
        assert await tracker.is_degraded("s1")

        await tracker.reset_skill("s1")
        assert not await tracker.is_degraded("s1")

    @pytest.mark.asyncio
    async def test_reset_nonexistent_is_noop(self, tmp_path: Path) -> None:
        tracker = _tracker(tmp_path)
        await tracker.reset_skill("nope")  # should not raise
