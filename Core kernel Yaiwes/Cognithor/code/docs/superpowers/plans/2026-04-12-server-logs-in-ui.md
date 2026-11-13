# Server Logs in Flutter UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hide the CMD console window and show live server events in a new "Live Logs" tab inside the MonitoringScreen.

**Architecture:** Two changes: (1) `cognithor.bat` uses `pythonw.exe` for invisible backend, (2) MonitoringScreen gets refactored from flat view to 3-tab layout (Dashboard, Events, Live Logs). Live Logs polls `/api/v1/monitoring/events` every 5s with severity filtering and auto-scroll.

**Tech Stack:** Flutter (Dart), Windows batch script

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `flutter_app/lib/widgets/monitoring/live_logs_tab.dart` | Live log viewer with polling, filtering, auto-scroll |
| Modify | `flutter_app/lib/screens/monitoring_screen.dart` | Refactor to TabBarView with 3 tabs |
| Modify | `C:\Users\ArtiCall\AppData\Local\Cognithor\cognithor.bat` | Use pythonw.exe for invisible backend |
| Modify | `installer/build_installer.py` | Generate launcher with pythonw.exe |

---

### Task 1: Hide CMD Window — cognithor.bat

**Files:**
- Modify: `C:\Users\ArtiCall\AppData\Local\Cognithor\cognithor.bat:50-51`
- Modify: `installer/build_installer.py:264`

- [ ] **Step 1: Update the installed cognithor.bat**

In `C:\Users\ArtiCall\AppData\Local\Cognithor\cognithor.bat`, change the `--ui` block (around line 50-51) from:

```batch
start "Cognithor Server" cmd /k ""%PYTHON%" -m cognithor --no-cli --api-port 8741"
```

to:

```batch
set "PYTHONW=%COGNITHOR_HOME%python\pythonw.exe"
if exist "%PYTHONW%" (
    start "" "%PYTHONW%" -m cognithor --no-cli --api-port 8741
) else (
    start "Cognithor Server" cmd /k ""%PYTHON%" -m cognithor --no-cli --api-port 8741"
)
```

- [ ] **Step 2: Update build_installer.py for future builds**

In `installer/build_installer.py`, find the line that generates the `--ui` launcher (around line 264). Change the generated batch script to include the same `pythonw.exe` logic with fallback.

- [ ] **Step 3: Test — kill Cognithor, restart via bat, verify no CMD window appears**

Run: `C:\Users\ArtiCall\AppData\Local\Cognithor\cognithor.bat --ui`
Expected: No visible console window. Browser opens after health check passes. `pythonw.exe` process visible in Task Manager.

- [ ] **Step 4: Commit**

```bash
git add installer/build_installer.py
git commit -m "feat(installer): use pythonw.exe for invisible backend in --ui mode (#108)"
```

---

### Task 2: Refactor MonitoringScreen to Tabs

**Files:**
- Modify: `flutter_app/lib/screens/monitoring_screen.dart`

- [ ] **Step 1: Read the current MonitoringScreen**

Read `flutter_app/lib/screens/monitoring_screen.dart` completely. It currently has:
- A `_MonitoringScreenState` with `_stats` (Map) and `_events` (List)
- A 10-second auto-refresh timer
- A flat layout: stats row at top, events list below
- Uses `ConnectionProvider` to get API client

- [ ] **Step 2: Refactor to TabBarView with 3 tabs**

Replace the existing flat layout with a `DefaultTabController` + `TabBar` + `TabBarView`. The existing content becomes the "Dashboard" tab. "Events" becomes the second tab (extracted from the existing events section). "Live Logs" is a placeholder for now (Task 3).

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:cognithor_ui/providers/connection_provider.dart';
import 'package:cognithor_ui/widgets/monitoring/live_logs_tab.dart';

class MonitoringScreen extends StatefulWidget {
  const MonitoringScreen({super.key});

  @override
  State<MonitoringScreen> createState() => _MonitoringScreenState();
}

