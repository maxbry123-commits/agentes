# Chat & Session Management Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix chat session UX — auto-new-session on inactivity, project folders, incognito mode, session export, full-text search, GDPR retention enforcement, and configurable history limits.

**Architecture:** Seven independent features built on the existing SessionStore (SQLite) + Gateway + Flutter app. Each feature adds a config field, backend logic, API endpoint, and Flutter UI. All changes are backwards-compatible — no DB migrations needed (folder column already exists).

**Tech Stack:** Python 3.13 (asyncio), SQLite WAL, FastAPI, Flutter/Dart, pytest (asyncio_mode=auto)

---

## File Map

| File | Changes | Responsibility |
|------|---------|----------------|
| `src/jarvis/config.py` | Modify | Add `SessionConfig` with timeout, history limit, incognito defaults |
| `src/jarvis/gateway/session_store.py` | Modify | Auto-session logic, search, export, incognito flag |
| `src/jarvis/gateway/gateway.py` | Modify | Wire auto-session, incognito context skip, GDPR cron |
| `src/jarvis/core/context_pipeline.py` | Modify | Respect incognito flag (skip enrichment) |
| `src/jarvis/channels/config_routes.py` | Modify | New API endpoints (export, search, incognito) |
| `src/jarvis/security/gdpr.py` | No changes | Already complete, just needs wiring |
| `flutter_app/lib/providers/sessions_provider.dart` | Modify | Auto-session, projects UI, search, export |
| `flutter_app/lib/providers/chat_provider.dart` | Modify | Incognito indicator |
| `flutter_app/lib/services/api_client.dart` | Modify | New API methods |
| `flutter_app/lib/services/websocket_service.dart` | Modify | Incognito flag in auth |
| `flutter_app/lib/screens/chat_page.dart` | Modify | Incognito badge, project drawer |
| `tests/test_session_management/` | Create | All new tests |

---

## Task 1: Auto-New-Session After Inactivity

When the app reconnects and the last session is older than a configurable timeout, automatically create a fresh session instead of resuming the stale one.

**Files:**
- Modify: `src/jarvis/config.py`
- Modify: `src/jarvis/gateway/session_store.py`
- Modify: `src/jarvis/channels/config_routes.py`
- Modify: `flutter_app/lib/providers/sessions_provider.dart`
- Modify: `flutter_app/lib/services/api_client.dart`
- Test: `tests/test_session_management/test_auto_session.py`

### Backend

- [ ] **Step 1: Write failing test for SessionConfig**

```python
# tests/test_session_management/test_auto_session.py
import pytest
from jarvis.config import JarvisConfig

def test_session_config_has_inactivity_timeout():
    config = JarvisConfig()
    assert hasattr(config, "session")
    assert config.session.inactivity_timeout_minutes == 30
    assert config.session.chat_history_limit == 100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_session_management/test_auto_session.py::test_session_config_has_inactivity_timeout -v`
Expected: FAIL — `AttributeError: 'JarvisConfig' object has no attribute 'session'`

- [ ] **Step 3: Add SessionConfig to config.py**

In `src/jarvis/config.py`, add after `ContextPipelineConfig`:

```python
@dataclass
class SessionConfig:
    """Session lifecycle settings."""
    inactivity_timeout_minutes: int = 30
    chat_history_limit: int = 100
```

And in `JarvisConfig.__init__()`, add:
```python
self.session = SessionConfig()
```

Wire YAML loading: in `_load_from_yaml()`, add:
```python
if "session" in data:
    s = data["session"]
    self.session.inactivity_timeout_minutes = s.get(
        "inactivity_timeout_minutes", self.session.inactivity_timeout_minutes
    )
    self.session.chat_history_limit = s.get(
        "chat_history_limit", self.session.chat_history_limit
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_session_management/test_auto_session.py::test_session_config_has_inactivity_timeout -v`
Expected: PASS

- [ ] **Step 5: Write failing test for should_create_new_session**

