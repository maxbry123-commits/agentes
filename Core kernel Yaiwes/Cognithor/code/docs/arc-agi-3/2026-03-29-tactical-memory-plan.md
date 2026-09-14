# Tactical Memory (Tier 6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 6th memory tier that tracks tool outcome causality, learns effectiveness per context, and auto-creates avoidance rules after repeated failures.

**Architecture:** Hybrid RAM+SQLite `TacticalMemory` class. Context Pipeline injects insights for the Planner (Wave 3). Executor records outcomes post-execution. Avoidance rules decay after 24h TTL. Integrates into existing MemoryManager lifecycle.

**Tech Stack:** Python 3.12, Pydantic, SQLite (via encrypted_connect), structlog, pytest

---

## File Structure

**Create:**
- `src/jarvis/memory/tactical.py` — TacticalMemory class, data models, SQLite schema
- `tests/test_memory/test_tactical.py` — Full test suite

**Modify:**
- `src/jarvis/models.py:87-94` — Add TACTICAL to MemoryTier enum
- `src/jarvis/config.py:518-548` — Add TacticalMemoryConfig
- `src/jarvis/memory/working.py:25-50` — Add tactical budget + injected_tactical field
- `src/jarvis/memory/manager.py:148-152,707-723` — Init + close tactical tier
- `src/jarvis/core/context_pipeline.py:165-192` — Wave 3 tactical injection
- `src/jarvis/core/executor.py:309-318` — Post-execution outcome recording

---

### Task 1: TacticalMemoryConfig + MemoryTier Enum

**Files:**
- Modify: `src/jarvis/models.py:87-94`
- Modify: `src/jarvis/config.py`

- [ ] **Step 1.1: Add TACTICAL to MemoryTier enum**

In `src/jarvis/models.py`, find the `MemoryTier` StrEnum (around line 87-94). Add after `WORKING = "working"`:

```python
class MemoryTier(StrEnum):
    """The 6 memory tiers. [B§4.1]"""

    CORE = "core"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"
    TACTICAL = "tactical"
```

- [ ] **Step 1.2: Add TacticalMemoryConfig to config.py**

In `src/jarvis/config.py`, find `MemoryConfig` (around line 518). Add `TacticalMemoryConfig` BEFORE it:

```python
class TacticalMemoryConfig(BaseModel):
    """Tactical Memory (Tier 6) — tool outcome tracking and avoidance rules."""

    enabled: bool = Field(default=True, description="Enable tactical memory tier")
    db_name: str = Field(default="tactical_memory.db", description="SQLite DB filename")
    ttl_hours: float = Field(default=24.0, ge=1.0, le=168.0, description="Avoidance rule TTL")
    flush_threshold: float = Field(
        default=0.7, ge=0.1, le=1.0, description="Min confidence to persist to DB"
    )
    max_outcomes: int = Field(default=50_000, ge=1000, description="Max in-memory outcomes")
    avoidance_consecutive_failures: int = Field(
        default=3, ge=2, le=10, description="Failures before avoidance rule"
    )
    budget_tokens: int = Field(
        default=400, ge=100, le=2000, description="Token budget for tactical insights"
    )
```

Then in `JarvisConfig`, add after the existing `memory` field:

```python
    tactical_memory: TacticalMemoryConfig = Field(default_factory=TacticalMemoryConfig)
```

- [ ] **Step 1.3: Run existing tests**

```bash
pytest tests/test_core/test_config.py -v --tb=short
```

Expected: ALL PASS (new field has defaults, no regressions)

- [ ] **Step 1.4: Commit**

```bash
git add src/jarvis/models.py src/jarvis/config.py
git commit -m "feat(memory): add TACTICAL tier enum + TacticalMemoryConfig"
```

---

### Task 2: TacticalMemory Core + Tests

**Files:**
- Create: `src/jarvis/memory/tactical.py`
- Create: `tests/test_memory/test_tactical.py`

- [ ] **Step 2.1: Write the failing tests**

Create `tests/test_memory/test_tactical.py`:

```python
"""Tests for Tactical Memory (Tier 6)."""

from __future__ import annotations

import time

import pytest

from jarvis.memory.tactical import (
    AvoidanceRule,
    TacticalMemory,
    ToolEffectiveness,
    ToolOutcome,
)


# ---------------------------------------------------------------------------
# ToolOutcome dataclass
# ---------------------------------------------------------------------------


class TestToolOutcome:
    def test_create_outcome(self):
        o = ToolOutcome(
            tool_name="web_search",
            params_hash="abc123",
            success=True,
            duration_ms=150,
            context_hash="ctx001",
            timestamp=time.time(),
        )
        assert o.tool_name == "web_search"
        assert o.success is True
        assert o.error_snippet is None
        assert o.caused_replan is False

    def test_outcome_with_error(self):
        o = ToolOutcome(
            tool_name="exec_command",
            params_hash="def456",
            success=False,
            duration_ms=5000,
            context_hash="ctx002",
            timestamp=time.time(),
            error_snippet="TimeoutError: command exceeded 30s",
        )
        assert o.success is False
        assert "TimeoutError" in o.error_snippet


# ---------------------------------------------------------------------------
# ToolEffectiveness
# ---------------------------------------------------------------------------


class TestToolEffectiveness:
    def test_default_values(self):
        e = ToolEffectiveness()
        assert e.total == 0
        assert e.successes == 0
        assert e.consecutive_failures == 0

    def test_effectiveness_score(self):
        e = ToolEffectiveness(total=10, successes=8, failures=2)
        assert e.effectiveness == pytest.approx(0.8)

    def test_effectiveness_zero_total(self):
        e = ToolEffectiveness()
        assert e.effectiveness == 0.5  # neutral prior


# ---------------------------------------------------------------------------
# TacticalMemory — Recording
# ---------------------------------------------------------------------------


class TestRecordOutcome:
    def setup_method(self):
        self.tm = TacticalMemory()

    def test_record_success(self):
        self.tm.record_outcome("web_search", {"query": "test"}, True, 200, "hello")
        eff = self.tm.get_tool_effectiveness("web_search")
        assert eff == 1.0

    def test_record_failure(self):
        self.tm.record_outcome("exec_command", {"cmd": "ls"}, False, 5000, "run ls")
        eff = self.tm.get_tool_effectiveness("exec_command")
        assert eff == 0.0

    def test_mixed_outcomes(self):
        for _ in range(7):
            self.tm.record_outcome("web_search", {}, True, 100, "ctx")
        for _ in range(3):
            self.tm.record_outcome("web_search", {}, False, 100, "ctx")
        eff = self.tm.get_tool_effectiveness("web_search")
        assert eff == pytest.approx(0.7)

    def test_unknown_tool_returns_neutral(self):
        assert self.tm.get_tool_effectiveness("never_used") == 0.5

    def test_max_outcomes_respected(self):
        tm = TacticalMemory(max_outcomes=10)
        for i in range(20):
            tm.record_outcome("tool", {}, True, 100, f"ctx{i}")
        assert len(tm._outcomes) <= 10

    def test_outcome_stored(self):
        self.tm.record_outcome("read_file", {"path": "/tmp/x"}, True, 50, "read x")
        assert len(self.tm._outcomes) == 1
        assert self.tm._outcomes[0].tool_name == "read_file"


# ---------------------------------------------------------------------------
# TacticalMemory — Avoidance Rules
# ---------------------------------------------------------------------------


class TestAvoidanceRules:
    def setup_method(self):
        self.tm = TacticalMemory(avoidance_consecutive_failures=3)

    def test_no_avoidance_on_first_failure(self):
        self.tm.record_outcome("bad_tool", {}, False, 100, "ctx")
        assert self.tm.check_avoidance("bad_tool", {}) is None

    def test_avoidance_after_n_failures(self):
        for _ in range(3):
            self.tm.record_outcome("bad_tool", {}, False, 100, "ctx")
        rule = self.tm.check_avoidance("bad_tool", {})
        assert rule is not None
        assert rule.tool_name == "bad_tool"
        assert rule.trigger_count == 3

    def test_success_resets_consecutive(self):
        self.tm.record_outcome("flaky", {}, False, 100, "ctx")
        self.tm.record_outcome("flaky", {}, False, 100, "ctx")
        self.tm.record_outcome("flaky", {}, True, 100, "ctx")  # resets
        self.tm.record_outcome("flaky", {}, False, 100, "ctx")
        assert self.tm.check_avoidance("flaky", {}) is None

    def test_avoidance_rule_expires(self):
        self.tm = TacticalMemory(avoidance_consecutive_failures=3, ttl_hours=0.0001)
        for _ in range(3):
            self.tm.record_outcome("bad_tool", {}, False, 100, "ctx")
        assert self.tm.check_avoidance("bad_tool", {}) is not None
        time.sleep(0.5)
        removed = self.tm.decay_rules()
        assert removed >= 1
        assert self.tm.check_avoidance("bad_tool", {}) is None

    def test_success_removes_active_rule(self):
        for _ in range(3):
            self.tm.record_outcome("bad_tool", {}, False, 100, "ctx")
        assert self.tm.check_avoidance("bad_tool", {}) is not None
        self.tm.record_outcome("bad_tool", {}, True, 100, "ctx")
        assert self.tm.check_avoidance("bad_tool", {}) is None


# ---------------------------------------------------------------------------
# TacticalMemory — LLM Insights
# ---------------------------------------------------------------------------


class TestInsights:
    def test_empty_returns_empty(self):
        tm = TacticalMemory()
        assert tm.get_insights_for_llm("ctx") == ""

    def test_includes_tool_data(self):
        tm = TacticalMemory()
        for _ in range(5):
            tm.record_outcome("search_and_read", {}, True, 200, "ctx")
        text = tm.get_insights_for_llm("ctx")
        assert "search_and_read" in text

    def test_includes_avoidance_warning(self):
        tm = TacticalMemory(avoidance_consecutive_failures=3)
        for _ in range(3):
            tm.record_outcome("bad_tool", {}, False, 100, "ctx")
        text = tm.get_insights_for_llm("ctx")
        assert "bad_tool" in text
        assert "WARNUNG" in text or "warnung" in text.lower() or "Warning" in text

    def test_respects_max_chars(self):
        tm = TacticalMemory()
        for i in range(50):
            tm.record_outcome(f"tool_{i}", {}, True, 100, "ctx")
        text = tm.get_insights_for_llm("ctx", max_chars=200)
        assert len(text) <= 250  # small buffer tolerance


# ---------------------------------------------------------------------------
# TacticalMemory — SQLite Persistence
# ---------------------------------------------------------------------------


class TestPersistence:
    def test_flush_and_load(self, tmp_path):
        db = tmp_path / "tactical.db"
        tm1 = TacticalMemory(db_path=db)
        for _ in range(5):
            tm1.record_outcome("web_search", {}, True, 100, "ctx")
        flushed = tm1.flush_to_db()
        assert flushed > 0
        tm1.close()

        tm2 = TacticalMemory(db_path=db)
        loaded = tm2.load_from_db()
        assert loaded > 0
        assert tm2.get_tool_effectiveness("web_search") > 0.5
        tm2.close()

    def test_avoidance_rules_persisted(self, tmp_path):
        db = tmp_path / "tactical.db"
        tm1 = TacticalMemory(db_path=db, avoidance_consecutive_failures=3)
        for _ in range(3):
            tm1.record_outcome("bad_tool", {}, False, 100, "ctx")
        tm1.flush_to_db()
        tm1.close()

        tm2 = TacticalMemory(db_path=db)
        tm2.load_from_db()
        rule = tm2.check_avoidance("bad_tool", {})
        assert rule is not None
        tm2.close()

    def test_flush_only_high_confidence(self, tmp_path):
        db = tmp_path / "tactical.db"
        tm = TacticalMemory(db_path=db, flush_threshold=0.7)
        # 1 success out of 1 = 100% but only 1 data point — might flush
        tm.record_outcome("rare_tool", {}, True, 100, "ctx")
        # 10 successes out of 10 = high confidence
        for _ in range(10):
            tm.record_outcome("reliable_tool", {}, True, 100, "ctx")
        flushed = tm.flush_to_db()
        assert flushed >= 1  # at least reliable_tool
        tm.close()


# ---------------------------------------------------------------------------
# TacticalMemory — Stats
# ---------------------------------------------------------------------------


class TestStats:
    def test_stats_structure(self):
        tm = TacticalMemory()
        stats = tm.get_stats()
        assert "outcomes_count" in stats
        assert "tools_tracked" in stats
        assert "avoidance_rules_active" in stats

    def test_stats_after_recording(self):
        tm = TacticalMemory()
        tm.record_outcome("web_search", {}, True, 100, "ctx")
        tm.record_outcome("read_file", {}, True, 50, "ctx")
        stats = tm.get_stats()
        assert stats["outcomes_count"] == 2
        assert stats["tools_tracked"] == 2
```

