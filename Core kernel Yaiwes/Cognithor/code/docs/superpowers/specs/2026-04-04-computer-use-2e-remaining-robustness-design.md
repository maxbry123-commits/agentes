# Computer Use Phase 2E: Remaining Robustness — Design Spec

**Date:** 2026-04-04
**Status:** Approved
**Depends on:** Phase 2D (Security & Robustness) — complete

## Goal

Fix 3 deferred robustness issues: A-B oscillation detection, content bag size limit, and popup/dialog handling. All quick fixes within `cu_agent.py`, no architectural changes.

## 1. A→B Oscillation Detection

### Problem

`_check_abort()` only catches identical repeated actions (`set(recent) == 1`). An agent oscillating between two actions (click A → click B → click A → click B) is never detected as stuck.

### Fix

Add a second condition in `_check_abort()` after the existing `stuck_loop` check:

```python
# Existing: identical actions
if (
    len(self._recent_actions) >= self._config.stuck_detection_threshold
    and len(set(self._recent_actions)) == 1
):
    return "stuck_loop"

# New: oscillation — 2 or fewer unique actions in last 6
if len(self._recent_actions) >= 6 and len(set(self._recent_actions[-6:])) <= 2:
    return "stuck_oscillation"
```

New abort reason: `"stuck_oscillation"`. The window size of 6 is hardcoded (not configurable) — oscillation detection doesn't need to be tunable.

## 2. Content Bag Size Limit

### Problem

`result.extracted_content` grows without bound as `extract_text` is called. For text-heavy tasks, this can reach megabytes.

### Fix

Cap `extracted_content` at 500KB. When the limit is reached, new extractions are still stored in the content bag (for prompt injection, already capped at 3000 chars) but not appended to `extracted_content`.

```python
_MAX_EXTRACTED_CONTENT = 512_000  # 500KB

# In the extract_text block of execute():
if len(result.extracted_content) < _MAX_EXTRACTED_CONTENT:
    result.extracted_content += labeled_text + "\n\n"
else:
    self._action_history.append(
        f"extract_text() -> {len(text)} chars [LIMIT erreicht, verworfen]"
    )
```

The content bag dict itself stays unlimited — it's only used as a preview in prompts (already capped at 3000 chars) and for file-writing sub-tasks (where the full content is needed).

## 3. Popup/Dialog Handling

### Problem

Unexpected dialogs (UAC, "Save changes?", cookie banners) block interaction with the underlying app. The agent keeps trying to click the app but hits the dialog.

### Fix — Two changes

**a) System prompt instruction:**

Append to `_CU_SYSTEM_PROMPT`:

```
"Wenn ein unerwartetes Dialogfenster, Popup oder Banner erscheint, "
"schliesse es zuerst (Escape, X-Button, oder Abbrechen) bevor du "
"mit der eigentlichen Aufgabe weitermachst."
```

**b) Enhanced stale-screen hint:**

When `stale_screen_count >= 2` triggers, change the failure hint from:

```
"Bildschirm hat sich nicht veraendert."
```

To:

```
"Bildschirm hat sich nicht veraendert. "
"Moeglicherweise blockiert ein Dialogfenster die Interaktion. "
"Versuche Escape zu druecken oder den Dialog zu schliessen."
```

This uses the existing failure escalation system — no new mechanism needed.

## Files Changed

| File | Change |
|------|--------|
| `src/jarvis/core/cu_agent.py` | Oscillation check in `_check_abort`. Content limit in `execute()`. System prompt extension. Stale-hint extension. `_MAX_EXTRACTED_CONTENT` constant. |
| `tests/test_core/test_cu_agent.py` | Tests for oscillation detection, content limit, dialog hint text. |

## Degradation Guarantees

- Oscillation check only fires after 6 actions (existing tests have fewer actions — no regressions)
- Content limit only affects `extracted_content` string, not the content bag or prompt previews
- Dialog hint is additive text — existing behavior unchanged
- All existing tests remain compatible
