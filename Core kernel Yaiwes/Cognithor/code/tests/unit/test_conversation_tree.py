"""Tests for ConversationTree — node CRUD, path computation, branching."""

import pytest


class TestConversationTree:
    @pytest.fixture
    def tree(self, tmp_path):
        from cognithor.core.conversation_tree import ConversationTree

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
        tree.add_node(conv_id, role="assistant", text="Hi!", parent_id=n1)
        # Fork: add another child to n1 (sibling of n2)
        tree.add_node(conv_id, role="user", text="Hola", parent_id=n1)
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
        tree.add_node(conv_id, role="assistant", text="A", parent_id=n1)
        tree.add_node(conv_id, role="assistant", text="B", parent_id=n1)
        forks = tree.get_fork_points(conv_id)
        assert n1 in forks
        assert forks[n1] == 2

    def test_get_tree_structure(self, tree):
        conv_id = tree.create_conversation()
        n1 = tree.add_node(conv_id, role="user", text="Root")
        tree.add_node(conv_id, role="assistant", text="A", parent_id=n1)
        structure = tree.get_tree_structure(conv_id)
        assert structure["conversation_id"] == conv_id
        assert len(structure["nodes"]) == 2

    def test_conversation_not_found(self, tree):
        path = tree.get_active_path("nonexistent")
        assert path == []
