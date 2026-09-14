# Skill Lifecycle Fix — Design Spec

**Date:** 2026-04-04
**Status:** Approved

## Goal

Fix the broken skill lifecycle pipeline so generated skills are proactively suggested to the planner, and integrate lifecycle management (audit, prune) into the gateway's background tasks.

## Problem Diagnosis

Skills ARE loaded into the registry at startup. The pipeline breaks at two points:

1. **Context Pipeline calls `find_matching_skills()`** — method doesn't exist on SkillRegistry. Should be `match()`. File: `context_pipeline.py:365`. Result: Context enrichment silently fails, planner never sees skill suggestions.

2. **Context Pipeline never receives SkillRegistry** — `set_skill_registry()` is never called during gateway initialization. File: `gateway.py`. Result: Even if the method name were correct, `_skill_registry` is always `None`.

Additionally:
3. Skills silently skipped when `tools_required` not available — no logging.
4. Lifecycle management (audit, repair, prune) is implemented in `lifecycle.py` but not integrated into gateway or cron.

## 1. Context Pipeline Fix

### Wrong Method Name

In `src/jarvis/core/context_pipeline.py`, replace `_get_skill_context()`:

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
            lines.append(
                f"- {s.name}: {s.description} "
                f"(Keywords: {', '.join(s.trigger_keywords[:5])})"
            )
        return "Verfuegbare Skills:\n" + "\n".join(lines)
    except Exception:
        log.debug("context_skill_lookup_failed", exc_info=True)
        return ""
```

Returns name + description + keywords (not just the name). ~30 tokens per skill, max 3 skills = ~90 tokens in context.

### Registry Injection

In gateway initialization, after both `_context_pipeline` and `_skill_registry` exist:

```python
if self._context_pipeline and self._skill_registry:
    self._context_pipeline.set_skill_registry(self._skill_registry)
```

This goes in the phase where both are already initialized — after `init_agents` completes (which creates the registry) and the context pipeline exists.

## 2. Tool-Availability Logging

In `src/jarvis/skills/registry.py`, where skills are silently skipped due to missing tools (around line 446-452), add a debug log:

```python
if (
    available_tools is not None
    and skill.tools_required
    and not all(t in available_tools for t in skill.tools_required)
):
    missing = [t for t in skill.tools_required if t not in available_tools]
    log.debug("skill_skipped_missing_tools", skill=skill.slug, missing=missing)
    continue
```

No functional change — only visibility for debugging.

## 3. Lifecycle Cron Integration

### Create Lifecycle Instance

In `src/jarvis/gateway/phases/agents.py`, after creating the skill registry, also create a `SkillLifecycleManager` and store it on the gateway:

```python
from jarvis.skills.lifecycle import SkillLifecycleManager

lifecycle = SkillLifecycleManager(
    registry=skill_registry,
    skills_dirs=skill_dirs,
)
if gateway:
    gateway._skill_lifecycle = lifecycle
```

### Add to Background Tasks

In `src/jarvis/gateway/gateway.py`, in the existing `_run_background_tasks()` method (which runs every 24h), add a skill lifecycle check:

```python
# Skill lifecycle: audit and prune unused skills
if hasattr(self, "_skill_lifecycle") and self._skill_lifecycle:
    try:
        audit_result = self._skill_lifecycle.audit_skills()
        if audit_result.get("pruned", 0) > 0:
            log.info("skill_lifecycle_pruned", count=audit_result["pruned"])
        if audit_result.get("repaired", 0) > 0:
            log.info("skill_lifecycle_repaired", count=audit_result["repaired"])
    except Exception:
        log.debug("skill_lifecycle_cron_failed", exc_info=True)
```

Runs once per 24h alongside existing cleanup tasks. Non-blocking — exceptions are caught and logged.

## 4. Files Changed

| File | Change |
|------|--------|
| `src/jarvis/core/context_pipeline.py` | Fix `_get_skill_context()`: correct method name + richer context |
| `src/jarvis/gateway/gateway.py` | `set_skill_registry()` call + lifecycle cron in background tasks |
| `src/jarvis/gateway/phases/agents.py` | Create `SkillLifecycleManager`, store on gateway |
| `src/jarvis/skills/registry.py` | Debug log for skipped skills (missing tools) |
| `tests/test_skills/test_skill_lifecycle_fix.py` | Tests for context pipeline fix, registry injection, tool-availability log |

### Unchanged

- `skills/generator.py` — already writes correctly
- `skills/manager.py` — no changes needed
- `mcp/skill_tools.py` — hot-loading already works
- `skills/lifecycle.py` — already implemented, just needs wiring

## 5. Degradation Guarantees

- Context pipeline without registry → returns empty string (existing behavior)
- Lifecycle cron failure → caught and logged, next run retries
- `match()` returns no results → empty context, no injection
- All existing tests remain compatible
