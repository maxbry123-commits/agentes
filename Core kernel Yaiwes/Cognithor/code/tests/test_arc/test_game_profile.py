"""Tests for GameProfile dataclass and persistence."""

from __future__ import annotations

import json

import pytest

from cognithor.arc.game_profile import GameProfile, StrategyMetrics


class TestStrategyMetrics:
    def test_defaults(self):
        m = StrategyMetrics()
        assert m.attempts == 0
        assert m.wins == 0
        assert m.total_levels_solved == 0
        assert m.avg_steps_to_win == 0.0
        assert m.avg_budget_ratio == 0.0

    def test_win_rate_no_attempts(self):
        m = StrategyMetrics()
        assert m.win_rate == 0.0

    def test_win_rate_with_data(self):
        m = StrategyMetrics(attempts=10, wins=3)
        assert m.win_rate == pytest.approx(0.3)


class TestGameProfile:
    def _make_profile(self, **overrides) -> GameProfile:
        defaults = dict(
            game_id="ft09",
            game_type="click",
            available_actions=[5, 6],
            click_zones=[(10, 20), (30, 40)],
            target_colors=[3],
            movement_effects={},
            win_condition="clear_board",
            vision_description="A grid puzzle with red clusters",
            vision_strategy="Click all red clusters",
            strategy_metrics={},
            analyzed_at="2026-04-04T12:00:00",
        )
        defaults.update(overrides)
        return GameProfile(**defaults)

    def test_create_profile(self):
        p = self._make_profile()
        assert p.game_id == "ft09"
        assert p.game_type == "click"
        assert p.total_runs == 0
        assert p.best_score == 0
        assert p.profile_version == 1

    def test_to_dict_roundtrip(self):
        p = self._make_profile(
            strategy_metrics={
                "cluster_click": StrategyMetrics(attempts=5, wins=2),
            },
        )
        d = p.to_dict()
        assert isinstance(d, dict)
        assert d["game_id"] == "ft09"
        assert d["strategy_metrics"]["cluster_click"]["attempts"] == 5

        p2 = GameProfile.from_dict(d)
        assert p2.game_id == p.game_id
        assert p2.strategy_metrics["cluster_click"].wins == 2

    def test_save_and_load(self, tmp_path):
        p = self._make_profile()
        p.save(base_dir=tmp_path)

        loaded = GameProfile.load("ft09", base_dir=tmp_path)
        assert loaded is not None
        assert loaded.game_id == "ft09"
        assert loaded.click_zones == [(10, 20), (30, 40)]

    def test_load_nonexistent_returns_none(self, tmp_path):
        assert GameProfile.load("nonexistent", base_dir=tmp_path) is None

    def test_exists(self, tmp_path):
        assert GameProfile.exists("ft09", base_dir=tmp_path) is False
        p = self._make_profile()
        p.save(base_dir=tmp_path)
        assert GameProfile.exists("ft09", base_dir=tmp_path) is True

    def test_save_creates_directory(self, tmp_path):
        sub = tmp_path / "deep" / "nested"
        p = self._make_profile()
        p.save(base_dir=sub)
        assert (sub / "game_profiles" / "ft09.json").exists()

    def test_load_corrupt_json_returns_none(self, tmp_path):
        profile_dir = tmp_path / "game_profiles"
        profile_dir.mkdir(parents=True)
        (profile_dir / "broken.json").write_text("{invalid json")
        assert GameProfile.load("broken", base_dir=tmp_path) is None


class TestMetricsUpdate:
    def _make_profile(self, **overrides) -> GameProfile:
        defaults = dict(
            game_id="ft09",
            game_type="click",
            available_actions=[5, 6],
            click_zones=[],
            target_colors=[],
            movement_effects={},
            win_condition="unknown",
            vision_description="",
            vision_strategy="",
            strategy_metrics={},
            analyzed_at="2026-04-04T12:00:00",
        )
        defaults.update(overrides)
        return GameProfile(**defaults)

    def test_update_metrics_new_strategy(self):
        p = self._make_profile()
        p.update_metrics("cluster_click", won=True, levels_solved=3, steps=25, budget_ratio=0.6)
        m = p.strategy_metrics["cluster_click"]
        assert m.attempts == 1
        assert m.wins == 1
        assert m.total_levels_solved == 3
        assert m.avg_steps_to_win == 25.0
        assert m.avg_budget_ratio == 0.6

    def test_update_metrics_existing_strategy(self):
        p = self._make_profile(
            strategy_metrics={
                "cluster_click": StrategyMetrics(
                    attempts=1,
                    wins=1,
                    total_levels_solved=2,
                    avg_steps_to_win=20.0,
                    avg_budget_ratio=0.5,
                )
            },
        )
        p.update_metrics("cluster_click", won=True, levels_solved=4, steps=30, budget_ratio=0.7)
        m = p.strategy_metrics["cluster_click"]
        assert m.attempts == 2
        assert m.wins == 2
        assert m.total_levels_solved == 6
        assert m.avg_steps_to_win == pytest.approx(25.0)
        assert m.avg_budget_ratio == pytest.approx(0.6)

    def test_update_metrics_loss(self):
        p = self._make_profile()
        p.update_metrics(
            "keyboard_explore", won=False, levels_solved=0, steps=100, budget_ratio=1.0
        )
        m = p.strategy_metrics["keyboard_explore"]
        assert m.attempts == 1
        assert m.wins == 0
        assert m.avg_steps_to_win == 0.0  # no wins, no avg

    def test_update_run_counter(self):
        p = self._make_profile()
        p.update_run(score=5)
        assert p.total_runs == 1
        assert p.best_score == 5
        p.update_run(score=3)
        assert p.total_runs == 2
        assert p.best_score == 5  # keeps best


