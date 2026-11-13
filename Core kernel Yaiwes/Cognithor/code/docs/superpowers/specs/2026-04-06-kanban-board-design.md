# Interactive Kanban Board — Design Spec

> **Goal:** Upgrade Cognithor's Kanban from a read-only pipeline monitor to a full interactive task management board with drag-and-drop, persistent storage, multi-source task creation, agent delegation, sub-tasks, and real-time WebSocket updates. Configurable entirely through the Flutter UI.

## 1. Data Model

### Enums

```python
class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    VERIFYING = "verifying"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskSource(str, Enum):
    MANUAL = "manual"          # UI "+ New Task" button
    CHAT = "chat"              # User in chat: "create task..."
    CRON = "cron"              # Cron job generates task
    EVOLUTION = "evolution"    # Evolution engine detects need
    AGENT = "agent"            # Agent creates sub-task or new task
    SYSTEM = "system"          # System-generated (heartbeat, error recovery)
```

### Task Table (SQLite, encrypted via SQLCipher)

| Field | Type | Description |
|---|---|---|
| `id` | TEXT PK | UUID4 |
| `title` | TEXT NOT NULL | Short title |
| `description` | TEXT | Detail (Markdown) |
| `status` | TEXT NOT NULL | TaskStatus value |
| `priority` | TEXT NOT NULL | TaskPriority value, default "medium" |
| `assigned_agent` | TEXT | Agent name (jarvis, researcher, coder, office, operator, frontier) |
| `source` | TEXT NOT NULL | TaskSource value |
| `source_ref` | TEXT | Reference (session ID, cron job name, parent task ID) |
| `parent_id` | TEXT FK | Null or parent task ID (sub-tasks) |
| `labels` | TEXT | JSON array of label strings |
| `sort_order` | INTEGER | Position within column for drag ordering |
| `created_at` | TEXT NOT NULL | ISO 8601 timestamp |
| `updated_at` | TEXT NOT NULL | ISO 8601 timestamp |
| `completed_at` | TEXT | Null or ISO 8601 timestamp |
| `created_by` | TEXT NOT NULL | "user", agent name, or "system" |
| `result_summary` | TEXT | Result after completion |

### Task History Table (audit trail, status changes only)

| Field | Type |
|---|---|
| `id` | INTEGER PK AUTOINCREMENT |
| `task_id` | TEXT FK |
| `old_status` | TEXT |
| `new_status` | TEXT |
| `changed_by` | TEXT |
| `changed_at` | TEXT |
| `note` | TEXT |

## 2. Backend Architecture

### New Module: `src/jarvis/kanban/`

| File | Responsibility |
|---|---|
| `__init__.py` | Package exports |
| `models.py` | TaskStatus, TaskPriority, TaskSource, Task dataclass, TaskHistory dataclass |
| `store.py` | KanbanStore: SQLite CRUD, queries, history tracking. Uses `encrypted_connect()` for SQLCipher. |
| `engine.py` | KanbanEngine: core business logic — task creation, status transitions, sub-task management, delegation, guards (max depth, max auto-tasks) |
| `sources.py` | Source adapters: ChatTaskDetector (keyword detection), CronTaskAdapter, EvolutionTaskAdapter, SystemTaskAdapter |
| `api.py` | FastAPI router: REST endpoints + WebSocket broadcast helper |

### Guards Against Runaway Task Creation

- `max_auto_tasks_per_session`: default 10. After this limit, agents cannot create more tasks in a single session.
- `max_subtask_depth`: default 3. Prevents infinite parent→child→grandchild chains.
- Debounced WebSocket broadcasts: max 1 per 500ms to prevent WS flooding from batch task creation.

### Sub-Task Lifecycle

- Parent cancel → cascading cancel of all sub-tasks (configurable)
- All sub-tasks DONE → parent moves to VERIFYING (not auto-DONE)
- Sub-task BLOCKED → parent stays IN_PROGRESS (does not auto-block)
- Deleting parent → cascading delete of sub-tasks

### Status Transitions (enforced by engine)

```
TODO → IN_PROGRESS, CANCELLED
IN_PROGRESS → VERIFYING, BLOCKED, CANCELLED, TODO (de-prioritize)
VERIFYING → DONE, IN_PROGRESS (failed verification)
BLOCKED → IN_PROGRESS, TODO, CANCELLED
DONE → (terminal, no further transitions)
CANCELLED → TODO (reopen)
```

