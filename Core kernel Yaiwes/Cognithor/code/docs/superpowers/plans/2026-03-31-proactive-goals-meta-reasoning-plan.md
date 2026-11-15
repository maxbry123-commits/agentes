# Proactive Goal Pursuit + Meta-Reasoning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Cognithor proactively set new goals from knowledge gaps and reflect on planning strategies — not just tool outcomes.

**Architecture:** Two tightly coupled extensions to existing systems. Feature 7 (Proactive Goals) extends the ATL thinking cycle to consume CuriosityEngine gaps as goal candidates and verify action outcomes. Feature 8 (Meta-Reasoning) adds a StrategyMemory to the CausalAnalyzer that tracks task_type → plan_strategy → success_rate, and injects "what worked before" hints into the Planner's system prompt.

**Tech Stack:** Python 3.13, existing SQLite/encrypted_connect, CausalAnalyzer, CuriosityEngine, ATL GoalManager, Planner system prompt injection

---

## File Structure

```
Modified files:
  src/jarvis/evolution/loop.py              — ATL: auto-create goals from curiosity gaps
  src/jarvis/learning/causal.py             — StrategyMemory: task_type → strategy → score
  src/jarvis/core/planner.py                — Inject strategy hints into system prompt
  src/jarvis/gateway/gateway.py             — Record strategy outcomes in post-processing

New files:
  src/jarvis/learning/strategy_memory.py    — StrategyRecord dataclass + StrategyMemory class

Test files:
  tests/test_learning/test_strategy_memory.py
  tests/test_atl/test_proactive_goals.py
```

---

### Task 1: StrategyMemory — track task_type → strategy → success

