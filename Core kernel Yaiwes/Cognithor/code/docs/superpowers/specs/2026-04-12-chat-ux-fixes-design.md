# Chat UX Fixes — Design Spec

**Date:** 2026-04-12
**Issues:** Chat header "Jarvis", white/gray chat background, approval keyboard shortcuts, agent delegation visibility

## 1. Chat Background Fix

The chat area shows a light gray/white background instead of the dark theme. The `ChatScreen` scaffold or body container is missing the dark theme background color.

**Fix:** Ensure the chat area uses `theme.scaffoldBackgroundColor` or `theme.colorScheme.surface`. Check `chat_screen.dart` for any hardcoded colors or missing theme references in the message list area.

## 2. Chat Header "Jarvis" → "Cognithor"

The header comes from `l.appTitle` which is hardcoded in localization files.

**Fix:** Change `appTitle` in all 4 localization files:
- `app_localizations_en.dart`: `'Jarvis'` → `'Cognithor'`
- `app_localizations_de.dart`: same
- `app_localizations_zh.dart`: same
- `app_localizations_ar.dart`: same

Also update the ARB source files if they exist (`lib/l10n/*.arb`).

## 3. Approval Keyboard Shortcuts

The `ApprovalDialog` widget exists and works. Add keyboard handling:
- **Enter** → approve
- **Escape** → reject

**Implementation:** Wrap the `ApprovalDialog` in a `Focus` widget with `autofocus: true` and an `onKeyEvent` handler that checks for `LogicalKeyboardKey.enter` and `LogicalKeyboardKey.escape`.

## 4. Agent Delegation Visibility

### Backend
Add WebSocket message type `agent_delegation` to `webui.py`. In `gateway.py` `execute_delegation()`, broadcast delegation event before executing:
```json
{
  "type": "status_update",
  "status": "delegation",
  "agent_from": "cognithor",
  "agent_to": "researcher",
  "task": "Recherchiere die neuesten LLM Releases"
}
```

Use existing `status_update` type rather than creating a new type — Flutter already handles `statusUpdate` via `_onStatusUpdate` in ChatProvider.

### Frontend
- `ChatProvider._onStatusUpdate()`: When status is "delegation", insert a system message showing the delegation
- Chat bubble: Show small agent badge (chip) on messages where `agentName` differs from default
