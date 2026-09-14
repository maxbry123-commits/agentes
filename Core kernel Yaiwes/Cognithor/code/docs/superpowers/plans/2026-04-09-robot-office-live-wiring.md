# Robot Office Live Wiring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the decorative Robot Office to real system data — real agents, real pipeline states, real metrics, real kanban tasks.

**Architecture:** A new `RobotOfficeProvider` aggregates WebSocket pipeline events (real-time) and REST polling (10s interval) into a unified state. The `RobotOfficeWidget` consumes this provider instead of hardcoded data. The `OfficePainter` kanban board shows real task dots with hover tooltips.

**Tech Stack:** Flutter Provider, WebSocketService events, REST API polling, CustomPainter hit testing

---

## File Structure

| File | Responsibility |
|------|---------------|
| `lib/providers/robot_office_provider.dart` | **New** — aggregates WS events + REST polling into unified Robot Office state |
| `lib/widgets/robot_office/robot_office_widget.dart` | Refactor `_createRobots()` to dynamic, consume provider |
| `lib/widgets/robot_office/office_painter.dart` | Real kanban dots + tooltip hit testing |
| `lib/widgets/robot_office/robot.dart` | Add `isSystem` field to Robot |
| `lib/screens/dashboard_screen.dart` | Wire provider, pass real data |
| `lib/main.dart` | Register `RobotOfficeProvider` |
| `lib/services/api_client.dart` | Add `getKanbanSummary()` method |

---

### Task 1: RobotOfficeProvider — data models and skeleton

**Files:**
- Create: `flutter_app/lib/providers/robot_office_provider.dart`
- Modify: `flutter_app/lib/main.dart:57`

- [ ] **Step 1: Create the provider with data models**

Create `flutter_app/lib/providers/robot_office_provider.dart`:

```dart
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:jarvis_ui/services/api_client.dart';
import 'package:jarvis_ui/services/websocket_service.dart';

/// PGE pipeline phase.
enum PgePhase { idle, planning, gating, executing, streaming }

/// Info about a single configured agent.
class AgentInfo {
  AgentInfo({required this.name, this.displayName, this.isWorking = false, this.currentTask = ''});
  final String name;
  final String? displayName;
  bool isWorking;
  String currentTask;
}

/// System resource metrics.
class SystemMetrics {
  double cpu;
  double memory;
  double load;
  SystemMetrics({this.cpu = 0, this.memory = 0, this.load = 0});
}

/// Aggregates real-time data for the Robot Office visualization.
class RobotOfficeProvider extends ChangeNotifier {
  ApiClient? _api;
  WebSocketService? _ws;
  Timer? _pollTimer;
  bool _wsListenersAttached = false;

  // ── Public state ──────────────────────────────────────────
  PgePhase pgePhase = PgePhase.idle;
  String plannerTask = '';
  String executorTask = '';
  String gatekeeperTask = '';
  List<AgentInfo> agents = [];
  SystemMetrics metrics = SystemMetrics();
  Map<String, int> kanbanCounts = {};
  Map<String, List<String>> kanbanTasks = {};
  DateTime _lastEventTime = DateTime.now();

  // ── Lifecycle ─────────────────────────────────────────────

  void init(ApiClient api, WebSocketService? ws) {
    _api = api;
    _ws = ws;
    _startPolling();
    _attachWsListeners();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _detachWsListeners();
    super.dispose();
  }

  // ── REST Polling (every 10s) ──────────────────────────────

  void _startPolling() {
    _poll(); // immediate first poll
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 10), (_) => _poll());
  }

  Future<void> _poll() async {
    if (_api == null) return;
    await Future.wait([
      _pollMetrics(),
      _pollAgents(),
      _pollKanban(),
    ]);
    notifyListeners();
  }

  Future<void> _pollMetrics() async {
    try {
      final res = await _api!.get('monitoring/dashboard');
      final sys = res['system'] as Map<String, dynamic>? ?? {};
      metrics.cpu = ((sys['cpu_percent'] as num?) ?? 0).toDouble() / 100.0;
      metrics.memory = ((sys['memory_percent'] as num?) ?? 0).toDouble() / 100.0;
      metrics.load = ((metrics.cpu + metrics.memory) / 2).clamp(0.0, 1.0);
    } catch (_) {}
  }

  Future<void> _pollAgents() async {
    try {
      final res = await _api!.get('agents');
      final list = res['agents'] as List<dynamic>? ?? [];
      agents = list.map((a) {
        final m = a as Map<String, dynamic>;
        return AgentInfo(
          name: m['name']?.toString() ?? '',
          displayName: m['display_name']?.toString(),
        );
      }).where((a) => a.name.isNotEmpty).toList();
    } catch (_) {}
  }

  Future<void> _pollKanban() async {
    try {
      final res = await _api!.get('tasks');
      final tasks = res['tasks'] as List<dynamic>? ?? [];
      final counts = <String, int>{};
      final titles = <String, List<String>>{};
      for (final t in tasks) {
        final m = t as Map<String, dynamic>;
        final status = m['status']?.toString() ?? 'backlog';
        final title = m['title']?.toString() ?? '';
        counts[status] = (counts[status] ?? 0) + 1;
        titles.putIfAbsent(status, () => []);
        if (titles[status]!.length < 5) titles[status]!.add(title);
        // Track agent assignment
        final agent = m['assigned_agent']?.toString() ?? '';
        if (agent.isNotEmpty && status == 'in_progress') {
          for (final a in agents) {
            if (a.name == agent) {
              a.isWorking = true;
              a.currentTask = title;
            }
          }
        }
      }
      kanbanCounts = counts;
      kanbanTasks = titles;
    } catch (_) {}
  }

  // ── WebSocket Events (real-time) ──────────────────────────

  void _attachWsListeners() {
    if (_ws == null || _wsListenersAttached) return;
    _ws!.on(WsType.statusUpdate, _onStatusUpdate);
    _ws!.on(WsType.pipelineEvent, _onPipelineEvent);
    _ws!.on(WsType.toolStart, _onToolStart);
    _ws!.on(WsType.toolResult, _onToolResult);
    _ws!.on(WsType.streamToken, _onStreamToken);
    _ws!.on(WsType.streamEnd, _onStreamEnd);
    _wsListenersAttached = true;
  }

  void _detachWsListeners() {
    if (_ws == null || !_wsListenersAttached) return;
    _ws!.off(WsType.statusUpdate, _onStatusUpdate);
    _ws!.off(WsType.pipelineEvent, _onPipelineEvent);
    _ws!.off(WsType.toolStart, _onToolStart);
    _ws!.off(WsType.toolResult, _onToolResult);
    _ws!.off(WsType.streamToken, _onStreamToken);
    _ws!.off(WsType.streamEnd, _onStreamEnd);
    _wsListenersAttached = false;
  }

  void _onStatusUpdate(Map<String, dynamic> msg) {
    _lastEventTime = DateTime.now();
    final status = msg['status']?.toString() ?? '';
    if (status == 'thinking') {
      pgePhase = PgePhase.planning;
      plannerTask = 'Planning: ${_truncate(msg['text']?.toString() ?? '', 30)}';
    }
    notifyListeners();
  }

  void _onPipelineEvent(Map<String, dynamic> msg) {
    _lastEventTime = DateTime.now();
    final phase = msg['phase']?.toString() ?? '';
    final action = msg['action']?.toString() ?? '';
    if (phase == 'plan' && action == 'start') {
      pgePhase = PgePhase.planning;
    } else if (phase == 'gate') {
      pgePhase = PgePhase.gating;
      gatekeeperTask = 'Reviewing: ${_truncate(msg['tool']?.toString() ?? '', 25)}';
    } else if (phase == 'execute') {
      pgePhase = PgePhase.executing;
    } else if (phase == 'complete' || action == 'end') {
      pgePhase = PgePhase.idle;
      plannerTask = '';
      executorTask = '';
      gatekeeperTask = '';
    }
    notifyListeners();
  }

  void _onToolStart(Map<String, dynamic> msg) {
    _lastEventTime = DateTime.now();
    pgePhase = PgePhase.executing;
    executorTask = 'Running: ${msg['tool']?.toString() ?? 'tool'}';
    notifyListeners();
  }

  void _onToolResult(Map<String, dynamic> msg) {
    _lastEventTime = DateTime.now();
    executorTask = '';
    notifyListeners();
  }

  void _onStreamToken(Map<String, dynamic> msg) {
    _lastEventTime = DateTime.now();
    if (pgePhase != PgePhase.streaming) {
      pgePhase = PgePhase.streaming;
      executorTask = 'Streaming response...';
      notifyListeners();
    }
  }

  void _onStreamEnd(Map<String, dynamic> msg) {
    _lastEventTime = DateTime.now();
    pgePhase = PgePhase.idle;
    plannerTask = '';
    executorTask = '';
    gatekeeperTask = '';
    notifyListeners();
  }

  /// True if no WS events received for 30+ seconds.
  bool get isSystemIdle =>
      DateTime.now().difference(_lastEventTime).inSeconds > 30;

  /// Active phase as int 0-4 for the painter.
  int get activePhaseInt {
    switch (pgePhase) {
      case PgePhase.planning:
        return 0;
      case PgePhase.gating:
        return 1;
      case PgePhase.executing:
        return 2;
      case PgePhase.streaming:
        return 3;
      case PgePhase.idle:
        return 4;
    }
  }

  static String _truncate(String s, int max) =>
      s.length <= max ? s : '${s.substring(0, max)}...';
}
```

