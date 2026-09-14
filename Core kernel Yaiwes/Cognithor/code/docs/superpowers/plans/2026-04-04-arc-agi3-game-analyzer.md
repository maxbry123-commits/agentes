# ARC-AGI-3 GameAnalyzer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GameAnalyzer that sacrifices one level per game to understand mechanics, persists the profile, and routes to a budget-based PerGameSolver that combines existing solver strategies.

**Architecture:** Three new files (`game_profile.py`, `game_analyzer.py`, `per_game_solver.py`) in `src/jarvis/arc/`. GameProfile is a persistent dataclass with learning metrics. GameAnalyzer runs an opferlevel + 2 vision calls. PerGameSolver allocates action budget across ranked strategies with stagnation-based switching. Entry via `--mode analyzer` in `__main__.py`.

**Tech Stack:** Python 3.11+, numpy, scipy.ndimage, PIL, ollama (qwen3-vl:32b), arc_agi SDK, pytest

**Spec:** `docs/superpowers/specs/2026-04-04-arc-agi3-game-analyzer-design.md`

---

### Task 1: GameProfile — Dataclasses & Serialization

**Files:**
- Create: `src/jarvis/arc/game_profile.py`
- Create: `tests/test_arc/test_game_profile.py`

- [ ] **Step 1: Write the failing tests for StrategyMetrics and GameProfile**

```python
"""Tests for GameProfile dataclass and persistence."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from jarvis.arc.game_profile import GameProfile, StrategyMetrics


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_profile.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jarvis.arc.game_profile'`

- [ ] **Step 3: Implement GameProfile and StrategyMetrics**

```python
"""ARC-AGI-3 GameProfile — persistent per-game mechanic profile with learning metrics."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from jarvis.utils.logging import get_logger

__all__ = ["GameProfile", "StrategyMetrics"]

log = get_logger(__name__)

_DEFAULT_BASE_DIR = Path.home() / ".cognithor" / "arc"


@dataclass
class StrategyMetrics:
    """Tracks success metrics for a single solver strategy."""

    attempts: int = 0
    wins: int = 0
    total_levels_solved: int = 0
    avg_steps_to_win: float = 0.0
    avg_budget_ratio: float = 0.0

    @property
    def win_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.wins / self.attempts


@dataclass
class GameProfile:
    """Persistent per-game mechanic profile."""

    game_id: str
    game_type: Literal["click", "keyboard", "mixed"]
    available_actions: list[int]

    # Analysis results
    click_zones: list[tuple[int, int]]
    target_colors: list[int]
    movement_effects: dict[int, str]
    win_condition: str
    vision_description: str
    vision_strategy: str

    # Learning metrics
    strategy_metrics: dict[str, StrategyMetrics]
    total_runs: int = 0
    best_score: int = 0

    # Meta
    analyzed_at: str = ""
    profile_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        d = {
            "game_id": self.game_id,
            "game_type": self.game_type,
            "available_actions": self.available_actions,
            "click_zones": self.click_zones,
            "target_colors": self.target_colors,
            "movement_effects": {str(k): v for k, v in self.movement_effects.items()},
            "win_condition": self.win_condition,
            "vision_description": self.vision_description,
            "vision_strategy": self.vision_strategy,
            "strategy_metrics": {
                name: asdict(m) for name, m in self.strategy_metrics.items()
            },
            "total_runs": self.total_runs,
            "best_score": self.best_score,
            "analyzed_at": self.analyzed_at,
            "profile_version": self.profile_version,
        }
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GameProfile:
        metrics = {}
        for name, m in d.get("strategy_metrics", {}).items():
            metrics[name] = StrategyMetrics(**m)
        movement = {int(k): v for k, v in d.get("movement_effects", {}).items()}
        click_zones = [tuple(z) for z in d.get("click_zones", [])]
        return cls(
            game_id=d["game_id"],
            game_type=d["game_type"],
            available_actions=d.get("available_actions", []),
            click_zones=click_zones,
            target_colors=d.get("target_colors", []),
            movement_effects=movement,
            win_condition=d.get("win_condition", "unknown"),
            vision_description=d.get("vision_description", ""),
            vision_strategy=d.get("vision_strategy", ""),
            strategy_metrics=metrics,
            total_runs=d.get("total_runs", 0),
            best_score=d.get("best_score", 0),
            analyzed_at=d.get("analyzed_at", ""),
            profile_version=d.get("profile_version", 1),
        )

    def save(self, base_dir: Path | None = None) -> None:
        base = base_dir or _DEFAULT_BASE_DIR
        profile_dir = base / "game_profiles"
        profile_dir.mkdir(parents=True, exist_ok=True)
        path = profile_dir / f"{self.game_id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        log.info("arc.profile_saved", game_id=self.game_id, path=str(path))

    @classmethod
    def load(cls, game_id: str, base_dir: Path | None = None) -> GameProfile | None:
        base = base_dir or _DEFAULT_BASE_DIR
        path = base / "game_profiles" / f"{game_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            log.warning("arc.profile_load_failed", game_id=game_id, error=str(exc))
            return None

    @classmethod
    def exists(cls, game_id: str, base_dir: Path | None = None) -> bool:
        base = base_dir or _DEFAULT_BASE_DIR
        return (base / "game_profiles" / f"{game_id}.json").exists()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_profile.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/game_profile.py tests/test_arc/test_game_profile.py
git commit -m "feat(arc): add GameProfile dataclass with persistence and metrics"
```

---

### Task 2: GameProfile — Metrics Update & Strategy Ranking

**Files:**
- Modify: `src/jarvis/arc/game_profile.py`
- Modify: `tests/test_arc/test_game_profile.py`

- [ ] **Step 1: Write the failing tests for update_metrics and ranked_strategies**

Append to `tests/test_arc/test_game_profile.py`:

```python
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
            strategy_metrics={"cluster_click": StrategyMetrics(attempts=1, wins=1, total_levels_solved=2, avg_steps_to_win=20.0, avg_budget_ratio=0.5)},
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
        p.update_metrics("keyboard_explore", won=False, levels_solved=0, steps=100, budget_ratio=1.0)
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
        p = self._make_profile({
            "a": StrategyMetrics(attempts=10, wins=8),
            "b": StrategyMetrics(attempts=10, wins=2),
            "c": StrategyMetrics(attempts=10, wins=5),
        })
        ranked = p.ranked_strategies()
        assert ranked == ["a", "c", "b"]

    def test_exploration_bonus_for_untried(self):
        p = self._make_profile({
            "tried": StrategyMetrics(attempts=10, wins=3),
            "untried": StrategyMetrics(attempts=0, wins=0),
        })
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
            ("cluster_click", 0.5),
            ("targeted_click", 0.3),
            ("hybrid", 0.2),
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_profile.py::TestMetricsUpdate -v`
Expected: FAIL with `AttributeError: 'GameProfile' object has no attribute 'update_metrics'`

- [ ] **Step 3: Implement update_metrics, update_run, ranked_strategies, default_strategies**

Add to `GameProfile` class in `src/jarvis/arc/game_profile.py`:

```python
    def update_metrics(
        self,
        strategy_name: str,
        *,
        won: bool,
        levels_solved: int,
        steps: int,
        budget_ratio: float,
    ) -> None:
        if strategy_name not in self.strategy_metrics:
            self.strategy_metrics[strategy_name] = StrategyMetrics()
        m = self.strategy_metrics[strategy_name]
        old_attempts = m.attempts
        m.attempts += 1
        m.total_levels_solved += levels_solved
        if won:
            m.wins += 1
            # Running average for steps and budget
            if m.wins == 1:
                m.avg_steps_to_win = float(steps)
                m.avg_budget_ratio = budget_ratio
            else:
                n = m.wins
                m.avg_steps_to_win = m.avg_steps_to_win * (n - 1) / n + steps / n
                m.avg_budget_ratio = m.avg_budget_ratio * (n - 1) / n + budget_ratio / n

    def update_run(self, score: int) -> None:
        self.total_runs += 1
        if score > self.best_score:
            self.best_score = score

    def ranked_strategies(self) -> list[str]:
        if not self.strategy_metrics:
            return []

        def score(name: str) -> float:
            m = self.strategy_metrics[name]
            if m.attempts == 0:
                return 1.0  # exploration bonus
            return m.win_rate

        return sorted(self.strategy_metrics.keys(), key=score, reverse=True)

    def default_strategies(self) -> list[tuple[str, float]]:
        if self.game_type == "click":
            return [("cluster_click", 0.5), ("targeted_click", 0.3), ("hybrid", 0.2)]
        if self.game_type == "keyboard":
            return [("keyboard_explore", 0.5), ("keyboard_sequence", 0.3), ("hybrid", 0.2)]
        return [("hybrid", 0.5), ("targeted_click", 0.3), ("keyboard_explore", 0.2)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_profile.py -v`
