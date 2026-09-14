# Smart Recovery & Transparency System

**Date:** 2026-03-27
**Author:** Alexander Soellner + Claude Opus 4.6
**Status:** Approved

---

## Problem

Users get frustrated when Cognithor misunderstands, does the wrong thing, or produces
subpar results. Currently the only recourse is editing the message (rewinding the
conversation) or starting over. There is no way to:

1. See what Cognithor is about to do before it does it
2. Course-correct mid-execution without editing/restarting
3. Have the system learn from corrections to avoid repeating mistakes

## Solution: 3-Component System

### Component 1: Pre-Flight Check

Before executing complex tool plans, Cognithor shows a compact plan preview in the
chat. The user has a configurable window (default 3 seconds) to intervene before
execution starts automatically.

**Rules for when to show Pre-Flight:**
- SHOW for: multi-step plans (2+ tools), file writes, shell commands, emails, any
  YELLOW/ORANGE tool
- SKIP for: simple text responses, single read-only tools (web_search, search_memory),
  direct answers to questions

**Pre-Flight UI:**
A compact expandable card in the chat:
```
[Plan] 3 Schritte: web_search → analyze_document → write_file
       Ziel: Vertrag analysieren und Zusammenfassung erstellen
       [Ausfuehren] [Aendern] [Abbrechen]           Auto in 5s...
```

If the user does nothing, it executes after the countdown. If the user clicks
"Aendern", the plan text goes into the input field for editing. "Abbrechen" stops.

**Implementation:**
- Backend: New WebSocket message type `pre_flight` sent BEFORE tool execution
  Contains: goal, steps (tool names + brief rationale), auto_execute_seconds
- Frontend: `PreFlightCard` widget with countdown timer, expand/collapse, 3 buttons
- Gateway: After Planner produces ActionPlan, check if pre-flight is needed
  (multi-step or risky tools). If yes, send pre_flight message and wait for
  user response (approve/modify/cancel) or timeout.

### Component 2: Live Correction

The user can type corrections while Cognithor is working. The system distinguishes
between:
- **New instruction**: "Suche nach X" → treated as new task
- **Correction**: "Nein, nicht so" / "Stopp" / "Stattdessen X" / "Das ist falsch"
  → treated as course correction, aborts current execution and replans

**Detection (keyword-based + context):**
Correction triggers: "nein", "stopp", "stop", "halt", "falsch", "nicht so",
"stattdessen", "anders", "korrigier", "abbrech", "cancel", "wrong", "no"

When a correction is detected:
1. Cancel current PGE loop iteration (set cancelled flag)
2. Inject the correction as context into the next Planner call
3. Planner sees: "User hat korrigiert: {correction_text}. Vorherige Aktion: {last_tool}.
   Passe deinen Plan an."
4. Cognithor replans with the correction context

**Implementation:**
- Gateway: Check incoming messages during active PGE loop for correction keywords
- If correction detected: set `_cancelled_sessions` flag (already exists!),
  inject correction context into WorkingMemory, replan
- Frontend: No special UI needed — user just types naturally

### Component 3: Post-Correction Learning

Every time the user corrects Cognithor, the correction is stored in a
`CorrectionMemory` (SQLite). When similar situations arise in the future,
the system checks if there is a relevant correction and proactively adjusts.

**Schema:**
```sql
CREATE TABLE corrections (
    id TEXT PRIMARY KEY,
    user_message TEXT NOT NULL,       -- original user request
    correction_text TEXT NOT NULL,    -- what the user said to correct
    original_plan TEXT DEFAULT '',    -- what Cognithor tried to do
    corrected_plan TEXT DEFAULT '',   -- what Cognithor did after correction
    keywords TEXT DEFAULT '',         -- extracted keywords for matching
    times_triggered INTEGER DEFAULT 1,
    created_at REAL NOT NULL,
    last_triggered_at REAL
);
```

**Learning flow:**
1. User corrects → store (user_message, correction_text, original_plan)
2. Next similar request → search corrections by keyword overlap
3. If match found (score > 0.6): inject into Planner context as
   "ERINNERUNG: Bei aehnlichen Anfragen hat der User korrigiert: {correction}.
   Beruecksichtige das."
4. If same correction 3+ times: proactively ask before acting

**Proactive question threshold:**
- 1 correction: stored silently
- 2 corrections (same pattern): Planner gets reminder
- 3+ corrections: Cognithor asks explicitly before acting

**Implementation:**
- New module `core/correction_memory.py` with `CorrectionMemory` class
- Integrated into Context Pipeline (pre-planner enrichment)
- Gateway stores corrections when live-correction is detected

### UI Changes

**1. Pre-Flight Card (new widget):**
- Compact card with plan summary, goal, countdown timer
- 3 buttons: Ausfuehren (green), Aendern (yellow), Abbrechen (red)
- Auto-collapses after execution starts
- Expandable to show full step details

**2. Plan Badge (enhancement to existing):**
The existing `plan` badge in the pipeline indicator already shows the plan.
Enhance it to be clickable and show the pre-flight details.

**3. Correction Indicator:**
When Cognithor learns from a correction, show a brief inline note:
"Gemerkt — werde das naechstes Mal beruecksichtigen."

**4. No Chat Branching needed:**
The version navigator (< 1/2 >) stays for edit history, but the primary
interaction model is: just tell Cognithor what's wrong and it adapts.

### Config

```yaml
recovery:
  pre_flight_enabled: true
  pre_flight_timeout_seconds: 5       # Auto-execute after N seconds
  pre_flight_min_steps: 2             # Show pre-flight for plans with N+ steps
  pre_flight_always_for_yellow: true  # Always show for YELLOW/ORANGE tools
  correction_learning_enabled: true
  correction_proactive_threshold: 3   # Ask proactively after N corrections
```

### Files

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/jarvis/core/correction_memory.py` | CorrectionMemory SQLite store |
| Modify | `src/jarvis/core/context_pipeline.py` | Inject correction reminders pre-planner |
| Modify | `src/jarvis/gateway/gateway.py` | Pre-flight flow + correction detection in PGE loop |
| Modify | `src/jarvis/config.py` | RecoveryConfig model |
| Modify | `src/jarvis/__main__.py` | WebSocket pre_flight message handling |
| Create | `flutter_app/lib/widgets/chat/pre_flight_card.dart` | Pre-flight UI |
| Modify | `flutter_app/lib/providers/chat_provider.dart` | Handle pre_flight WS messages |
| Modify | `flutter_app/lib/screens/chat_screen.dart` | Render PreFlightCard |
| Create | `tests/unit/test_correction_memory.py` | Tests |

### Not in Scope

- Full conversation tree / branching (solved by correction instead)
- Undo/redo for tool executions (too complex, not needed)
- Multi-user correction merging (single user system)