## 3. REST API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/kanban/tasks` | List tasks. Filters: status, agent, priority, source, parent_id, label |
| `POST` | `/api/v1/kanban/tasks` | Create task |
| `GET` | `/api/v1/kanban/tasks/{id}` | Get task with sub-tasks |
| `PATCH` | `/api/v1/kanban/tasks/{id}` | Update task fields |
| `DELETE` | `/api/v1/kanban/tasks/{id}` | Delete task (cascading sub-tasks) |
| `POST` | `/api/v1/kanban/tasks/{id}/move` | Drag-and-drop: change status + sort_order |
| `GET` | `/api/v1/kanban/tasks/{id}/history` | Status change audit trail |
| `GET` | `/api/v1/kanban/stats` | Board statistics (per agent, per status, per source) |
| `GET` | `/api/v1/kanban/config` | Load Kanban configuration |
| `PATCH` | `/api/v1/kanban/config` | Update Kanban configuration |

## 4. WebSocket Events

New message type: `kanban_update`

```json
{"type": "kanban_update", "action": "created", "task": {full task object}}
{"type": "kanban_update", "action": "updated", "task_id": "...", "changes": {"status": "in_progress"}}
{"type": "kanban_update", "action": "deleted", "task_id": "..."}
{"type": "kanban_update", "action": "moved", "task_id": "...", "from_status": "todo", "to_status": "in_progress", "sort_order": 2}
```

Broadcasting: debounced at 500ms. Multiple rapid changes within 500ms are batched into a single broadcast.

## 5. MCP Tools (for Agent Task Management)

3 new tools registered in `src/jarvis/mcp/kanban_tools.py`:

| Tool | Parameters | Description |
|---|---|---|
| `kanban_create_task` | title, description, priority, labels, parent_id | Agent creates task or sub-task |
| `kanban_update_task` | task_id, status, result_summary | Agent updates own task |
| `kanban_list_tasks` | status, assigned_to_me | Agent sees assigned tasks |

Gatekeeper classification: all 3 tools → GREEN (read/write own tasks only).

## 6. Task Sources Integration

### Manual (Flutter UI)
"+ New Task" button opens TaskDialog. Fields: title, description, agent, priority, labels.

### Chat
ChatTaskDetector in `sources.py` — keyword-based detection in Planner output:
- Keywords: "erstelle task", "create task", "add to board", "neuer task"
- Planner includes `[KANBAN:title]` tag in plan output when task creation is intended
- Configurable: `auto_create_from_chat: bool`

### Cron
CronTaskAdapter — after each cron job execution, optionally creates a task with the result:
- Configurable: `auto_create_from_cron: bool`
- Source ref: cron job name
- Default status: DONE (result documentation) or TODO (follow-up needed)

### Evolution Engine
EvolutionTaskAdapter — when evolution loop detects improvement opportunities:
- Skill with high failure rate → task "Optimize skill X"
- Knowledge gap detected → task "Research topic Y"
- Configurable: `auto_create_from_evolution: bool`

### Agent
Agent calls `kanban_create_task` MCP tool during execution:
- Coder finds bug → "Fix: NPE in module Y"
- Researcher identifies follow-up → "Deep-dive: topic Z"
- Configurable: `auto_create_from_agents: bool`
- Guard: max_auto_tasks_per_session

### System
RecoveryEngine (V3) creates task on repeated failures:
- Tool crashes 3x → "Investigate: web_search failures"
- Configurable: auto-created, always visible

## 7. Flutter UI

### New 6th Tab: KanbanScreen

Bottom navigation gains a 6th tab (icon: `Icons.view_kanban`).

### Widget Tree

```
KanbanScreen
  ├─ Toolbar
  │   ├─ Toggle: [My Tasks] [Live Pipeline]
  │   ├─ Filter chips (by agent, priority, label)
  │   ├─ "+ New Task" button
  │   └─ Settings gear icon → KanbanConfigDialog
  ├─ KanbanBoard (horizontal scroll)
  │   ├─ KanbanColumn "To Do" (DragTarget)
  │   │   └─ KanbanCard[] (Draggable)
  │   ├─ KanbanColumn "In Progress"
  │   ├─ KanbanColumn "Verifying"
  │   ├─ KanbanColumn "Done"
  │   └─ KanbanColumn "Blocked" (collapsible)
  └─ TaskDetailSheet (bottom sheet on card tap)
      ├─ Title, Description, Agent, Priority, Labels
      ├─ Sub-Tasks list (expandable, with add button)
      ├─ Status history timeline
      └─ Result summary (when DONE)
```

### Drag-and-Drop
- Flutter built-in: `Draggable<Task>` + `DragTarget<Task>`
- On drop: `POST /kanban/tasks/{id}/move` with new status + sort_order
- WebSocket broadcast updates all connected clients