```python
# tests/test_session_management/test_auto_session.py
from datetime import datetime, timedelta, UTC

def test_should_create_new_session_stale(tmp_path):
    from jarvis.gateway.session_store import SessionStore
    from jarvis.models import SessionContext

    store = SessionStore(tmp_path / "sessions.db")
    # Create a session that was active 2 hours ago
    old_session = SessionContext(
        session_id="old123",
        user_id="web_user",
        channel="webui",
        agent_name="jarvis",
    )
    old_session.last_activity = datetime.now(tz=UTC) - timedelta(hours=2)
    store.save_session(old_session)

    assert store.should_create_new_session(
        channel="webui",
        user_id="web_user",
        inactivity_timeout_minutes=30,
    ) is True

def test_should_create_new_session_recent(tmp_path):
    from jarvis.gateway.session_store import SessionStore
    from jarvis.models import SessionContext

    store = SessionStore(tmp_path / "sessions.db")
    recent = SessionContext(
        session_id="new456",
        user_id="web_user",
        channel="webui",
        agent_name="jarvis",
    )
    recent.last_activity = datetime.now(tz=UTC) - timedelta(minutes=5)
    store.save_session(recent)

    assert store.should_create_new_session(
        channel="webui",
        user_id="web_user",
        inactivity_timeout_minutes=30,
    ) is False
```

- [ ] **Step 6: Implement should_create_new_session in SessionStore**

In `src/jarvis/gateway/session_store.py`, add method:

```python
def should_create_new_session(
    self,
    channel: str,
    user_id: str,
    inactivity_timeout_minutes: int = 30,
    agent_id: str = "jarvis",
) -> bool:
    """Check if the most recent session is too old to resume."""
    row = self.conn.execute(
        """
        SELECT last_activity FROM sessions
        WHERE channel = ? AND user_id = ? AND agent_id = ? AND active = 1
        ORDER BY last_activity DESC LIMIT 1
        """,
        (channel, user_id, agent_id),
    ).fetchone()
    if row is None:
        return True  # No session exists
    last = datetime.fromtimestamp(row["last_activity"], tz=UTC)
    age = datetime.now(tz=UTC) - last
    return age.total_seconds() > inactivity_timeout_minutes * 60
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/test_session_management/test_auto_session.py -v`
Expected: ALL PASS

- [ ] **Step 8: Add API endpoint**

In `src/jarvis/channels/config_routes.py`, inside `_register_session_routes()`, add:

```python
@app.get("/api/v1/sessions/should-new", dependencies=deps)
async def should_new_session(
    channel: str = "webui",
    timeout_minutes: int = 30,
) -> dict[str, Any]:
    """Check if client should start a new session."""
    store = _get_session_store()
    if not store:
        return {"should_new": True}
    should_new = store.should_create_new_session(
        channel=channel,
        user_id="web_user",
        inactivity_timeout_minutes=timeout_minutes,
    )
    return {"should_new": should_new}
```

- [ ] **Step 9: Commit backend**

```bash
git add src/jarvis/config.py src/jarvis/gateway/session_store.py \
        src/jarvis/channels/config_routes.py \
        tests/test_session_management/
git commit -m "feat: auto-new-session — backend logic + API endpoint

Adds SessionConfig with inactivity_timeout_minutes (default 30).
SessionStore.should_create_new_session() checks if the most recent
session is too old to resume. GET /api/v1/sessions/should-new exposes
this to the Flutter app."
```

### Frontend

- [ ] **Step 10: Add API method in api_client.dart**

In `flutter_app/lib/services/api_client.dart`, add:

```dart
Future<bool> shouldNewSession({int timeoutMinutes = 30}) async {
  final data = await get(
    '/api/v1/sessions/should-new?timeout_minutes=$timeoutMinutes',
  );
  return data['should_new'] == true;
}
```

- [ ] **Step 11: Implement auto-session logic in SessionsProvider**

In `flutter_app/lib/providers/sessions_provider.dart`, add method:

```dart
/// Check if we should auto-create a new session on app open.
Future<String?> autoSessionOnStartup({int timeoutMinutes = 30}) async {
  if (_api == null) return null;
  try {
    final shouldNew = await _api!.shouldNewSession(
      timeoutMinutes: timeoutMinutes,
    );
    if (shouldNew) {
      return createNewSession();
    }
    // Resume most recent session
    await loadSessions();
    if (sessions.isNotEmpty) {
      final mostRecent = sessions.first;
      activeSessionId = mostRecent['id'] as String?;
      return activeSessionId;
    }
    return createNewSession();
  } catch (_) {
    return null;
  }
}
```

- [ ] **Step 12: Wire into app startup (chat_page.dart or splash_screen.dart)**

In the app's initial session resolution logic, call `autoSessionOnStartup()` instead of blindly resuming the last session.

- [ ] **Step 13: Commit frontend**

