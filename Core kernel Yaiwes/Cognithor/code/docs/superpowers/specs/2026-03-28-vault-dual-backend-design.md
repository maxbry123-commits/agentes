# Vault Dual-Backend — Design Spec

> **For agentic workers:** Use superpowers:writing-plans to create the implementation plan.

**Goal:** Replace scattered .md files with encrypted SQLite when `vault.encrypt_files=true`. Preserve Obsidian-compatible .md files when `false`. Automatic bidirectional migration on toggle change.

**Date:** 2026-03-28
**Status:** Approved

---

## 1. Architecture

VaultTools gets a pluggable storage backend. The MCP interface (7 tools) stays identical.

```
VaultTools (MCP Interface — unchanged)
    |
    ├── encrypt_files = false → FileBackend
    |       ├── .md files on disk (YAML frontmatter + Markdown)
    |       └── _index.json (metadata cache)
    |
    └── encrypt_files = true  → DBBackend
            └── vault.db (SQLCipher via encrypted_connect)
                ├── notes table (structured columns)
                └── notes_fts (FTS5 full-text search)
```

## 2. Backend Interface (ABC)

```python
class VaultBackend(ABC):
    @abstractmethod
    def save(self, path: str, title: str, content: str, tags: str,
             folder: str, sources: str, backlinks: list[str]) -> str: ...

    @abstractmethod
    def read(self, path: str) -> dict | None: ...
        # Returns: {path, title, content, tags, folder, sources, backlinks, created_at, updated_at}

    @abstractmethod
    def search(self, query: str, folder: str = "", tags: str = "",
               limit: int = 10) -> list[dict]: ...

    @abstractmethod
    def list_notes(self, folder: str = "", limit: int = 50) -> list[dict]: ...

    @abstractmethod
    def update(self, path: str, content: str, append: bool = False) -> str: ...

    @abstractmethod
    def delete(self, path: str) -> str: ...

    @abstractmethod
    def link(self, source_path: str, target_path: str) -> str: ...

    @abstractmethod
    def exists(self, path: str) -> bool: ...
```

## 3. DB Schema (DBBackend)

```sql
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '',
    folder TEXT DEFAULT '',
    sources TEXT DEFAULT '',
    backlinks TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_notes_folder ON notes(folder);
CREATE INDEX idx_notes_tags ON notes(tags);

CREATE VIRTUAL TABLE notes_fts USING fts5(
    title, content, tags,
    content=notes, content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(rowid, title, content, tags)
    VALUES (new.rowid, new.title, new.content, new.tags);
END;

CREATE TRIGGER notes_ad AFTER DELETE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, content, tags)
    VALUES('delete', old.rowid, old.title, old.content, old.tags);
END;

CREATE TRIGGER notes_au AFTER UPDATE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, content, tags)
    VALUES('delete', old.rowid, old.title, old.content, old.tags);
    INSERT INTO notes_fts(rowid, title, content, tags)
    VALUES (new.rowid, new.title, new.content, new.tags);
END;
```

Database file: `~/.cognithor/vault/vault.db` (encrypted via `encrypted_connect()`)

## 4. FileBackend

Wraps the current vault.py logic into the `VaultBackend` interface:
- save → write .md file with YAML frontmatter + update _index.json
- read → parse .md file frontmatter + body
- search → read _index.json + grep file contents
- list → read _index.json filtered by folder
- update → read + modify + write .md file
- delete → unlink file + remove from _index.json
- link → read both files, add [[backlink]], write back

This is a refactor of existing code into the interface, not new logic.

## 5. DBBackend

- save → INSERT INTO notes + FTS auto-synced via trigger
- read → SELECT * FROM notes WHERE path = ?
- search → SELECT FROM notes_fts WHERE notes_fts MATCH ? (FTS5 query)
- list → SELECT FROM notes WHERE folder = ? ORDER BY updated_at DESC
- update → UPDATE notes SET content = ?, updated_at = ?
- delete → DELETE FROM notes WHERE path = ?
- link → UPDATE backlinks JSON array on both notes

## 6. Migration

### Marker file
`~/.cognithor/vault/.vault_mode` contains `"file"` or `"db"`.

### On VaultTools init:
```python
current_mode = "db" if config.vault.encrypt_files else "file"
last_mode = read .vault_mode file (default "file")

if current_mode != last_mode:
    if current_mode == "db":
        migrate_files_to_db()
    else:
        migrate_db_to_files()
    write current_mode to .vault_mode
```

### migrate_files_to_db():
1. Scan all .md files in vault root (recursive)
2. For each file: parse YAML frontmatter → extract title, tags, folder, sources
3. INSERT into vault.db
4. Do NOT delete .md files (keep as backup until next startup confirms DB works)

### migrate_db_to_files():
1. SELECT * FROM notes
2. For each row: render YAML frontmatter + content → write .md file
3. Rebuild _index.json from the exported files

## 7. VaultTools Refactor

```python
class VaultTools:
    def __init__(self, config):
        if config.vault.encrypt_files:
            self._backend = DBBackend(vault_root, config)
        else:
            self._backend = FileBackend(vault_root, config)

        # Auto-migrate if mode changed
        self._check_migration(config)

    async def vault_save(self, title, content, tags, folder, sources, linked_notes):
        return self._backend.save(path, title, content, tags, folder, sources, backlinks)

    async def vault_search(self, query, folder, tags, limit):
        return self._backend.search(query, folder, tags, limit)

    # ... etc for all 7 tools
```

## 8. What Changes

| Component | Change |
|-----------|--------|
| `src/jarvis/mcp/vault.py` | Refactored to use VaultBackend interface |
| `src/jarvis/mcp/vault_backend.py` | NEW: VaultBackend ABC |
| `src/jarvis/mcp/vault_file_backend.py` | NEW: FileBackend (extracted from vault.py) |
| `src/jarvis/mcp/vault_db_backend.py` | NEW: DBBackend (SQLCipher) |
| `src/jarvis/mcp/vault_migration.py` | NEW: bidirectional migration |
| Tests | NEW: test_vault_db_backend.py, test_vault_migration.py |

## 9. What Does NOT Change

- All 7 MCP tool signatures and return values
- The `register_vault_tools()` function
- Flutter UI (already has the toggle)
- Gatekeeper classifications
- Any other module that calls vault tools

## 10. Error Handling

- Migration failure: log error, keep previous mode, don't lose data
- DB corruption: fall back to FileBackend with WARNING
- Missing .md files during migration: skip with warning, continue
- FTS index corruption: rebuild from notes table

---

*Vault Dual-Backend Spec v1.0 | Apache 2.0*
