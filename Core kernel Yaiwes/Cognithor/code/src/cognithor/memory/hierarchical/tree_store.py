"""SQLite persistence for hierarchical document trees."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from cognithor.memory.hierarchical.models import DocumentMetadata, DocumentTree, TreeNode


class TreeStore:
    """Persist and retrieve :class:`DocumentTree` instances in SQLite."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._ensure_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _ensure_tables(self) -> None:
        self._conn.executescript(
            """\
            CREATE TABLE IF NOT EXISTS hierarchical_documents (
                document_id   TEXT PRIMARY KEY,
                source_path   TEXT NOT NULL,
                source_hash   TEXT NOT NULL,
                title         TEXT NOT NULL,
                root_node_id  TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                parser_used   TEXT NOT NULL,
                total_tokens  INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hierarchical_nodes (
                node_id       TEXT PRIMARY KEY,
                document_id   TEXT NOT NULL
                    REFERENCES hierarchical_documents(document_id) ON DELETE CASCADE,
                parent_id     TEXT,
                level         INTEGER NOT NULL,
                title         TEXT NOT NULL,
                summary       TEXT NOT NULL DEFAULT '',
                content       TEXT NOT NULL DEFAULT '',
                content_hash  TEXT NOT NULL DEFAULT '',
                token_count   INTEGER NOT NULL DEFAULT 0,
                children_ids  TEXT NOT NULL DEFAULT '[]',
                position      INTEGER NOT NULL DEFAULT 0,
                page_number   INTEGER,
                metadata      TEXT NOT NULL DEFAULT '{}'
            );

            CREATE INDEX IF NOT EXISTS idx_hn_document
                ON hierarchical_nodes(document_id);

            CREATE INDEX IF NOT EXISTS idx_hn_parent
                ON hierarchical_nodes(parent_id);
            """
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_tree(self, tree: DocumentTree) -> None:
        """Persist *tree*.  Replaces an existing tree with the same id."""
        with self._conn:
            # Delete first (CASCADE removes nodes)
            self._conn.execute(
                "DELETE FROM hierarchical_documents WHERE document_id = ?",
                (tree.document_id,),
            )
            self._conn.execute(
                "INSERT INTO hierarchical_documents "
                "(document_id, source_path, source_hash, title, root_node_id, "
                "created_at, parser_used, total_tokens) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    tree.document_id,
                    str(tree.source_path),
                    tree.source_hash,
                    tree.title,
                    tree.root_node_id,
                    tree.created_at.isoformat(),
                    tree.parser_used,
                    tree.total_tokens,
                ),
            )
            for node in tree.nodes.values():
                self._conn.execute(
                    "INSERT INTO hierarchical_nodes "
                    "(node_id, document_id, parent_id, level, title, summary, "
                    "content, content_hash, token_count, children_ids, position, "
                    "page_number, metadata) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        node.node_id,
                        node.document_id,
                        node.parent_id,
                        node.level,
                        node.title,
                        node.summary,
                        node.content,
                        node.content_hash,
                        node.token_count,
                        json.dumps(list(node.children_ids)),
                        node.position,
                        node.page_number,
                        json.dumps(dict(node.metadata)),
                    ),
                )

    def load_tree(self, document_id: str) -> DocumentTree | None:
        """Load a tree by *document_id*.  Returns ``None`` if not found."""
        row = self._conn.execute(
            "SELECT document_id, source_path, source_hash, title, root_node_id, "
            "created_at, parser_used, total_tokens "
            "FROM hierarchical_documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()
        if row is None:
            return None

        node_rows = self._conn.execute(
            "SELECT node_id, document_id, parent_id, level, title, summary, "
            "content, content_hash, token_count, children_ids, position, "
            "page_number, metadata "
            "FROM hierarchical_nodes WHERE document_id = ?",
            (document_id,),
        ).fetchall()

        nodes: dict[str, TreeNode] = {}
        for nr in node_rows:
            nodes[nr[0]] = TreeNode(
                node_id=nr[0],
                document_id=nr[1],
                parent_id=nr[2],
                level=nr[3],
                title=nr[4],
                summary=nr[5],
                content=nr[6],
                content_hash=nr[7],
                token_count=nr[8],
                children_ids=tuple(json.loads(nr[9])),
                position=nr[10],
                page_number=nr[11],
                metadata=json.loads(nr[12]),
            )

        return DocumentTree(
            document_id=row[0],
            source_path=Path(row[1]),
            source_hash=row[2],
            title=row[3],
            root_node_id=row[4],
            nodes=nodes,
            created_at=datetime.fromisoformat(row[5]),
            parser_used=row[6],
            total_tokens=row[7],
        )

    def delete_tree(self, document_id: str) -> None:
        """Delete a document and all its nodes (via CASCADE)."""
        with self._conn:
            self._conn.execute(
                "DELETE FROM hierarchical_documents WHERE document_id = ?",
                (document_id,),
            )

    def list_documents(self) -> list[DocumentMetadata]:
        """Return lightweight metadata for every indexed document."""
        rows = self._conn.execute(
            "SELECT d.document_id, d.title, d.source_path, d.parser_used, "
            "d.total_tokens, COUNT(n.node_id), d.created_at "
            "FROM hierarchical_documents d "
            "LEFT JOIN hierarchical_nodes n ON d.document_id = n.document_id "
            "GROUP BY d.document_id "
            "ORDER BY d.created_at DESC"
        ).fetchall()
        return [
            DocumentMetadata(
                document_id=r[0],
                title=r[1],
                source_path=r[2],
                parser_used=r[3],
                total_tokens=r[4],
                node_count=r[5],
                created_at=r[6],
            )
            for r in rows
        ]

    def has_any_documents(self) -> bool:
        """Return ``True`` if at least one document is stored."""
        row = self._conn.execute("SELECT EXISTS(SELECT 1 FROM hierarchical_documents)").fetchone()
        return bool(row and row[0])