```bash
git add flutter_app/lib/
git commit -m "feat: auto-new-session — Flutter auto-creates fresh session after inactivity"
```

---

## Task 2: Project Folders (Group Sessions)

Promote the existing `folder` column to a full "Projects" feature with UI.

**Files:**
- Modify: `flutter_app/lib/providers/sessions_provider.dart`
- Modify: `flutter_app/lib/screens/chat_page.dart`
- Test: `tests/test_session_management/test_projects.py`

- [ ] **Step 1: Write failing test for project listing**

```python
# tests/test_session_management/test_projects.py
def test_list_sessions_by_folder(tmp_path):
    from jarvis.gateway.session_store import SessionStore
    from jarvis.models import SessionContext

    store = SessionStore(tmp_path / "sessions.db")
    for i, folder in enumerate(["work", "work", "personal"]):
        s = SessionContext(
            session_id=f"s{i}", user_id="web_user",
            channel="webui", agent_name="jarvis",
        )
        store.save_session(s)
        store.update_session_folder(f"s{i}", folder)

    folders = store.list_folders(channel="webui", user_id="web_user")
    assert "work" in folders
    assert "personal" in folders
    assert len(folders) == 2
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_session_management/test_projects.py -v`
Expected: PASS (folder support already exists in DB)

- [ ] **Step 3: Add filtered listing by folder**

In `src/jarvis/gateway/session_store.py`, add method:

```python
def list_sessions_by_folder(
    self,
    folder: str,
    channel: str = "webui",
    user_id: str = "web_user",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List sessions filtered by project/folder."""
    rows = self.conn.execute(
        """
        SELECT session_id, title, message_count, started_at,
               last_activity, folder
        FROM sessions
        WHERE channel = ? AND user_id = ? AND folder = ? AND active = 1
        ORDER BY last_activity DESC
        LIMIT ?
        """,
        (channel, user_id, folder, limit),
    ).fetchall()
    return [
        {
            "id": r["session_id"],
            "title": r["title"] or "",
            "message_count": r["message_count"],
            "started_at": r["started_at"],
            "last_activity": r["last_activity"],
            "folder": r["folder"] or "",
        }
        for r in rows
    ]
```

- [ ] **Step 4: Add API endpoint for filtered listing**

In `src/jarvis/channels/config_routes.py`:

```python
@app.get("/api/v1/sessions/by-folder/{folder}", dependencies=deps)
async def list_sessions_by_folder(folder: str, limit: int = 50) -> dict[str, Any]:
    store = _get_session_store()
    if not store:
        return {"sessions": []}
    sessions = store.list_sessions_by_folder(folder, limit=limit)
    return {"sessions": sessions}
```

- [ ] **Step 5: Write test for folder filtering**

```python
def test_list_sessions_by_folder_api(tmp_path):
    from jarvis.gateway.session_store import SessionStore
    from jarvis.models import SessionContext

    store = SessionStore(tmp_path / "sessions.db")
    for i, folder in enumerate(["work", "work", "personal"]):
        s = SessionContext(
            session_id=f"s{i}", user_id="web_user",
            channel="webui", agent_name="jarvis",
        )
        store.save_session(s)
        store.update_session_folder(f"s{i}", folder)

    work = store.list_sessions_by_folder("work")
    assert len(work) == 2
    personal = store.list_sessions_by_folder("personal")
    assert len(personal) == 1
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_session_management/test_projects.py -v`
Expected: ALL PASS

- [ ] **Step 7: Flutter — add project grouping in session sidebar**

In `flutter_app/lib/providers/sessions_provider.dart`, add:

```dart
/// Sessions grouped by folder/project.
Map<String, List<Map<String, dynamic>>> get sessionsByProject {
  final grouped = <String, List<Map<String, dynamic>>>{};
  for (final s in sessions) {
    final folder = (s['folder'] as String?) ?? '';
    final key = folder.isEmpty ? 'Allgemein' : folder;
    grouped.putIfAbsent(key, () => []).add(s);
  }
  return grouped;
}
```

In `api_client.dart`, add:

```dart
Future<Map<String, dynamic>> listSessionsByFolder(String folder, {int limit = 50}) async {
  return get('/api/v1/sessions/by-folder/$folder?limit=$limit');
}
```

- [ ] **Step 8: Build project drawer/sidebar UI**

In `chat_page.dart` session drawer, replace flat list with grouped `ExpansionTile` per project:

```dart
for (final entry in sessionsProvider.sessionsByProject.entries)
  ExpansionTile(
    title: Text(entry.key),
    initiallyExpanded: true,
    children: entry.value.map((s) => ListTile(
      title: Text(s['title'] ?? 'Neue Session'),
      onTap: () => _switchToSession(s['id']),
    )).toList(),
  ),
```

- [ ] **Step 9: Commit**

```bash
git add src/jarvis/gateway/session_store.py src/jarvis/channels/config_routes.py \
        flutter_app/lib/ tests/test_session_management/test_projects.py
git commit -m "feat: project folders — group sessions into projects with sidebar UI"
```

---

## Task 3: Incognito Mode

Sessions that skip memory enrichment and don't save to long-term memory.

**Files:**
- Modify: `src/jarvis/gateway/session_store.py` (DB migration: `incognito` column)
- Modify: `src/jarvis/gateway/gateway.py` (skip context pipeline + memory save)
- Modify: `src/jarvis/core/context_pipeline.py` (respect incognito)
- Modify: `src/jarvis/channels/config_routes.py` (new endpoint)
- Modify: `flutter_app/lib/providers/sessions_provider.dart`
- Modify: `flutter_app/lib/providers/chat_provider.dart`
- Test: `tests/test_session_management/test_incognito.py`

- [ ] **Step 1: Write failing test for incognito session creation**

```python
# tests/test_session_management/test_incognito.py
def test_create_incognito_session(tmp_path):
    from jarvis.gateway.session_store import SessionStore
    from jarvis.models import SessionContext

    store = SessionStore(tmp_path / "sessions.db")
    s = SessionContext(
        session_id="incog1", user_id="web_user",
        channel="webui", agent_name="jarvis",
    )
    s.incognito = True
    store.save_session(s)

    loaded = store.load_session("webui", "web_user")
    assert loaded is not None
    assert loaded.incognito is True
```

- [ ] **Step 2: Add incognito field to SessionContext**

In `src/jarvis/models.py` (or wherever `SessionContext` is defined), add:

```python
incognito: bool = False
```

- [ ] **Step 3: Add DB migration for incognito column**

In `session_store.py`, add migration 6:

```python
# Migration 6: incognito column
try:
    self.conn.execute(
        "ALTER TABLE sessions ADD COLUMN incognito INTEGER DEFAULT 0"
    )
    self.conn.commit()
except Exception:
    pass  # Column already exists
```

Update `save_session()` to persist incognito:
```python
# In the INSERT/UPDATE, add incognito field
```

Update `load_session()` to read incognito:
```python
# session.incognito = bool(row["incognito"]) if "incognito" in row.keys() else False
```

- [ ] **Step 4: Skip context pipeline for incognito sessions**

In `src/jarvis/gateway/gateway.py`, in the context enrichment section (~line 1223):

```python
# Skip context pipeline for incognito sessions
if session.incognito:
    log.info("incognito_mode_active", session=session.session_id[:8])
else:
    if self._context_pipeline:
        ctx = await self._context_pipeline.enrich(msg.text, wm)
```

- [ ] **Step 5: Skip memory save for incognito sessions**

In `gateway.py`, in `_persist_session()` (~line 2819):

```python
# Don't save chat history for incognito sessions
if session.incognito:
    # Still save session metadata (for list display) but not chat content
    if self._session_store:
        self._session_store.save_session(session)
    return
```

Also skip `save_to_memory` tool calls — in the executor or gatekeeper, block `save_to_memory` for incognito:

```python
# In the PGE loop, before executing tools:
if session.incognito and step.tool == "save_to_memory":
    log.info("incognito_memory_save_blocked", session=session.session_id[:8])
    continue
```

- [ ] **Step 6: Add API endpoint for incognito session creation**

In `config_routes.py`:

```python
@app.post("/api/v1/sessions/new-incognito", dependencies=deps)
async def create_incognito_session() -> dict[str, Any]:
    store = _get_session_store()
    if not store:
        return {"error": "Session store not available"}
    session_id = uuid4().hex[:16]
    session = SessionContext(
        session_id=session_id,
        user_id="web_user",
        channel="webui",
        agent_name="jarvis",
    )
    session.incognito = True
    store.save_session(session)
    return {"session_id": session_id, "incognito": True}
```

Also update `GET /api/v1/sessions/list` to include `incognito` field in response.

