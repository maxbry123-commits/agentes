# Chat Branching — Full Conversation Tree Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace linear chat messages with a full conversation tree where every message can have multiple children (branches), navigable via inline `< 1/3 >` controls and an optional tree sidebar, with hybrid backend memory (active branch in RAM, inactive branches replay from SQLite).

**Architecture:** New `ConversationTree` class (Python backend + Dart frontend) manages nodes with `parentId`/`childIds`. The Gateway stores one WorkingMemory per active branch. Branch switches trigger a replay of the target branch's message history into a fresh WorkingMemory. Frontend renders only the "active path" (root→leaf), with branch navigators at fork points. Edit = automatic fork.

**Tech Stack:** Python 3.12+ (sqlite3, asyncio), Flutter/Dart (Provider), pytest

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/jarvis/core/conversation_tree.py` | ConversationTree: node CRUD, path computation, SQLite persistence |
| Modify | `src/jarvis/gateway/gateway.py` | Branch-aware WM management, branch_switch handling, fork on edit |
| Modify | `src/jarvis/__main__.py` | WebSocket branch_switch + branch_create message types |
| Modify | `src/jarvis/channels/config_routes.py` | REST endpoints: GET tree, POST branch, GET path |
| Create | `flutter_app/lib/models/chat_node.dart` | ChatNode + ConversationTree data models |
| Create | `flutter_app/lib/providers/tree_provider.dart` | Tree state management, active path, branch switching |
| Create | `flutter_app/lib/widgets/chat/branch_navigator.dart` | Inline < 1/3 > branch controls |
| Create | `flutter_app/lib/widgets/chat/tree_sidebar.dart` | Optional collapsible tree overview panel |
| Modify | `flutter_app/lib/providers/chat_provider.dart` | Replace versions with tree integration |
| Modify | `flutter_app/lib/screens/chat_screen.dart` | Tree-aware rendering, sidebar toggle |
| Create | `tests/unit/test_conversation_tree.py` | Backend tree tests |

---

### Task 1: ConversationTree Backend — Node Model + SQLite

**Files:**
- Create: `src/jarvis/core/conversation_tree.py`
- Create: `tests/unit/test_conversation_tree.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_conversation_tree.py`:

```python
"""Tests for ConversationTree — node CRUD, path computation, branching."""

import pytest
from pathlib import Path