- [ ] **Step 2.2: Run tests to verify they fail**

```bash
pytest tests/test_memory/test_tactical.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 2.3: Implement tactical.py**

Create `src/jarvis/memory/tactical.py` implementing:

- `ToolOutcome` dataclass (tool_name, params_hash, success, duration_ms, context_hash, timestamp, error_snippet, caused_replan)
- `ToolEffectiveness` dataclass with computed `effectiveness` property (successes/total, 0.5 if total==0)
- `AvoidanceRule` dataclass (tool_name, params_pattern, context_pattern, reason, created_at, expires_at, trigger_count)
- `TacticalMemory` class with:
  - `__init__(db_path=None, ttl_hours=24.0, flush_threshold=0.7, max_outcomes=50000, avoidance_consecutive_failures=3)`
  - `_outcomes: list[ToolOutcome]` (bounded by max_outcomes, FIFO eviction)
  - `_effectiveness: dict[str, ToolEffectiveness]` (per tool)
  - `_avoidance_rules: list[AvoidanceRule]`
  - `_consecutive_failures: dict[str, int]` (per tool, resets on success)
  - `record_outcome()` — updates effectiveness, checks consecutive failures, creates avoidance rules
  - On success: reset consecutive_failures, remove active avoidance rule for that tool
  - On failure: increment consecutive_failures, create AvoidanceRule if threshold reached
  - `get_tool_effectiveness()` — returns 0.5 for unknown
  - `get_insights_for_llm()` — formatted string with top tools + avoidance warnings
  - `check_avoidance()` — returns matching AvoidanceRule or None
  - `decay_rules()` — removes rules where time.time() > expires_at
  - `flush_to_db()` — writes effectiveness + avoidance rules to SQLite
  - `load_from_db()` — loads effectiveness + avoidance rules from SQLite
  - `close()` — flushes then closes DB connection
  - `get_stats()` — dict with counts
  - `_hash_params()` — static, MD5 of sorted JSON params, first 12 chars
  - `_hash_context()` — static, MD5 of context string, first 12 chars

Use `from jarvis.utils.logging import get_logger` for logging.
Use `from jarvis.security.encrypted_db import encrypted_connect, compatible_row_factory` for DB.
Use `from __future__ import annotations` and add `__all__`.

- [ ] **Step 2.4: Run tests to verify they pass**

```bash
pytest tests/test_memory/test_tactical.py -v
```

Expected: ALL PASS

- [ ] **Step 2.5: Ruff format + lint**

```bash
ruff format src/jarvis/memory/tactical.py tests/test_memory/test_tactical.py
ruff check src/jarvis/memory/tactical.py --select=F,UP --no-fix
```

- [ ] **Step 2.6: Commit**

```bash
git add src/jarvis/memory/tactical.py tests/test_memory/test_tactical.py
git commit -m "feat(memory): tactical memory tier 6 — core + tests"
```

---

### Task 3: Working Memory Budget + Injection Field

**Files:**
- Modify: `src/jarvis/memory/working.py:25-50`

- [ ] **Step 3.1: Add tactical budget constant**

In `src/jarvis/memory/working.py`, find the budget constants section (around line 25-50). Add:

```python
_DEFAULT_BUDGET_TACTICAL = 400  # Tactical Memory insights
```

- [ ] **Step 3.2: Add injected_tactical field to WorkingMemory**

Find the WorkingMemory dataclass/class. Add a new field:

```python
injected_tactical: str = ""
```

- [ ] **Step 3.3: Include tactical budget in static budget calculation**

Find where `_static_budget` is calculated (sum of all budget categories). Add `_DEFAULT_BUDGET_TACTICAL` to the sum. Also add config key `budget_tactical_insights` with fallback to `_DEFAULT_BUDGET_TACTICAL`.

- [ ] **Step 3.4: Include injected_tactical in build_context_parts()**

Find the `build_context_parts()` method. Add a section that includes `self.injected_tactical` if non-empty, under a header like `"[Tactical Insights]"`.

- [ ] **Step 3.5: Run existing working memory tests**

```bash
pytest tests/test_memory/ -v --tb=short -k "working"
```

Expected: ALL PASS

- [ ] **Step 3.6: Commit**

```bash
git add src/jarvis/memory/working.py
git commit -m "feat(memory): add tactical budget + injected_tactical to working memory"
```

---

### Task 4: MemoryManager Integration

**Files:**
- Modify: `src/jarvis/memory/manager.py:148-152,707-723`

- [ ] **Step 4.1: Initialize TacticalMemory in MemoryManager**

In `memory/manager.py`, after `WorkingMemoryManager` initialization (around line 148-152), add:

```python
# Tier 6: Tactical Memory
self._tactical: TacticalMemory | None = None
try:
    from jarvis.memory.tactical import TacticalMemory
    tactical_cfg = getattr(config, "tactical_memory", None)
    if tactical_cfg is None or tactical_cfg.enabled:
        db_path = self._jarvis_home / "db" / "tactical_memory.db"
        self._tactical = TacticalMemory(
            db_path=db_path,
            ttl_hours=getattr(tactical_cfg, "ttl_hours", 24.0) if tactical_cfg else 24.0,
            flush_threshold=getattr(tactical_cfg, "flush_threshold", 0.7) if tactical_cfg else 0.7,
            max_outcomes=getattr(tactical_cfg, "max_outcomes", 50_000) if tactical_cfg else 50_000,
            avoidance_consecutive_failures=(
                getattr(tactical_cfg, "avoidance_consecutive_failures", 3) if tactical_cfg else 3
            ),
        )
        self._tactical.load_from_db()
        log.info("tactical_memory_initialized", db=str(db_path)[-40:])