- [ ] **Step 7: Write comprehensive tests**

```python
def test_incognito_skips_context_pipeline():
    """Context pipeline must not run for incognito sessions."""
    # Mock ContextPipeline, verify enrich() not called
    ...

def test_incognito_blocks_memory_save():
    """save_to_memory tool must be blocked in incognito mode."""
    ...

def test_incognito_no_chat_history_persisted(tmp_path):
    """Chat messages must not be saved to DB for incognito sessions."""
    ...

def test_incognito_session_listed_with_flag(tmp_path):
    """API must return incognito flag in session list."""
    ...
```

- [ ] **Step 8: Run all tests**

Run: `pytest tests/test_session_management/test_incognito.py -v`
Expected: ALL PASS

- [ ] **Step 9: Flutter — incognito button + visual indicator**

In `api_client.dart`:
```dart
Future<Map<String, dynamic>> createIncognitoSession() async {
  return post('/api/v1/sessions/new-incognito', {});
}
```

In `sessions_provider.dart`:
```dart
Future<String?> createIncognitoSession() async {
  if (_api == null) return null;
  final data = await _api!.createIncognitoSession();
  if (data.containsKey('error')) return null;
  final id = data['session_id'] as String?;
  if (id != null) {
    activeSessionId = id;
    await loadSessions();
  }
  return id;
}
```

In `chat_page.dart`, add incognito badge:
```dart
if (isIncognito)
  Container(
    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    decoration: BoxDecoration(
      color: Colors.purple.withValues(alpha: 0.3),
      borderRadius: BorderRadius.circular(12),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.visibility_off, size: 14, color: Colors.purple),
        SizedBox(width: 4),
        Text('Inkognito', style: TextStyle(fontSize: 12, color: Colors.purple)),
      ],
    ),
  ),
```

- [ ] **Step 10: Commit**

```bash
git add src/ flutter_app/ tests/
git commit -m "feat: incognito mode — sessions without memory enrichment or persistence"
```

---

## Task 4: Session Export (JSON + PDF)

**Files:**
- Modify: `src/jarvis/gateway/session_store.py`
- Modify: `src/jarvis/channels/config_routes.py`
- Modify: `flutter_app/lib/services/api_client.dart`
- Test: `tests/test_session_management/test_export.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_session_management/test_export.py
def test_export_session_json(tmp_path):
    from jarvis.gateway.session_store import SessionStore
    from jarvis.models import SessionContext, Message, MessageRole
    from datetime import datetime, UTC

    store = SessionStore(tmp_path / "sessions.db")
    s = SessionContext(session_id="exp1", user_id="u", channel="webui", agent_name="jarvis")
    store.save_session(s)
    store.save_chat_history("exp1", [
        Message(role=MessageRole.USER, content="Hallo", timestamp=datetime.now(tz=UTC)),
        Message(role=MessageRole.ASSISTANT, content="Hi!", timestamp=datetime.now(tz=UTC)),
    ])

    export = store.export_session("exp1", format="json")
    assert export["session_id"] == "exp1"
    assert len(export["messages"]) == 2
    assert export["messages"][0]["role"] == "user"
```

- [ ] **Step 2: Implement export_session in SessionStore**

```python
def export_session(
    self,
    session_id: str,
    format: str = "json",
) -> dict[str, Any]:
    """Export a session with metadata and messages."""
    session_row = self.conn.execute(
        "SELECT * FROM sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if not session_row:
        return {"error": "Session not found"}

    messages = self.get_session_history(session_id, limit=10000)

    return {
        "session_id": session_id,
        "title": session_row["title"] or "",
        "folder": session_row["folder"] or "",
        "started_at": session_row["started_at"],
        "last_activity": session_row["last_activity"],
        "message_count": len(messages),
        "messages": messages,
        "exported_at": datetime.now(tz=UTC).isoformat(),
    }
```

- [ ] **Step 3: Add API endpoint**

```python
@app.get("/api/v1/sessions/{session_id}/export", dependencies=deps)
async def export_session(session_id: str, format: str = "json") -> dict[str, Any]:
    store = _get_session_store()
    if not store:
        return {"error": "Store not available"}
    return store.export_session(session_id, format=format)
```

- [ ] **Step 4: Run tests, commit**

Run: `pytest tests/test_session_management/test_export.py -v`

```bash
git add src/ tests/
git commit -m "feat: session export — download chat history as JSON"
```

