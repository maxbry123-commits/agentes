# Skill Lifecycle Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the broken skill lifecycle pipeline so skills are proactively suggested, and integrate lifecycle management into gateway background tasks.

**Architecture:** Four targeted fixes: (1) context pipeline method name, (2) registry injection into context pipeline, (3) tool-availability debug logging, (4) lifecycle cron in gateway background tasks.

**Tech Stack:** Python 3.13, pytest

**Spec:** `docs/superpowers/specs/2026-04-04-skill-lifecycle-fix-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/jarvis/core/context_pipeline.py` | Fix `_get_skill_context()` method |
| `src/jarvis/gateway/gateway.py` | Inject registry into context pipeline + lifecycle cron |
| `src/jarvis/gateway/phases/agents.py` | Create SkillLifecycleManager, store on gateway |
| `src/jarvis/skills/registry.py` | Debug log for skipped skills |
| `tests/test_skills/test_skill_lifecycle_fix.py` | All new tests |

---

### Task 1: Fix Context Pipeline `_get_skill_context`

**Files:**
- Modify: `src/jarvis/core/context_pipeline.py:359-378`
- Create: `tests/test_skills/test_skill_lifecycle_fix.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_skills/test_skill_lifecycle_fix.py`:

```python
"""Tests for Skill Lifecycle Fix — context pipeline, registry injection, lifecycle cron."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestContextPipelineSkillLookup:
    def test_get_skill_context_returns_matches(self):
        """_get_skill_context should call registry.match() and return formatted skills."""
        from jarvis.core.context_pipeline import ContextPipeline

        cp = ContextPipeline.__new__(ContextPipeline)
        cp._skill_registry = MagicMock()

        mock_skill = MagicMock()
        mock_skill.name = "ARC-AGI-3 Benchmark"
        mock_skill.description = "Spielt ARC-AGI-3 Games"
        mock_skill.trigger_keywords = ["arc", "benchmark", "puzzle"]

        mock_match = MagicMock()
        mock_match.skill = mock_skill

        cp._skill_registry.match.return_value = [mock_match]

        result = cp._get_skill_context("spiele arc benchmark")

        assert "ARC-AGI-3 Benchmark" in result
        assert "Spielt ARC-AGI-3" in result
        assert "arc" in result
        cp._skill_registry.match.assert_called_once()

    def test_get_skill_context_no_registry_returns_empty(self):
        from jarvis.core.context_pipeline import ContextPipeline

        cp = ContextPipeline.__new__(ContextPipeline)
        cp._skill_registry = None

        result = cp._get_skill_context("anything")
        assert result == ""

    def test_get_skill_context_no_matches_returns_empty(self):
        from jarvis.core.context_pipeline import ContextPipeline

        cp = ContextPipeline.__new__(ContextPipeline)
        cp._skill_registry = MagicMock()
        cp._skill_registry.match.return_value = []

        result = cp._get_skill_context("something unrelated")
        assert result == ""

    def test_get_skill_context_exception_returns_empty(self):
        from jarvis.core.context_pipeline import ContextPipeline

        cp = ContextPipeline.__new__(ContextPipeline)
        cp._skill_registry = MagicMock()
        cp._skill_registry.match.side_effect = RuntimeError("DB error")

        result = cp._get_skill_context("test")
        assert result == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_skills/test_skill_lifecycle_fix.py::TestContextPipelineSkillLookup -v`
Expected: FAIL — `find_matching_skills` is called instead of `match()`, so mock assertion fails

- [ ] **Step 3: Fix `_get_skill_context` in context_pipeline.py**

Replace lines 359-378 in `src/jarvis/core/context_pipeline.py`:

```python
    def _get_skill_context(self, query: str) -> str:
        """Look up relevant skill context from SkillRegistry."""
        if not self._skill_registry:
            return ""
        try:
            matches = self._skill_registry.match(query, top_k=3)
            if not matches:
                return ""
            lines = []
            for m in matches[:3]:
                s = m.skill
                kw = ", ".join(s.trigger_keywords[:5]) if s.trigger_keywords else ""
                lines.append(f"- {s.name}: {s.description} (Keywords: {kw})")
            return "Verfuegbare Skills:\n" + "\n".join(lines)
        except Exception:
            log.debug("context_skill_lookup_failed", exc_info=True)
            return ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_skills/test_skill_lifecycle_fix.py::TestContextPipelineSkillLookup -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/core/context_pipeline.py tests/test_skills/test_skill_lifecycle_fix.py
git commit -m "fix(skills): context pipeline calls registry.match() with rich skill context"
```

---

### Task 2: Inject SkillRegistry into Context Pipeline

**Files:**
- Modify: `src/jarvis/gateway/gateway.py`
- Test: `tests/test_skills/test_skill_lifecycle_fix.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_skills/test_skill_lifecycle_fix.py`:

```python
class TestRegistryInjection:
    def test_set_skill_registry_stores_reference(self):
        from jarvis.core.context_pipeline import ContextPipeline

        cp = ContextPipeline.__new__(ContextPipeline)
        cp._skill_registry = None

        mock_registry = MagicMock()
        cp.set_skill_registry(mock_registry)

        assert cp._skill_registry is mock_registry
```