- [ ] **Step 2: Register in main.dart**

In `flutter_app/lib/main.dart`, add import and insert the provider after `KanbanProvider` (line 57):

```dart
import 'package:jarvis_ui/providers/robot_office_provider.dart';
```

In the `MultiProvider` children list, after the `KanbanProvider()` line:

```dart
ChangeNotifierProvider(create: (_) => RobotOfficeProvider()),
```

- [ ] **Step 3: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 4: Commit**

```bash
git add flutter_app/lib/providers/robot_office_provider.dart flutter_app/lib/main.dart
git commit -m "feat: add RobotOfficeProvider — aggregates WS events + REST polling (#84)"
```

---

### Task 2: Add `isSystem` to Robot + dynamic robot creation

**Files:**
- Modify: `flutter_app/lib/widgets/robot_office/robot.dart:22-99`
- Modify: `flutter_app/lib/widgets/robot_office/robot_office_widget.dart:295-497`

- [ ] **Step 1: Add `isSystem` field to Robot**

In `flutter_app/lib/widgets/robot_office/robot.dart`, add to the constructor and fields:

```dart
this.isSystem = false,
```

And the field:

```dart
final bool isSystem;
```

- [ ] **Step 2: Refactor RobotOfficeWidget to accept dynamic agents**

In `flutter_app/lib/widgets/robot_office/robot_office_widget.dart`, add a new parameter to `RobotOfficeWidget`:

```dart
const RobotOfficeWidget({
    super.key,
    this.isRunning = true,
    this.onTaskCompleted,
    this.onStateChanged,
    this.cpuUsage = 0,
    this.memoryUsage = 0,
    this.activePhase = 0,
    this.systemLoad = 0,
    this.agentNames = const [],
    this.pgePhase = 0,
    this.plannerTask = '',
    this.executorTask = '',
    this.gatekeeperTask = '',
    this.agentTasks = const {},
  });

  // ... existing fields ...
  final List<String> agentNames;
  final int pgePhase;
  final String plannerTask;
  final String executorTask;
  final String gatekeeperTask;
  final Map<String, String> agentTasks; // agentName -> currentTask
```

- [ ] **Step 3: Refactor `_createRobots()` to be dynamic**

Replace the existing `_createRobots()` method (lines 425-497) with:

```dart
  static const _agentColors = [
    Color(0xFF8b5cf6), // violet
    Color(0xFFf59e0b), // amber
    Color(0xFF06b6d4), // cyan
    Color(0xFFec4899), // pink
    Color(0xFF84cc16), // lime
    Color(0xFFf97316), // orange
    Color(0xFF14b8a6), // teal
    Color(0xFFa855f7), // purple
  ];

  static const _agentEyeColors = [
    Color(0xFFc4b5fd),
    Color(0xFFfcd34d),
    Color(0xFF67e8f9),
    Color(0xFFf9a8d4),
    Color(0xFFbef264),
    Color(0xFFfdba74),
    Color(0xFF5eead4),
    Color(0xFFd8b4fe),
  ];

  List<Robot> _createRobots() {
    final l = _locale;
    final robots = <Robot>[
      // PGE Trinity — always present
      Robot(
        id: 'planner', name: 'Planner',
        color: const Color(0xFF6366f1), eyeColor: const Color(0xFFa5b4fc),
        role: _RobotMessages.role('planner', l), hasAntenna: true, isSystem: true,
        x: 0.18, y: 0.72,
        state: RobotState.idle,
        stateTimer: 3.0 + _rng.nextDouble() * 3,
      ),
      Robot(
        id: 'executor', name: 'Executor',
        color: const Color(0xFF10b981), eyeColor: const Color(0xFF6ee7b7),
        role: _RobotMessages.role('executor', l), isSystem: true,
        x: 0.45, y: 0.58,
        state: RobotState.idle,
        stateTimer: 2.0 + _rng.nextDouble() * 4,
      ),
      Robot(
        id: 'gatekeeper', name: 'Gatekeeper',
        color: const Color(0xFFef4444), eyeColor: const Color(0xFFfca5a5),
        role: _RobotMessages.role('gatekeeper', l), isSystem: true,
        x: 0.88, y: 0.42,
        state: RobotState.idle,
        stateTimer: 0.5 + _rng.nextDouble(),
      ),
    ];

    // Dynamic user agents
    final names = widget.agentNames;
    final positions = _agentPositions(names.length);
    for (var i = 0; i < names.length; i++) {
      final colorIdx = i % _agentColors.length;
      final pos = positions[i];
      robots.add(Robot(
        id: 'agent_$i', name: names[i],
        color: _agentColors[colorIdx], eyeColor: _agentEyeColors[colorIdx],
        role: names[i],
        x: pos.dx, y: pos.dy,
        state: RobotState.idle,
        stateTimer: 1.0 + _rng.nextDouble() * 3,
      ));
    }

    return robots;
  }

  /// Generate evenly distributed positions for N user agents.
  List<Offset> _agentPositions(int count) {
    if (count == 0) return [];
    // Available floor positions (avoiding Trinity positions and furniture)
    const slots = [
      Offset(0.30, 0.52), Offset(0.72, 0.75), Offset(0.08, 0.35),
      Offset(0.58, 0.28), Offset(0.60, 0.80), Offset(0.35, 0.35),
      Offset(0.78, 0.58), Offset(0.15, 0.50), Offset(0.50, 0.42),
    ];
    return [for (var i = 0; i < count && i < slots.length; i++) slots[i]];
  }
```

- [ ] **Step 4: Rebuild robots when agent list changes**

In `didUpdateWidget`, check if `agentNames` changed and rebuild:

```dart
  @override
  void didUpdateWidget(RobotOfficeWidget old) {
    super.didUpdateWidget(old);
    if (!listEquals(old.agentNames, widget.agentNames)) {
      _robots = _createRobots();
    }
  }
```

Add `import 'package:flutter/foundation.dart' show listEquals;` if not present.

- [ ] **Step 5: Apply PGE phase to Trinity robot states each frame**

In the `_tick()` or beginning of the animation callback, before `_updateRobot` calls, add a method `_syncPgeStates()` that maps `widget.pgePhase` to Trinity robot states:

```dart
  void _syncPgeStates() {
    final planner = _robots.firstWhere((r) => r.id == 'planner', orElse: () => _robots.first);
    final executor = _robots.firstWhere((r) => r.id == 'executor', orElse: () => _robots.first);
    final gatekeeper = _robots.firstWhere((r) => r.id == 'gatekeeper', orElse: () => _robots.first);

    switch (widget.pgePhase) {
      case 0: // planning
        if (planner.state != RobotState.working) {
          planner.state = RobotState.working;
          planner.typing = true;
          planner.stateTimer = 30.0;
        }
        planner.taskMsg = widget.plannerTask;
        planner.msgTimer = 5.0;
      case 1: // gating
        if (gatekeeper.state != RobotState.working) {
          gatekeeper.state = RobotState.working;
          gatekeeper.stateTimer = 30.0;
        }
        gatekeeper.taskMsg = widget.gatekeeperTask;
        gatekeeper.msgTimer = 5.0;
      case 2: // executing
        if (executor.state != RobotState.working) {
          executor.state = RobotState.working;
          executor.typing = true;
          executor.stateTimer = 30.0;
        }
        executor.taskMsg = widget.executorTask;
        executor.msgTimer = 5.0;
      case 3: // streaming
        if (executor.state != RobotState.working) {
          executor.state = RobotState.working;
          executor.typing = true;
          executor.stateTimer = 30.0;
        }
        executor.taskMsg = widget.executorTask;
        executor.msgTimer = 5.0;
      default: // idle (4)
        // Let normal idle behavior take over — don't force states
        break;
    }

    // User agents: working if assigned to in-progress task
    for (final r in _robots) {
      if (r.isSystem) continue;
      final task = widget.agentTasks[r.name] ?? '';
      if (task.isNotEmpty) {
        if (r.state == RobotState.idle || r.state == RobotState.coffeeBreak) {
          r.state = RobotState.working;
          r.typing = true;
          r.stateTimer = 30.0;
        }
        r.taskMsg = 'Processing: ${task.length > 25 ? '${task.substring(0, 25)}...' : task}';
        r.msgTimer = 5.0;
      }
    }
  }
```

Call `_syncPgeStates()` at the start of the animation tick, before the robot update loop.

- [ ] **Step 6: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 7: Commit**

```bash
git add flutter_app/lib/widgets/robot_office/robot.dart flutter_app/lib/widgets/robot_office/robot_office_widget.dart
git commit -m "feat: dynamic robot creation from real agents + PGE state sync (#84)"
```

---

### Task 3: Wire Dashboard → RobotOfficeProvider → Widget

**Files:**
- Modify: `flutter_app/lib/screens/dashboard_screen.dart:125-168`

- [ ] **Step 1: Initialize provider on dashboard load**

In `dashboard_screen.dart`, in `didChangeDependencies` or `initState`, wire the provider:

```dart
final roProvider = context.read<RobotOfficeProvider>();
final conn = context.read<ConnectionProvider>();
if (conn.state == JarvisConnectionState.connected) {
  roProvider.init(conn.api, conn.ws);
}
```

- [ ] **Step 2: Replace hardcoded widget props with provider data**

Change the `RobotOfficeWidget` instantiation (around line 156) to use `Consumer<RobotOfficeProvider>`:

```dart
Consumer<RobotOfficeProvider>(
  builder: (context, ro, _) => RobotOfficeWidget(
    isRunning: true,
    cpuUsage: ro.metrics.cpu,
    memoryUsage: ro.metrics.memory,
    activePhase: ro.activePhaseInt,
    systemLoad: ro.metrics.load,
    agentNames: ro.agents.map((a) => a.name).toList(),
    pgePhase: ro.activePhaseInt,
    plannerTask: ro.plannerTask,
    executorTask: ro.executorTask,
    gatekeeperTask: ro.gatekeeperTask,
    agentTasks: {
      for (final a in ro.agents)
        if (a.currentTask.isNotEmpty) a.name: a.currentTask,
    },
    onStateChanged: (task, count) {
      setState(() {
        _robotCurrentTask = task;
        _robotTaskCount = count;
      });
    },
  ),
),
```

Remove the old manual `cpuNorm`/`memNorm`/`systemLoad` computations if they're only used for the Robot Office.

- [ ] **Step 3: Add import**

```dart
import 'package:jarvis_ui/providers/robot_office_provider.dart';
```

- [ ] **Step 4: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 5: Commit**

```bash
git add flutter_app/lib/screens/dashboard_screen.dart
git commit -m "feat: wire dashboard to RobotOfficeProvider with real data (#84)"
```