- [ ] **Step 5: Flutter — export button + share**

In `api_client.dart`:
```dart
Future<Map<String, dynamic>> exportSession(String sessionId) async {
  return get('/api/v1/sessions/$sessionId/export');
}
```

Wire into session context menu (long-press on session in sidebar).

- [ ] **Step 6: Commit frontend**

```bash
git add flutter_app/
git commit -m "feat: session export — share/download chat as JSON from Flutter"
```

---

## Task 5: Full-Text Search Across Sessions

**Files:**
- Modify: `src/jarvis/gateway/session_store.py`
- Modify: `src/jarvis/channels/config_routes.py`
- Modify: `flutter_app/lib/services/api_client.dart`
- Modify: `flutter_app/lib/providers/sessions_provider.dart`
- Test: `tests/test_session_management/test_search.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_session_management/test_search.py
def test_search_chat_history(tmp_path):
    from jarvis.gateway.session_store import SessionStore
    from jarvis.models import SessionContext, Message, MessageRole
    from datetime import datetime, UTC

    store = SessionStore(tmp_path / "sessions.db")
    for sid in ["s1", "s2"]:
        s = SessionContext(session_id=sid, user_id="u", channel="webui", agent_name="jarvis")
        store.save_session(s)

    store.save_chat_history("s1", [
        Message(role=MessageRole.USER, content="Wie wird das Wetter?", timestamp=datetime.now(tz=UTC)),
        Message(role=MessageRole.ASSISTANT, content="Morgen wird es sonnig.", timestamp=datetime.now(tz=UTC)),
    ])
    store.save_chat_history("s2", [
        Message(role=MessageRole.USER, content="Schreibe einen Python-Script", timestamp=datetime.now(tz=UTC)),
    ])

    results = store.search_chat_history("Wetter")
    assert len(results) >= 1
    assert results[0]["session_id"] == "s1"
    assert "Wetter" in results[0]["content"]
```

- [ ] **Step 2: Implement search_chat_history**

```python
def search_chat_history(
    self,
    query: str,
    channel: str = "webui",
    user_id: str = "web_user",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Full-text search across all chat messages."""
    pattern = f"%{query}%"
    rows = self.conn.execute(
        """
        SELECT ch.session_id, ch.role, ch.content, ch.timestamp,
               s.title, s.folder
        FROM chat_history ch
        JOIN sessions s ON ch.session_id = s.session_id
        WHERE ch.content LIKE ?
          AND ch.role IN ('user', 'assistant')
          AND s.active = 1
          AND s.channel = ?
          AND s.user_id = ?
        ORDER BY ch.timestamp DESC
        LIMIT ?
        """,
        (pattern, channel, user_id, limit),
    ).fetchall()
    return [
        {
            "session_id": r["session_id"],
            "role": r["role"],
            "content": r["content"],
            "timestamp": r["timestamp"],
            "session_title": r["title"] or "",
            "folder": r["folder"] or "",
        }
        for r in rows
    ]
```

- [ ] **Step 3: Add API endpoint**

```python
@app.get("/api/v1/sessions/search", dependencies=deps)
async def search_sessions(q: str, limit: int = 20) -> dict[str, Any]:
    store = _get_session_store()
    if not store:
        return {"results": []}
    results = store.search_chat_history(q, limit=limit)
    return {"results": results, "query": q}
```

- [ ] **Step 4: Run tests, commit**

Run: `pytest tests/test_session_management/test_search.py -v`

```bash
git add src/ tests/
git commit -m "feat: full-text search across all chat sessions"
```

- [ ] **Step 5: Flutter — search bar + results**

In `api_client.dart`:
```dart
Future<Map<String, dynamic>> searchSessions(String query, {int limit = 20}) async {
  return get('/api/v1/sessions/search?q=${Uri.encodeComponent(query)}&limit=$limit');
}
```

In `sessions_provider.dart`:
```dart
List<Map<String, dynamic>> searchResults = [];

Future<void> searchChats(String query) async {
  if (_api == null || query.trim().isEmpty) {
    searchResults = [];
    notifyListeners();
    return;
  }
  final data = await _api!.searchSessions(query);
  searchResults = List<Map<String, dynamic>>.from(data['results'] ?? []);
  notifyListeners();
}
```

- [ ] **Step 6: Commit frontend**

```bash
git add flutter_app/
git commit -m "feat: chat search — search across all sessions from Flutter"
```