class TestConversationTree:

    @pytest.fixture
    def tree(self, tmp_path):
        from jarvis.core.conversation_tree import ConversationTree
        return ConversationTree(db_path=tmp_path / "tree.db")

    def test_create_conversation(self, tree):
        conv_id = tree.create_conversation()
        assert conv_id.startswith("conv_")

    def test_add_root_node(self, tree):
        conv_id = tree.create_conversation()
        node_id = tree.add_node(conv_id, role="user", text="Hello")
        assert node_id.startswith("node_")
        node = tree.get_node(node_id)
        assert node is not None
        assert node["role"] == "user"
        assert node["text"] == "Hello"
        assert node["parent_id"] is None

    def test_add_child_node(self, tree):
        conv_id = tree.create_conversation()
        parent = tree.add_node(conv_id, role="user", text="Hello")
        child = tree.add_node(conv_id, role="assistant", text="Hi!", parent_id=parent)
        node = tree.get_node(child)
        assert node["parent_id"] == parent

    def test_get_children(self, tree):
        conv_id = tree.create_conversation()
        parent = tree.add_node(conv_id, role="user", text="Hello")
        c1 = tree.add_node(conv_id, role="assistant", text="Hi!", parent_id=parent)
        c2 = tree.add_node(conv_id, role="assistant", text="Hey!", parent_id=parent)
        children = tree.get_children(parent)
        assert len(children) == 2
        assert {c["id"] for c in children} == {c1, c2}

    def test_get_path_to_root(self, tree):
        conv_id = tree.create_conversation()
        n1 = tree.add_node(conv_id, role="user", text="A")
        n2 = tree.add_node(conv_id, role="assistant", text="B", parent_id=n1)
        n3 = tree.add_node(conv_id, role="user", text="C", parent_id=n2)
        path = tree.get_path_to_root(n3)
        assert [p["id"] for p in path] == [n1, n2, n3]

    def test_fork_creates_sibling(self, tree):
        conv_id = tree.create_conversation()
        n1 = tree.add_node(conv_id, role="user", text="Hello")
        n2 = tree.add_node(conv_id, role="assistant", text="Hi!", parent_id=n1)
        # Fork: add another child to n1 (sibling of n2)
        n3 = tree.add_node(conv_id, role="user", text="Hola", parent_id=n1)
        children = tree.get_children(n1)
        assert len(children) == 2

    def test_get_branch_index(self, tree):
        conv_id = tree.create_conversation()
        parent = tree.add_node(conv_id, role="user", text="Root")
        c1 = tree.add_node(conv_id, role="assistant", text="A", parent_id=parent)
        c2 = tree.add_node(conv_id, role="assistant", text="B", parent_id=parent)
        assert tree.get_branch_index(c1) == 0
        assert tree.get_branch_index(c2) == 1

    def test_get_active_path(self, tree):
        conv_id = tree.create_conversation()
        n1 = tree.add_node(conv_id, role="user", text="A")
        n2 = tree.add_node(conv_id, role="assistant", text="B", parent_id=n1)
        n3 = tree.add_node(conv_id, role="user", text="C", parent_id=n2)
        tree.set_active_leaf(conv_id, n3)
        path = tree.get_active_path(conv_id)
        assert len(path) == 3
        assert path[0]["text"] == "A"
        assert path[2]["text"] == "C"

    def test_get_fork_points(self, tree):
        conv_id = tree.create_conversation()
        n1 = tree.add_node(conv_id, role="user", text="Root")
        n2 = tree.add_node(conv_id, role="assistant", text="A", parent_id=n1)
        n3 = tree.add_node(conv_id, role="assistant", text="B", parent_id=n1)
        forks = tree.get_fork_points(conv_id)
        assert n1 in forks
        assert forks[n1] == 2

    def test_get_tree_structure(self, tree):
        conv_id = tree.create_conversation()
        n1 = tree.add_node(conv_id, role="user", text="Root")
        n2 = tree.add_node(conv_id, role="assistant", text="A", parent_id=n1)
        structure = tree.get_tree_structure(conv_id)
        assert structure["conversation_id"] == conv_id
        assert len(structure["nodes"]) == 2

    def test_conversation_not_found(self, tree):
        path = tree.get_active_path("nonexistent")
        assert path == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_conversation_tree.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement ConversationTree**

Create `src/jarvis/core/conversation_tree.py`:

```python
"""Conversation Tree — full branching chat history.

Each message is a node with parentId/childIds. Conversations are trees,
not linear lists. Supports forking, path computation, and SQLite persistence.
"""

from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.utils.logging import get_logger

log = get_logger(__name__)

__all__ = ["ConversationTree"]

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT DEFAULT '',
    active_leaf_id TEXT,
    created_at REAL NOT NULL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS chat_nodes (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    parent_id TEXT,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    branch_index INTEGER DEFAULT 0,
    agent_name TEXT DEFAULT 'jarvis',
    model_used TEXT DEFAULT '',
    duration_ms INTEGER DEFAULT 0,
    created_at REAL NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
CREATE INDEX IF NOT EXISTS idx_nodes_conv ON chat_nodes(conversation_id);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON chat_nodes(parent_id);
"""


class ConversationTree:
    """SQLite-backed conversation tree with branching support."""

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ── Conversations ──────────────────────────────────────────────

    def create_conversation(self, title: str = "") -> str:
        """Create a new conversation. Returns conversation ID."""
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, created_at) VALUES (?,?,?)",
                (conv_id, title, time.time()),
            )
        return conv_id

    def set_active_leaf(self, conversation_id: str, node_id: str) -> None:
        """Set the active leaf node for a conversation."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE conversations SET active_leaf_id=?, updated_at=? WHERE id=?",
                (node_id, time.time(), conversation_id),
            )

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        """Get conversation metadata."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id=?", (conversation_id,)
            ).fetchone()
        return dict(row) if row else None

    # ── Nodes ──────────────────────────────────────────────────────

    def add_node(
        self,
        conversation_id: str,
        role: str,
        text: str,
        parent_id: str | None = None,
        agent_name: str = "jarvis",
        model_used: str = "",
        duration_ms: int = 0,
    ) -> str:
        """Add a message node to the tree. Returns node ID."""
        node_id = f"node_{uuid.uuid4().hex[:12]}"

        # Determine branch_index (position among siblings)
        branch_index = 0
        if parent_id:
            with self._conn() as conn:
                count = conn.execute(
                    "SELECT COUNT(*) FROM chat_nodes WHERE parent_id=?",
                    (parent_id,),
                ).fetchone()[0]
                branch_index = count  # 0-based, next available

        with self._conn() as conn:
            conn.execute(
                "INSERT INTO chat_nodes "
                "(id, conversation_id, parent_id, role, text, branch_index, "
                " agent_name, model_used, duration_ms, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (node_id, conversation_id, parent_id, role, text,
                 branch_index, agent_name, model_used, duration_ms,
                 time.time()),
            )

        # Update conversation active leaf
        self.set_active_leaf(conversation_id, node_id)

        return node_id

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get a single node by ID."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM chat_nodes WHERE id=?", (node_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_children(self, node_id: str) -> list[dict[str, Any]]:
        """Get all children of a node, ordered by branch_index."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_nodes WHERE parent_id=? ORDER BY branch_index",
                (node_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_branch_index(self, node_id: str) -> int:
        """Get the branch index of a node among its siblings."""
        node = self.get_node(node_id)
        if not node:
            return 0
        return node.get("branch_index", 0)

    # ── Path Computation ──────────────────────────────────────────

    def get_path_to_root(self, node_id: str) -> list[dict[str, Any]]:
        """Get the path from root to this node (inclusive, ordered root→node)."""
        path = []
        current_id: str | None = node_id
        with self._conn() as conn:
            while current_id:
                row = conn.execute(
                    "SELECT * FROM chat_nodes WHERE id=?", (current_id,)
                ).fetchone()
                if not row:
                    break
                path.append(dict(row))
                current_id = row["parent_id"]
        path.reverse()
        return path

    def get_active_path(self, conversation_id: str) -> list[dict[str, Any]]:
        """Get the currently active path (root to active leaf)."""
        conv = self.get_conversation(conversation_id)
        if not conv or not conv.get("active_leaf_id"):
            return []
        return self.get_path_to_root(conv["active_leaf_id"])

    # ── Fork Points ───────────────────────────────────────────────

    def get_fork_points(self, conversation_id: str) -> dict[str, int]:
        """Get all nodes that have multiple children (fork points).

        Returns: {node_id: child_count} for nodes with 2+ children.
        """
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT parent_id, COUNT(*) as cnt FROM chat_nodes "
                "WHERE conversation_id=? AND parent_id IS NOT NULL "
                "GROUP BY parent_id HAVING cnt > 1",
                (conversation_id,),
            ).fetchall()
        return {r["parent_id"]: r["cnt"] for r in rows}

    # ── Tree Structure ────────────────────────────────────────────

    def get_tree_structure(self, conversation_id: str) -> dict[str, Any]:
        """Get the full tree structure for visualization."""
        with self._conn() as conn:
            nodes = conn.execute(
                "SELECT * FROM chat_nodes WHERE conversation_id=? "
                "ORDER BY created_at",
                (conversation_id,),
            ).fetchall()
        conv = self.get_conversation(conversation_id)
        return {
            "conversation_id": conversation_id,
            "active_leaf_id": conv.get("active_leaf_id") if conv else None,
            "nodes": [dict(n) for n in nodes],
            "fork_points": self.get_fork_points(conversation_id),
        }

    # ── Utility ───────────────────────────────────────────────────

    def get_messages_for_replay(
        self, conversation_id: str, leaf_id: str
    ) -> list[dict[str, Any]]:
        """Get ordered messages from root to leaf for WM replay.

        Returns only role + text, suitable for rebuilding WorkingMemory.
        """
        path = self.get_path_to_root(leaf_id)
        return [
            {"role": n["role"], "text": n["text"], "agent_name": n.get("agent_name", "")}
            for n in path
        ]
```

- [ ] **Step 4: Run tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_conversation_tree.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/core/conversation_tree.py tests/unit/test_conversation_tree.py
git commit -m "feat: ConversationTree with node CRUD, path computation, fork detection, SQLite persistence"
```

---

### Task 2: Gateway Branch-Aware Session Management

**Files:**
- Modify: `src/jarvis/gateway/gateway.py`

- [ ] **Step 1: Initialize ConversationTree in gateway startup**

Near the CorrectionMemory initialization, add:

```python
        # Conversation Tree (Chat Branching)
        try:
            from jarvis.core.conversation_tree import ConversationTree
            self._conversation_tree = ConversationTree(
                db_path=self._config.jarvis_home / "conversations.db"
            )
            log.info("conversation_tree_initialized")
        except Exception:
            log.debug("conversation_tree_init_failed", exc_info=True)
            self._conversation_tree = None
