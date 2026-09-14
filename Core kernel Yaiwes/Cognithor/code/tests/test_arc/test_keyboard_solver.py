"""Tests for KeyboardSolver — incremental DFS for keyboard-based ARC games."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np

from cognithor.arc.keyboard_solver import KeyboardSolver


def _make_grid(avatar_pos=(5, 5), size=16):
    """Create a simple grid with avatar at given position."""
    g = np.full((64, 64), 1, dtype=np.int8)  # background
    r, c = avatar_pos
    # 4x4 avatar block so downsampled hash still detects movement
    g[r : r + 4, c : c + 4] = 3
    return g


def _make_mock_env(maze_map, start, goal, actions_available=None):
    """Create a mock env that simulates a grid maze.

    maze_map: dict of (row,col) -> set of allowed action_ids from that cell
    start: (row, col) starting position
    goal: (row, col) winning position
    """
    from arcengine.enums import GameState

    pos = list(start)
    level = [0]
    DELTAS = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}

    def make_obs():
        g = _make_grid(tuple(pos))
        obs = MagicMock()
        obs.frame = np.expand_dims(g, 0)
        obs.levels_completed = level[0]
        if tuple(pos) == goal and level[0] == 0:
            level[0] = 1
            obs.levels_completed = 1
        obs.state = GameState.NOT_FINISHED
        obs.available_actions = actions_available or [1, 2, 3, 4]
        return obs

    def step(action, data=None):
        p = tuple(pos)
        allowed = maze_map.get(p, set())
        if action in allowed:
            dr, dc = DELTAS.get(action, (0, 0))
            pos[0] += dr
            pos[1] += dc
        return make_obs()

    def reset():
        pos[0], pos[1] = start
        level[0] = 0
        return make_obs()

    env = MagicMock()
    env.step = step
    env.reset = reset
    return env


class TestKeyboardSolverBasic:
    def test_solves_simple_path(self):
        """DFS should find a path from start to goal in a simple corridor."""
        # Simple corridor: (5,5) → right → right → right → (5,8) = goal
        maze = {
            (5, 5): {4},  # can only go RIGHT
            (5, 6): {3, 4},  # LEFT or RIGHT
            (5, 7): {3, 4},  # LEFT or RIGHT
        }
        mock_env = _make_mock_env(maze, start=(5, 5), goal=(5, 8))

        mock_arcade = MagicMock()
        mock_arcade.make.return_value = mock_env

        solver = KeyboardSolver(mock_arcade, "test_game", [1, 2, 3, 4])
        result = solver.solve(max_levels=1, timeout_s=10.0)

        assert result.levels_completed >= 1

    def test_backtracks_on_dead_end(self):
        """DFS should backtrack from dead ends and find alternative path."""
        # Maze: start (5,5), dead end at (4,5), goal at (5,7)
        maze = {
            (5, 5): {1, 4},  # UP or RIGHT
            (4, 5): {2},  # can only go DOWN (dead end)
            (5, 6): {3, 4},  # LEFT or RIGHT
        }
        mock_env = _make_mock_env(maze, start=(5, 5), goal=(5, 7))

        mock_arcade = MagicMock()
        mock_arcade.make.return_value = mock_env

        solver = KeyboardSolver(mock_arcade, "test_game", [1, 2, 3, 4])
        result = solver.solve(max_levels=1, timeout_s=10.0)

        assert result.levels_completed >= 1

    def test_returns_zero_when_stuck(self):
        """Should return 0 levels when no path exists."""
        # No moves possible
        maze = {}
        mock_env = _make_mock_env(maze, start=(5, 5), goal=(5, 8))

        mock_arcade = MagicMock()
        mock_arcade.make.return_value = mock_env

        solver = KeyboardSolver(mock_arcade, "test_game", [1, 2, 3, 4])
        result = solver.solve(max_levels=1, timeout_s=2.0)

        assert result.levels_completed == 0

    def test_handles_game_over(self):
        """Should backtrack when hitting GAME_OVER."""
        from arcengine.enums import GameState

        pos = [5, 5]
        level = [0]

        def step(action, data=None):
            if action == 1:  # UP causes GAME_OVER
                obs = MagicMock()
                obs.frame = np.expand_dims(_make_grid((4, 5)), 0)
                obs.state = GameState.GAME_OVER
                obs.levels_completed = 0
                return obs
            if action == 4:  # RIGHT moves to goal
                pos[1] += 1
                obs = MagicMock()
                obs.frame = np.expand_dims(_make_grid((5, pos[1])), 0)
                obs.state = GameState.NOT_FINISHED
                obs.levels_completed = 1 if pos[1] >= 7 else 0
                return obs
            obs = MagicMock()
            obs.frame = np.expand_dims(_make_grid(tuple(pos)), 0)
            obs.state = GameState.NOT_FINISHED
            obs.levels_completed = 0
            return obs

        def reset():
            pos[0], pos[1] = 5, 5
            level[0] = 0
            obs = MagicMock()
            obs.frame = np.expand_dims(_make_grid((5, 5)), 0)
            obs.state = GameState.NOT_FINISHED
            obs.levels_completed = 0
            return obs

        mock_env = MagicMock()
        mock_env.step = step
        mock_env.reset = reset

        mock_arcade = MagicMock()
        mock_arcade.make.return_value = mock_env

        solver = KeyboardSolver(mock_arcade, "test_game", [1, 2, 3, 4])
        result = solver.solve(max_levels=1, timeout_s=10.0)

        assert result.levels_completed >= 1