- [ ] **Step 2: Run test (should pass — method already exists)**

Run: `pytest tests/test_skills/test_skill_lifecycle_fix.py::TestRegistryInjection -v`
Expected: PASS (the `set_skill_registry` method exists at line 75 of context_pipeline.py)

- [ ] **Step 3: Add registry injection to gateway.py**

In `src/jarvis/gateway/gateway.py`, find where `_context_pipeline` is created (around line 236 in `initialize()`). After the `init_agents` phase is applied (which creates `_skill_registry`), add the wiring. Find the line after `apply_phase(self, agents_result)` (around line 284) and add:

```python
        # Wire skill registry into context pipeline for proactive skill suggestions
        if self._context_pipeline and self._skill_registry:
            self._context_pipeline.set_skill_registry(self._skill_registry)
            log.info("skill_registry_wired_to_context_pipeline")
```

- [ ] **Step 4: Run all skill tests**

Run: `pytest tests/test_skills/test_skill_lifecycle_fix.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/gateway/gateway.py tests/test_skills/test_skill_lifecycle_fix.py
git commit -m "fix(skills): inject SkillRegistry into ContextPipeline during gateway init"
```

---

### Task 3: Tool-Availability Debug Logging

**Files:**
- Modify: `src/jarvis/skills/registry.py:446-452`
- Test: `tests/test_skills/test_skill_lifecycle_fix.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_skills/test_skill_lifecycle_fix.py`:

```python
class TestToolAvailabilityLogging:
    def test_skill_skipped_when_tools_missing(self):
        """Skills with unavailable required tools should be skipped."""
        from jarvis.skills.registry import SkillRegistry

        registry = SkillRegistry()

        # Create a mock skill that requires arc_play tool
        from jarvis.skills.registry import Skill

        skill = Skill(
            name="ARC Test",
            slug="arc_test",
            file_path=None,
            trigger_keywords=["arc", "test"],
            tools_required=["arc_play", "arc_status"],
            description="Test skill needing ARC tools",
            category="test",
            body="# Test\nDo ARC stuff.",
        )
        registry._register(skill)

        # Match with available_tools that don't include arc_play
        matches = registry.match(
            "play arc game",
            available_tools=["read_file", "write_file"],
        )

        # Skill should be skipped (not in matches)
        assert len(matches) == 0

    def test_skill_matches_when_tools_available(self):
        """Skills should match when all required tools are available."""
        from jarvis.skills.registry import SkillRegistry, Skill

        registry = SkillRegistry()

        skill = Skill(
            name="ARC Test",
            slug="arc_test",
            file_path=None,
            trigger_keywords=["arc", "test"],
            tools_required=["arc_play"],
            description="Test skill needing ARC tools",
            category="test",
            body="# Test\nDo ARC stuff.",
        )
        registry._register(skill)

        matches = registry.match(
            "play arc game",
            available_tools=["arc_play", "read_file"],
        )

        assert len(matches) >= 1
        assert matches[0].skill.slug == "arc_test"
```

- [ ] **Step 2: Run test (should already pass — logic exists)**

Run: `pytest tests/test_skills/test_skill_lifecycle_fix.py::TestToolAvailabilityLogging -v`
Expected: PASS (the filtering logic already works)

- [ ] **Step 3: Add debug log for skipped skills**

In `src/jarvis/skills/registry.py`, find the tool availability check (around lines 446-452). Replace:

```python
            # Tool-Verfuegbarkeit pruefen
            if (
                available_tools is not None
                and skill.tools_required
                and not all(t in available_tools for t in skill.tools_required)
            ):
                continue
```

With:

```python
            # Tool-Verfuegbarkeit pruefen
            if (
                available_tools is not None
                and skill.tools_required
                and not all(t in available_tools for t in skill.tools_required)
            ):
                missing = [t for t in skill.tools_required if t not in available_tools]
                log.debug(
                    "skill_skipped_missing_tools", skill=skill.slug, missing=missing
                )
                continue
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_skills/test_skill_lifecycle_fix.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/skills/registry.py tests/test_skills/test_skill_lifecycle_fix.py
git commit -m "fix(skills): log debug when skills skipped due to missing tools"
```

---

### Task 4: Lifecycle Cron in Gateway Background Tasks

**Files:**
- Modify: `src/jarvis/gateway/phases/agents.py`
- Modify: `src/jarvis/gateway/gateway.py`
- Test: `tests/test_skills/test_skill_lifecycle_fix.py`

- [ ] **Step 1: Write test for lifecycle manager creation**

Add to `tests/test_skills/test_skill_lifecycle_fix.py`:

```python
class TestLifecycleCronIntegration:
    def test_lifecycle_manager_can_be_created(self):
        """SkillLifecycleManager can be instantiated with registry and dir."""
        from jarvis.skills.lifecycle import SkillLifecycleManager
        from jarvis.skills.registry import SkillRegistry
        from pathlib import Path

        registry = SkillRegistry()
        lifecycle = SkillLifecycleManager(
            registry=registry,
            generated_dir=Path("/tmp/test_skills"),
        )
        assert lifecycle is not None

    def test_audit_all_returns_list(self):
        """audit_all() should return a list of SkillHealthStatus objects."""
        from jarvis.skills.lifecycle import SkillLifecycleManager
        from jarvis.skills.registry import SkillRegistry
        from pathlib import Path
        import tempfile

        registry = SkillRegistry()
        with tempfile.TemporaryDirectory() as tmp:
            lifecycle = SkillLifecycleManager(
                registry=registry,
                generated_dir=Path(tmp),
            )
            result = lifecycle.audit_all()
            assert isinstance(result, list)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_skills/test_skill_lifecycle_fix.py::TestLifecycleCronIntegration -v`
Expected: PASS (SkillLifecycleManager already exists and works)

- [ ] **Step 3: Create lifecycle manager in agents.py**

In `src/jarvis/gateway/phases/agents.py`, after the skill registry is created and loaded (around line 120), add:

```python
    # Create SkillLifecycleManager for periodic auditing
    skill_lifecycle = None
    try:
        from jarvis.skills.lifecycle import SkillLifecycleManager

        generated_dir = jarvis_home / "skills" / "generated"
        skill_lifecycle = SkillLifecycleManager(
            registry=skill_registry,
            generated_dir=generated_dir,
        )
        log.info("skill_lifecycle_manager_created")
    except Exception:
        log.debug("skill_lifecycle_manager_creation_failed", exc_info=True)
```

And add to the result dict (near line 129):

```python
    result["skill_lifecycle"] = skill_lifecycle
```

- [ ] **Step 4: Add lifecycle cron to gateway.py**

In `src/jarvis/gateway/gateway.py`, find the background task creation area (around line 1176 where `_daily_retention_cleanup` is defined). After the existing retention cleanup task, add a new skill lifecycle task following the exact same pattern:

```python
        # Skill lifecycle: daily audit and prune
        async def _daily_skill_lifecycle():
            while True:
                await asyncio.sleep(86400)  # 24 hours
                try:
                    if hasattr(self, "_skill_lifecycle") and self._skill_lifecycle:
                        audit_results = self._skill_lifecycle.audit_all()
                        healthy = sum(1 for r in audit_results if r.healthy)
                        unhealthy = len(audit_results) - healthy
                        if unhealthy > 0:
                            log.info(
                                "skill_lifecycle_audit",
                                total=len(audit_results),
                                healthy=healthy,
                                unhealthy=unhealthy,
                            )
                except Exception:
                    log.debug("skill_lifecycle_cron_failed", exc_info=True)

        _skill_lifecycle_task = asyncio.create_task(
            _daily_skill_lifecycle(), name="daily-skill-lifecycle"
        )
        self._background_tasks.add(_skill_lifecycle_task)
        _skill_lifecycle_task.add_done_callback(self._background_tasks.discard)
```

- [ ] **Step 5: Run all tests**

Run: `pytest tests/test_skills/test_skill_lifecycle_fix.py -v`
Expected: All PASS

Run: `pytest tests/test_skills/ -v -x`
Expected: All PASS (no regressions in existing skill tests)

- [ ] **Step 6: Commit**

```bash
git add src/jarvis/gateway/phases/agents.py src/jarvis/gateway/gateway.py tests/test_skills/test_skill_lifecycle_fix.py
git commit -m "feat(skills): lifecycle cron in gateway background tasks (daily audit)"
```

---

### Task 5: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run all skill tests**

Run: `pytest tests/test_skills/ -v`
Expected: All PASS

- [ ] **Step 2: Run context pipeline tests**

Run: `pytest tests/test_core/test_context_pipeline.py -v` (if it exists)
Expected: PASS

- [ ] **Step 3: Run gateway tests**

Run: `pytest tests/test_integration/test_phase10_13_wiring.py -v`
Expected: PASS

- [ ] **Step 4: Run broad sweep**

Run: `pytest tests/ -x -q --ignore=tests/test_skills/test_marketplace_persistence.py --ignore=tests/test_mcp/test_tool_registry_db.py`
Expected: No new failures

- [ ] **Step 5: Ruff lint**

Run: `ruff format --check src/ tests/ && ruff check src/jarvis/core/context_pipeline.py src/jarvis/skills/registry.py src/jarvis/gateway/phases/agents.py`
Expected: Clean

- [ ] **Step 6: Commit and push**

```bash
git push origin main
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Fix 1 (Context Pipeline method name): Task 1
- [x] Fix 2 (Registry injection): Task 2
- [x] Fix 3 (Tool-availability logging): Task 3
- [x] Fix 4 (Lifecycle cron): Task 4
- [x] Degradation guarantees: All exception handlers return safe defaults

**Placeholder scan:** No TBD, TODO, or vague instructions.

**Type consistency:**
- `match(query, top_k=3)` matches SkillRegistry signature ✓
- `SkillLifecycleManager(registry=, generated_dir=)` matches constructor ✓
- `audit_all()` returns `list[SkillHealthStatus]` — used correctly ✓
- `set_skill_registry()` exists at line 75 of context_pipeline.py ✓
- Background task follows exact pattern of `_daily_retention_cleanup` ✓