```

- [ ] **Step 2: Add branch_switch handler method**

Add a method to the Gateway class:

```python
    async def switch_branch(
        self, conversation_id: str, leaf_id: str, session: SessionContext
    ) -> WorkingMemory:
        """Switch to a different branch by replaying its message history.

        1. Get message path from root to leaf_id
        2. Create fresh WorkingMemory
        3. Load messages into WM chat_history
        4. Update active leaf in ConversationTree
        """
        if not self._conversation_tree:
            raise RuntimeError("ConversationTree not initialized")

        messages = self._conversation_tree.get_messages_for_replay(
            conversation_id, leaf_id
        )

        # Create fresh WM with replayed history
        wm = WorkingMemory(
            session_id=session.session_id,
            max_tokens=getattr(self._config.planner, "context_window", 32768),
        )

        # Load core memory
        core_path = self._config.core_memory_path
        if core_path.exists():
            wm.core_memory_text = core_path.read_text(encoding="utf-8")

        # Replay messages into chat history
        for msg_data in messages:
            role = MessageRole.USER if msg_data["role"] == "user" else MessageRole.ASSISTANT
            wm.add_message(Message(
                role=role,
                content=msg_data["text"],
                channel="webui",
            ))

        # Update active leaf
        self._conversation_tree.set_active_leaf(conversation_id, leaf_id)

        # Replace working memory for this session
        self._working_memories[session.session_id] = wm

        log.info(
            "branch_switched",
            conversation=conversation_id[:12],
            leaf=leaf_id[:12],
            messages=len(messages),
        )
        return wm
```

- [ ] **Step 3: Store nodes when messages are sent/received**

In `_run_pge_loop`, after the user message is processed and after the assistant response is finalized, add node storage. Find the point where the final response is set. Add a helper that stores nodes:

```python
        # Store user message as tree node
        if (
            hasattr(self, "_conversation_tree")
            and self._conversation_tree
            and hasattr(session, "conversation_id")
            and session.conversation_id
        ):
            _user_node_id = self._conversation_tree.add_node(
                session.conversation_id,
                role="user",
                text=msg.text,
                parent_id=getattr(session, "active_leaf_id", None),
            )
            session.active_leaf_id = _user_node_id
```

And after the assistant response:

```python
        # Store assistant response as tree node
        if (
            hasattr(self, "_conversation_tree")
            and self._conversation_tree
            and hasattr(session, "conversation_id")
            and session.conversation_id
            and final_response
        ):
            _asst_node_id = self._conversation_tree.add_node(
                session.conversation_id,
                role="assistant",
                text=final_response,
                parent_id=getattr(session, "active_leaf_id", None),
                agent_name=agent_name,
            )
            session.active_leaf_id = _asst_node_id
```

- [ ] **Step 4: Verify syntax**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -c "from jarvis.gateway.gateway import Gateway; print('OK')"`

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/gateway/gateway.py
git commit -m "feat: branch-aware gateway with ConversationTree node storage + switch_branch replay"
```

---

### Task 3: WebSocket Branch Messages + REST API

**Files:**
- Modify: `src/jarvis/__main__.py`
- Modify: `src/jarvis/channels/config_routes.py`

- [ ] **Step 1: Add WebSocket handlers for branch_switch**

In `__main__.py`, in the WebSocket message handler (where `feedback` type is handled), add:

```python
elif msg_type == "branch_switch":
    conv_id = data.get("conversation_id", "")
    leaf_id = data.get("leaf_id", "")
    if conv_id and leaf_id and gateway:
        try:
            session = gateway._get_or_create_session("webui", user_id, "jarvis")
            wm = await gateway.switch_branch(conv_id, leaf_id, session)
            await ws.send_json({
                "type": "branch_switched",
                "conversation_id": conv_id,
                "leaf_id": leaf_id,
                "message_count": len(wm.chat_history),
            })
        except Exception as exc:
            await ws.send_json({
                "type": "error",
                "text": f"Branch switch failed: {exc}",
            })