**Files:**
- Create: `src/jarvis/learning/strategy_memory.py`
- Test: `tests/test_learning/test_strategy_memory.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_learning/test_strategy_memory.py
"""Tests for StrategyMemory — meta-reasoning about planning strategies."""
from __future__ import annotations

import pytest
from pathlib import Path

from jarvis.learning.strategy_memory import StrategyMemory, StrategyRecord


@pytest.fixture
def sm(tmp_path):
    return StrategyMemory(db_path=tmp_path / "strategy.db")


def test_record_and_query(sm):
    sm.record(StrategyRecord(
        task_type="web_research",
        strategy="search_and_read → save_to_memory",
        success=True,
        duration_ms=1500,
        tool_count=2,
    ))
    sm.record(StrategyRecord(
        task_type="web_research",
        strategy="web_search → web_fetch → save_to_memory",
        success=False,
        duration_ms=5000,
        tool_count=3,
    ))
    best = sm.best_strategy("web_research")
    assert best is not None
    assert best.strategy == "search_and_read → save_to_memory"
    assert best.success_rate == 1.0


def test_best_strategy_no_data(sm):
    assert sm.best_strategy("unknown_type") is None


def test_success_rate_calculation(sm):
    for _ in range(7):
        sm.record(StrategyRecord(
            task_type="code_fix",
            strategy="analyze → run_python → test",
            success=True, duration_ms=2000, tool_count=3,
        ))
    for _ in range(3):
        sm.record(StrategyRecord(
            task_type="code_fix",
            strategy="analyze → run_python → test",
            success=False, duration_ms=3000, tool_count=3,
        ))
    best = sm.best_strategy("code_fix")
    assert best.success_rate == pytest.approx(0.7)
    assert best.total_uses == 10


def test_hint_for_planner(sm):
    sm.record(StrategyRecord(
        task_type="document_creation",
        strategy="typst_render",
        success=True, duration_ms=800, tool_count=1,
    ))
    hint = sm.get_strategy_hint("document_creation")
    assert "typst_render" in hint
    assert "100%" in hint


def test_hint_empty_returns_empty(sm):
    assert sm.get_strategy_hint("unknown") == ""


def test_classify_task():
    from jarvis.learning.strategy_memory import classify_task_type
    assert classify_task_type(["search_and_read", "web_fetch"]) == "web_research"
    assert classify_task_type(["run_python", "analyze_code"]) == "code_execution"
    assert classify_task_type(["vault_save", "save_to_memory"]) == "knowledge_management"
    assert classify_task_type(["document_export", "typst_render"]) == "document_creation"
    assert classify_task_type(["exec_command"]) == "system_command"
    assert classify_task_type([]) == "general"


def test_persistence(tmp_path):
    path = tmp_path / "strategy.db"
    sm1 = StrategyMemory(db_path=path)
    sm1.record(StrategyRecord(
        task_type="test", strategy="a → b", success=True,
        duration_ms=100, tool_count=2,
    ))
    sm2 = StrategyMemory(db_path=path)
    assert sm2.best_strategy("test") is not None
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement strategy_memory.py**

```python
# src/jarvis/learning/strategy_memory.py
"""StrategyMemory — meta-reasoning about planning strategies.

Tracks which tool sequences (strategies) work best for which task types.
The Planner uses this to inject "what worked before" hints into its
system prompt, enabling strategy-level learning across sessions.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jarvis.security.encrypted_db import encrypted_connect
from jarvis.utils.logging import get_logger

log = get_logger(__name__)

__all__ = ["StrategyMemory", "StrategyRecord", "StrategyStats", "classify_task_type"]

_TOOL_TYPE_MAP = {
    "web_research": {"search_and_read", "web_search", "web_fetch", "web_news_search",
                     "deep_research", "verified_web_lookup"},
    "code_execution": {"run_python", "analyze_code", "exec_command"},
    "knowledge_management": {"save_to_memory", "search_memory", "vault_save",
                             "vault_search", "add_entity", "add_relation"},
    "document_creation": {"document_export", "document_create", "typst_render",
                          "template_render"},
    "file_operations": {"read_file", "write_file", "edit_file", "list_directory",
                        "find_in_files", "search_files"},
    "system_command": {"exec_command"},
    "browser_automation": {"browser_navigate", "browser_click", "browser_fill",
                           "browser_screenshot", "browser_solve_captcha"},
    "communication": {"send_notification", "email_send"},
}


def classify_task_type(tools_used: list[str]) -> str:
    """Classify a tool sequence into a task type."""
    if not tools_used:
        return "general"
    tool_set = set(tools_used)
    best_type = "general"
    best_overlap = 0
    for task_type, type_tools in _TOOL_TYPE_MAP.items():
        overlap = len(tool_set & type_tools)
        if overlap > best_overlap:
            best_overlap = overlap
            best_type = task_type
    return best_type


@dataclass
class StrategyRecord:
    """A single strategy execution record."""
    task_type: str
    strategy: str  # "tool_a → tool_b → tool_c"
    success: bool
    duration_ms: int
    tool_count: int


@dataclass
class StrategyStats:
    """Aggregated stats for a strategy."""
    task_type: str
    strategy: str
    success_rate: float
    total_uses: int
    avg_duration_ms: float


class StrategyMemory:
    """Persistent store for task_type → strategy → success patterns."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = str(db_path) if db_path else ":memory:"
        self._conn = encrypted_connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                strategy TEXT NOT NULL,
                success INTEGER NOT NULL,
                duration_ms INTEGER NOT NULL,
                tool_count INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_strat_type
                ON strategies(task_type);
        """)
        self._conn.commit()

    def record(self, rec: StrategyRecord) -> None:
        """Record a strategy execution."""
        self._conn.execute(
            "INSERT INTO strategies (task_type, strategy, success, duration_ms, tool_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (rec.task_type, rec.strategy, int(rec.success), rec.duration_ms, rec.tool_count),
        )
        self._conn.commit()

    def best_strategy(self, task_type: str, min_uses: int = 1) -> StrategyStats | None:
        """Return the most successful strategy for a task type."""
        row = self._conn.execute(
            "SELECT strategy, "
            "  AVG(success) as success_rate, "
            "  COUNT(*) as total_uses, "
            "  AVG(duration_ms) as avg_duration "
            "FROM strategies "
            "WHERE task_type = ? "
            "GROUP BY strategy "
            "HAVING total_uses >= ? "
            "ORDER BY success_rate DESC, avg_duration ASC "
            "LIMIT 1",
            (task_type, min_uses),
        ).fetchone()
        if not row:
            return None
        return StrategyStats(
            task_type=task_type,
            strategy=row["strategy"] if isinstance(row, dict) else row[0],
            success_rate=row["success_rate"] if isinstance(row, dict) else row[1],
            total_uses=row["total_uses"] if isinstance(row, dict) else row[2],
            avg_duration_ms=row["avg_duration"] if isinstance(row, dict) else row[3],
        )

    def get_strategy_hint(self, task_type: str) -> str:
        """Return a human-readable hint for the Planner system prompt."""
        stats = self.best_strategy(task_type, min_uses=2)
        if not stats:
            return ""
        return (
            f"Fuer '{task_type}' hat die Strategie [{stats.strategy}] "
            f"eine Erfolgsrate von {stats.success_rate:.0%} "
            f"({stats.total_uses} Ausfuehrungen, ~{stats.avg_duration_ms:.0f}ms)."
        )

    def close(self) -> None:
        if self._conn:
            self._conn.close()
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

### Task 2: Record strategy outcomes in Gateway post-processing

**Files:**
- Modify: `src/jarvis/gateway/gateway.py` — record strategy after each PGE cycle
- Modify: `src/jarvis/gateway/phases/advanced.py` — instantiate StrategyMemory

- [ ] **Step 1: Instantiate StrategyMemory in init_advanced**

In `src/jarvis/gateway/phases/advanced.py`, after the existing GEPA block, add:

```python
# StrategyMemory (Meta-Reasoning)
try:
    from jarvis.learning.strategy_memory import StrategyMemory
    jarvis_home = getattr(config, "jarvis_home", Path.home() / ".cognithor")
    strat_db = Path(jarvis_home) / "index" / "strategy_memory.db"
    result["strategy_memory"] = StrategyMemory(db_path=strat_db)
    log.info("strategy_memory_initialized", db=str(strat_db))
except Exception:
    log.debug("strategy_memory_init_skipped", exc_info=True)
```

- [ ] **Step 2: Record strategy in _run_post_processing**

In `gateway.py`, inside `_run_post_processing()`, after the reflection block, add:

```python
# Meta-Reasoning: record strategy outcome for this PGE cycle
if getattr(self, "_strategy_memory", None) and all_results:
    try:
        from jarvis.learning.strategy_memory import (
            StrategyRecord, classify_task_type,
        )
        tools_used = [r.tool_name for r in all_results if r.tool_name]
        task_type = classify_task_type(tools_used)
        strategy = " → ".join(dict.fromkeys(tools_used))  # deduplicated order
        success = any(r.success for r in all_results)
        total_ms = sum(getattr(r, "duration_ms", 0) or 0 for r in all_results)
        self._strategy_memory.record(StrategyRecord(
            task_type=task_type,
            strategy=strategy[:200],
            success=success,
            duration_ms=total_ms,
            tool_count=len(tools_used),
        ))
    except Exception:
        log.debug("strategy_record_failed", exc_info=True)
```

- [ ] **Step 3: Run tests, commit**

---

### Task 3: Inject strategy hints into Planner system prompt

**Files:**
- Modify: `src/jarvis/core/planner.py` — add strategy hints section
- Modify: `src/jarvis/gateway/gateway.py` — wire strategy_memory to planner

- [ ] **Step 1: Add _strategy_memory to Planner**

In `planner.py`, add `self._strategy_memory = None` in `__init__`.

- [ ] **Step 2: Inject hints in _build_system_prompt**

In `_build_system_prompt()`, after the "Taktische Einsichten" block and before "Causal-Learning-Vorschlaege", add:

```python
# Meta-Reasoning: strategy hints from past successes
if self._strategy_memory is not None:
    try:
        # Classify likely task type from the current tools in context
        all_tool_names = list(tool_schemas.keys()) if tool_schemas else []
        # Get hints for common task types
        hints = []
        for tt in ["web_research", "code_execution", "document_creation",
                    "knowledge_management", "file_operations"]:
            h = self._strategy_memory.get_strategy_hint(tt)
            if h:
                hints.append(h)
        if hints:
            context_parts.append(
                "### Bewaehrte Strategien\n" + "\n".join(hints[:3])
            )
    except Exception:
        pass
```

- [ ] **Step 3: Wire strategy_memory to planner in gateway.py**

After the `_confidence_manager` wiring block:

```python
# Wire strategy_memory to planner (meta-reasoning hints)
if getattr(self, "_strategy_memory", None) and getattr(self, "_planner", None):
    self._planner._strategy_memory = self._strategy_memory
```

- [ ] **Step 4: Run tests, commit**

---

### Task 4: ATL auto-creates goals from CuriosityEngine gaps

**Files:**
- Modify: `src/jarvis/evolution/loop.py` — extend thinking_cycle
- Test: `tests/test_atl/test_proactive_goals.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_atl/test_proactive_goals.py
"""Tests for ATL proactive goal creation from curiosity gaps."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from jarvis.evolution.atl_config import ATLConfig
from jarvis.evolution.goal_manager import GoalManager