class _MonitoringScreenState extends State<MonitoringScreen> {
  Map<String, dynamic> _stats = {};
  List<dynamic> _events = [];
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 10), (_) => _refresh());
    WidgetsBinding.instance.addPostFrameCallback((_) => _refresh());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    final conn = context.read<ConnectionProvider>();
    if (conn.state != JarvisConnectionState.connected) return;
    final api = conn.api;
    try {
      final results = await Future.wait([
        api.getMonitoringDashboard(),
        api.getMonitoringEvents(n: 50),
      ]);
      if (mounted) {
        setState(() {
          _stats = results[0];
          _events = (results[1]['events'] as List<dynamic>?) ?? [];
        });
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Monitoring'),
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: _refresh,
            ),
          ],
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.dashboard_outlined), text: 'Dashboard'),
              Tab(icon: Icon(Icons.event_note_outlined), text: 'Events'),
              Tab(icon: Icon(Icons.terminal_outlined), text: 'Live Logs'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _DashboardTab(stats: _stats),
            _EventsTab(events: _events),
            const LiveLogsTab(),
          ],
        ),
      ),
    );
  }
}
```

Extract the existing stats row into `_DashboardTab` and the existing events list into `_EventsTab` as private widgets in the same file. Keep the same visual design.

- [ ] **Step 3: Verify the refactored screen builds**

Run: `cd flutter_app && flutter build web --release 2>&1 | tail -3`
Expected: Build succeeds (LiveLogsTab can be a placeholder `Center(child: Text('Coming soon'))` for now)

- [ ] **Step 4: Commit**

```bash
git add flutter_app/lib/screens/monitoring_screen.dart
git commit -m "refactor(flutter): MonitoringScreen from flat view to 3-tab layout"
```

---

### Task 3: Implement LiveLogsTab Widget

**Files:**
- Create: `flutter_app/lib/widgets/monitoring/live_logs_tab.dart`
- Modify: `flutter_app/lib/screens/monitoring_screen.dart` (import)

- [ ] **Step 1: Create the LiveLogsTab widget**

```dart
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:cognithor_ui/providers/connection_provider.dart';

class LiveLogsTab extends StatefulWidget {
  const LiveLogsTab({super.key});

  @override
  State<LiveLogsTab> createState() => _LiveLogsTabState();
}

class _LiveLogsTabState extends State<LiveLogsTab> {
  final List<Map<String, dynamic>> _logs = [];
  final ScrollController _scrollCtrl = ScrollController();
  Timer? _pollTimer;
  String _filter = 'all'; // all, info, warning, error
  bool _autoScroll = true;
  int _newCount = 0;