```

- [ ] **Step 2: Add REST endpoints**

In `config_routes.py`, add:

```python
    @app.get("/api/v1/chat/tree/{conversation_id}", dependencies=deps)
    async def get_chat_tree(conversation_id: str) -> dict[str, Any]:
        """Get full conversation tree structure."""
        tree = getattr(gateway, "_conversation_tree", None)
        if not tree:
            return {"error": "Conversation tree not available"}
        return tree.get_tree_structure(conversation_id)

    @app.get("/api/v1/chat/path/{conversation_id}/{leaf_id}", dependencies=deps)
    async def get_chat_path(conversation_id: str, leaf_id: str) -> dict[str, Any]:
        """Get active path from root to a specific leaf."""
        tree = getattr(gateway, "_conversation_tree", None)
        if not tree:
            return {"error": "Conversation tree not available"}
        path = tree.get_path_to_root(leaf_id)
        return {"path": path, "count": len(path)}

    @app.post("/api/v1/chat/branch", dependencies=deps)
    async def create_branch(request: Request) -> dict[str, Any]:
        """Explicitly create a branch at a specific node."""
        body = await request.json()
        tree = getattr(gateway, "_conversation_tree", None)
        if not tree:
            return {"error": "Conversation tree not available"}
        conv_id = body.get("conversation_id", "")
        parent_id = body.get("parent_id", "")
        text = body.get("text", "")
        role = body.get("role", "user")
        if not conv_id or not text:
            return {"error": "conversation_id and text required"}
        node_id = tree.add_node(conv_id, role=role, text=text, parent_id=parent_id or None)
        return {"node_id": node_id, "branch_index": tree.get_branch_index(node_id)}
```

- [ ] **Step 3: Verify syntax**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -c "from jarvis.channels.config_routes import create_config_routes; print('OK')"`

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/__main__.py src/jarvis/channels/config_routes.py
git commit -m "feat: WebSocket branch_switch handler + REST API for chat tree/path/branch"
```

---

### Task 4: Flutter Data Models

**Files:**
- Create: `flutter_app/lib/models/chat_node.dart`

- [ ] **Step 1: Create ChatNode + ConversationTree models**

Create `flutter_app/lib/models/chat_node.dart`:

```dart
/// Data models for the conversation tree (chat branching).