def test_auto_goal_from_curiosity(tmp_path):
    from jarvis.evolution.loop import EvolutionLoop

    idle = MagicMock()
    idle.is_idle = True
    idle.idle_seconds = 300.0

    loop = EvolutionLoop(idle_detector=idle)
    loop._atl_config = ATLConfig(enabled=True)

    gm = GoalManager(goals_path=tmp_path / "goals.yaml")
    loop._goal_manager = gm

    # Simulate curiosity gaps
    curiosity = MagicMock()
    gap = MagicMock()
    gap.entity_name = "Kubernetes"
    gap.gap_type = "low_confidence"
    gap.importance = 0.8
    gap.description = "Low confidence entity needs verification"
    curiosity.propose_exploration.return_value = [gap]
    loop._curiosity = curiosity

    # Run proactive goal creation
    created = loop._create_goals_from_curiosity()
    assert created >= 1
    goals = gm.active_goals()
    assert any("Kubernetes" in g.title for g in goals)
    assert goals[0].source == "curiosity"


def test_no_duplicate_goals(tmp_path):
    from jarvis.evolution.loop import EvolutionLoop
    from jarvis.evolution.goal_manager import Goal

    idle = MagicMock()
    idle.is_idle = True
    loop = EvolutionLoop(idle_detector=idle)
    loop._atl_config = ATLConfig(enabled=True)

    gm = GoalManager(goals_path=tmp_path / "goals.yaml")
    gm.add_goal(Goal(
        title="Lerne Kubernetes", description="Already exists",
        priority=3, source="user",
    ))
    loop._goal_manager = gm

    curiosity = MagicMock()
    gap = MagicMock()
    gap.entity_name = "Kubernetes"
    gap.gap_type = "low_confidence"
    gap.importance = 0.5
    gap.description = "duplicate"
    curiosity.propose_exploration.return_value = [gap]
    loop._curiosity = curiosity

    created = loop._create_goals_from_curiosity()
    assert created == 0  # No duplicates
    assert len(gm.active_goals()) == 1
