"""Integration tests for GameAnalyzer -> PerGameSolver pipeline."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from cognithor.arc.game_analyzer import GameAnalyzer
from cognithor.arc.game_profile import GameProfile, StrategyMetrics
from cognithor.arc.per_game_solver import PerGameSolver, SolveResult


def _make_mock_game_state(name):
    state = MagicMock()
    state.name = name
    state.__eq__ = lambda self, other: getattr(other, "name", other) == name
    return state


def _make_mock_obs(grid=None, state_name="NOT_FINISHED", levels=0, actions=None):
    if grid is None:
        grid = np.zeros((1, 64, 64), dtype=np.int8)
    obs = MagicMock()
    obs.frame = grid
    obs.state = _make_mock_game_state(state_name)
    obs.levels_completed = levels
    obs.available_actions = actions or [MagicMock(value=a) for a in [5, 6]]
    obs.win_levels = 0
    return obs


class TestFullPipeline:
    def test_analyze_then_solve(self, tmp_path):
        """Full pipeline: analyze -> profile -> solve -> metrics updated."""
        # Setup: a simple click game with clusters
        grid = np.zeros((64, 64), dtype=np.int8)
        grid[10:15, 10:15] = 3  # cluster 1
        grid[40:45, 40:45] = 3  # cluster 2

        step_count = [0]

        def make_env(game_id=None):
            env = MagicMock()
            step_count[0] = 0

            def mock_step(action, data=None):
                step_count[0] += 1
                if step_count[0] >= 3:
                    return _make_mock_obs(state_name="WIN", levels=1)
                if step_count[0] >= 10:
                    return _make_mock_obs(state_name="GAME_OVER")
                return _make_mock_obs(grid=np.expand_dims(grid, 0))

            env.step = mock_step
            env.reset.return_value = _make_mock_obs(
                grid=np.expand_dims(grid, 0),
                actions=[MagicMock(value=a) for a in [5, 6]],
            )
            return env

        mock_arcade = MagicMock()
        mock_arcade.make = make_env

        vision_resp = {
            "message": {
                "content": json.dumps(
                    {
                        "game_type": "click",
                        "target_color": 3,
                        "strategy": "Click red clusters",
                        "description": "Grid with red blocks",
                        "win_condition": "clear_board",
                    }
                )
            }
        }

        # Step 1: Analyze
        with patch("cognithor.arc.game_analyzer.ollama") as mock_ollama:
            mock_ollama.chat.return_value = vision_resp
            analyzer = GameAnalyzer(arcade=mock_arcade)
            profile = analyzer.analyze("test_integration", base_dir=tmp_path)

        assert profile.game_id == "test_integration"
        assert profile.game_type == "click"
        assert GameProfile.exists("test_integration", base_dir=tmp_path)

        # Step 2: Solve
        solver = PerGameSolver(profile, arcade=mock_arcade)
        result = solver.solve(max_levels=1, base_dir=tmp_path)

        assert isinstance(result, SolveResult)
        assert result.total_steps > 0

        # Step 3: Verify profile was updated with metrics
        reloaded = GameProfile.load("test_integration", base_dir=tmp_path)
        assert reloaded is not None
        assert reloaded.total_runs == 1

    def test_cached_profile_skips_analysis(self, tmp_path):
        """Second run loads cached profile without vision calls."""
        profile = GameProfile(
            game_id="cached_run",
            game_type="click",
            available_actions=[5, 6],
            click_zones=[(12, 12)],
            target_colors=[3],
            movement_effects={},
            win_condition="clear_board",
            vision_description="cached test",
            vision_strategy="click stuff",
            strategy_metrics={"targeted_click": StrategyMetrics(attempts=1, wins=1)},
            analyzed_at="2026-04-04",
        )
        profile.save(base_dir=tmp_path)

        analyzer = GameAnalyzer(arcade=MagicMock())

        # Should NOT call ollama
        with patch("cognithor.arc.game_analyzer.ollama") as mock_ollama:
            loaded = analyzer.analyze("cached_run", base_dir=tmp_path)
            mock_ollama.chat.assert_not_called()

        assert loaded.vision_description == "cached test"
        assert loaded.strategy_metrics["targeted_click"].wins == 1

    def test_profile_learning_across_runs(self, tmp_path):
        """Profile metrics improve across multiple runs."""
        profile = GameProfile(
            game_id="learning_test",
            game_type="click",
            available_actions=[6],
            click_zones=[(10, 10)],
            target_colors=[3],
            movement_effects={},
            win_condition="clear_board",
            vision_description="test",
            vision_strategy="test",
            strategy_metrics={},
            analyzed_at="2026-04-04",
        )

        # Simulate 3 runs with improving results
        profile.update_metrics(
            "cluster_click", won=True, levels_solved=1, steps=50, budget_ratio=0.8
        )
        profile.update_metrics(
            "cluster_click", won=True, levels_solved=2, steps=30, budget_ratio=0.5
        )
        profile.update_metrics(
            "targeted_click", won=False, levels_solved=0, steps=20, budget_ratio=1.0
        )

        ranked = profile.ranked_strategies()
        assert ranked[0] == "cluster_click"  # 100% win rate
        assert ranked[1] == "targeted_click"  # 0% win rate

        m = profile.strategy_metrics["cluster_click"]
        assert m.attempts == 2
        assert m.wins == 2
        assert m.total_levels_solved == 3
        assert m.avg_steps_to_win == pytest.approx(40.0)


class TestSequenceClickPipeline:
    def test_no_toggle_game_uses_sequence_click(self, tmp_path):
        """Games without toggles should prefer sequence_click strategy."""
        from cognithor.arc.game_profile import GameProfile

        profile = GameProfile(
            game_id="no_toggle_game",
            game_type="click",
            available_actions=[6],
            click_zones=[],
            target_colors=[],
            movement_effects={},
            win_condition="unknown",
            vision_description="test",
            vision_strategy="test",
            strategy_metrics={},
            analyzed_at="2026-04-05",
            has_toggles=False,
        )

        defaults = profile.default_strategies()
        assert defaults[0][0] == "sequence_click"
        assert defaults[0][1] == 0.6

    def test_toggle_game_uses_cluster_click(self, tmp_path):
        """Games with toggles should prefer cluster_click strategy."""
        from cognithor.arc.game_profile import GameProfile

        profile = GameProfile(
            game_id="toggle_game",
            game_type="click",
            available_actions=[6],
            click_zones=[(10, 10)],
            target_colors=[3],
            movement_effects={},
            win_condition="clear_board",
            vision_description="test",
            vision_strategy="test",
            strategy_metrics={},
            analyzed_at="2026-04-05",
            has_toggles=True,
        )

        defaults = profile.default_strategies()
        assert defaults[0][0] == "cluster_click"
        assert defaults[0][1] == 0.6

    def test_profile_has_toggles_persists(self, tmp_path):
        """has_toggles should survive save/load cycle."""
        from cognithor.arc.game_profile import GameProfile

        for val in [True, False]:
            p = GameProfile(
                game_id=f"persist_{val}",
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
                has_toggles=val,
            )
            p.save(base_dir=tmp_path)
            loaded = GameProfile.load(f"persist_{val}", base_dir=tmp_path)
            assert loaded.has_toggles is val