---

### Task 4: Kanban board dots + tooltip hit testing

**Files:**
- Modify: `flutter_app/lib/widgets/robot_office/office_painter.dart:595-726`
- Modify: `flutter_app/lib/widgets/robot_office/robot_office_widget.dart` (build method)

- [ ] **Step 1: Add kanban data to OfficePainter**

Add constructor parameters to `OfficePainter`:

```dart
final Map<String, int> kanbanCounts;
final Map<String, List<String>> kanbanTasks;
```

Default to empty maps in the constructor.

- [ ] **Step 2: Replace hardcoded sticky notes with real dots**

In `_drawKanbanBoard()` (line 672-715), replace the hardcoded sticky notes block with:

```dart
    // Draw real kanban dots
    final columns = {
      0: ['backlog'],
      1: ['in_progress'],
      2: ['done', 'verifying'],
    };
    final dotColors = {
      'backlog': const Color(0xFF9CA3AF),    // grey
      'in_progress': const Color(0xFF3B82F6), // blue
      'verifying': const Color(0xFFF59E0B),   // yellow
      'done': const Color(0xFF22C55E),         // green
      'blocked': const Color(0xFFEF4444),      // red
    };

    for (var col = 0; col < 3; col++) {
      final statuses = columns[col] ?? [];
      var count = 0;
      for (final s in statuses) {
        count += kanbanCounts[s] ?? 0;
      }

      final dotRadius = colW * 0.08;
      final maxDots = 8;
      final dotsToShow = count.clamp(0, maxDots);
      final dotAreaTop = bodyY + headerH + colLabelH + 4;
      final dotAreaLeft = bx + col * colW + 2;

      for (var d = 0; d < dotsToShow; d++) {
        final row = d ~/ 2;
        final colOffset = (d % 2) * (dotRadius * 3);
        final dx = dotAreaLeft + dotRadius + colOffset;
        final dy = dotAreaTop + row * (dotRadius * 2.5) + dotRadius;
        final color = dotColors[statuses.firstOrNull ?? 'backlog'] ?? const Color(0xFF9CA3AF);
        canvas.drawCircle(Offset(dx, dy), dotRadius, Paint()..color = color);
      }

      // Show count if more than maxDots
      if (count > maxDots) {
        final tp = TextPainter(
          text: TextSpan(
            text: '+${count - maxDots}',
            style: TextStyle(color: Colors.white54, fontSize: dotRadius * 1.5),
          ),
          textDirection: TextDirection.ltr,
        )..layout();
        tp.paint(canvas, Offset(dotAreaLeft + colW - tp.width - 2, dotAreaTop));
      }
    }
```

- [ ] **Step 3: Store column hit rects for tooltip detection**

Add a field to `OfficePainter`:

```dart
final List<Rect> kanbanColumnRects = [];
```

In `_drawKanbanBoard()`, after computing each column area, store the rect:

```dart
    kanbanColumnRects.clear();
    for (var col = 0; col < 3; col++) {
      kanbanColumnRects.add(Rect.fromLTWH(
        bx + col * colW, bodyY + headerH, colW, bodyH - headerH,
      ));
    }
```

- [ ] **Step 4: Add hover position + tooltip to the widget**

In `robot_office_widget.dart`, add state:

```dart
  Offset? _hoverPosition;
  String? _kanbanTooltip;
```

Wrap the `Stack` in a `MouseRegion`:

```dart
MouseRegion(
  onHover: (event) => _updateKanbanTooltip(event.localPosition),
  onExit: (_) => setState(() { _hoverPosition = null; _kanbanTooltip = null; }),
  child: Stack(/* existing stack */),
),
```

Add `_updateKanbanTooltip`:

```dart
  void _updateKanbanTooltip(Offset position) {
    // Map position to kanban column
    // This is approximate — the kanban board is at ~4% x, ~20% y
    final size = context.size;
    if (size == null) return;
    final bx = size.width * 0.04;
    final by = size.height * 0.20;
    final bw = size.width * 0.10;
    final bh = size.height * 0.18;

    if (!Rect.fromLTWH(bx, by, bw, bh).contains(position)) {
      if (_kanbanTooltip != null) setState(() { _kanbanTooltip = null; _hoverPosition = null; });
      return;
    }

    final colW = bw / 3;
    final col = ((position.dx - bx) / colW).floor().clamp(0, 2);
    final statuses = [['backlog'], ['in_progress'], ['done', 'verifying']][col];
    final titles = <String>[];
    for (final s in statuses) {
      titles.addAll(widget.kanbanTasks[s] ?? []);
    }

    final tooltip = titles.isEmpty ? null : titles.take(5).join('\n');
    if (tooltip != _kanbanTooltip) {
      setState(() { _kanbanTooltip = tooltip; _hoverPosition = position; });
    }
  }
```

In the `Stack`, add a `Tooltip` overlay when `_kanbanTooltip != null`:

```dart
if (_kanbanTooltip != null && _hoverPosition != null)
  Positioned(
    left: _hoverPosition!.dx + 10,
    top: _hoverPosition!.dy - 20,
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.black87,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        _kanbanTooltip!,
        style: const TextStyle(color: Colors.white, fontSize: 10),
      ),
    ),
  ),
```

- [ ] **Step 5: Pass kanban data through widget → painter**

Add `kanbanCounts` and `kanbanTasks` props to `RobotOfficeWidget`. Pass `kanbanCounts` to `OfficePainter` in the `build()` method. Also pass `kanbanTasks` to the widget state for tooltip use.

- [ ] **Step 6: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 7: Commit**

```bash
git add flutter_app/lib/widgets/robot_office/office_painter.dart flutter_app/lib/widgets/robot_office/robot_office_widget.dart
git commit -m "feat: real kanban dots + hover tooltips in Robot Office board (#84)"
```

---

### Task 5: System glow on Trinity robots + robot painter update

**Files:**
- Modify: `flutter_app/lib/widgets/robot_office/robot_office_painter.dart:58-206`

- [ ] **Step 1: Add system glow to Trinity robots**

In `_drawRobot()`, after drawing the body but before the head, check `r.isSystem` and draw a subtle glow:

```dart
    // System robot glow (PGE Trinity distinction)
    if (r.isSystem) {
      final glowPaint = Paint()
        ..color = r.color.withValues(alpha: 0.15 + 0.05 * sin(elapsed * 2))
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8);
      canvas.drawCircle(Offset(0, -12 * scale), 18 * scale, glowPaint);
    }
```

This requires `elapsed` to be passed to `_drawRobot`. Add it as a parameter or use the existing `elapsed` field from the painter.

- [ ] **Step 2: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 3: Commit**

```bash
git add flutter_app/lib/widgets/robot_office/robot_office_painter.dart
git commit -m "feat: system glow on PGE Trinity robots (#84)"
```

---

### Task 6: Final wiring + integration test

**Files:**
- Modify: `flutter_app/lib/screens/dashboard_screen.dart`
- Modify: `flutter_app/lib/widgets/robot_office/robot_office_widget.dart`

- [ ] **Step 1: Pass kanban data from provider through dashboard**

In the `Consumer<RobotOfficeProvider>` in dashboard_screen.dart, add:

```dart
    kanbanCounts: ro.kanbanCounts,
    kanbanTasks: ro.kanbanTasks,
```

- [ ] **Step 2: Forward kanbanCounts to OfficePainter in robot_office_widget build()**

In the `build()` method where `bg.OfficePainter` is created, add:

```dart
    kanbanCounts: widget.kanbanCounts,
    kanbanTasks: widget.kanbanTasks,
```

- [ ] **Step 3: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 4: Run Python tests (no changes but verify nothing broke)**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/ tests/ && python -m pytest tests/ -x -q --tb=short --ignore=tests/test_channels/test_voice_ws_bridge.py`
Expected: All pass

- [ ] **Step 5: Final commit**

```bash
git add -A flutter_app/lib/
git commit -m "feat: complete Robot Office live wiring — real agents, metrics, kanban (#84)

Closes #84"
```

- [ ] **Step 6: Comment on issue and push**

Comment on #84 explaining the full implementation, then push.