Expected: 19 passed

- [ ] **Step 5: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/game_profile.py tests/test_arc/test_game_profile.py
git commit -m "feat(arc): add metrics update and strategy ranking to GameProfile"
```

---

### Task 3: GameAnalyzer — Vision Helpers & SacrificeReport

**Files:**
- Create: `src/jarvis/arc/game_analyzer.py`
- Create: `tests/test_arc/test_game_analyzer.py`

- [ ] **Step 1: Write the failing tests for vision helpers and SacrificeReport**

```python
"""Tests for GameAnalyzer — opferlevel + vision analysis."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from jarvis.arc.game_analyzer import (
    GameAnalyzer,
    SacrificeReport,
    _grid_to_png_b64,
    _parse_vision_json,
)


class TestVisionHelpers:
    def test_grid_to_png_b64_produces_base64(self):
        grid = np.zeros((64, 64), dtype=np.int8)
        grid[10:20, 10:20] = 3  # red block
        b64 = _grid_to_png_b64(grid, scale=4)
        assert isinstance(b64, str)
        assert len(b64) > 100
        # Should be valid base64
        import base64
        raw = base64.b64decode(b64)
        assert raw[:4] == b"\x89PNG"

    def test_grid_to_png_b64_handles_3d(self):
        grid = np.zeros((1, 64, 64), dtype=np.int8)
        b64 = _grid_to_png_b64(grid, scale=2)
        assert isinstance(b64, str)

    def test_parse_vision_json_direct(self):
        raw = '{"game_type": "click", "target_color": 3}'
        result = _parse_vision_json(raw)
        assert result["game_type"] == "click"

    def test_parse_vision_json_markdown(self):
        raw = 'Some text\n```json\n{"game_type": "keyboard"}\n```\nMore text'
        result = _parse_vision_json(raw)
        assert result["game_type"] == "keyboard"

    def test_parse_vision_json_with_think_tags(self):
        raw = '<think>reasoning here</think>\n{"game_type": "mixed"}'
        result = _parse_vision_json(raw)
        assert result["game_type"] == "mixed"

    def test_parse_vision_json_balanced_brace(self):
        raw = 'The answer is {"game_type": "click", "nested": {"a": 1}} and more'
        result = _parse_vision_json(raw)
        assert result["game_type"] == "click"

    def test_parse_vision_json_unparseable(self):
        assert _parse_vision_json("no json here at all") is None


class TestSacrificeReport:
    def test_defaults(self):
        r = SacrificeReport()
        assert r.clicks_tested == []
        assert r.movements_tested == {}
        assert r.unique_states_seen == 0
        assert r.game_over_trigger is None
        assert r.frames == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_analyzer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jarvis.arc.game_analyzer'`

- [ ] **Step 3: Implement vision helpers and SacrificeReport**

```python
"""ARC-AGI-3 GameAnalyzer — sacrifice-level analysis + 2 vision calls to build GameProfile."""

from __future__ import annotations

import base64
import io
import json
import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from jarvis.utils.logging import get_logger

__all__ = ["GameAnalyzer"]

log = get_logger(__name__)

PALETTE = [
    (255, 255, 255), (0, 0, 0), (0, 116, 217), (255, 65, 54),
    (46, 204, 64), (255, 220, 0), (170, 170, 170), (255, 133, 27),
    (127, 219, 255), (135, 12, 37), (240, 18, 190), (200, 200, 200),
    (200, 200, 100), (100, 50, 150), (0, 200, 200), (128, 0, 255),
]

_ACTION_NAMES = {1: "UP", 2: "DOWN", 3: "LEFT", 4: "RIGHT", 5: "Interact", 6: "Click(x,y)"}


def _grid_to_png_b64(grid: np.ndarray, scale: int = 4) -> str:
    """Convert 64x64 colour-index grid to upscaled PNG as base64."""
    from PIL import Image

    if grid.ndim == 3:
        grid = grid[0]
    h, w = grid.shape
    img = np.zeros((h * scale, w * scale, 3), dtype=np.uint8)
    for r in range(h):
        for c in range(w):
            color = PALETTE[min(int(grid[r, c]), 15)]
            img[r * scale : (r + 1) * scale, c * scale : (c + 1) * scale] = color
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _parse_vision_json(raw: str) -> dict | None:
    """3-tier JSON extraction: direct parse, markdown block, balanced brace."""
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    md = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if md:
        try:
            data = json.loads(md.group(1))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, ValueError):
            pass

    pos = raw.find("{")
    if pos != -1:
        depth = 0
        for i in range(pos, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
            if depth == 0:
                try:
                    data = json.loads(raw[pos : i + 1])
                    if isinstance(data, dict):
                        return data
                except (json.JSONDecodeError, ValueError):
                    pass
                break

    return None


@dataclass
class SacrificeReport:
    """Results from the sacrifice level exploration."""

    clicks_tested: list[tuple[int, int, str]] = field(default_factory=list)
    movements_tested: dict[int, int] = field(default_factory=dict)
    unique_states_seen: int = 0
    game_over_trigger: str | None = None
    frames: list[np.ndarray] = field(default_factory=list)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_analyzer.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/game_analyzer.py tests/test_arc/test_game_analyzer.py
git commit -m "feat(arc): add GameAnalyzer vision helpers and SacrificeReport"
```

---

### Task 4: GameAnalyzer — Sacrifice Level Execution

**Files:**
- Modify: `src/jarvis/arc/game_analyzer.py`
- Modify: `tests/test_arc/test_game_analyzer.py`

- [ ] **Step 1: Write the failing tests for sacrifice level**

Append to `tests/test_arc/test_game_analyzer.py`:

```python
from jarvis.arc.error_handler import safe_frame_extract


def _make_mock_obs(grid=None, state="NOT_FINISHED", levels=0, actions=None):
    """Create a mock ARC SDK observation."""
    if grid is None:
        grid = np.zeros((1, 64, 64), dtype=np.int8)
    obs = MagicMock()
    obs.frame = grid
    obs.state = state
    obs.levels_completed = levels
    obs.available_actions = actions or []
    obs.win_levels = 0
    return obs


def _make_mock_game_state(name):
    state = MagicMock()
    state.name = name
    state.__eq__ = lambda self, other: getattr(other, "name", other) == name
    return state


class TestSacrificeLevel:
    def test_run_sacrifice_keyboard_only(self):
        """Keyboard-only game: tests directions 1-4, no clicks."""
        initial_grid = np.zeros((64, 64), dtype=np.int8)
        initial_grid[30:34, 30:34] = 2  # blue block

        moved_grid = np.zeros((64, 64), dtype=np.int8)
        moved_grid[31:35, 30:34] = 2  # shifted down

        not_finished = _make_mock_game_state("NOT_FINISHED")

        mock_env = MagicMock()
        call_count = [0]

        def mock_step(action, data=None):
            call_count[0] += 1
            obs = _make_mock_obs(
                grid=np.expand_dims(moved_grid if call_count[0] % 2 else initial_grid, 0),
                state=not_finished,
                actions=[MagicMock(value=a) for a in [1, 2, 3, 4, 5]],
            )
            return obs

        mock_env.step = mock_step

        analyzer = GameAnalyzer.__new__(GameAnalyzer)
        report = analyzer._run_sacrifice_level(
            mock_env, initial_grid, available_action_ids=[1, 2, 3, 4, 5]
        )

        assert isinstance(report, SacrificeReport)
        # Should have tested all 4 directions
        assert len(report.movements_tested) == 4
        assert report.unique_states_seen >= 1

    def test_run_sacrifice_click_game(self):
        """Click game: finds clusters and tests clicks."""
        initial_grid = np.zeros((64, 64), dtype=np.int8)
        # Two distinct clusters of colour 3
        initial_grid[10:15, 10:15] = 3
        initial_grid[40:45, 40:45] = 3

        toggled_grid = initial_grid.copy()
        toggled_grid[10:15, 10:15] = 5  # toggled to colour 5

        not_finished = _make_mock_game_state("NOT_FINISHED")

        mock_env = MagicMock()
        click_count = [0]

        def mock_step(action, data=None):
            click_count[0] += 1
            obs = _make_mock_obs(
                grid=np.expand_dims(toggled_grid, 0),
                state=not_finished,
                actions=[MagicMock(value=a) for a in [5, 6]],
            )
            return obs

        mock_env.step = mock_step

        analyzer = GameAnalyzer.__new__(GameAnalyzer)
        report = analyzer._run_sacrifice_level(
            mock_env, initial_grid, available_action_ids=[5, 6]
        )

        assert isinstance(report, SacrificeReport)
        assert len(report.clicks_tested) > 0
        assert report.unique_states_seen >= 1

    def test_run_sacrifice_game_over(self):
        """GAME_OVER during sacrifice is handled gracefully."""
        initial_grid = np.zeros((64, 64), dtype=np.int8)
        initial_grid[20:30, 20:30] = 3

        game_over = _make_mock_game_state("GAME_OVER")

        mock_env = MagicMock()
        mock_env.step.return_value = _make_mock_obs(
            grid=np.expand_dims(initial_grid, 0),
            state=game_over,
            actions=[MagicMock(value=6)],
        )

        analyzer = GameAnalyzer.__new__(GameAnalyzer)
        report = analyzer._run_sacrifice_level(
            mock_env, initial_grid, available_action_ids=[5, 6]
        )

        assert report.game_over_trigger is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_analyzer.py::TestSacrificeLevel -v`
Expected: FAIL with `AttributeError: 'GameAnalyzer' object has no attribute '_run_sacrifice_level'`

- [ ] **Step 3: Implement _run_sacrifice_level**

Add to `game_analyzer.py` after the `SacrificeReport` class:

```python
class GameAnalyzer:
    """Analyzes ARC-AGI-3 games by sacrificing one level + 2 vision calls."""

    def __init__(self, arcade: Any | None = None):
        self._arcade = arcade

    def _run_sacrifice_level(
        self,
        env: Any,
        initial_grid: np.ndarray,
        available_action_ids: list[int],
    ) -> SacrificeReport:
        """Execute the sacrifice level: test actions systematically."""
        from arcengine.enums import GameState

        report = SacrificeReport()
        report.frames.append(initial_grid.copy())
        seen_states: set[int] = {hash(initial_grid.tobytes())}
        current_grid = initial_grid.copy()

        has_click = 6 in available_action_ids
        has_keyboard = any(a in available_action_ids for a in [1, 2, 3, 4])

        # Phase 1: Test keyboard directions (3 times each)
        if has_keyboard:
            for action_id in [1, 2, 3, 4]:
                if action_id not in available_action_ids:
                    continue
                total_diff = 0
                for _ in range(3):
                    obs = env.step(action_id)
                    new_grid = safe_frame_extract(obs)
                    diff = int(np.sum(new_grid != current_grid))
                    total_diff += diff
                    state_hash = hash(new_grid.tobytes())
                    if state_hash not in seen_states:
                        seen_states.add(state_hash)
                    current_grid = new_grid

                    if hasattr(obs, "state") and obs.state == GameState.GAME_OVER:
                        report.game_over_trigger = f"keyboard_action_{action_id}"
                        report.unique_states_seen = len(seen_states)
                        return report

                report.movements_tested[action_id] = total_diff

        # Phase 2: Test clicks on cluster centers
        if has_click:
            from jarvis.arc.cluster_solver import ClusterSolver

            # Find non-background colours
            unique_colors = [int(c) for c in np.unique(initial_grid) if c != 0]

            for color in unique_colors:
                solver = ClusterSolver(target_color=color, max_skip=0)
                centers = solver.find_clusters(initial_grid)

                for cx, cy in centers:
                    obs = env.step(6, data={"x": cx, "y": cy})
                    new_grid = safe_frame_extract(obs)
                    diff = int(np.sum(new_grid != current_grid))
                    effect = "changed" if diff > 0 else "no_effect"
                    report.clicks_tested.append((cx, cy, effect))

                    state_hash = hash(new_grid.tobytes())
                    if state_hash not in seen_states:
                        seen_states.add(state_hash)
                        report.frames.append(new_grid.copy())
                    current_grid = new_grid

                    if hasattr(obs, "state") and obs.state == GameState.GAME_OVER:
                        report.game_over_trigger = f"click_at_{cx}_{cy}"
                        report.unique_states_seen = len(seen_states)
                        return report

        report.unique_states_seen = len(seen_states)
        return report
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_analyzer.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/game_analyzer.py tests/test_arc/test_game_analyzer.py
git commit -m "feat(arc): implement sacrifice level execution in GameAnalyzer"
```

---

### Task 5: GameAnalyzer — Vision Calls & Profile Assembly

**Files:**
- Modify: `src/jarvis/arc/game_analyzer.py`
- Modify: `tests/test_arc/test_game_analyzer.py`

- [ ] **Step 1: Write the failing tests for vision calls and analyze()**

Append to `tests/test_arc/test_game_analyzer.py`:

```python
class TestVisionCalls:
    def test_vision_call_1_returns_dict(self):
        analyzer = GameAnalyzer.__new__(GameAnalyzer)
        grid = np.zeros((64, 64), dtype=np.int8)
        grid[10:20, 10:20] = 3

        mock_resp = {
            "message": {
                "content": json.dumps({
                    "game_type": "click",
                    "target_color": 3,
                    "strategy": "Click red clusters",
                    "description": "Grid with red blocks",
                })
            }
        }

        with patch("jarvis.arc.game_analyzer.ollama") as mock_ollama:
            mock_ollama.chat.return_value = mock_resp
            result = analyzer._vision_call_initial(grid, [5, 6])

        assert result is not None
        assert result["game_type"] == "click"

    def test_vision_call_1_ollama_error_returns_none(self):
        analyzer = GameAnalyzer.__new__(GameAnalyzer)
        grid = np.zeros((64, 64), dtype=np.int8)

        with patch("jarvis.arc.game_analyzer.ollama") as mock_ollama:
            mock_ollama.chat.side_effect = ConnectionError("Ollama offline")
            result = analyzer._vision_call_initial(grid, [1, 2, 3, 4])

        assert result is None

    def test_vision_call_2_with_diff(self):
        analyzer = GameAnalyzer.__new__(GameAnalyzer)
        grid_before = np.zeros((64, 64), dtype=np.int8)
        grid_after = np.zeros((64, 64), dtype=np.int8)
        grid_after[10:20, 10:20] = 5

        mock_resp = {
            "message": {
                "content": json.dumps({
                    "win_condition": "clear_board",
                    "correction": None,
                    "description": "Clusters toggled from red to yellow",
                })
            }
        }

        with patch("jarvis.arc.game_analyzer.ollama") as mock_ollama:
            mock_ollama.chat.return_value = mock_resp
            result = analyzer._vision_call_final(grid_before, grid_after)

        assert result is not None
        assert result["win_condition"] == "clear_board"


class TestAnalyze:
    def test_analyze_uses_cache(self, tmp_path):
        from jarvis.arc.game_profile import GameProfile

        # Pre-save a profile
        p = GameProfile(
            game_id="cached_game",
            game_type="click",
            available_actions=[6],
            click_zones=[(10, 10)],
            target_colors=[3],
            movement_effects={},
            win_condition="clear_board",
            vision_description="cached",
            vision_strategy="cached",
            strategy_metrics={},
            analyzed_at="2026-01-01",
        )
        p.save(base_dir=tmp_path)

        analyzer = GameAnalyzer(arcade=None)
        result = analyzer.analyze("cached_game", base_dir=tmp_path)

        assert result.game_id == "cached_game"
        assert result.vision_description == "cached"

    def test_analyze_force_ignores_cache(self, tmp_path):
        from jarvis.arc.game_profile import GameProfile

        p = GameProfile(
            game_id="force_test",
            game_type="click",
            available_actions=[6],
            click_zones=[],
            target_colors=[],
            movement_effects={},
            win_condition="unknown",
            vision_description="old",
            vision_strategy="old",
            strategy_metrics={},
            analyzed_at="2026-01-01",
        )
        p.save(base_dir=tmp_path)

        initial_grid = np.zeros((64, 64), dtype=np.int8)
        initial_grid[10:15, 10:15] = 3
        not_finished = _make_mock_game_state("NOT_FINISHED")
        game_over = _make_mock_game_state("GAME_OVER")

        mock_env = MagicMock()
        step_count = [0]

        def mock_step(action, data=None):
            step_count[0] += 1
            # After a few steps, return GAME_OVER to end sacrifice
            state = game_over if step_count[0] > 3 else not_finished
            return _make_mock_obs(
                grid=np.expand_dims(initial_grid, 0),
                state=state,
                actions=[MagicMock(value=6)],
            )

        mock_env.step = mock_step
        mock_env.reset.return_value = _make_mock_obs(
            grid=np.expand_dims(initial_grid, 0),
            state=not_finished,
            actions=[MagicMock(value=a) for a in [5, 6]],
        )

        mock_arcade = MagicMock()
        mock_arcade.make.return_value = mock_env

        vision_resp = {
            "message": {
                "content": json.dumps({
                    "game_type": "click",
                    "target_color": 3,
                    "strategy": "new strategy",
                    "description": "new description",
                })
            }
        }

        analyzer = GameAnalyzer(arcade=mock_arcade)
        with patch("jarvis.arc.game_analyzer.ollama") as mock_ollama:
            mock_ollama.chat.return_value = vision_resp
            result = analyzer.analyze("force_test", force=True, base_dir=tmp_path)

        assert result.vision_description != "old"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_analyzer.py::TestVisionCalls -v`
Expected: FAIL with `AttributeError: 'GameAnalyzer' object has no attribute '_vision_call_initial'`

- [ ] **Step 3: Implement _vision_call_initial, _vision_call_final, and analyze()**

Add to `GameAnalyzer` class in `game_analyzer.py`:

```python
    def _vision_call_initial(
        self, grid: np.ndarray, action_ids: list[int]
    ) -> dict | None:
        """Vision call 1: ask what the game is from initial frame."""
        try:
            import ollama as ollama_mod

            b64 = _grid_to_png_b64(grid, scale=4)
            action_desc = [f"ACTION{a}={_ACTION_NAMES.get(a, '?')}" for a in action_ids]

            resp = ollama_mod.chat(
                model="qwen3-vl:32b",
                messages=[{
                    "role": "user",
                    "content": (
                        f"64x64 pixel puzzle game. Available actions: {', '.join(action_desc)}.\n"
                        "Analyze this game:\n"
                        "1. What type of game is this? (click, keyboard, or mixed)\n"
                        "2. What is the goal?\n"
                        "3. Which colors are interactive?\n"
                        "4. What strategy should I use?\n"
                        'Reply JSON: {"game_type": "click"|"keyboard"|"mixed", '
                        '"target_color": N or null, "strategy": "...", '
                        '"description": "..."}'
                    ),
                    "images": [b64],
                }],
                options={"num_predict": 8192, "temperature": 0.3, "num_ctx": 8192},
            )

            raw = resp.get("message", {}).get("content", "")
            return _parse_vision_json(raw)
        except Exception as exc:
            log.debug("arc.vision_call_1_failed", error=str(exc)[:200])
            return None

    def _vision_call_final(
        self, grid_before: np.ndarray, grid_after: np.ndarray
    ) -> dict | None:
        """Vision call 2: compare before/after sacrifice level."""
        try:
            import ollama as ollama_mod

            b64_before = _grid_to_png_b64(grid_before, scale=4)
            b64_after = _grid_to_png_b64(grid_after, scale=4)

            # Create diff image: highlight changed pixels in red
            diff_grid = np.where(grid_before != grid_after, 3, grid_before)
            b64_diff = _grid_to_png_b64(diff_grid.astype(np.int8), scale=4)

            resp = ollama_mod.chat(
                model="qwen3-vl:32b",
                messages=[{
                    "role": "user",
                    "content": (
                        "Three images of a 64x64 puzzle game:\n"
                        "1. Initial state\n"
                        "2. After testing actions\n"
                        "3. Diff (changes highlighted in red)\n\n"
                        "What changed? What is the win condition?\n"
                        'Reply JSON: {"win_condition": "clear_board"|"reach_state"|'
                        '"navigate"|"unknown", "correction": null or "...", '
                        '"description": "..."}'
                    ),
                    "images": [b64_before, b64_after, b64_diff],
                }],
                options={"num_predict": 8192, "temperature": 0.3, "num_ctx": 8192},
            )

            raw = resp.get("message", {}).get("content", "")
            return _parse_vision_json(raw)
        except Exception as exc:
            log.debug("arc.vision_call_2_failed", error=str(exc)[:200])
            return None

    def analyze(
        self,
        game_id: str,
        *,
        force: bool = False,
        base_dir: Any | None = None,
    ) -> GameProfile:
        """Analyze a game: load from cache or run sacrifice level + 2 vision calls."""
        from datetime import datetime, timezone

        from jarvis.arc.error_handler import safe_frame_extract
        from jarvis.arc.game_profile import GameProfile

        # Cache check
        if not force and GameProfile.exists(game_id, base_dir=base_dir):
            cached = GameProfile.load(game_id, base_dir=base_dir)
            if cached is not None:
                log.info("arc.profile_cache_hit", game_id=game_id)
                return cached

        # Create environment
        env = self._arcade.make(game_id)
        obs = env.reset()
        initial_grid = safe_frame_extract(obs)

        # Extract available action IDs
        action_ids = []
        if hasattr(obs, "available_actions") and obs.available_actions:
            for a in obs.available_actions:
                action_ids.append(a.value if hasattr(a, "value") else int(a))
        if not action_ids:
            action_ids = [1, 2, 3, 4, 5, 6]

        # Determine game type from actions
        has_click = 6 in action_ids
        has_keyboard = any(a in action_ids for a in [1, 2, 3, 4])
        if has_click and has_keyboard:
            game_type = "mixed"
        elif has_click:
            game_type = "click"
        else:
            game_type = "keyboard"

        # Vision call 1
        vision1 = self._vision_call_initial(initial_grid, action_ids)
        if vision1 and "game_type" in vision1:
            game_type = vision1["game_type"]

        # Sacrifice level
        report = self._run_sacrifice_level(env, initial_grid, action_ids)

        # Vision call 2
        final_grid = report.frames[-1] if report.frames else initial_grid
        vision2 = self._vision_call_final(initial_grid, final_grid)

        # Determine win condition
        win_condition = "unknown"
        if vision2 and "win_condition" in vision2:
            win_condition = vision2["win_condition"]

        # Correct game_type if vision2 disagrees
        if vision2 and vision2.get("correction"):
            correction = vision2["correction"]
            if correction in ("click", "keyboard", "mixed"):
                game_type = correction

        # Extract target colors from clicks that had effects
        target_colors = []
        if vision1 and vision1.get("target_color") is not None:
            target_colors = [int(vision1["target_color"])]

        # Extract click zones from report
        click_zones = [(x, y) for x, y, effect in report.clicks_tested if effect == "changed"]

        # Build movement effects
        movement_effects = {}
        for action_id, diff in report.movements_tested.items():
            if diff > 20:
                movement_effects[action_id] = "moves_player"
            elif diff > 0:
                movement_effects[action_id] = "transforms"
            else:
                movement_effects[action_id] = "no_effect"

        profile = GameProfile(
            game_id=game_id,
            game_type=game_type,
            available_actions=action_ids,
            click_zones=click_zones,
            target_colors=target_colors,
            movement_effects=movement_effects,
            win_condition=win_condition,
            vision_description=vision1.get("description", "") if vision1 else "unavailable",
            vision_strategy=vision1.get("strategy", "") if vision1 else "unavailable",
            strategy_metrics={},
            analyzed_at=datetime.now(timezone.utc).isoformat(),
        )

        profile.save(base_dir=base_dir)
        return profile
```

Also add the missing import at the top of `game_analyzer.py`:

```python
from jarvis.arc.error_handler import safe_frame_extract
from jarvis.arc.game_profile import GameProfile
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_analyzer.py -v`
Expected: 14 passed

- [ ] **Step 5: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/game_analyzer.py tests/test_arc/test_game_analyzer.py
git commit -m "feat(arc): implement vision calls and analyze() in GameAnalyzer"
```

---

### Task 6: PerGameSolver — Budget Allocation & Stagnation Detection

**Files:**
- Create: `src/jarvis/arc/per_game_solver.py`
- Create: `tests/test_arc/test_per_game_solver.py`

- [ ] **Step 1: Write the failing tests for budget allocation and stagnation**

```python
"""Tests for PerGameSolver — budget-based strategy execution."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from jarvis.arc.game_profile import GameProfile, StrategyMetrics
from jarvis.arc.per_game_solver import (
    BudgetSlot,
    PerGameSolver,
    SolveResult,
)