class ChatNode {
  ChatNode({
    required this.id,
    required this.conversationId,
    this.parentId,
    required this.role,
    required this.text,
    this.branchIndex = 0,
    this.agentName = 'jarvis',
    this.modelUsed = '',
    this.durationMs = 0,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  final String id;
  final String conversationId;
  final String? parentId;
  final String role; // 'user' | 'assistant' | 'system'
  String text;
  final int branchIndex;
  final String agentName;
  final String modelUsed;
  final int durationMs;
  final DateTime createdAt;

  bool get isUser => role == 'user';
  bool get isAssistant => role == 'assistant';

  factory ChatNode.fromJson(Map<String, dynamic> json) {
    return ChatNode(
      id: json['id'] as String,
      conversationId: json['conversation_id'] as String? ?? '',
      parentId: json['parent_id'] as String?,
      role: json['role'] as String,
      text: json['text'] as String,
      branchIndex: json['branch_index'] as int? ?? 0,
      agentName: json['agent_name'] as String? ?? 'jarvis',
      modelUsed: json['model_used'] as String? ?? '',
      durationMs: json['duration_ms'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'conversation_id': conversationId,
    'parent_id': parentId,
    'role': role,
    'text': text,
    'branch_index': branchIndex,
    'agent_name': agentName,
  };
}

class ForkPoint {
  const ForkPoint({required this.nodeId, required this.childCount, this.activeChildIndex = 0});

  final String nodeId;
  final int childCount;
  final int activeChildIndex;
}
```

- [ ] **Step 2: Verify Flutter analyze**

Run: `cd "D:\Jarvis\jarvis complete v20\flutter_app" && flutter analyze lib/models/chat_node.dart`

- [ ] **Step 3: Commit**

```bash
git add flutter_app/lib/models/chat_node.dart
git commit -m "feat: ChatNode + ForkPoint data models for conversation tree"
```

---

### Task 5: Flutter TreeProvider

**Files:**
- Create: `flutter_app/lib/providers/tree_provider.dart`

- [ ] **Step 1: Create TreeProvider**

Create `flutter_app/lib/providers/tree_provider.dart`:

```dart
/// Conversation tree state management.
///
/// Manages nodes, active path, fork points, and branch switching.
/// Integrates with ChatProvider for message rendering and
/// WebSocketService for branch_switch commands.
import 'package:flutter/foundation.dart';
import 'package:jarvis_ui/models/chat_node.dart';
import 'package:jarvis_ui/services/api_client.dart';
import 'package:jarvis_ui/services/websocket_service.dart';

class TreeProvider extends ChangeNotifier {
  ApiClient? _api;
  WebSocketService? _ws;

  String? conversationId;
  final Map<String, ChatNode> nodes = {};
  List<String> activePath = []; // Node IDs from root to current leaf
  Map<String, int> forkPoints = {}; // nodeId → childCount
  Map<String, int> activeChildAtFork = {}; // nodeId → which child is active (0-based)

  bool get hasTree => nodes.isNotEmpty;
  bool get hasBranches => forkPoints.isNotEmpty;

  void setApi(ApiClient api) => _api = api;
  void setWs(WebSocketService ws) => _ws = ws;

  /// Load full tree from backend for a conversation.
  Future<void> loadTree(String convId) async {
    if (_api == null) return;
    conversationId = convId;
    try {
      final data = await _api!.get('chat/tree/$convId');
      nodes.clear();
      forkPoints.clear();

      final nodeList = data['nodes'] as List? ?? [];
      for (final n in nodeList) {
        final node = ChatNode.fromJson(n as Map<String, dynamic>);
        nodes[node.id] = node;
      }

      // Fork points
      final fps = data['fork_points'] as Map<String, dynamic>? ?? {};
      forkPoints = fps.map((k, v) => MapEntry(k, v as int));

      // Active path
      final leafId = data['active_leaf_id'] as String?;
      if (leafId != null) {
        _computeActivePath(leafId);
      }

      // Compute active child indices at each fork
      _computeActiveChildIndices();

      notifyListeners();
    } catch (e) {
      debugPrint('[Tree] loadTree failed: $e');
    }
  }

  /// Add a node locally (called when user sends message or assistant responds).
  void addNode(ChatNode node) {
    nodes[node.id] = node;
    activePath.add(node.id);

    // Check if parent now has multiple children (new fork point)
    if (node.parentId != null) {
      final siblings = nodes.values
          .where((n) => n.parentId == node.parentId)
          .length;
      if (siblings > 1) {
        forkPoints[node.parentId!] = siblings;
      }
    }

    notifyListeners();
  }

  /// Switch to a different branch at a fork point.
  Future<void> switchBranch(String forkNodeId, int newChildIndex) async {
    if (conversationId == null) return;

    // Find the children of the fork node
    final children = nodes.values
        .where((n) => n.parentId == forkNodeId)
        .toList()
      ..sort((a, b) => a.branchIndex.compareTo(b.branchIndex));

    if (newChildIndex < 0 || newChildIndex >= children.length) return;

    final targetChild = children[newChildIndex];

    // Find the deepest leaf in this branch
    String leafId = targetChild.id;
    while (true) {
      final childrenOfLeaf = nodes.values
          .where((n) => n.parentId == leafId)
          .toList();
      if (childrenOfLeaf.isEmpty) break;
      // Follow first child (default branch)
      childrenOfLeaf.sort((a, b) => a.branchIndex.compareTo(b.branchIndex));
      leafId = childrenOfLeaf.first.id;
    }

    // Update active path
    _computeActivePath(leafId);
    activeChildAtFork[forkNodeId] = newChildIndex;

    // Notify backend to replay this branch's history into WorkingMemory
    if (_ws != null) {
      _ws!.send({
        'type': 'branch_switch',
        'conversation_id': conversationId,
        'leaf_id': leafId,
      });
    }

    notifyListeners();
  }

  /// Get children count at a fork point.
  int getChildCount(String nodeId) => forkPoints[nodeId] ?? 0;

  /// Get active child index at a fork point.
  int getActiveChildIndex(String nodeId) => activeChildAtFork[nodeId] ?? 0;

  /// Check if a node is a fork point (has multiple children).
  bool isForkPoint(String nodeId) => (forkPoints[nodeId] ?? 0) > 1;

  /// Clear tree state (on session change).
  void clear() {
    conversationId = null;
    nodes.clear();
    activePath.clear();
    forkPoints.clear();
    activeChildAtFork.clear();
    notifyListeners();
  }

  // ── Internal ────────────────────────────────────────────────────

  void _computeActivePath(String leafId) {
    activePath.clear();
    String? currentId = leafId;
    while (currentId != null) {
      activePath.insert(0, currentId);
      currentId = nodes[currentId]?.parentId;
    }
  }

  void _computeActiveChildIndices() {
    activeChildAtFork.clear();
    final activeSet = activePath.toSet();
    for (final forkId in forkPoints.keys) {
      final children = nodes.values
          .where((n) => n.parentId == forkId)
          .toList()
        ..sort((a, b) => a.branchIndex.compareTo(b.branchIndex));
      for (var i = 0; i < children.length; i++) {
        if (activeSet.contains(children[i].id)) {
          activeChildAtFork[forkId] = i;
          break;
        }
      }
    }
  }
}
```

- [ ] **Step 2: Verify Flutter analyze**

Run: `cd "D:\Jarvis\jarvis complete v20\flutter_app" && flutter analyze lib/providers/tree_provider.dart`

- [ ] **Step 3: Commit**

```bash
git add flutter_app/lib/providers/tree_provider.dart
git commit -m "feat: TreeProvider with active path, fork detection, branch switching"
```

---

### Task 6: Flutter Branch Navigator + Tree Sidebar

**Files:**
- Create: `flutter_app/lib/widgets/chat/branch_navigator.dart`
- Create: `flutter_app/lib/widgets/chat/tree_sidebar.dart`

- [ ] **Step 1: Create BranchNavigator widget**

Create `flutter_app/lib/widgets/chat/branch_navigator.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:jarvis_ui/theme/jarvis_theme.dart';

/// Inline branch navigator shown at fork points: < 1/3 >
class BranchNavigator extends StatelessWidget {
  const BranchNavigator({
    super.key,
    required this.currentIndex,
    required this.totalBranches,
    required this.onPrevious,
    required this.onNext,
  });

  final int currentIndex;
  final int totalBranches;
  final VoidCallback onPrevious;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: JarvisTheme.accent.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: JarvisTheme.accent.withValues(alpha: 0.2)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _NavBtn(
            icon: Icons.chevron_left,
            enabled: currentIndex > 0,
            onTap: onPrevious,
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 6),
            child: Text(
              '${currentIndex + 1} / $totalBranches',
              style: TextStyle(
                fontSize: 11,
                color: JarvisTheme.accent,
                fontFamily: 'monospace',
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          _NavBtn(
            icon: Icons.chevron_right,
            enabled: currentIndex < totalBranches - 1,
            onTap: onNext,
          ),
        ],
      ),
    );
  }
}

class _NavBtn extends StatelessWidget {
  const _NavBtn({required this.icon, required this.enabled, required this.onTap});
  final IconData icon;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(10),
      onTap: enabled ? onTap : null,
      child: Icon(
        icon,
        size: 18,
        color: enabled ? JarvisTheme.accent : JarvisTheme.textTertiary,
      ),
    );
  }
}
```

- [ ] **Step 2: Create TreeSidebar widget**

Create `flutter_app/lib/widgets/chat/tree_sidebar.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:jarvis_ui/models/chat_node.dart';
import 'package:jarvis_ui/providers/tree_provider.dart';
import 'package:jarvis_ui/theme/jarvis_theme.dart';