```

- [ ] **Step 2: Implement _create_goals_from_curiosity() in loop.py**

Add this method to `EvolutionLoop`:

```python
def _create_goals_from_curiosity(self) -> int:
    """Auto-create ATL goals from CuriosityEngine knowledge gaps.

    Only creates goals for gaps with importance >= 0.6 that don't
    already have a matching goal (by entity name in title).
    Returns number of goals created.
    """
    if not self._curiosity or not self._goal_manager:
        return 0

    try:
        gaps = self._curiosity.propose_exploration(max_tasks=5)
    except Exception:
        return 0

    if not gaps:
        return 0

    existing_titles = {
        g.title.lower() for g in self._goal_manager.active_goals()
    }
    created = 0

    for gap in gaps:
        entity = getattr(gap, "entity_name", str(gap))
        importance = getattr(gap, "importance", 0.5)
        if importance < 0.6:
            continue
        # Deduplicate: skip if entity name is already in any goal title
        if any(entity.lower() in t for t in existing_titles):
            continue

        from jarvis.evolution.goal_manager import Goal
        goal = Goal(
            title=f"Lerne {entity}",
            description=getattr(gap, "description", f"Knowledge gap: {entity}"),
            priority=4,  # Lower than user goals (3)
            source="curiosity",
        )
        try:
            self._goal_manager.add_goal(goal)
            existing_titles.add(goal.title.lower())
            created += 1
            log.info("atl_goal_auto_created", entity=entity, importance=importance)
        except Exception:
            pass

    return created