def _make_profile(game_type="click", metrics=None) -> GameProfile:
    return GameProfile(
        game_id="test_game",
        game_type=game_type,
        available_actions=[5, 6] if game_type == "click" else [1, 2, 3, 4, 5],
        click_zones=[(10, 10), (30, 30)] if game_type == "click" else [],
        target_colors=[3] if game_type == "click" else [],
        movement_effects={1: "moves_player", 2: "moves_player"} if game_type != "click" else {},
        win_condition="clear_board",
        vision_description="test",
        vision_strategy="test",
        strategy_metrics=metrics or {},
        analyzed_at="2026-04-04",
    )


class TestBudgetAllocation:
    def test_default_click_allocation(self):
        profile = _make_profile("click")
        solver = PerGameSolver(profile, arcade=MagicMock())
        slots = solver._allocate_budget(level_num=0)

        assert len(slots) == 3
        assert slots[0].strategy == "cluster_click"
        assert slots[0].max_actions == 10  # 50% of 20
        assert slots[1].strategy == "targeted_click"
        assert slots[1].max_actions == 6   # 30% of 20
        assert slots[2].strategy == "hybrid"
        assert slots[2].max_actions == 4   # 20% of 20

    def test_default_keyboard_allocation(self):
        profile = _make_profile("keyboard")
        solver = PerGameSolver(profile, arcade=MagicMock())
        slots = solver._allocate_budget(level_num=0)

        assert len(slots) == 3
        assert slots[0].strategy == "keyboard_explore"
        assert slots[0].max_actions == 100  # 50% of 200

    def test_default_mixed_allocation(self):
        profile = _make_profile("mixed")
        solver = PerGameSolver(profile, arcade=MagicMock())
        slots = solver._allocate_budget(level_num=0)

        assert slots[0].strategy == "hybrid"
        assert slots[0].max_actions == 50  # 50% of 100

    def test_ranked_allocation_overrides_defaults(self):
        metrics = {
            "keyboard_explore": StrategyMetrics(attempts=10, wins=8),
            "cluster_click": StrategyMetrics(attempts=10, wins=2),
            "hybrid": StrategyMetrics(attempts=5, wins=1),
        }
        profile = _make_profile("click", metrics=metrics)
        solver = PerGameSolver(profile, arcade=MagicMock())
        slots = solver._allocate_budget(level_num=0)

        # keyboard_explore has highest win_rate → gets 50%
        assert slots[0].strategy == "keyboard_explore"
        assert slots[1].strategy == "cluster_click"
        assert slots[2].strategy == "hybrid"