---

## Task 6: GDPR Retention Enforcement

Wire the existing `RetentionEnforcer` into the gateway's cron system.

**Files:**
- Modify: `src/jarvis/gateway/gateway.py`
- Modify: `src/jarvis/gateway/session_store.py`
- Test: `tests/test_session_management/test_retention.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_session_management/test_retention.py
def test_cleanup_old_sessions_called(tmp_path):
    from jarvis.gateway.session_store import SessionStore
    from jarvis.models import SessionContext
    from datetime import datetime, timedelta, UTC

    store = SessionStore(tmp_path / "sessions.db")
    old = SessionContext(session_id="old1", user_id="u", channel="webui", agent_name="jarvis")
    old.last_activity = datetime.now(tz=UTC) - timedelta(days=60)
    store.save_session(old)

    recent = SessionContext(session_id="new1", user_id="u", channel="webui", agent_name="jarvis")
    store.save_session(recent)

    cleaned = store.cleanup_old_sessions(max_age_days=30)
    assert cleaned == 1

    # Verify old session is deactivated
    sessions = store.list_sessions_for_channel("webui", "u")
    assert len(sessions) == 1
    assert sessions[0]["id"] == "new1"
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_session_management/test_retention.py -v`
Expected: PASS (cleanup_old_sessions already exists)

- [ ] **Step 3: Wire cleanup into gateway cron**

In `src/jarvis/gateway/gateway.py`, in the cron/heartbeat setup or in `_maybe_cleanup_sessions()`, ensure it actually runs:

```python
async def _run_retention_cleanup(self) -> None:
    """Periodic cleanup: deactivate old sessions, enforce GDPR retention."""
    if self._session_store:
        cleaned = self._session_store.cleanup_old_sessions(max_age_days=30)
        if cleaned:
            log.info("sessions_cleaned", count=cleaned)
        mapped = self._session_store.cleanup_channel_mappings(max_age_days=30)
        if mapped:
            log.info("channel_mappings_cleaned", count=mapped)
```

Register as a cron job in gateway init:
```python
# In gateway init, after cron engine setup:
self._cron_engine.add_job(
    self._run_retention_cleanup,
    "interval",
    hours=6,
    id="retention_cleanup",
)
```

- [ ] **Step 4: Run tests, commit**

```bash
git add src/jarvis/gateway/gateway.py tests/
git commit -m "feat: wire GDPR retention cleanup into gateway cron (6h interval)"
```

---

## Task 7: Configurable Chat History Limit

Replace hardcoded `limit=20` with `config.session.chat_history_limit`.

**Files:**
- Modify: `src/jarvis/gateway/gateway.py`
- Test: `tests/test_session_management/test_history_limit.py`

- [ ] **Step 1: Write test**

```python
# tests/test_session_management/test_history_limit.py
def test_history_limit_from_config():
    from jarvis.config import JarvisConfig
    config = JarvisConfig()
    assert config.session.chat_history_limit == 100
```

- [ ] **Step 2: Update gateway to use config**

In `src/jarvis/gateway/gateway.py`, in `_get_or_create_working_memory()` (~line 3577):

Replace:
```python
history = self._session_store.load_chat_history(
    session.session_id,
    limit=20,
)
```

With:
```python
history_limit = getattr(
    getattr(self._config, "session", None),
    "chat_history_limit", 100,
)
history = self._session_store.load_chat_history(
    session.session_id,
    limit=history_limit,
)
```

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/test_session_management/ -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/gateway/gateway.py tests/
git commit -m "feat: configurable chat history limit (default 100, was hardcoded 20)"
```

---

## Task 8: Integration Tests + Final Verification

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -x -q --tb=short 2>&1 | tail -20
```
Expected: ALL PASS, no regressions

- [ ] **Step 2: Manual smoke test**

1. Start Jarvis: `python -m jarvis --no-cli --api-host 0.0.0.0`
2. Open Flutter app on iPhone
3. Verify: New session auto-created (not resuming stale chat)
4. Send "Wie wird das Wetter?" → verify JSON plan (no permission asking)
5. Switch to old session → verify only user/assistant messages shown
6. Create incognito session → verify no memory context injected
7. Export session → verify JSON download
8. Search "Wetter" → verify cross-session results

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "test: integration tests for chat session management overhaul"
```

---

## Task 9: Documentation & Release

Covered in separate task #3 — update README, CHANGELOG, version bump.