except Exception:
    log.debug("tactical_memory_init_failed", exc_info=True)
```

- [ ] **Step 4.2: Add tactical property**

Add a property for external access:

```python
@property
def tactical(self) -> TacticalMemory | None:
    return self._tactical
```

- [ ] **Step 4.3: Add tactical close to close() methods**

In both `close()` (async) and `close_sync()` methods, add before existing close calls:

```python
if self._tactical:
    try:
        self._tactical.close()
    except Exception:
        log.debug("tactical_memory_close_failed", exc_info=True)
```

- [ ] **Step 4.4: Run existing memory tests**

```bash
pytest tests/test_memory/ -v --tb=short
```

Expected: ALL PASS

- [ ] **Step 4.5: Commit**

```bash
git add src/jarvis/memory/manager.py
git commit -m "feat(memory): wire tactical memory into MemoryManager lifecycle"
```

---

### Task 5: Context Pipeline — Wave 3

**Files:**
- Modify: `src/jarvis/core/context_pipeline.py:165-192`

- [ ] **Step 5.1: Add tactical injection after Wave 2**

In `context_pipeline.py`, find where Wave 2 results are processed (after skills + preferences, around line 192-204). After the existing injection code, add:

```python
# Wave 3: Tactical Memory insights
tactical_memory = getattr(self._memory_manager, "tactical", None)
if tactical_memory is not None:
    try:
        tactical_text = tactical_memory.get_insights_for_llm(
            msg.text or "",
            max_chars=getattr(
                self._config, "tactical_memory", None
            )
            and self._config.tactical_memory.budget_tokens
            or 400,
        )
        if tactical_text:
            wm.injected_tactical = tactical_text
    except Exception:
        log.debug("context_pipeline_tactical_failed", exc_info=True)