### KanbanProvider (ChangeNotifier)
- Holds full board state: `Map<TaskStatus, List<Task>>`
- WebSocket listener for `kanban_update` events
- Optimistic UI: update locally before server confirms
- API methods: fetchTasks(), createTask(), updateTask(), moveTask(), deleteTask()

### KanbanConfigDialog
Accessible via gear icon in Kanban toolbar. Sections:

- **Task Sources**: Toggle switches for each auto-create source (Chat, Cron, Evolution, Agents)
- **Guards**: Sliders for max_auto_tasks (1-50), max_subtask_depth (1-5)
- **Columns**: Reorderable list, add/remove/rename columns
- **Labels**: Tag editor with color picker
- **Archive**: Days until auto-archive (7-365 slider)
- **Defaults**: Default priority dropdown, default agent dropdown
- **WebSocket**: Debounce interval slider (100-2000ms)

All changes: `PATCH /api/v1/kanban/config` → persisted in config.yaml.

### Live Pipeline Mode
Toggle switches KanbanBoard data source from KanbanStore tasks to ChatProvider's `pipelineState`. Same board UI, different data. Pipeline cards are read-only (no drag-and-drop in pipeline mode).

## 8. Configuration

New section in `config.py`:

```python
class KanbanConfig(BaseModel):
    enabled: bool = True
    max_auto_tasks_per_session: int = 10
    max_subtask_depth: int = 3
    ws_debounce_ms: int = 500
    auto_create_from_chat: bool = True
    auto_create_from_cron: bool = True
    auto_create_from_evolution: bool = True
    auto_create_from_agents: bool = True
    auto_verify_on_complete: bool = False
    cascade_cancel_subtasks: bool = True
    default_priority: str = "medium"
    default_agent: str = "jarvis"
    archive_after_days: int = 30
    columns: list[str] = ["todo", "in_progress", "verifying", "done", "blocked"]
    custom_labels: list[str] = []
```

All fields editable via KanbanConfigDialog in Flutter UI.

## 9. Files to Create/Modify

### New Files

| File | Lines (est.) |
|---|---|
| `src/jarvis/kanban/__init__.py` | 10 |
| `src/jarvis/kanban/models.py` | 80 |
| `src/jarvis/kanban/store.py` | 250 |
| `src/jarvis/kanban/engine.py` | 200 |
| `src/jarvis/kanban/sources.py` | 150 |
| `src/jarvis/kanban/api.py` | 200 |
| `src/jarvis/mcp/kanban_tools.py` | 100 |
| `flutter_app/lib/screens/kanban_screen.dart` | 200 |
| `flutter_app/lib/widgets/kanban/kanban_board.dart` | 150 |
| `flutter_app/lib/widgets/kanban/kanban_column.dart` | 100 |
| `flutter_app/lib/widgets/kanban/kanban_card.dart` | 80 |
| `flutter_app/lib/widgets/kanban/task_dialog.dart` | 150 |
| `flutter_app/lib/widgets/kanban/task_detail_sheet.dart` | 150 |
| `flutter_app/lib/widgets/kanban/kanban_config_dialog.dart` | 200 |
| `flutter_app/lib/providers/kanban_provider.dart` | 200 |
| `tests/test_kanban_store.py` | 150 |
| `tests/test_kanban_engine.py` | 200 |
| `tests/test_kanban_api.py` | 150 |

### Modified Files

| File | Change |
|---|---|
| `src/jarvis/config.py` | Add KanbanConfig |
| `src/jarvis/gateway/gateway.py` | Init KanbanEngine, wire to PGE loop |
| `src/jarvis/gateway/phases/agents.py` | Pass KanbanEngine to AgentRouter |
| `src/jarvis/cron/engine.py` | CronTaskAdapter integration |
| `src/jarvis/evolution/loop.py` | EvolutionTaskAdapter integration |
| `src/jarvis/core/executor.py` | Task status updates after tool execution |
| `src/jarvis/core/gatekeeper.py` | Add kanban tools to GREEN list |
| `src/jarvis/channels/webui.py` | Add kanban_update WS message type |
| `src/jarvis/__main__.py` | Register kanban API routes |
| `flutter_app/lib/screens/main_shell.dart` | Add 6th tab |
| `flutter_app/lib/main.dart` | Add KanbanProvider |
| `flutter_app/lib/services/websocket_service.dart` | Add kanban_update WS type |
| `flutter_app/lib/l10n/app_en.arb` | Kanban i18n strings |
| `flutter_app/lib/l10n/app_de.arb` | Kanban i18n strings |

### Estimated Total: ~2,600 lines new code + ~200 lines modifications
