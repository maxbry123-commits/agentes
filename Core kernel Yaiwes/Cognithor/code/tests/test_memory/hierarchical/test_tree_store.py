"""Tests for the SQLite tree store."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from cognithor.memory.hierarchical.models import DocumentTree, TreeNode
from cognithor.memory.hierarchical.tree_store import TreeStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tree(doc_id: str = "doc-1", title: str = "Test Doc") -> DocumentTree:
    root_id = f"{doc_id}-root"
    child_id = f"{doc_id}-child-1"
    root = TreeNode(
        node_id=root_id,
        document_id=doc_id,
        parent_id=None,
        level=0,
        title=title,
        summary="Root summary",
        content="Root content",
        content_hash="abc123",
        token_count=10,
        children_ids=(child_id,),
        position=0,
    )
    child = TreeNode(
        node_id=child_id,
        document_id=doc_id,
        parent_id=root_id,
        level=1,
        title="Section 1",
        summary="Child summary",
        content="Child content",
        content_hash="def456",
        token_count=8,
        children_ids=(),
        position=1,
        page_number=2,
        metadata={"key": "value"},
    )
    return DocumentTree(
        document_id=doc_id,
        source_path=Path("/tmp/test.md"),
        source_hash="hash-aaa",
        title=title,
        root_node_id=root_id,
        nodes={root_id: root, child_id: child},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        parser_used="MarkdownParser",
        total_tokens=18,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTreeStore:
    def test_save_and_load(self, tmp_path: Path) -> None:
        store = TreeStore(tmp_path / "test.db")
        tree = _make_tree()
        store.save_tree(tree)

        loaded = store.load_tree("doc-1")
        assert loaded is not None
        assert loaded.document_id == tree.document_id
        assert loaded.title == tree.title
        assert loaded.source_hash == tree.source_hash
        assert loaded.parser_used == tree.parser_used
        assert loaded.total_tokens == tree.total_tokens
        assert loaded.root_node_id == tree.root_node_id
        assert len(loaded.nodes) == 2
        assert loaded.nodes["doc-1-child-1"].title == "Section 1"
        assert loaded.nodes["doc-1-child-1"].page_number == 2
        assert loaded.nodes["doc-1-child-1"].metadata == {"key": "value"}
        assert loaded.nodes["doc-1-child-1"].children_ids == ()
        assert loaded.nodes["doc-1-root"].children_ids == ("doc-1-child-1",)

    def test_delete_cascades(self, tmp_path: Path) -> None:
        store = TreeStore(tmp_path / "test.db")
        store.save_tree(_make_tree())

        store.delete_tree("doc-1")
        assert store.load_tree("doc-1") is None

        # Verify nodes are also gone
        row = store._conn.execute(
            "SELECT COUNT(*) FROM hierarchical_nodes WHERE document_id = ?",
            ("doc-1",),
        ).fetchone()
        assert row[0] == 0

    def test_list_documents(self, tmp_path: Path) -> None:
        store = TreeStore(tmp_path / "test.db")
        store.save_tree(_make_tree("doc-1", "Doc One"))
        store.save_tree(_make_tree("doc-2", "Doc Two"))

        docs = store.list_documents()
        assert len(docs) == 2
        ids = {d.document_id for d in docs}
        assert ids == {"doc-1", "doc-2"}
        for d in docs:
            assert d.node_count == 2

    def test_has_any_documents(self, tmp_path: Path) -> None:
        store = TreeStore(tmp_path / "test.db")
        assert store.has_any_documents() is False

        store.save_tree(_make_tree())
        assert store.has_any_documents() is True

    def test_duplicate_replaces(self, tmp_path: Path) -> None:
        store = TreeStore(tmp_path / "test.db")
        store.save_tree(_make_tree("doc-1", "Version 1"))
        store.save_tree(_make_tree("doc-1", "Version 2"))

        docs = store.list_documents()
        assert len(docs) == 1
        loaded = store.load_tree("doc-1")
        assert loaded is not None
        assert loaded.title == "Version 2"

    def test_load_nonexistent(self, tmp_path: Path) -> None:
        store = TreeStore(tmp_path / "test.db")
        assert store.load_tree("nope") is None

    def test_tables_created_on_init(self, tmp_path: Path) -> None:
        store = TreeStore(tmp_path / "test.db")
        tables = {
            row[0]
            for row in store._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "hierarchical_documents" in tables
        assert "hierarchical_nodes" in tables