class TestStagnationDetection:
    def test_no_stagnation_with_changes(self):
        solver = PerGameSolver(_make_profile(), arcade=MagicMock())
        grids = [np.random.randint(0, 10, (64, 64)) for _ in range(5)]
        assert solver._detect_stagnation(grids) is False

    def test_stagnation_with_identical_frames(self):
        solver = PerGameSolver(_make_profile(), arcade=MagicMock())
        same = np.zeros((64, 64), dtype=np.int8)
        grids = [same.copy() for _ in range(5)]
        assert solver._detect_stagnation(grids) is True

    def test_stagnation_with_tiny_changes(self):
        solver = PerGameSolver(_make_profile(), arcade=MagicMock())
        base = np.zeros((64, 64), dtype=np.int8)
        grids = []
        for i in range(5):
            g = base.copy()
            g[0, i] = 1  # only 1 pixel changes per frame
            grids.append(g)
        # Max diff between consecutive = 2 pixels (one removed, one added)
        # Under threshold of 10 → stagnation
        assert solver._detect_stagnation(grids) is True

    def test_no_stagnation_with_short_history(self):
        solver = PerGameSolver(_make_profile(), arcade=MagicMock())
        same = np.zeros((64, 64), dtype=np.int8)
        assert solver._detect_stagnation([same, same]) is False  # < 5 frames