```

- [ ] **Step 3: Call from thinking_cycle()**

In `thinking_cycle()`, before the LLM call (before "Build context"), add:

```python
# Proactive: auto-create goals from curiosity gaps
self._create_goals_from_curiosity()
```

- [ ] **Step 4: Run tests, commit**

---

### Task 5: ATL verifies action outcomes

**Files:**
- Modify: `src/jarvis/evolution/loop.py` — check if research actions produced results

- [ ] **Step 1: Add outcome verification after action dispatch**

In `thinking_cycle()`, after the action dispatch loop and before the journal write, add:

```python
# Verify action outcomes: did the research actually produce new knowledge?
_verified_actions: list[str] = []
for desc in executed_actions:
    if "[OK]" in desc and "research" in desc:
        # Check if vault/memory grew
        if self._memory and hasattr(self._memory, "search_memory_sync"):
            try:
                query = desc.split(":", 1)[-1].strip()[:50]
                results = self._memory.search_memory_sync(query=query, top_k=1)
                if results:
                    _verified_actions.append(f"{desc} [VERIFIED: found in memory]")
                else:
                    _verified_actions.append(f"{desc} [UNVERIFIED: not in memory yet]")
                continue
            except Exception:
                pass
    _verified_actions.append(desc)
if _verified_actions:
    executed_actions = _verified_actions
```

- [ ] **Step 2: Commit**

---

### Task 6: Final wiring + lint + test

**Files:**
- All modified files

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/test_atl/ tests/test_learning/test_strategy_memory.py -v`

- [ ] **Step 2: Run ruff**

Run: `ruff check src/jarvis/learning/strategy_memory.py src/jarvis/evolution/loop.py src/jarvis/core/planner.py src/jarvis/gateway/gateway.py`

- [ ] **Step 3: Final commit**

---

## Coverage Check

| Feature | Covered by Task |
|---------|-----------------|
| **7: Proactive Goal Pursuit** | |
| ATL auto-creates goals from curiosity gaps | Task 4 |
| Deduplication (no duplicate goals) | Task 4 |
| Outcome verification (did actions produce results) | Task 5 |
| Goals from curiosity have lower priority than user goals | Task 4 (priority=4) |
| **8: Meta-Reasoning** | |
| StrategyMemory data model + persistence | Task 1 |
| classify_task_type() from tool lists | Task 1 |
| Record strategy outcomes in post-processing | Task 2 |
| Strategy hints in Planner system prompt | Task 3 |
| best_strategy() with success_rate ranking | Task 1 |

## Test Summary

| Task | Tests |
|------|-------|
| 1: StrategyMemory | 7 |
| 4: Proactive Goals | 2 |
| **Total** | **9** |