class TestRankedStrategies:
    def _make_profile(self, metrics: dict[str, StrategyMetrics]) -> GameProfile:
        return GameProfile(
            game_id="test",
            game_type="click",
            available_actions=[6],
            click_zones=[],
            target_colors=[],
            movement_effects={},
            win_condition="unknown",
            vision_description="",
            vision_strategy="",
            strategy_metrics=metrics,
            analyzed_at="",
        )

    def test_ranked_by_win_rate(self):
        p = self._make_profile(
            {
                "a": StrategyMetrics(attempts=10, wins=8),
                "b": StrategyMetrics(attempts=10, wins=2),
                "c": StrategyMetrics(attempts=10, wins=5),
            }
        )
        ranked = p.ranked_strategies()
        assert ranked == ["a", "c", "b"]

    def test_exploration_bonus_for_untried(self):
        p = self._make_profile(
            {
                "tried": StrategyMetrics(attempts=10, wins=3),
                "untried": StrategyMetrics(attempts=0, wins=0),
            }
        )
        ranked = p.ranked_strategies()
        # untried gets exploration bonus (1.0) > tried win_rate (0.3)
        assert ranked[0] == "untried"

    def test_empty_metrics(self):
        p = self._make_profile({})
        assert p.ranked_strategies() == []

    def test_default_strategies_for_click(self):
        p = self._make_profile({})
        p.game_type = "click"
        defaults = p.default_strategies()
        assert defaults == [
            ("sequence_click", 0.6),
            ("cluster_click", 0.3),
            ("targeted_click", 0.1),
        ]

    def test_default_strategies_for_keyboard(self):
        p = self._make_profile({})
        p.game_type = "keyboard"
        defaults = p.default_strategies()
        assert defaults == [
            ("keyboard_explore", 0.5),
            ("keyboard_sequence", 0.3),
            ("hybrid", 0.2),
        ]

    def test_default_strategies_for_mixed(self):
        p = self._make_profile({})
        p.game_type = "mixed"
        defaults = p.default_strategies()
        assert defaults == [
            ("hybrid", 0.5),
            ("targeted_click", 0.3),
            ("keyboard_explore", 0.2),
        ]


class TestHasToggles:
    def _make_profile(self, has_toggles=False, **overrides) -> GameProfile:
        defaults = dict(
            game_id="test",
            game_type="click",
            available_actions=[6],
            click_zones=[],
            target_colors=[],
            movement_effects={},
            win_condition="unknown",
            vision_description="",
            vision_strategy="",
            strategy_metrics={},
            analyzed_at="",
            has_toggles=has_toggles,
        )
        defaults.update(overrides)
        return GameProfile(**defaults)

    def test_has_toggles_default_false(self):
        p = self._make_profile()
        assert p.has_toggles is False

    def test_has_toggles_serialization(self, tmp_path):
        p = self._make_profile(has_toggles=True)
        p.save(base_dir=tmp_path)
        loaded = GameProfile.load("test", base_dir=tmp_path)
        assert loaded is not None
        assert loaded.has_toggles is True

    def test_has_toggles_backward_compat(self, tmp_path):
        """Old profiles without has_toggles should load with False."""
        profile_dir = tmp_path / "game_profiles"
        profile_dir.mkdir(parents=True)
        old_data = {
            "game_id": "old_game",
            "game_type": "click",
            "available_actions": [6],
            "click_zones": [],
            "target_colors": [],
            "movement_effects": {},
            "win_condition": "unknown",
            "vision_description": "",
            "vision_strategy": "",
            "strategy_metrics": {},
            "total_runs": 0,
            "best_score": 0,
            "analyzed_at": "",
            "profile_version": 1,
        }
        (profile_dir / "old_game.json").write_text(json.dumps(old_data))
        loaded = GameProfile.load("old_game", base_dir=tmp_path)
        assert loaded is not None
        assert loaded.has_toggles is False

    def test_default_strategies_with_toggles(self):
        p = self._make_profile(has_toggles=True)
        defaults = p.default_strategies()
        assert defaults[0][0] == "cluster_click"
        assert defaults[1][0] == "sequence_click"

    def test_default_strategies_without_toggles(self):
        p = self._make_profile(has_toggles=False)
        defaults = p.default_strategies()
        assert defaults[0][0] == "sequence_click"
        assert defaults[1][0] == "cluster_click"
