# ARC-AGI-3 KeyboardSolver Design

**Date:** 2026-04-05
**Status:** Approved
**Scope:** 1 new file `keyboard_solver.py`, minor changes to `per_game_solver.py`

## Problem

Keyboard games (WA30, TR87, LS20, G50T) need 50-150 steps per level. Our BFS approach replays the entire action sequence from env.reset() for every search node, costing 15-45ms per node. With 120s timeout, only ~3000 nodes are explored — insufficient for deep mazes.

## Solution: Incremental DFS

Step forward with env.step() (0.3ms) instead of resetting for every node. Only reset when backtracking to a branch point. ~50x faster than replay-based BFS.

**Cost comparison:**
- BFS with replay: 100 nodes x 50 steps x 0.3ms = 1500ms per level
- Incremental DFS: 300 forward steps (0.3ms each) + 50 backtracks (10ms each) = 590ms per level

## Verified Observations

- LS20 Level 0 solved with BFS: 13 steps (LLLUUUURRRUUU), Score 3.57
- LS20 Level 1 fails BFS: 2783 states in 120s (replay overhead)
- WA30: 17,896 states in 30s, no solve (too many states)
- G50T: 1 state only — actions produce identical/GAME_OVER state
- env.reset() = 0.5ms, env.step() = 0.3ms
- Grid hash on rows 2-62 excludes timer bars (same pattern as click solver)

## Architecture

### New file: `src/jarvis/arc/keyboard_solver.py`

```python
class KeyboardSolver:
    def __init__(self, arcade, game_id, keyboard_actions=None):
        self._arcade = arcade
        self._game_id = game_id
        self._actions = keyboard_actions or [1, 2, 3, 4]

    def solve(self, max_levels=10, timeout_s=300.0) -> SolveResult:
        """Solve keyboard game level by level with incremental DFS."""

    def _solve_level(self, env, replay_prefix, timeout) -> list[int] | None:
        """Incremental DFS for one level. Returns action sequence or None."""

    def _grid_hash(self, grid) -> int:
        """Hash grid rows 2-62, excluding timer bars."""
        return hash(grid[2:62].tobytes())
```

### Integration: `src/jarvis/arc/per_game_solver.py`

Add `_execute_keyboard()` method and route keyboard strategies to it:

```python
def _execute_keyboard(self, max_actions) -> StrategyOutcome:
    from jarvis.arc.keyboard_solver import KeyboardSolver
    actions = [a for a in self._profile.available_actions if a in (1,2,3,4,5)]
    ks = KeyboardSolver(self._arcade, self._profile.game_id, actions)
    result = ks.solve(max_levels=10, timeout_s=300.0)
    return StrategyOutcome(
        won=result.levels_completed > 0,
        levels_solved=result.levels_completed,
        steps=result.total_steps,
    )
```

Route in `_execute_strategy`:
```python
if strategy in ("keyboard_explore", "keyboard_sequence"):
    return self._execute_keyboard(max_actions)
```

## DFS Algorithm Detail

```
def _solve_level(env, replay_prefix, timeout):
    UNDO = {1:2, 2:1, 3:4, 4:3}  # UP↔DOWN, LEFT↔RIGHT

    env.reset()
    replay(prefix)
    initial_grid = extract(env)
    current_levels = obs.levels_completed

    path = []                           # current action sequence
    visited = {grid_hash(initial_grid)}
    stack = [list(self._actions)]       # remaining actions per depth

    while stack:
        if timeout exceeded: break
        if len(visited) > max_states: break

        remaining = stack[-1]

        if not remaining:
            # All directions tried at this depth — backtrack
            stack.pop()
            if path:
                path.pop()
            # Reset to current path position
            env.reset()
            replay(prefix + path)
            continue

        action = remaining.pop()
        obs = env.step(action)  # INCREMENTAL — no reset!

        if obs.levels_completed > current_levels:
            return path + [action]  # WIN

        if obs.state == GAME_OVER:
            # Reset to current path position
            env.reset()
            replay(prefix + path)
            continue

        grid = extract(obs)
        h = grid_hash(grid)

        if h in visited:
            # Try undo instead of full reset
            if action in UNDO:
                env.step(UNDO[action])
            else:
                env.reset()
                replay(prefix + path)
            continue

        # New state — go deeper
        visited.add(h)
        path.append(action)
        stack.append(list(self._actions))

        # Also try INTERACT if available
        if 5 in self._actions:
            obs2 = env.step(5)
            if obs2.levels_completed > current_levels:
                return path + [5]  # WIN via interact
            # Undo interact (usually no-op)

    return None  # exhausted or timeout
```

## Error Handling

- GAME_OVER: reset to current path, skip this direction
- Undo fails (grid doesn't match pre-step): fall back to full reset+replay
- Timeout: return None, solver moves to next strategy
- max_states (50,000): return None

## Limits

- max_depth: 500 (WA30 baseline max = 259)
- max_states: 50,000
- timeout: 300s per level
- Undo map: {UP:DOWN, DOWN:UP, LEFT:RIGHT, RIGHT:LEFT}

## Testing

- `tests/test_arc/test_keyboard_solver.py`:
  - test_solves_simple_maze: mock 3x3 grid, DFS finds path
  - test_backtracks_on_dead_end: mock maze with dead end, DFS backtracks
  - test_handles_game_over: mock GAME_OVER on certain moves
  - test_multi_level: mock 2-level game, solves both
  - test_undo_optimization: verify undo used instead of reset when possible

## Files

### New
- `src/jarvis/arc/keyboard_solver.py`
- `tests/test_arc/test_keyboard_solver.py`

### Modified
- `src/jarvis/arc/per_game_solver.py` — add `_execute_keyboard()` + routing