```

- [ ] **Step 5.2: Run context pipeline tests**

```bash
pytest tests/ -v --tb=short -k "context_pipeline"
```

Expected: ALL PASS

- [ ] **Step 5.3: Commit**

```bash
git add src/jarvis/core/context_pipeline.py
git commit -m "feat(memory): inject tactical insights into context pipeline (Wave 3)"
```

---

### Task 6: Executor Post-Execution Recording

**Files:**
- Modify: `src/jarvis/core/executor.py:309-318`

- [ ] **Step 6.1: Add tactical outcome recording after tool execution**

In `executor.py`, find where `executor_tool_result` is logged (around line 309-318, after each tool result). Add after the existing log:

```python
# Record outcome in Tactical Memory
tactical_memory = getattr(self, "_tactical_memory", None)
if tactical_memory is not None:
    try:
        tactical_memory.record_outcome(
            tool=action.tool,
            params=action.params or {},
            success=result.success,
            duration_ms=int(getattr(result, "duration_ms", 0)),
            context=getattr(self, "_last_user_message", "") or "",
            error=result.content[:100] if not result.success and result.content else None,
        )
    except Exception:
        pass  # Tactical recording must never break execution
```

- [ ] **Step 6.2: Add tactical_memory injection point in executor init or wiring**

Find where the Executor is created/wired (in `gateway/phases/pge.py` or `executor.__init__`). Add a way to inject the tactical memory reference. The cleanest approach: add `_tactical_memory` attribute, set it during gateway initialization:

In the executor's `__init__` or as a setter:
```python
self._tactical_memory = None  # Set by gateway after memory init
```

In gateway initialization (after both memory and executor are ready):
```python
if hasattr(self, "_executor") and self._executor and self._memory_manager:
    self._executor._tactical_memory = self._memory_manager.tactical