class TestSolveResult:
    def test_defaults(self):
        r = SolveResult(game_id="test", levels_completed=0, total_steps=0, strategy_log=[], score=0.0)
        assert r.game_id == "test"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_per_game_solver.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jarvis.arc.per_game_solver'`

- [ ] **Step 3: Implement PerGameSolver skeleton with budget allocation and stagnation**

```python
"""ARC-AGI-3 PerGameSolver — budget-based strategy execution per game."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from jarvis.arc.error_handler import safe_frame_extract
from jarvis.arc.game_profile import GameProfile
from jarvis.utils.logging import get_logger

__all__ = ["BudgetSlot", "PerGameSolver", "SolveResult"]

log = get_logger(__name__)

# Default total budget per game type
_BUDGET_BY_TYPE = {"click": 20, "keyboard": 200, "mixed": 100}

_STAGNATION_WINDOW = 5
_STAGNATION_THRESHOLD = 10  # pixels


@dataclass
class BudgetSlot:
    """One strategy with its allocated action budget."""

    strategy: str
    max_actions: int
    priority: int


@dataclass
class SolveResult:
    """Outcome of solving a game."""

    game_id: str
    levels_completed: int
    total_steps: int
    strategy_log: list[dict]
    score: float


class PerGameSolver:
    """Budget-based solver that combines strategies from a GameProfile."""

    def __init__(self, profile: GameProfile, arcade: Any):
        self._profile = profile
        self._arcade = arcade

    def _allocate_budget(self, level_num: int) -> list[BudgetSlot]:
        """Allocate action budget across strategies."""
        total = _BUDGET_BY_TYPE.get(self._profile.game_type, 100)

        ranked = self._profile.ranked_strategies()
        if ranked:
            # Use learned ranking: top 3 with 50/30/20 split
            top3 = ranked[:3]
            ratios = [0.5, 0.3, 0.2]
        else:
            # Use defaults for this game type
            defaults = self._profile.default_strategies()
            top3 = [name for name, _ in defaults]
            ratios = [ratio for _, ratio in defaults]

        slots = []
        for i, strategy in enumerate(top3):
            ratio = ratios[i] if i < len(ratios) else 0.1
            slots.append(BudgetSlot(
                strategy=strategy,
                max_actions=int(total * ratio),
                priority=i,
            ))

        return slots

    def _detect_stagnation(self, frame_history: list[np.ndarray]) -> bool:
        """Check if recent frames show no meaningful change."""
        if len(frame_history) < _STAGNATION_WINDOW:
            return False

        window = frame_history[-_STAGNATION_WINDOW:]
        for i in range(1, len(window)):
            diff = int(np.sum(window[i] != window[i - 1]))
            if diff >= _STAGNATION_THRESHOLD:
                return False

        return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_per_game_solver.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/per_game_solver.py tests/test_arc/test_per_game_solver.py
git commit -m "feat(arc): add PerGameSolver with budget allocation and stagnation detection"
```

---

### Task 7: PerGameSolver — Strategy Implementations

**Files:**
- Modify: `src/jarvis/arc/per_game_solver.py`
- Modify: `tests/test_arc/test_per_game_solver.py`

- [ ] **Step 1: Write the failing tests for strategy execution**

Append to `tests/test_arc/test_per_game_solver.py`:

```python
from jarvis.arc.per_game_solver import StrategyOutcome


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
    obs.available_actions = actions or []
    obs.win_levels = 0
    return obs


class TestStrategyExecution:
    def test_execute_cluster_click_win(self):
        """cluster_click strategy finds solution and wins."""
        profile = _make_profile("click")
        win_state = _make_mock_game_state("WIN")

        mock_arcade = MagicMock()
        step_count = [0]

        def mock_step(action, data=None):
            step_count[0] += 1
            # Win after 2 clicks
            if step_count[0] >= 2:
                return _make_mock_obs(state_name="WIN", levels=1)
            return _make_mock_obs()

        mock_env = MagicMock()
        mock_env.step = mock_step
        mock_env.reset.return_value = _make_mock_obs()
        mock_arcade.make.return_value = mock_env

        solver = PerGameSolver(profile, arcade=mock_arcade)
        outcome = solver._execute_strategy(mock_env, "targeted_click", max_actions=10)

        assert isinstance(outcome, StrategyOutcome)
        assert outcome.won is True
        assert outcome.steps > 0

    def test_execute_keyboard_explore(self):
        """keyboard_explore strategy runs actions without error."""
        profile = _make_profile("keyboard")
        mock_env = MagicMock()
        mock_env.step.return_value = _make_mock_obs()

        solver = PerGameSolver(profile, arcade=MagicMock())
        outcome = solver._execute_strategy(mock_env, "keyboard_explore", max_actions=20)

        assert isinstance(outcome, StrategyOutcome)
        assert outcome.steps == 20  # used full budget

    def test_execute_stops_on_game_over(self):
        """Strategy stops when GAME_OVER is received."""
        profile = _make_profile("click")
        mock_env = MagicMock()
        mock_env.step.return_value = _make_mock_obs(state_name="GAME_OVER")

        solver = PerGameSolver(profile, arcade=MagicMock())
        outcome = solver._execute_strategy(mock_env, "targeted_click", max_actions=10)

        assert outcome.won is False
        assert outcome.game_over is True

    def test_execute_stops_on_stagnation(self):
        """Strategy switches on stagnation (identical frames)."""
        profile = _make_profile("keyboard")
        same_grid = np.zeros((1, 64, 64), dtype=np.int8)
        mock_env = MagicMock()
        mock_env.step.return_value = _make_mock_obs(grid=same_grid)

        solver = PerGameSolver(profile, arcade=MagicMock())
        outcome = solver._execute_strategy(mock_env, "keyboard_explore", max_actions=50)

        # Should stop early due to stagnation (after ~5 identical frames)
        assert outcome.steps < 50
        assert outcome.stagnated is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_per_game_solver.py::TestStrategyExecution -v`
Expected: FAIL with `ImportError: cannot import name 'StrategyOutcome'`

- [ ] **Step 3: Implement _execute_strategy and StrategyOutcome**

Add to `per_game_solver.py`:

```python
@dataclass
class StrategyOutcome:
    """Result of executing one strategy on one level."""

    won: bool = False
    game_over: bool = False
    stagnated: bool = False
    steps: int = 0
    levels_solved: int = 0
    budget_ratio: float = 0.0
```

Add to `PerGameSolver` class:

```python
    def _execute_strategy(
        self, env: Any, strategy: str, max_actions: int
    ) -> StrategyOutcome:
        """Execute a single strategy with a given action budget."""
        from arcengine.enums import GameState

        outcome = StrategyOutcome()
        frame_history: list[np.ndarray] = []
        initial_levels = 0

        for step in range(max_actions):
            action_id, data = self._pick_action(strategy, frame_history)
            obs = env.step(action_id, data=data)
            grid = safe_frame_extract(obs)
            frame_history.append(grid)
            outcome.steps += 1

            if hasattr(obs, "levels_completed"):
                initial_levels = initial_levels or obs.levels_completed

            # Check terminal states
            if obs.state == GameState.WIN:
                outcome.won = True
                outcome.levels_solved = getattr(obs, "levels_completed", 0) - initial_levels + 1
                outcome.budget_ratio = outcome.steps / max_actions
                return outcome

            if obs.state == GameState.GAME_OVER:
                outcome.game_over = True
                outcome.budget_ratio = outcome.steps / max_actions
                return outcome

            # Check stagnation
            if self._detect_stagnation(frame_history):
                outcome.stagnated = True
                outcome.budget_ratio = outcome.steps / max_actions
                return outcome

        outcome.budget_ratio = 1.0
        return outcome

    def _pick_action(
        self, strategy: str, frame_history: list[np.ndarray]
    ) -> tuple[int, dict | None]:
        """Pick next action based on strategy."""
        profile = self._profile

        if strategy == "cluster_click" or strategy == "targeted_click":
            # Click on known zones from profile
            if profile.click_zones:
                idx = len(frame_history) % len(profile.click_zones)
                x, y = profile.click_zones[idx]
                return 6, {"x": x, "y": y}
            # Fallback: random position
            return 6, {"x": 32, "y": 32}

        if strategy == "keyboard_explore":
            # Cycle through directions
            directions = [a for a in profile.available_actions if a in (1, 2, 3, 4)]
            if directions:
                idx = len(frame_history) % len(directions)
                return directions[idx], None
            return 1, None

        if strategy == "keyboard_sequence":
            # Use directions in order, repeat
            directions = [a for a in profile.available_actions if a in (1, 2, 3, 4)]
            if directions:
                idx = len(frame_history) % len(directions)
                return directions[idx], None
            return 5, None  # interact as fallback

        if strategy == "hybrid":
            # Alternate: keyboard for first half, click for second
            if profile.click_zones and len(frame_history) % 4 == 3:
                idx = len(frame_history) % len(profile.click_zones)
                x, y = profile.click_zones[idx]
                return 6, {"x": x, "y": y}
            directions = [a for a in profile.available_actions if a in (1, 2, 3, 4)]
            if directions:
                idx = len(frame_history) % len(directions)
                return directions[idx], None
            return 5, None

        # Unknown strategy → interact
        return 5, None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_per_game_solver.py -v`
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/per_game_solver.py tests/test_arc/test_per_game_solver.py
git commit -m "feat(arc): implement strategy execution with stagnation and game-over handling"
```

---

### Task 8: PerGameSolver — solve() Level Loop

**Files:**
- Modify: `src/jarvis/arc/per_game_solver.py`
- Modify: `tests/test_arc/test_per_game_solver.py`

- [ ] **Step 1: Write the failing tests for solve()**

Append to `tests/test_arc/test_per_game_solver.py`:

```python
class TestSolve:
    def test_solve_single_level_win(self):
        """solve() wins a single level and returns SolveResult."""
        profile = _make_profile("click")
        win_grid = np.ones((1, 64, 64), dtype=np.int8)

        mock_env = MagicMock()
        step_count = [0]

        def mock_step(action, data=None):
            step_count[0] += 1
            if step_count[0] >= 2:
                return _make_mock_obs(grid=win_grid, state_name="WIN", levels=1)
            return _make_mock_obs()

        mock_env.step = mock_step
        mock_env.reset.return_value = _make_mock_obs()

        mock_arcade = MagicMock()
        mock_arcade.make.return_value = mock_env

        solver = PerGameSolver(profile, arcade=mock_arcade)
        result = solver.solve(max_levels=1)

        assert isinstance(result, SolveResult)
        assert result.levels_completed >= 1
        assert result.total_steps > 0
        assert len(result.strategy_log) >= 1

    def test_solve_skips_failed_level(self):
        """solve() moves to next level after all strategies fail."""
        profile = _make_profile("click")

        mock_env = MagicMock()
        # Always return same grid → stagnation → all strategies fail
        same_grid = np.zeros((1, 64, 64), dtype=np.int8)
        mock_env.step.return_value = _make_mock_obs(grid=same_grid)
        mock_env.reset.return_value = _make_mock_obs(grid=same_grid)

        mock_arcade = MagicMock()
        mock_arcade.make.return_value = mock_env

        solver = PerGameSolver(profile, arcade=mock_arcade)
        result = solver.solve(max_levels=2)

        assert result.levels_completed == 0

    def test_solve_updates_profile_metrics(self, tmp_path):
        """solve() updates strategy metrics in the profile."""
        profile = _make_profile("click")
        profile.save(base_dir=tmp_path)

        mock_env = MagicMock()
        step_count = [0]

        def mock_step(action, data=None):
            step_count[0] += 1
            if step_count[0] >= 2:
                return _make_mock_obs(state_name="WIN", levels=1)
            return _make_mock_obs()

        mock_env.step = mock_step
        mock_env.reset.return_value = _make_mock_obs()

        mock_arcade = MagicMock()
        mock_arcade.make.return_value = mock_env

        solver = PerGameSolver(profile, arcade=mock_arcade)
        solver.solve(max_levels=1, base_dir=tmp_path)

        # Profile should have been updated
        assert profile.total_runs == 1
        assert len(profile.strategy_metrics) > 0

    def test_solve_respects_timeout(self):
        """solve() respects the 5-minute timeout per game."""
        profile = _make_profile("keyboard")

        mock_env = MagicMock()
        # Never-ending game
        mock_env.step.return_value = _make_mock_obs(
            grid=np.random.randint(0, 10, (1, 64, 64), dtype=np.int8)
        )
        mock_env.reset.return_value = _make_mock_obs()

        mock_arcade = MagicMock()
        mock_arcade.make.return_value = mock_env

        solver = PerGameSolver(profile, arcade=mock_arcade)
        # With a tiny timeout, should return quickly
        result = solver.solve(max_levels=10, timeout_s=0.1)

        assert isinstance(result, SolveResult)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_per_game_solver.py::TestSolve -v`
Expected: FAIL with `TypeError: PerGameSolver.solve() got an unexpected keyword argument 'max_levels'`

- [ ] **Step 3: Implement solve() and _solve_level()**

Add to `PerGameSolver` class:

```python
    def solve(
        self,
        max_levels: int = 10,
        timeout_s: float = 300.0,
        base_dir: Any | None = None,
    ) -> SolveResult:
        """Solve the game level by level with budget-based strategy mix."""
        import time

        from arcengine.enums import GameState

        env = self._arcade.make(self._profile.game_id)
        obs = env.reset()

        result = SolveResult(
            game_id=self._profile.game_id,
            levels_completed=0,
            total_steps=0,
            strategy_log=[],
            score=0.0,
        )

        start_time = time.monotonic()
        max_resets = 3

        for level_num in range(max_levels):
            if time.monotonic() - start_time > timeout_s:
                log.info("arc.solver_timeout", game_id=self._profile.game_id)
                break

            level_result = self._solve_level(env, level_num, max_resets, start_time, timeout_s)
            result.total_steps += level_result["steps"]
            result.strategy_log.append(level_result)

            if level_result["won"]:
                result.levels_completed += 1
                # Update profile metrics for the winning strategy
                self._profile.update_metrics(
                    level_result["strategy"],
                    won=True,
                    levels_solved=1,
                    steps=level_result["steps"],
                    budget_ratio=level_result.get("budget_ratio", 1.0),
                )
            else:
                # Update metrics for failed strategies
                for failed in level_result.get("tried", []):
                    self._profile.update_metrics(
                        failed,
                        won=False,
                        levels_solved=0,
                        steps=level_result["steps"],
                        budget_ratio=1.0,
                    )

            # Check if game is complete (no more levels)
            if hasattr(obs, "state") and obs.state == GameState.WIN:
                break

        self._profile.update_run(score=result.levels_completed)
        self._profile.save(base_dir=base_dir)
        result.score = float(result.levels_completed)
        return result

    def _solve_level(
        self,
        env: Any,
        level_num: int,
        max_resets: int,
        start_time: float,
        timeout_s: float,
    ) -> dict:
        """Try all budget slots on one level."""
        import time

        from arcengine.enums import GameState

        slots = self._allocate_budget(level_num)
        total_steps = 0
        tried: list[str] = []
        resets_used = 0

        for slot in slots:
            if time.monotonic() - start_time > timeout_s:
                break

            tried.append(slot.strategy)
            outcome = self._execute_strategy(env, slot.strategy, slot.max_actions)
            total_steps += outcome.steps

            if outcome.won:
                return {
                    "level": level_num,
                    "strategy": slot.strategy,
                    "won": True,
                    "steps": total_steps,
                    "budget_ratio": outcome.budget_ratio,
                    "tried": tried,
                }

            if outcome.game_over:
                resets_used += 1
                if resets_used >= max_resets:
                    break
                # Reset level
                try:
                    env.reset()
                except Exception:
                    break

        return {
            "level": level_num,
            "strategy": tried[-1] if tried else "none",
            "won": False,
            "steps": total_steps,
            "tried": tried,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_per_game_solver.py -v`
Expected: 17 passed

- [ ] **Step 5: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/per_game_solver.py tests/test_arc/test_per_game_solver.py
git commit -m "feat(arc): implement solve() level loop with timeout and metrics update"
```

---

### Task 9: PerGameSolver — ClusterSolver Integration for cluster_click Strategy

**Files:**
- Modify: `src/jarvis/arc/per_game_solver.py`
- Modify: `tests/test_arc/test_per_game_solver.py`

- [ ] **Step 1: Write the failing test for cluster_click with subset search**

Append to `tests/test_arc/test_per_game_solver.py`:

```python
class TestClusterClickStrategy:
    def test_cluster_click_uses_subset_search(self):
        """cluster_click should find clusters and try subsets via arcade.make()."""
        profile = _make_profile("click")
        profile.target_colors = [3]

        # Initial grid with 3 clusters of color 3
        grid = np.zeros((64, 64), dtype=np.int8)
        grid[10:15, 10:15] = 3
        grid[30:35, 30:35] = 3
        grid[50:55, 50:55] = 3

        not_finished = _make_mock_game_state("NOT_FINISHED")
        win = _make_mock_game_state("WIN")

        make_count = [0]

        def mock_make(game_id):
            make_count[0] += 1
            env = MagicMock()
            click_count = [0]

            def env_step(action, data=None):
                click_count[0] += 1
                # Win when clicking exactly 2 of the 3 clusters
                if click_count[0] == 2:
                    return _make_mock_obs(state_name="WIN", levels=1)
                return _make_mock_obs(grid=np.expand_dims(grid, 0))

            env.step = env_step
            env.reset.return_value = _make_mock_obs(grid=np.expand_dims(grid, 0))
            return env

        mock_arcade = MagicMock()
        mock_arcade.make = mock_make

        solver = PerGameSolver(profile, arcade=mock_arcade)
        outcome = solver._execute_cluster_click(
            initial_grid=grid, target_color=3, max_actions=20
        )

        assert outcome.won is True
        assert make_count[0] > 0  # Used arcade.make for subset search

    def test_cluster_click_no_target_color_returns_empty(self):
        """cluster_click with no target color returns no-win outcome."""
        profile = _make_profile("click")
        profile.target_colors = []

        solver = PerGameSolver(profile, arcade=MagicMock())
        grid = np.zeros((64, 64), dtype=np.int8)
        outcome = solver._execute_cluster_click(grid, target_color=None, max_actions=10)

        assert outcome.won is False
        assert outcome.steps == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_per_game_solver.py::TestClusterClickStrategy -v`
Expected: FAIL with `AttributeError: 'PerGameSolver' object has no attribute '_execute_cluster_click'`

- [ ] **Step 3: Implement _execute_cluster_click**

Add to `PerGameSolver` class:

```python
    def _execute_cluster_click(
        self,
        initial_grid: np.ndarray,
        target_color: int | None,
        max_actions: int,
    ) -> StrategyOutcome:
        """Cluster-based click strategy: find clusters, try subsets via arcade.make()."""
        import itertools

        from arcengine.enums import GameState

        from jarvis.arc.cluster_solver import ClusterSolver

        outcome = StrategyOutcome()

        if target_color is None:
            return outcome

        solver = ClusterSolver(target_color=target_color, max_skip=6)
        centers = solver.find_clusters(initial_grid)

        if not centers:
            return outcome

        n = len(centers)
        max_skip = min(n, 6)
        combos_tried = 0

        for skip in range(max_skip + 1):
            for skip_combo in itertools.combinations(range(n), skip):
                if combos_tried >= max_actions:
                    outcome.budget_ratio = 1.0
                    return outcome

                click_idx = [i for i in range(n) if i not in skip_combo]
                combos_tried += 1

                # Test this combo in a fresh env
                env = self._arcade.make(self._profile.game_id)
                obs = env.reset()

                won = False
                for idx in click_idx:
                    cx, cy = centers[idx]
                    obs = env.step(6, data={"x": cx, "y": cy})
                    outcome.steps += 1

                    if obs.state == GameState.WIN:
                        won = True
                        break
                    if obs.state == GameState.GAME_OVER:
                        break

                if won:
                    outcome.won = True
                    outcome.levels_solved = 1
                    outcome.budget_ratio = combos_tried / max_actions
                    return outcome

        outcome.budget_ratio = 1.0
        return outcome
```

Update `_pick_action` and `_execute_strategy` to route `cluster_click` to the new method. In `_execute_strategy`, add this before the generic loop:

```python
        # Special handling for cluster_click: uses arcade.make() per combo
        if strategy == "cluster_click":
            target_color = self._profile.target_colors[0] if self._profile.target_colors else None
            last_grid = safe_frame_extract(env.reset()) if not hasattr(self, '_last_grid') else self._last_grid
            obs = env.reset()
            last_grid = safe_frame_extract(obs)
            return self._execute_cluster_click(last_grid, target_color, max_actions)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_per_game_solver.py -v`
Expected: 19 passed

- [ ] **Step 5: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/per_game_solver.py tests/test_arc/test_per_game_solver.py
git commit -m "feat(arc): add cluster_click strategy with subset search via arcade.make()"
```

---

### Task 10: CLI Integration — `--mode analyzer`

**Files:**
- Modify: `src/jarvis/arc/__main__.py`
- Modify: `tests/test_arc/test_game_analyzer.py`

- [ ] **Step 1: Write the failing test for CLI --mode analyzer**

Append to `tests/test_arc/test_game_analyzer.py`:

```python
class TestCLIIntegration:
    def test_build_parser_accepts_analyzer_mode(self):
        from jarvis.arc.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--mode", "analyzer", "--game", "ft09"])
        assert args.mode == "analyzer"
        assert args.game == "ft09"

    def test_build_parser_accepts_reanalyze_flag(self):
        from jarvis.arc.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--mode", "analyzer", "--reanalyze"])
        assert args.reanalyze is True

    def test_analyzer_mode_requires_game_or_all(self):
        """analyzer mode should work without --game (runs all games)."""
        from jarvis.arc.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--mode", "analyzer"])
        assert args.mode == "analyzer"
        assert args.game == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_analyzer.py::TestCLIIntegration -v`
Expected: FAIL with `error: argument --mode: invalid choice: 'analyzer'`

- [ ] **Step 3: Modify __main__.py to add analyzer mode**

In `src/jarvis/arc/__main__.py`, make these changes:

Change the `--mode` argument choices (line 35):
```python
    parser.add_argument(
        "--mode",
        choices=["single", "benchmark", "swarm", "analyzer"],
        default="single",
        help="Run mode: single (default), benchmark, swarm (parallel), analyzer (game analysis)",
    )
```

Add `--reanalyze` argument after `--config` (line 75):
```python
    parser.add_argument(
        "--reanalyze",
        action="store_true",
        default=False,
        help="Force re-analysis of games (ignore cached profiles, analyzer mode only)",
    )
```

Add `_run_analyzer` function after `_run_swarm` (before `main`):
```python
def _run_analyzer(game_id: str, reanalyze: bool, verbose: bool, config: Any) -> int:
    """Run GameAnalyzer + PerGameSolver. Returns exit code."""
    try:
        from jarvis.arc.game_analyzer import GameAnalyzer
        from jarvis.arc.per_game_solver import PerGameSolver
    except ImportError as exc:
        print(f"[FAIL] Could not import GameAnalyzer: {exc}", file=sys.stderr)
        return 1

    try:
        import arc_agi

        arcade = arc_agi.Arcade()
    except Exception as exc:
        print(f"[FAIL] Could not create Arcade: {exc}", file=sys.stderr)
        return 1

    # Determine games to analyze
    if game_id:
        game_ids = [game_id]
    else:
        try:
            from jarvis.arc.adapter import ArcEnvironmentAdapter

            game_ids = ArcEnvironmentAdapter.list_games()
        except Exception:
            game_ids = []

    if not game_ids:
        print("[FAIL] No games found.", file=sys.stderr)
        return 1

    if verbose:
        print(f"[INFO] Analyzer mode: {len(game_ids)} game(s), reanalyze={reanalyze}")

    analyzer = GameAnalyzer(arcade=arcade)
    total_levels = 0
    total_score = 0.0

    for gid in game_ids:
        if verbose:
            print(f"\n[INFO] Analyzing {gid}...")

        try:
            profile = analyzer.analyze(gid, force=reanalyze)
            if verbose:
                print(f"  type={profile.game_type}, actions={profile.available_actions}")
                print(f"  click_zones={len(profile.click_zones)}, win={profile.win_condition}")

            solver = PerGameSolver(profile, arcade=arcade)
            result = solver.solve()

            total_levels += result.levels_completed
            total_score += result.score

            print(f"[RESULT] {gid}: {result.levels_completed} levels, {result.total_steps} steps")
            for entry in result.strategy_log:
                status = "WIN" if entry["won"] else "FAIL"
                print(f"  Level {entry['level']}: {status} via {entry['strategy']} ({entry['steps']} steps)")

        except Exception as exc:
            print(f"[FAIL] {gid}: {exc}", file=sys.stderr)
            if verbose:
                import traceback

                traceback.print_exc()

    print(f"\n[SUMMARY] Total levels: {total_levels}, Total score: {total_score:.1f}")

    try:
        scorecard = arcade.get_scorecard()
        print(f"[SCORECARD] {scorecard.score}")
    except Exception:
        pass

    return 0
```

Add routing in `main()` function, after the swarm block (before the "Unknown mode" print):
```python
    if args.mode == "analyzer":
        return _run_analyzer(
            game_id=args.game,
            reanalyze=args.reanalyze,
            verbose=args.verbose,
            config=config,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_game_analyzer.py::TestCLIIntegration -v`
Expected: 3 passed

- [ ] **Step 5: Run all ARC tests to verify no regressions**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/ -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/__main__.py tests/test_arc/test_game_analyzer.py
git commit -m "feat(arc): add --mode analyzer CLI entry point with GameAnalyzer + PerGameSolver"
```

---

### Task 11: Final Integration Test & Smoke Test

**Files:**
- Create: `tests/test_arc/test_analyzer_integration.py`

- [ ] **Step 1: Write integration test for the full pipeline**

```python
"""Integration tests for GameAnalyzer → PerGameSolver pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from jarvis.arc.game_analyzer import GameAnalyzer
from jarvis.arc.game_profile import GameProfile, StrategyMetrics
from jarvis.arc.per_game_solver import PerGameSolver, SolveResult


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
        """Full pipeline: analyze → profile → solve → metrics updated."""
        # Setup: a simple click game with clusters
        grid = np.zeros((64, 64), dtype=np.int8)
        grid[10:15, 10:15] = 3  # cluster 1
        grid[40:45, 40:45] = 3  # cluster 2

        not_finished = _make_mock_game_state("NOT_FINISHED")
        game_over = _make_mock_game_state("GAME_OVER")
        win = _make_mock_game_state("WIN")

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
                "content": json.dumps({
                    "game_type": "click",
                    "target_color": 3,
                    "strategy": "Click red clusters",
                    "description": "Grid with red blocks",
                    "win_condition": "clear_board",
                })
            }
        }

        # Step 1: Analyze
        with patch("jarvis.arc.game_analyzer.ollama") as mock_ollama:
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
        with patch("jarvis.arc.game_analyzer.ollama") as mock_ollama:
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
        profile.update_metrics("cluster_click", won=True, levels_solved=1, steps=50, budget_ratio=0.8)
        profile.update_metrics("cluster_click", won=True, levels_solved=2, steps=30, budget_ratio=0.5)
        profile.update_metrics("targeted_click", won=False, levels_solved=0, steps=20, budget_ratio=1.0)

        ranked = profile.ranked_strategies()
        assert ranked[0] == "cluster_click"  # 100% win rate
        assert ranked[1] == "targeted_click"  # 0% win rate

        m = profile.strategy_metrics["cluster_click"]
        assert m.attempts == 2
        assert m.wins == 2
        assert m.total_levels_solved == 3
        assert m.avg_steps_to_win == pytest.approx(40.0)
```

- [ ] **Step 2: Run integration tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/test_analyzer_integration.py -v`
Expected: 3 passed

- [ ] **Step 3: Run all ARC tests together**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/ -v`
Expected: All tests pass, no regressions

- [ ] **Step 4: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add tests/test_arc/test_analyzer_integration.py
git commit -m "test(arc): add integration tests for GameAnalyzer pipeline"
```

---

### Task 12: Exports & Docmodule Hygiene

**Files:**
- Modify: `src/jarvis/arc/__init__.py`

- [ ] **Step 1: Check current __init__.py exports**

Run: `cd "D:/Jarvis/jarvis complete v20" && cat src/jarvis/arc/__init__.py`

- [ ] **Step 2: Add new module exports if __init__.py has explicit exports**

If `__init__.py` has explicit `__all__` or imports, add:

```python
from jarvis.arc.game_analyzer import GameAnalyzer
from jarvis.arc.game_profile import GameProfile, StrategyMetrics
from jarvis.arc.per_game_solver import PerGameSolver, SolveResult
```

If `__init__.py` is empty or just a marker, leave it as-is.

- [ ] **Step 3: Run full test suite one final time**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_arc/ -v --tb=short`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
cd "D:/Jarvis/jarvis complete v20"
git add src/jarvis/arc/__init__.py
git commit -m "chore(arc): add GameAnalyzer exports to arc package"
```
