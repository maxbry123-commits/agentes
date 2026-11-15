# Server Logs in Flutter UI — Design Spec

**Issue:** #108
**Date:** 2026-04-12
**Status:** Approved

## Goal

Replace the visible CMD console window with an invisible backend process, and show live server events in a new "Live Logs" tab inside the existing MonitoringScreen in the Flutter UI.

## Backend Changes

### cognithor.bat (installer/build/cognithor.bat + AppData copy)

In `--ui` mode, replace `python.exe` with `pythonw.exe` so the backend runs without a console window:

```batch
REM Before:
start "Cognithor Server" cmd /k ""%PYTHON%" -m cognithor --no-cli --api-port 8741"

REM After:
set "PYTHONW=%COGNITHOR_HOME%python\pythonw.exe"
start "" "%PYTHONW%" -m cognithor --no-cli --api-port 8741
```

Fallback: if `pythonw.exe` doesn't exist, fall back to `python.exe` with the old `cmd /k` approach.

### build_installer.py

Same change in the generated launcher script for future builds.

### No new API endpoints

Existing endpoints are sufficient:
- `GET /api/v1/monitoring/events?n=100&severity=info` — paginated event history
- `GET /api/v1/monitoring/stream` — SSE live stream (already implemented)

## Flutter Changes

### MonitoringScreen (flutter_app/lib/screens/monitoring_screen.dart)

Currently has 2 tabs. Add a 3rd tab:

```
[Metrics] [Events] [Live Logs]
```

### New Widget: LiveLogsTab

**Location:** `flutter_app/lib/widgets/monitoring/live_logs_tab.dart`

**Data source:** Polls `GET /api/v1/monitoring/events?n=50` every 5 seconds. Appends new events (deduplicates by event ID or timestamp). Initial load fetches last 100 events.

**UI layout:**
```
┌──────────────────────────────────────────────┐
│ [All] [Info] [Warning] [Error]    [Clear]    │  ← Filter chips
├──────────────────────────────────────────────┤
│ 22:15:03  INFO   tool_executed               │
│           web_search completed (1.2s)        │
│ 22:15:05  INFO   message_received            │
│           User: "Was ist das Wetter?"        │
│ 22:15:08  WARN   model_fallback              │
│           requested=qwen3.5:27b using=...    │
│ 22:15:12  ERROR  llm_error                   │
│           Ollama timeout after 30s           │
│                                              │
│              ↓ Neue Events (3)               │  ← Appears when scrolled up
└──────────────────────────────────────────────┘
```

**Event card design:**
- Left: Timestamp in `HH:MM:SS` format, monospace
- Center-left: Severity badge (colored chip: INFO=blue, WARNING=orange, ERROR=red)
- Center: Event name in bold, description below in lighter text
- Dense layout (no card borders, just dividers)

**Behavior:**
- Auto-scrolls to bottom when new events arrive (unless user has scrolled up)
- "Neue Events (N)" floating button appears when user is scrolled up and new events arrive
- Tapping the button scrolls to bottom
- Max 500 events in memory — oldest discarded when exceeded
- Filter chips toggle severity levels (multiple can be active)
- "Clear" button resets the in-memory list (does not affect backend)

**State management:** Local StatefulWidget state (no Provider needed — this is display-only, not shared).

### MonitoringScreen Tab Integration

Add `LiveLogsTab` as third tab:

```dart
TabBar(
  tabs: [
    Tab(icon: Icon(Icons.bar_chart), text: 'Metrics'),
    Tab(icon: Icon(Icons.event_note), text: 'Events'),
    Tab(icon: Icon(Icons.terminal), text: 'Live Logs'),  // NEW
  ],
)
```

## What This Does NOT Include

- No `pystray` system tray icon
- No raw log file streaming (structlog jsonl)
- No new WebSocket message types
- No new backend endpoints
- No new Python dependencies

## Testing

- Manual: Start Cognithor with `--ui`, verify no CMD window appears, open MonitoringScreen → Live Logs tab, send a chat message, verify events appear in real-time
- Verify filter chips work (toggle severity)
- Verify auto-scroll and "Neue Events" button behavior
- Verify the health polling (ConnectionGuard) still works when backend is invisible