  static const int _maxLogs = 500;
  static const Duration _pollInterval = Duration(seconds: 5);

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_onScroll);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _fetchInitial();
      _pollTimer = Timer.periodic(_pollInterval, (_) => _poll());
    });
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onScroll() {
    final atBottom = _scrollCtrl.position.pixels >=
        _scrollCtrl.position.maxScrollExtent - 50;
    if (atBottom && !_autoScroll) {
      setState(() {
        _autoScroll = true;
        _newCount = 0;
      });
    } else if (!atBottom && _autoScroll) {
      setState(() => _autoScroll = false);
    }
  }

  Future<void> _fetchInitial() async {
    final conn = context.read<ConnectionProvider>();
    if (conn.state != JarvisConnectionState.connected) return;
    try {
      final data = await conn.api.getMonitoringEvents(n: 100);
      final events = (data['events'] as List<dynamic>?) ?? [];
      if (mounted) {
        setState(() {
          _logs.clear();
          for (final e in events) {
            _logs.add(Map<String, dynamic>.from(e as Map));
          }
        });
        _scrollToBottom();
      }
    } catch (_) {}
  }

  Future<void> _poll() async {
    final conn = context.read<ConnectionProvider>();
    if (conn.state != JarvisConnectionState.connected) return;
    try {
      final data = await conn.api.getMonitoringEvents(n: 20);
      final events = (data['events'] as List<dynamic>?) ?? [];
      if (!mounted || events.isEmpty) return;

      final existingIds = _logs.map((l) => l['id'] ?? l['timestamp']).toSet();
      final newEvents = events
          .map((e) => Map<String, dynamic>.from(e as Map))
          .where((e) => !existingIds.contains(e['id'] ?? e['timestamp']))
          .toList();

      if (newEvents.isNotEmpty) {
        setState(() {
          _logs.addAll(newEvents);
          if (_logs.length > _maxLogs) {
            _logs.removeRange(0, _logs.length - _maxLogs);
          }
          if (!_autoScroll) {
            _newCount += newEvents.length;
          }
        });
        if (_autoScroll) _scrollToBottom();
      }
    } catch (_) {}
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  List<Map<String, dynamic>> get _filtered {
    if (_filter == 'all') return _logs;
    return _logs.where((l) {
      final sev = (l['severity'] as String? ?? 'info').toLowerCase();
      return sev == _filter;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final filtered = _filtered;

    return Column(
      children: [
        // Filter bar
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            children: [
              for (final f in ['all', 'info', 'warning', 'error'])
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(f[0].toUpperCase() + f.substring(1)),
                    selected: _filter == f,
                    onSelected: (_) => setState(() => _filter = f),
                  ),
                ),
              const Spacer(),
              TextButton.icon(
                onPressed: () => setState(() {
                  _logs.clear();
                  _newCount = 0;
                }),
                icon: const Icon(Icons.clear_all, size: 18),
                label: const Text('Clear'),
              ),
            ],
          ),
        ),
        // Log list
        Expanded(
          child: Stack(
            children: [
              filtered.isEmpty
                  ? Center(
                      child: Text(
                        'Keine Events',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurface
                              .withValues(alpha: 0.5),
                        ),
                      ),
                    )
                  : ListView.separated(
                      controller: _scrollCtrl,
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      itemCount: filtered.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final log = filtered[index];
                        return _LogEntry(log: log);
                      },
                    ),
              // "New events" button
              if (_newCount > 0 && !_autoScroll)
                Positioned(
                  bottom: 16,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        setState(() {
                          _autoScroll = true;
                          _newCount = 0;
                        });
                        _scrollToBottom();
                      },
                      icon: const Icon(Icons.arrow_downward, size: 16),
                      label: Text('Neue Events ($_newCount)'),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _LogEntry extends StatelessWidget {
  final Map<String, dynamic> log;
  const _LogEntry({required this.log});

  static const _severityColors = {
    'info': Colors.blue,
    'warning': Colors.orange,
    'error': Colors.red,
  };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final severity = (log['severity'] as String? ?? 'info').toLowerCase();
    final color = _severityColors[severity] ?? Colors.grey;
    final timestamp = log['timestamp'] as String? ?? '';
    final time = timestamp.length >= 19 ? timestamp.substring(11, 19) : timestamp;
    final action = log['action'] as String? ?? log['event'] as String? ?? '';
    final desc = log['description'] as String? ?? log['message'] as String? ?? '';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 70,
            child: Text(
              time,
              style: theme.textTheme.bodySmall?.copyWith(
                fontFamily: 'monospace',
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              severity.toUpperCase(),
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  action,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (desc.isNotEmpty)
                  Text(
                    desc,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 2: Add import in monitoring_screen.dart**

At the top of `monitoring_screen.dart`, add:
```dart
import 'package:cognithor_ui/widgets/monitoring/live_logs_tab.dart';
```

Make sure the `LiveLogsTab()` placeholder in Task 2's TabBarView is now using the real widget.

- [ ] **Step 3: Create the widgets/monitoring/ directory if needed**

```bash
mkdir -p flutter_app/lib/widgets/monitoring
```

- [ ] **Step 4: Build and verify**

Run: `cd flutter_app && flutter build web --release 2>&1 | tail -3`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
git add flutter_app/lib/widgets/monitoring/live_logs_tab.dart flutter_app/lib/screens/monitoring_screen.dart
git commit -m "feat(flutter): add Live Logs tab to MonitoringScreen (#108)"
```

---

### Task 4: Deploy and Close Issue

**Files:**
- No new files

- [ ] **Step 1: Copy Flutter build to installed Cognithor**

```bash
cp -r "D:/Jarvis/jarvis complete v20/flutter_app/build/web/"* "C:/Users/ArtiCall/AppData/Local/Cognithor/flutter_app/web/"
```

- [ ] **Step 2: Push to GitHub**

```bash
git push
```

- [ ] **Step 3: Comment and close #108**

Post comment on GitHub issue #108 with fix details and close.

- [ ] **Step 4: Verify manually**

- Restart Cognithor.exe
- Verify: No CMD window visible
- Open browser → localhost:8741
- Navigate to Monitoring → Live Logs tab
- Send a chat message
- Verify events appear in Live Logs with timestamp, severity badge, and description
- Test filter chips (All/Info/Warning/Error)
- Scroll up, verify "Neue Events" button appears