/// Collapsible sidebar showing the full conversation tree.
class TreeSidebar extends StatelessWidget {
  const TreeSidebar({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<TreeProvider>(
      builder: (context, tree, _) {
        if (!tree.hasTree) {
          return const SizedBox(
            width: 200,
            child: Center(
              child: Text('No conversation', style: TextStyle(fontSize: 12)),
            ),
          );
        }

        // Find root nodes (no parent)
        final roots = tree.nodes.values
            .where((n) => n.parentId == null)
            .toList()
          ..sort((a, b) => a.createdAt.compareTo(b.createdAt));

        return Container(
          width: 220,
          decoration: BoxDecoration(
            border: Border(
              right: BorderSide(color: JarvisTheme.border, width: 1),
            ),
          ),
          child: ListView(
            padding: const EdgeInsets.all(8),
            children: [
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    Icon(Icons.account_tree, size: 16, color: JarvisTheme.accent),
                    const SizedBox(width: 6),
                    Text(
                      'Conversation Tree',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: JarvisTheme.accent,
                      ),
                    ),
                  ],
                ),
              ),
              for (final root in roots) _buildNode(context, tree, root, 0),
            ],
          ),
        );
      },
    );
  }

  Widget _buildNode(BuildContext context, TreeProvider tree, ChatNode node, int depth) {
    final isActive = tree.activePath.contains(node.id);
    final isFork = tree.isForkPoint(node.id);
    final children = tree.nodes.values
        .where((n) => n.parentId == node.id)
        .toList()
      ..sort((a, b) => a.branchIndex.compareTo(b.branchIndex));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          borderRadius: BorderRadius.circular(6),
          onTap: () {
            // Navigate to this node's branch
            if (node.parentId != null) {
              tree.switchBranch(node.parentId!, node.branchIndex);
            }
          },
          child: Container(
            margin: EdgeInsets.only(left: depth * 12.0, bottom: 2),
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
            decoration: BoxDecoration(
              color: isActive
                  ? JarvisTheme.accent.withValues(alpha: 0.1)
                  : Colors.transparent,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Row(
              children: [
                Icon(
                  node.isUser ? Icons.person : Icons.smart_toy,
                  size: 12,
                  color: isActive ? JarvisTheme.accent : JarvisTheme.textTertiary,
                ),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    node.text.length > 30 ? '${node.text.substring(0, 30)}...' : node.text,
                    style: TextStyle(
                      fontSize: 11,
                      color: isActive ? JarvisTheme.text : JarvisTheme.textSecondary,
                      fontWeight: isActive ? FontWeight.w500 : FontWeight.normal,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (isFork)
                  Icon(Icons.call_split, size: 12, color: JarvisTheme.orange),
              ],
            ),
          ),
        ),
        for (final child in children) _buildNode(context, tree, child, depth + 1),
      ],
    );
  }
}
```

- [ ] **Step 3: Verify Flutter analyze**

Run: `cd "D:\Jarvis\jarvis complete v20\flutter_app" && flutter analyze lib/widgets/chat/branch_navigator.dart lib/widgets/chat/tree_sidebar.dart`

- [ ] **Step 4: Commit**

```bash
git add flutter_app/lib/widgets/chat/branch_navigator.dart flutter_app/lib/widgets/chat/tree_sidebar.dart
git commit -m "feat: BranchNavigator inline controls + TreeSidebar overview panel"
```

---

### Task 7: Integrate Tree into ChatScreen

**Files:**
- Modify: `flutter_app/lib/providers/chat_provider.dart`
- Modify: `flutter_app/lib/screens/chat_screen.dart`

- [ ] **Step 1: Remove old versioning from ChatProvider**

In `chat_provider.dart`:
- Remove `versions` and `activeVersion` from ChatMessage class
- Remove `MessageVersion` class
- Remove `switchVersion()` method
- Keep `editAndResend()` but modify it to work with TreeProvider (fork at edit point)

The `editAndResend` method should now:
1. Clear messages after the edit point (as before)
2. Notify TreeProvider to create a fork node
3. Send the new text via WebSocket

- [ ] **Step 2: Register TreeProvider in app**

In the app's main widget tree (likely `main.dart`), register `TreeProvider` alongside ChatProvider.

- [ ] **Step 3: Modify chat_screen.dart**

Replace VersionNavigator with BranchNavigator at fork points:

- Import `branch_navigator.dart`, `tree_sidebar.dart`, `tree_provider.dart`
- Add tree sidebar toggle button to the toolbar
- Add state: `bool _showTreeSidebar = false`
- In the message list: at each message that is a fork point (check TreeProvider), show BranchNavigator
- Wrap chat content in a Row with optional TreeSidebar

- [ ] **Step 4: Build + Analyze**

Run: `flutter analyze && flutter build web --release --no-tree-shake-icons`

- [ ] **Step 5: Commit**

```bash
git add flutter_app/lib/providers/chat_provider.dart flutter_app/lib/screens/chat_screen.dart flutter_app/lib/
git commit -m "feat: tree-aware chat screen with BranchNavigator + TreeSidebar toggle"
```

---

### Task 8: Full Test Suite

- [ ] **Step 1: Run tree tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_conversation_tree.py -v`
Expected: All 11 PASS

- [ ] **Step 2: Run all unit tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/ -v`
Expected: All PASS

- [ ] **Step 3: Ruff check**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m ruff check src/jarvis/ --select=F401,F811,F821,E501 --no-fix && python -m ruff format src/jarvis/`

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: test adjustments for chat branching"
```
