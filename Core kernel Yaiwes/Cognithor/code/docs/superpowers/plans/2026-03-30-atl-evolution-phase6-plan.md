# ATL (Evolution Phase 6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Evolution Engine with an Autonomous Thinking Loop that evaluates goals, takes actions, writes journal entries, and notifies the user proactively.

**Architecture:** New modules (goal_manager, action_queue, atl_journal, atl_prompt, atl_config) integrate into the existing evolution/ package. The EvolutionLoop gets a new `_thinking_cycle()` alongside the existing `run_cycle()`. Gatekeeper gets a `risk_ceiling` parameter.

**Tech Stack:** Python 3.13, asyncio, PyYAML, APScheduler (existing), structlog (existing)

---

### Task 1: ATLConfig dataclass

**Files:**
- Create: `src/jarvis/evolution/atl_config.py`
- Modify: `src/jarvis/config.py` (add ATLConfig to JarvisConfig)
- Test: `tests/test_atl/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_atl/test_config.py
import pytest
from jarvis.evolution.atl_config import ATLConfig

def test_atl_config_defaults():
    cfg = ATLConfig()
    assert cfg.enabled is False
    assert cfg.interval_minutes == 15
    assert cfg.max_actions_per_cycle == 3
    assert cfg.max_tokens_per_cycle == 4000
    assert cfg.risk_ceiling == "YELLOW"
    assert cfg.notification_level == "important"
    assert "shell_exec" in cfg.blocked_action_types

def test_atl_config_quiet_hours():
    cfg = ATLConfig(quiet_hours_start="22:00", quiet_hours_end="08:00")
    assert cfg.quiet_hours_start == "22:00"
    assert cfg.quiet_hours_end == "08:00"

def test_atl_config_validates_interval():
    cfg = ATLConfig(interval_minutes=3)
    assert cfg.interval_minutes == 5  # clamped to minimum

    cfg2 = ATLConfig(interval_minutes=120)
    assert cfg2.interval_minutes == 60  # clamped to maximum
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_atl/test_config.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Create tests/__init__.py and implement ATLConfig**

Create `tests/test_atl/__init__.py` (empty).

```python
# src/jarvis/evolution/atl_config.py
"""ATL Configuration dataclass."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ATLConfig:
    """Configuration for the Autonomous Thinking Loop."""

    enabled: bool = False
    interval_minutes: int = 15
    quiet_hours_start: str = "23:00"
    quiet_hours_end: str = "07:00"
    max_actions_per_cycle: int = 3
    max_tokens_per_cycle: int = 4000
    notification_channel: str = ""
    notification_level: str = "important"  # all | important | critical
    goal_review_interval: str = "daily"
    risk_ceiling: str = "YELLOW"  # GREEN | YELLOW
    allowed_action_types: list[str] = field(default_factory=lambda: [
        "memory_update", "research", "notification",
        "file_management", "goal_management",
    ])
    blocked_action_types: list[str] = field(default_factory=lambda: [
        "shell_exec", "send_message_unprompted",
    ])

    def __post_init__(self) -> None:
        self.interval_minutes = max(5, min(60, self.interval_minutes))
        if self.risk_ceiling not in ("GREEN", "YELLOW"):
            self.risk_ceiling = "YELLOW"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_atl/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Wire ATLConfig into JarvisConfig**

In `src/jarvis/config.py`, add `atl: ATLConfig = field(default_factory=ATLConfig)` to JarvisConfig, import ATLConfig, and add YAML parsing in `_parse_atl()`.

- [ ] **Step 6: Commit**

```bash
git add src/jarvis/evolution/atl_config.py tests/test_atl/
git commit -m "feat(atl): add ATLConfig dataclass with defaults and validation"
```

---

### Task 2: GoalManager with YAML persistence

**Files:**
- Create: `src/jarvis/evolution/goal_manager.py`
- Test: `tests/test_atl/test_goal_manager.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_atl/test_goal_manager.py
import pytest
from pathlib import Path
from jarvis.evolution.goal_manager import GoalManager, Goal

@pytest.fixture
def gm(tmp_path):
    return GoalManager(goals_path=tmp_path / "goals.yaml")

def test_add_and_list_goals(gm):
    gm.add_goal(Goal(
        id="g_001", title="Learn Solvency II",
        description="Full knowledge of insurance regulation",
        priority=2, source="user",
    ))
    goals = gm.active_goals()
    assert len(goals) == 1
    assert goals[0].id == "g_001"
    assert goals[0].status == "active"

def test_update_progress(gm):
    gm.add_goal(Goal(id="g_001", title="Test", description="", priority=3, source="user"))
    gm.update_progress("g_001", delta=0.25, note="First chunk done")
    goal = gm.get_goal("g_001")
    assert goal.progress == pytest.approx(0.25)

def test_complete_goal(gm):
    gm.add_goal(Goal(id="g_001", title="Test", description="", priority=3, source="user"))
    gm.complete_goal("g_001")
    assert gm.get_goal("g_001").status == "completed"
    assert len(gm.active_goals()) == 0

def test_pause_and_resume(gm):
    gm.add_goal(Goal(id="g_001", title="Test", description="", priority=3, source="user"))
    gm.pause_goal("g_001")
    assert gm.get_goal("g_001").status == "paused"
    assert len(gm.active_goals()) == 0
    gm.resume_goal("g_001")
    assert gm.get_goal("g_001").status == "active"

def test_persistence(tmp_path):
    path = tmp_path / "goals.yaml"
    gm1 = GoalManager(goals_path=path)
    gm1.add_goal(Goal(id="g_001", title="Persist", description="", priority=3, source="user"))
    # New instance reads from disk
    gm2 = GoalManager(goals_path=path)
    assert len(gm2.active_goals()) == 1

def test_migrate_learning_goals(gm):
    old = ["Learn ARC-AGI", "Master cybersecurity"]
    gm.migrate_learning_goals(old)
    goals = gm.active_goals()
    assert len(goals) == 2
    assert goals[0].source == "user"
    assert "ARC-AGI" in goals[0].title

def test_priority_sorting(gm):
    gm.add_goal(Goal(id="g_low", title="Low", description="", priority=5, source="self"))
    gm.add_goal(Goal(id="g_high", title="High", description="", priority=1, source="user"))
    goals = gm.active_goals()
    assert goals[0].id == "g_high"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_atl/test_goal_manager.py -v`
Expected: FAIL

- [ ] **Step 3: Implement GoalManager**

Create `src/jarvis/evolution/goal_manager.py` with:
- `Goal` dataclass (id, title, description, priority, status, created_at, updated_at, deadline, progress, sub_goals, success_criteria, tags, source)
- `GoalManager` class with YAML load/save, CRUD methods, `migrate_learning_goals()`
- Auto-generates `id` if not provided (uuid4 hex[:8])
- `active_goals()` returns sorted by priority (ascending = highest first)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_atl/test_goal_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/goal_manager.py tests/test_atl/test_goal_manager.py
git commit -m "feat(atl): GoalManager with YAML persistence and migration"
```

---

### Task 3: ActionQueue

**Files:**
- Create: `src/jarvis/evolution/action_queue.py`
- Test: `tests/test_atl/test_action_queue.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_atl/test_action_queue.py
from jarvis.evolution.action_queue import ActionQueue, ATLAction

def test_enqueue_and_dequeue():
    q = ActionQueue(max_actions=3)
    a1 = ATLAction(type="research", params={"query": "test"}, priority=2, rationale="test")
    a2 = ATLAction(type="notification", params={}, priority=1, rationale="urgent")
    q.enqueue(a1)
    q.enqueue(a2)
    # Higher priority (lower number) dequeued first
    assert q.dequeue().type == "notification"
    assert q.dequeue().type == "research"

def test_max_limit():
    q = ActionQueue(max_actions=2)
    for i in range(5):
        q.enqueue(ATLAction(type="research", params={}, priority=3, rationale=f"r{i}"))
    assert q.size() == 2  # Excess dropped

def test_empty():
    q = ActionQueue(max_actions=3)
    assert q.empty()
    q.enqueue(ATLAction(type="research", params={}, priority=3, rationale=""))
    assert not q.empty()

def test_blocked_types():
    q = ActionQueue(max_actions=3, blocked_types={"shell_exec"})
    rejected = q.enqueue(ATLAction(type="shell_exec", params={}, priority=1, rationale=""))
    assert not rejected
    assert q.empty()
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement ActionQueue**

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/action_queue.py tests/test_atl/test_action_queue.py
git commit -m "feat(atl): priority ActionQueue with blocked types"
```

---

### Task 4: ATL Journal

**Files:**
- Create: `src/jarvis/evolution/atl_journal.py`
- Test: `tests/test_atl/test_journal.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_atl/test_journal.py
import pytest
from pathlib import Path
from jarvis.evolution.atl_journal import ATLJournal

@pytest.fixture
def journal(tmp_path):
    return ATLJournal(journal_dir=tmp_path / "journal")

@pytest.mark.asyncio
async def test_log_cycle(journal):
    await journal.log_cycle(
        cycle=1, summary="Evaluated BU goals",
        goal_updates=[{"goal_id": "g_001", "delta": 0.05}],
        actions=["memory_update: saved BU tariff"],
    )
    content = journal.today()
    assert content is not None
    assert "Zyklus #1" in content
    assert "BU goals" in content

@pytest.mark.asyncio
async def test_multiple_cycles(journal):
    await journal.log_cycle(cycle=1, summary="First", goal_updates=[], actions=[])
    await journal.log_cycle(cycle=2, summary="Second", goal_updates=[], actions=[])
    content = journal.today()
    assert "Zyklus #1" in content
    assert "Zyklus #2" in content

def test_recent(journal, tmp_path):
    # Write a fake journal file for yesterday
    import datetime
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    jdir = tmp_path / "journal"
    jdir.mkdir(parents=True, exist_ok=True)
    (jdir / f"{yesterday}.md").write_text("# Yesterday\nSome thoughts")
    entries = journal.recent(days=3)
    assert len(entries) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement ATLJournal**

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/atl_journal.py tests/test_atl/test_journal.py
git commit -m "feat(atl): daily Markdown journal with append and search"
```

---

### Task 5: ATL System Prompt + Response Parser

**Files:**
- Create: `src/jarvis/evolution/atl_prompt.py`
- Test: `tests/test_atl/test_prompt.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_atl/test_prompt.py
from jarvis.evolution.atl_prompt import build_atl_prompt, parse_atl_response, AutonomousThought

def test_build_prompt():
    prompt = build_atl_prompt(
        identity="I am Jarvis",
        goals_formatted="- g_001: Learn BU (35%)",
        recent_events="User asked about WWK",
        goal_knowledge="BU Protect: ...",
        now="2026-03-30 08:15",
        max_actions=3,
    )
    assert "autonomen Denkmodus" in prompt
    assert "Learn BU" in prompt
    assert "max. 3 Aktionen" in prompt or "3" in prompt

def test_parse_valid_response():
    raw = '''{"summary": "All good", "goal_evaluations": [{"goal_id": "g_001", "progress_delta": 0.05, "note": "ok"}], "proposed_actions": [], "wants_to_notify": false, "notification": null, "priority": "low"}'''
    thought = parse_atl_response(raw)
    assert isinstance(thought, AutonomousThought)
    assert thought.summary == "All good"
    assert len(thought.goal_evaluations) == 1
    assert thought.priority == "low"

def test_parse_with_think_tags():
    raw = '<think>reasoning</think>{"summary": "test", "goal_evaluations": [], "proposed_actions": [], "wants_to_notify": false, "notification": null, "priority": "low"}'
    thought = parse_atl_response(raw)
    assert thought.summary == "test"

def test_parse_invalid_returns_empty():
    thought = parse_atl_response("not json at all")
    assert thought.summary == ""
    assert thought.proposed_actions == []
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement atl_prompt.py**

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/atl_prompt.py tests/test_atl/test_prompt.py
git commit -m "feat(atl): system prompt builder and JSON response parser"
```

---

### Task 6: Thinking Cycle in EvolutionLoop

**Files:**
- Modify: `src/jarvis/evolution/loop.py`
- Test: `tests/test_atl/test_thinking_cycle.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_atl/test_thinking_cycle.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from jarvis.evolution.atl_config import ATLConfig

@pytest.mark.asyncio
async def test_thinking_cycle_skips_when_not_idle():
    from jarvis.evolution.loop import EvolutionLoop
    idle = MagicMock()
    idle.is_idle = False
    loop = EvolutionLoop(idle_detector=idle)
    loop._atl_config = ATLConfig(enabled=True)
    loop._goal_manager = MagicMock()
    result = await loop._thinking_cycle()
    assert result.skipped
    assert result.reason == "not_idle"

@pytest.mark.asyncio
async def test_thinking_cycle_quiet_hours():
    from jarvis.evolution.loop import EvolutionLoop
    idle = MagicMock()
    idle.is_idle = True
    loop = EvolutionLoop(idle_detector=idle)
    loop._atl_config = ATLConfig(enabled=True, quiet_hours_start="00:00", quiet_hours_end="23:59")
    loop._goal_manager = MagicMock()
    result = await loop._thinking_cycle()
    assert result.skipped
    assert "quiet" in result.reason
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement `_thinking_cycle()` in EvolutionLoop**

Add to `loop.py`:
- `_atl_config: ATLConfig | None` attribute
- `_goal_manager: GoalManager | None` attribute
- `_atl_journal: ATLJournal | None` attribute
- `_thinking_cycle()` method: build context, call LLM with ATL prompt, parse response, execute actions through Gatekeeper (with risk_ceiling), write journal, optionally notify user
- `_should_think()` method: checks ATL interval timer
- `_in_quiet_hours()` method: checks time against config

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/loop.py tests/test_atl/test_thinking_cycle.py
git commit -m "feat(atl): thinking cycle in EvolutionLoop with quiet hours"
```

---

### Task 7: Gatekeeper Risk Ceiling

**Files:**
- Modify: `src/jarvis/core/gatekeeper.py`
- Test: `tests/test_atl/test_risk_ceiling.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_atl/test_risk_ceiling.py
import pytest
from jarvis.core.gatekeeper import Gatekeeper
from jarvis.models import RiskLevel

@pytest.fixture
def gk():
    from jarvis.config import JarvisConfig
    return Gatekeeper(JarvisConfig())

def test_risk_ceiling_blocks_orange(gk):
    # exec_command is normally ORANGE
    level = gk.classify_risk("exec_command", {"command": "ls"}, risk_ceiling="YELLOW")
    assert level == RiskLevel.RED  # blocked by ceiling

def test_risk_ceiling_allows_green(gk):
    level = gk.classify_risk("search_memory", {"query": "test"}, risk_ceiling="YELLOW")
    assert level == RiskLevel.GREEN  # within ceiling

def test_no_ceiling_unchanged(gk):
    level = gk.classify_risk("exec_command", {"command": "ls"})
    assert level == RiskLevel.ORANGE  # normal behavior
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Add risk_ceiling parameter to Gatekeeper**

In `_classify_risk()`, add optional `risk_ceiling: str | None = None` parameter.
If the classified level exceeds the ceiling, return `RiskLevel.RED` (blocked).

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/core/gatekeeper.py tests/test_atl/test_risk_ceiling.py
git commit -m "feat(atl): risk ceiling parameter in Gatekeeper"
```

---

### Task 8: Gateway Wiring + MCP Tools

**Files:**
- Modify: `src/jarvis/gateway/gateway.py`
- Modify: `src/jarvis/mcp/skill_tools.py` (or new `mcp/atl_tools.py`)
- Modify: `src/jarvis/core/gatekeeper.py` (add new tools to GREEN/YELLOW)
- Test: `tests/test_atl/test_integration.py`

- [ ] **Step 1: Wire ATL into gateway init**

In `gateway.py` Phase 6 init block:
- Create `GoalManager` with `config.jarvis_home / "evolution" / "goals.yaml"`
- Create `ATLJournal` with `config.jarvis_home / "evolution" / "journal"`
- Set `evolution_loop._atl_config = config.atl`
- Set `evolution_loop._goal_manager = goal_manager`
- Set `evolution_loop._atl_journal = atl_journal`
- Run `goal_manager.migrate_learning_goals()` on first start if goals.yaml doesn't exist

- [ ] **Step 2: Add 3 MCP tools**

```python
# atl_status: Returns ATL status, cycle count, active goals summary
# atl_goals: CRUD for goals (action: list|add|pause|complete|resume)
# atl_journal: Read journal (today or last N days)
```

- [ ] **Step 3: Add tools to Gatekeeper classifications**

- `atl_status` → GREEN
- `atl_journal` → GREEN
- `atl_goals` → YELLOW

- [ ] **Step 4: Write integration test**

```python
# tests/test_atl/test_integration.py
@pytest.mark.asyncio
async def test_full_thinking_cycle_mock():
    """End-to-end: context -> LLM -> parse -> actions -> journal"""
    # Mock LLM to return valid ATL JSON
    # Verify goal progress updated, journal written, no notification
```

- [ ] **Step 5: Run all ATL tests**

Run: `pytest tests/test_atl/ -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/jarvis/gateway/gateway.py src/jarvis/mcp/ src/jarvis/core/gatekeeper.py tests/test_atl/
git commit -m "feat(atl): gateway wiring, MCP tools, and integration test"
```

---

### Task 9: Version Bump + Documentation

**Files:**
- Modify: `src/jarvis/__init__.py` (version bump if needed)
- Modify: `src/jarvis/core/gatekeeper.py` (update tool count assertions if any)

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -x --timeout=30 -q`
Expected: ALL PASS, no regressions

- [ ] **Step 2: Run ruff lint**

Run: `ruff check src/jarvis/evolution/ tests/test_atl/`
Expected: 0 errors

- [ ] **Step 3: Commit final**

```bash
git add -A
git commit -m "feat(atl): Evolution Phase 6 — Autonomous Thinking Loop complete"
```

---

## Summary

| Task | Component | Est. Tests |
|------|-----------|-----------|
| 1 | ATLConfig | 3 |
| 2 | GoalManager | 7 |
| 3 | ActionQueue | 4 |
| 4 | ATLJournal | 3 |
| 5 | ATL Prompt + Parser | 4 |
| 6 | Thinking Cycle | 2+ |
| 7 | Risk Ceiling | 3 |
| 8 | Gateway + MCP + Integration | 1+ |
| 9 | Lint + Full Suite | 0 |
| **Total** | | **~27+ tests** |
