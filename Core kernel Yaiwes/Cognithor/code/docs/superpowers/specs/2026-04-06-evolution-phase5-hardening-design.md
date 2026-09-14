# Evolution Engine Phase 5 Hardening — Design Spec

> **Goal:** Harden the existing Evolution Engine (Phases 1-6 already implemented) with a self-directed learning cycle with autonomous exams, missing ATL action types, risk ceiling enforcement, and a Flutter UI for goals management.

## 1. Self-Directed Learning Cycle with Autonomous Exams

### New Module: `evolution/cycle_controller.py`

Sits between `DeepLearner` and `HorizonScanner`. Controls the Expand → Examine → Decide loop.

### State Machine

```
LEARNING → (after 10 expansions) → EXAMINING
EXAMINING → score ≥ 0.8 → MASTERED (stop)
EXAMINING → score < 0.8 + progress (Δ ≥ 0.05) → LEARNING (continue, full frequency)
EXAMINING → score < 0.8 + stagnating (Δ < 0.05 over 2 consecutive exams) → STAGNATING
STAGNATING → frequency reduced to 25%, Kanban task created, continue learning
STAGNATING → score rises again (Δ > 0.05) → LEARNING (back to full frequency)
```

### Data Model

```python
class CycleState(str, Enum):
    LEARNING = "learning"
    EXAMINING = "examining"
    MASTERED = "mastered"
    STAGNATING = "stagnating"

@dataclass
class ExamResult:
    score: float                   # 0.0-1.0
    questions_total: int
    questions_passed: int
    gaps: list[str]                # Topics where knowledge is missing
    expansion_count: int           # Expansions since last exam
    timestamp: str

@dataclass
class CycleHistory:
    plan_id: str
    exam_results: list[ExamResult]
    total_expansions: int
    state: CycleState
    stagnation_count: int          # Consecutive exams with Δ < 0.05
    frequency_multiplier: float    # 1.0 = full, 0.25 = stagnating
```

### Algorithm

```python
def after_expansion(self, plan, expansion_count):
    if expansion_count % 10 != 0:
        return  # Don't examine yet

    # Run exam
    exam = self.quality_assessor.run_quality_test(plan)
    self.history.exam_results.append(exam)
    self.history.total_expansions = expansion_count

    # Mastered?
    if exam.score >= 0.8:
        self.state = CycleState.MASTERED
        plan.status = "mastered"
        self._create_mastery_report(plan, exam)
        return

    # Check progress (delta to previous exam)
    if len(self.history.exam_results) >= 2:
        delta = exam.score - self.history.exam_results[-2].score
        if delta < 0.05:
            self.history.stagnation_count += 1
        else:
            self.history.stagnation_count = 0
            # Was stagnating, now progressing again → restore full frequency
            if self.state == CycleState.STAGNATING:
                self.state = CycleState.LEARNING
                self.history.frequency_multiplier = 1.0

    if self.history.stagnation_count >= 2 and self.state != CycleState.STAGNATING:
        self.state = CycleState.STAGNATING
        self.history.frequency_multiplier = 0.25
        # Create Kanban task
        self._create_stagnation_task(plan, exam)
    elif self.state != CycleState.STAGNATING:
        self.state = CycleState.LEARNING

    # Target gaps for next expansion cycle
    for gap in exam.gaps:
        self.horizon_scanner.add_targeted_expansion(gap)
```

### Integration Point

In `deep_learner.py`, `run_subgoal()` calls `cycle_controller.after_expansion()` after each horizon scan expansion. The controller decides whether to continue, slow down, or stop.

### Persistence

CycleHistory saved as JSON alongside the plan: `~/.cognithor/evolution/plans/{plan_id}/cycle_history.json`

## 2. Missing ATL Actions + Risk Ceiling Enforcement

### 2A: `goal_management` Action

ATL can autonomously manage goals during thinking cycles:

```python
case "goal_management":
    sub_action = action.get("sub_action")
    match sub_action:
        case "add":
            goal_manager.add_goal(Goal(
                title=action["title"],
                description=action.get("description", ""),
                priority=action.get("priority", 3),
            ))
        case "pause":
            goal_manager.pause_goal(action["goal_id"])
        case "resume":
            goal_manager.resume_goal(action["goal_id"])
        case "complete":
            goal_manager.complete_goal(action["goal_id"])
        case "adjust_priority":
            goal = goal_manager.get_goal(action["goal_id"])
            if goal:
                goal.priority = action["priority"]
                goal_manager.save()
```

