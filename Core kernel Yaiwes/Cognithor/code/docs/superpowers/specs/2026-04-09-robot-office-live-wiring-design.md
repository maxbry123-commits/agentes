# Robot Office Live Wiring

**Date:** 2026-04-09
**Issue:** #84
**Status:** Approved

## Problem

Robot Office is purely decorative — 8 hardcoded robots with fake states, fake task messages, and no connection to real system data. Users are confused because it looks like a dashboard but reflects nothing real.

## Design

### Architecture

Three data streams feed into a new `RobotOfficeProvider`:

1. **WebSocket Pipeline Events** → Robot states (real-time)
2. **REST Polling** `/monitoring/dashboard` → System metrics every 10s (CPU, RAM, load)
3. **REST Polling** `/tasks` + `/agents` → Kanban dots + agent list every 10s

### Component 1: RobotOfficeProvider (new Flutter Provider)

Central state manager that aggregates all data sources.

**Inputs:**
- WebSocket events: `status_update`, `pipeline_event`, `tool_start`, `tool_result`, `stream_token`, `stream_end`
- REST polling every 10s: `/monitoring/dashboard`, `/agents`, kanban task summary

**Exposed state:**
- `List<AgentInfo> agents` — name, state, currentTask for each configured agent
- `PgePhase pgePhase` — which Trinity phase is active (idle/planning/gating/executing/streaming)
- `SystemMetrics metrics` — cpu (0.0-1.0), memory (0.0-1.0), load (0.0-1.0)
- `Map<String, int> kanbanCounts` — task count per status column
- `Map<String, List<String>> kanbanTasks` — task titles per status column (max 5 per column)

**State mapping (WS Events → PGE Phase → Robot States):**

| WS Event | PGE Phase | Robot Effect |
|----------|-----------|--------------|
| `status_update` type=thinking | planning | Planner → working+typing, taskMsg="Planning: [msg]" |
| `pipeline_event` phase=plan complete | plan_done | Planner → idle |
| `pipeline_event` phase=gate | gating | Gatekeeper → working, taskMsg="Reviewing: [tool]" |
| `tool_start` | executing | Executor → working, taskMsg="Running: [tool_name]" |
| `tool_result` | tool_done | Executor → carry animation |
| `stream_token` | streaming | Executor → typing |
| `stream_end` | idle | All Trinity → idle |
| No events for 30s | system_idle | All → coffeeBreak/idle randomly |

**User-Agent state mapping:**
- User agents from `/agents` endpoint are idle by default
- An agent is `working` if it is the `assigned_agent` on an in-progress Kanban task

### Component 2: Dynamic Robot Creation

`_createRobots()` refactored from hardcoded list to dynamic:

**Always present (PGE Trinity):**
- Planner (indigo `#6366f1`) — antenna, system glow
- Executor (emerald `#10b981`) — system glow
- Gatekeeper (red `#ef4444`) — system glow

Trinity robots have a subtle glow/border to distinguish them from user agents.

**Dynamic (User Agents):**
- One robot per agent from `GET /api/v1/agents`
- Color from predefined palette (8 colors), assigned by index
- Name and role from agent config

**Predefined color palette for user agents:**
```
#8b5cf6 (violet), #f59e0b (amber), #06b6d4 (cyan),
#ec4899 (pink), #84cc16 (lime), #f97316 (orange),
#14b8a6 (teal), #a855f7 (purple)
```

**Layout:**
- Grid-based positioning that adapts to robot count (3-12)
- Desk positions calculated dynamically, evenly distributed across office floor
- Trinity robots always at fixed prominent positions (left-center-right)
- User agents fill remaining positions

### Component 3: System Metrics Wiring

The `RobotOfficeWidget` already accepts `cpuUsage`, `memoryUsage`, `activePhase`, `systemLoad` props but they're always 0. Now wired to real data from `RobotOfficeProvider.metrics`:

- `cpuUsage` → Server rack LED blink speed
- `memoryUsage` → LED color shifts toward red when > 0.8
- `systemLoad` → Ceiling light brightness
- `activePhase` → Highlights matching kanban column in the painted board

### Component 4: Kanban Board Dots + Tooltips

The painted kanban board in `robot_office_painter.dart`:

**Visual:**
- Each column shows colored dots proportional to task count
- Colors: Backlog=grey, In Progress=blue, Review=yellow, Done=green, Blocked=red
- Max 8 dots per column; if more, show count number beside dots

**Interaction:**
- `HitTest` on the canvas detects hover over column areas
- Tooltip appears on hover showing task titles (max 5 per column)
- Data from `RobotOfficeProvider.kanbanCounts` and `kanbanTasks`

### Component 5: Real Task Messages

When a robot is `working`, its `taskMsg` shows real context:

- **Planner:** "Planning: [first 30 chars of user message]..."
- **Executor:** "Running: [tool_name]"
- **Gatekeeper:** "Reviewing: [tool_name] (risk: [level])"
- **User Agents:** "Processing: [kanban_task_title]"
- **Idle robots:** No taskMsg (empty string)

Chat bubbles between robots remain playful/decorative (from #88 fix) — robot banter, not system status.

### Data Flow

```
WebSocket ──→ RobotOfficeProvider ──→ RobotOfficeWidget
                  ↑                       ├── Robot states + task messages
              REST Polling (10s)          ├── Server rack LEDs + ceiling light
                  ├── /monitoring/dashboard → cpu/ram/load
                  ├── /agents              → Robot count + names
                  └── /tasks (kanban)      → Kanban dots + tooltips
```

### Files to Create/Modify

| File | Change |
|------|--------|
| `flutter_app/lib/providers/robot_office_provider.dart` | **New** — central state manager |
| `flutter_app/lib/widgets/robot_office/robot_office_widget.dart` | Refactor `_createRobots()` to dynamic, wire provider props |
| `flutter_app/lib/widgets/robot_office/robot_office_painter.dart` | Kanban dots + tooltip hit testing |
| `flutter_app/lib/screens/dashboard_screen.dart` | Wire `RobotOfficeProvider` into widget tree, pass real props |
| `flutter_app/lib/main.dart` or app setup | Register `RobotOfficeProvider` |
| `flutter_app/lib/services/api_client.dart` | Add `getKanbanSummary()` if not exists |

### Not In Scope

- Clickable robots (navigate to agent detail) — follow-up
- Sound effects
- Robot customization (color/name) by user
- Custom robot sprites/skins