```

- [ ] **Step 6.3: Run executor tests**

```bash
pytest tests/test_core/test_executor.py -v --tb=short
```

Expected: ALL PASS

- [ ] **Step 6.4: Commit**

```bash
git add src/jarvis/core/executor.py
git commit -m "feat(memory): record tool outcomes in tactical memory post-execution"
```

---

### Task 7: Full Integration Test + Lint

- [ ] **Step 7.1: Run all tactical memory tests**

```bash
pytest tests/test_memory/test_tactical.py -v
```

Expected: ALL PASS

- [ ] **Step 7.2: Run full test suite for regressions**

```bash
pytest tests/test_memory/ tests/test_core/test_config.py tests/test_core/test_executor.py tests/test_arc/ -v --tb=short
```

Expected: ALL PASS

- [ ] **Step 7.3: Ruff format + lint all changed files**

```bash
ruff format src/jarvis/memory/tactical.py src/jarvis/memory/working.py src/jarvis/memory/manager.py src/jarvis/core/context_pipeline.py src/jarvis/core/executor.py src/jarvis/models.py src/jarvis/config.py tests/test_memory/test_tactical.py
ruff check src/jarvis/memory/tactical.py src/jarvis/models.py --no-fix
```

Expected: 0 errors

- [ ] **Step 7.4: Verify import chain**

```bash
python -c "from jarvis.memory.tactical import TacticalMemory; tm = TacticalMemory(); tm.record_outcome('test', {}, True, 100, 'ctx'); print(f'effectiveness={tm.get_tool_effectiveness(\"test\")}, stats={tm.get_stats()}'); tm.close(); print('OK')"
```

Expected: `effectiveness=1.0, stats={...}, OK`

- [ ] **Step 7.5: Final commit**

```bash
git add -A
git commit -m "feat(memory): tactical memory tier 6 — full integration

New 6th memory tier with hybrid RAM+SQLite persistence:
- ToolOutcome tracking with effectiveness scoring
- Avoidance rules after 3 consecutive failures (24h TTL decay)
- Context Pipeline Wave 3 injection for LLM planner
- Executor post-execution outcome recording
- TacticalMemoryConfig in JarvisConfig
- Full test suite"
```

---

## Timeline

| Task | Scope | Duration |
|------|-------|----------|
| Task 1 | Enum + Config | 5 min |
| Task 2 | Core TacticalMemory + Tests | 30 min |
| Task 3 | Working Memory budget | 10 min |
| Task 4 | MemoryManager wiring | 10 min |
| Task 5 | Context Pipeline Wave 3 | 10 min |
| Task 6 | Executor recording | 15 min |
| Task 7 | Integration + lint | 10 min |