### 2B: `file_management` Action

ATL can create reports and notes:

```python
case "file_management":
    sub_action = action.get("sub_action")
    match sub_action:
        case "create_report":
            # Save learning progress report to Vault
            await mcp_client.call_tool("vault_save", {
                "title": action["title"],
                "content": action["content"],
                "tags": ["atl", "report", "evolution"],
            })
        case "save_note":
            await mcp_client.call_tool("save_to_memory", {
                "content": action["content"],
                "metadata": json.dumps({"source": "atl", "type": "note"}),
            })
```

### 2C: Risk Ceiling Enforcement

Currently configured but not enforced. Add check before action dispatch:

```python
_ACTION_RISK: dict[str, str] = {
    "research": "GREEN",
    "memory_update": "GREEN",
    "notification": "GREEN",
    "goal_management": "GREEN",
    "file_management": "YELLOW",
}

def _check_risk_ceiling(self, action_type: str) -> bool:
    ceiling = self._atl_config.risk_ceiling  # "GREEN" or "YELLOW"
    risk = _ACTION_RISK.get(action_type, "YELLOW")
    if ceiling == "GREEN" and risk != "GREEN":
        return False
    return True
```

Called in `thinking_cycle()` before dispatching each action. Blocked actions logged but not executed.

## 3. Flutter UI — Evolution Page in Admin Hub

### Location

New page in Admin Hub: `EvolutionPage` — accessible via Admin Hub sidebar.

### Page Structure (3 Tabs)

**Goals Tab:**
- List of all goals with: title, status badge (active/paused/mastered/stagnating), progress bar, priority chip
- Tap → GoalDetailSheet (bottom sheet with sub-goals, exam results, cycle state)
- FAB → CreateGoalDialog (title, description, priority, seed sources)

**Plans Tab:**
- Active learning plans with: goal title, sub-goal count + completion %, coverage score, last exam score
- Expand to see sub-goals with individual status (pending/researching/building/testing/passed/failed)
- Cycle state indicator (LEARNING/EXAMINING/STAGNATING/MASTERED)

**Journal Tab:**
- Daily journal entries in chronological order
- Each entry: timestamp, summary, goal updates, actions taken
- Filter by goal
- Last 7 days by default

### REST API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/evolution/goals` | List all goals |
| `POST` | `/api/v1/evolution/goals` | Create goal |
| `PATCH` | `/api/v1/evolution/goals/{id}` | Update goal (pause/resume/priority) |
| `DELETE` | `/api/v1/evolution/goals/{id}` | Delete goal |
| `GET` | `/api/v1/evolution/plans` | List all learning plans |
| `GET` | `/api/v1/evolution/plans/{id}` | Plan details with sub-goals + exam history |
| `GET` | `/api/v1/evolution/journal` | Journal entries (query: days=7) |
| `GET` | `/api/v1/evolution/stats` | Overall statistics |

### Provider

`EvolutionProvider` (ChangeNotifier): holds goals, plans, journal. REST API calls. No WebSocket needed (goals don't change in real-time — user refreshes or pulls).

## 4. Files to Create/Modify

### New Files

| File | Est. Lines |
|---|---|
| `src/jarvis/evolution/cycle_controller.py` | 150 |
| `src/jarvis/evolution/api.py` | 180 |
| `flutter_app/lib/screens/evolution_goals_page.dart` | 200 |
| `flutter_app/lib/providers/evolution_provider.dart` | 150 |
| `flutter_app/lib/widgets/evolution/goal_detail_sheet.dart` | 120 |
| `flutter_app/lib/widgets/evolution/create_goal_dialog.dart` | 100 |
| `tests/test_cycle_controller.py` | 150 |
| `tests/test_evolution_api.py` | 100 |

### Modified Files

| File | Change |
|---|---|
| `src/jarvis/evolution/deep_learner.py` | Wire CycleController after expansions |
| `src/jarvis/evolution/loop.py` | Add goal_management + file_management actions, risk ceiling check |
| `src/jarvis/evolution/horizon_scanner.py` | Add `add_targeted_expansion()` method for gap-directed research |
| `src/jarvis/gateway/gateway.py` | Init CycleController, register evolution API |
| `src/jarvis/__main__.py` | Register evolution API routes |
| `flutter_app/lib/screens/admin_hub_screen.dart` | Add Evolution page to admin hub |
| `flutter_app/lib/main.dart` | Add EvolutionProvider |

### Estimated Total: ~1,150 lines new code + ~100 lines modifications
