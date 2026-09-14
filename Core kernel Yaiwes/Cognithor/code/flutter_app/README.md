# Cognithor Flutter UI

Cross-platform web UI for Cognithor Agent OS, built with Flutter 3.41.

## Features

- **Sci-Fi Command Center** aesthetic with Cyberpunk-Neon theme
- **Chat** with markdown rendering, file upload, voice mode, hacker terminal mode
- **Dashboard** with Robot Office visualization, radial gauges, event ticker
- **Administration** hub with 12 sub-screens (Config, Agents, Models, Security, etc.)
- **Skills Marketplace** with install/uninstall
- **Identity** management
- **Real-time** WebSocket communication with backend
- **Responsive** layout with morphing sidebar
- **Internationalization** (EN, DE, ZH, AR)

## Prerequisites

- Flutter SDK 3.41+
- Backend running at `http://localhost:8741`

## Development

```bash
cd flutter_app
flutter pub get
flutter run -d chrome    # Development with hot reload
```

## Build

```bash
flutter build web --release
```

The built files go to `build/web/` and are automatically served by the Cognithor backend.

## Architecture

- **State Management**: Provider (12+ providers)
- **Navigation**: AnimatedIndexedStack with morphing sidebar
- **WebSocket**: Real-time chat, tool events, pipeline updates (21 message types)
- **Theme**: Centralized in `lib/theme/jarvis_theme.dart` -- 5 section colors, dark/light modes
- **Widgets**: GlassPanel (static panels), NeonCard (list items), NeonGlow (action buttons)

## Project Structure

```
lib/
├── l10n/           # Internationalization (ARB files + generated)
├── providers/      # State management (12+ ChangeNotifiers)
├── screens/        # Top-level screens (Chat, Dashboard, Admin, etc.)
│   └── config/     # 18 config sub-pages
├── services/       # API client, WebSocket service
├── theme/          # Centralized theme (colors, spacing, typography)
└── widgets/        # Reusable components
    ├── chat/       # Chat-specific (hacker view, matrix rain, context panel)
    ├── form/       # Form widgets (text, number, slider, toggle, etc.)
    ├── observe/    # Observe panel (agent log, kanban, DAG)
    └── robot_office/ # Robot Office animation (8 robots, pets, office)
```

## Key Files

| File | Purpose |
|------|---------|
| `lib/main.dart` | App entry, MultiProvider setup |
| `lib/screens/main_shell.dart` | Navigation shell with sidebar |
| `lib/providers/chat_provider.dart` | Chat state, WebSocket listeners |
| `lib/services/websocket_service.dart` | WebSocket connection, auth, heartbeat |
| `lib/theme/jarvis_theme.dart` | Complete design system |
