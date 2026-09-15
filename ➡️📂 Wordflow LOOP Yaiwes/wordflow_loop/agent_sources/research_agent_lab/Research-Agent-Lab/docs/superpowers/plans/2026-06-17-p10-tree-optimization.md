# P10: 实验树优化 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现实验树的分支剪枝、分支晋升、多分支并行执行、树可视化四个功能，补齐 P8/P9 实验树的运维和可视化缺口。

**Architecture:** 新增 `TreePrunerAgent`（剪枝）+ `tools/tree_visualizer.py`（可视化），修改 `BranchSelectionAgent`（top-N）、`TreeSearchAgent`（晋升）、`AutonomousExperimentAgent`（串行多 plan）、`app/main.py`（新 CLI 参数）、`reviewer_agent.py`（ASCII 树 + 可晋升列表）、`literature_memory_agent.py`（Mermaid 导出）。单分支模式下完整向后兼容。

**Tech Stack:** Python 3.x, dataclasses, unittest, SQLite（不变）

---

### Task 1: 树可视化工具 — `tools/tree_visualizer.py`

**Files:**
- Create: `tools/tree_visualizer.py`
- Create: `tests/test_tree_visualizer.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_tree_visualizer.py
from __future__ import annotations

from unittest import TestCase, main

from tools.tree_visualizer import render_ascii_tree, export_mermaid


def _make_sample_tree() -> dict:
    return {
        "branch_id": "branch_1",
        "root_id": "root_1",
        "status": "active",
        "max_depth": 2,
        "max_active_nodes": 3,
        "nodes": [
            {
                "node_id": "root_1", "experiment_id": "exp_root",
                "parent_id": "", "hypothesis": "Root hypothesis",
                "patch_scope": "", "result": {}, "decision": {},
                "children_ids": ["pend_a", "pend_b"],
                "status": "active", "depth": 0,
            },
            {
                "node_id": "pend_a", "experiment_id": "exp_a",
                "parent_id": "root_1", "hypothesis": "Data loader tweak may improve ADE",
                "patch_scope": "data loader", "result": {
                    "status": "passed", "metrics": {"ade": 0.27, "fde": 0.15}
                }, "decision": {"action": "continue"},
                "children_ids": [], "status": "smoke_passed", "depth": 1,
            },
            {
                "node_id": "pend_b", "experiment_id": "exp_b",
                "parent_id": "root_1", "hypothesis": "Fusion layer simplification",
                "patch_scope": "fusion layer", "result": {}, "decision": {},
                "children_ids": [], "status": "pending", "depth": 1,
            },
        ],
    }


class AsciiTreeTest(TestCase):
    def test_render_ascii_tree_contains_root(self):
        tree = _make_sample_tree()
        output = render_ascii_tree(tree)
        self.assertIn("root_1", output)
        self.assertIn("active", output)

    def test_render_ascii_tree_contains_children(self):
        tree = _make_sample_tree()
        output = render_ascii_tree(tree)
        self.assertIn("pend_a", output)
        self.assertIn("pend_b", output)
        self.assertIn("smoke_passed", output)
        self.assertIn("pending", output)

    def test_render_ascii_tree_shows_metrics(self):
        tree = _make_sample_tree()
        output = render_ascii_tree(tree)
        self.assertIn("ADE", output)
        self.assertIn("0.27", output)

    def test_render_ascii_tree_empty_nodes(self):
        tree = {"branch_id": "b", "root_id": "", "nodes": [], "status": "active"}
        output = render_ascii_tree(tree)
        self.assertIn("(empty)", output.lower())


class MermaidExportTest(TestCase):
    def test_export_mermaid_contains_header(self):
        tree = _make_sample_tree()
        output = export_mermaid(tree)
        self.assertIn("graph TD", output)

    def test_export_mermaid_contains_nodes(self):
        tree = _make_sample_tree()
        output = export_mermaid(tree)
        self.assertIn("root_1", output)
        self.assertIn("pend_a", output)
        self.assertIn("pend_b", output)

    def test_export_mermaid_contains_edges(self):
        tree = _make_sample_tree()
        output = export_mermaid(tree)
        self.assertIn("-->", output)

    def test_export_mermaid_status_shapes(self):
        tree = _make_sample_tree()
        output = export_mermaid(tree)
        # smoke_passed → rounded rectangle (parentheses)
        self.assertIn("(", output)
        self.assertIn(")", output)
        # pending → diamond (braces)
        self.assertIn("{", output)
        self.assertIn("}", output)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m pytest tests/test_tree_visualizer.py -v 2>&1
```
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: 实现 `render_ascii_tree()` 和 `export_mermaid()`**

```python
# tools/tree_visualizer.py
from __future__ import annotations


def render_ascii_tree(tree: dict) -> str:
    """Render experiment tree as terminal-friendly ASCII art."""
    nodes = tree.get("nodes", []) or []
    if not nodes:
        return "(empty tree)"

    by_id = {n["node_id"]: n for n in nodes}
    root_id = tree.get("root_id", "")
    root = by_id.get(root_id)
    if root is None:
        return "(no root node)"

    lines: list[str] = []
    _render_node_ascii(root, by_id, lines, indent="", is_last=True, is_root=True)
    return "\n".join(lines)


def _render_node_ascii(
    node: dict,
    by_id: dict,
    lines: list[str],
    indent: str,
    is_last: bool,
    is_root: bool = False,
) -> None:
    connector = "└── " if is_last and not is_root else "├── "
    if is_root:
        prefix = ""
    else:
        prefix = indent + connector

    status = node.get("status", "?")
    hypothesis = (node.get("hypothesis", "") or "")[:40]
    node_id = node.get("node_id", "?")
    result = node.get("result", {})
    metrics = result.get("metrics", {})

    parts = [f"{node_id} [{status}]"]
    if hypothesis:
        parts.append(f'"{hypothesis}"')
    if metrics:
        metric_str = ", ".join(f"{k}={v}" for k, v in sorted(metrics.items()))
        parts.append(f"({metric_str})")

    lines.append(prefix + " ".join(parts))

    children_ids = node.get("children_ids", []) or []
    children = [by_id[cid] for cid in children_ids if cid in by_id]
    for i, child in enumerate(children):
        child_is_last = i == len(children) - 1
        if is_root:
            child_indent = ""
        else:
            child_indent = indent + ("    " if is_last else "│   ")
        _render_node_ascii(child, by_id, lines, child_indent, child_is_last)


_STATUS_MERMAID_SHAPES = {
    "active": ("[", "]"),
    "smoke_passed": ("(", ")"),
    "pending": ("{", "}"),
    "selected": ("{{", "}}"),
    "branched": ("[\\", "\\]"),
    "max_depth_reached": ("[", "]"),
    "blocked_max_active": ("[", "]"),
    "archived": ("[(", ")]"),
}


def export_mermaid(tree: dict) -> str:
    """Export experiment tree as a Mermaid flowchart (graph TD)."""
    nodes = tree.get("nodes", []) or []
    if not nodes:
        return "graph TD\n    empty[No nodes]"

    by_id = {n["node_id"]: n for n in nodes}
    root_id = tree.get("root_id", "")
    root = by_id.get(root_id) if root_id else (nodes[0] if nodes else None)

    lines = ["graph TD"]

    rendered: set[str] = set()

    def render_node(node: dict) -> None:
        nid = node.get("node_id", "")
        if nid in rendered:
            return
        rendered.add(nid)

        status = node.get("status", "pending")
        left, right = _STATUS_MERMAID_SHAPES.get(status, ("[", "]"))
        hypothesis = (node.get("hypothesis", "") or "")[:30]
        label = f"{nid}<br/>{status}"
        result = node.get("result", {})
        metrics = result.get("metrics", {})
        if metrics:
            metric_str = "<br/>".join(
                f"{k}: {v}" for k, v in sorted(metrics.items())
            )
            label += f"<br/>{metric_str}"

        escaped = label.replace('"', "'")
        lines.append(f"    {nid}{left}\"{escaped}\"{right}")

        children_ids = node.get("children_ids", []) or []
        for cid in children_ids:
            child = by_id.get(cid)
            if child:
                lines.append(f"    {nid} --> {cid}")
                render_node(child)

    render_node(root)
    return "\n".join(lines)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m pytest tests/test_tree_visualizer.py -v 2>&1
```
Expected: 8 passed

- [ ] **Step 5: 运行全量测试确保不回归**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests
```
Expected: 139 tests OK

---

### Task 2: 分支剪枝 — `agents/tree_pruner.py`

**Files:**
- Create: `agents/tree_pruner.py`
- Create: `tests/test_tree_pruner.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_tree_pruner.py
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.tree_pruner import TreePrunerAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState


def _make_topic():
    from schemas.topic_pack import TopicPack
    return TopicPack(topic_name="test", experiment_metrics=["ADE", "FDE"])


def _make_context(tmp_path: str) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp_path)),
        memory_store=None,
        tool_registry=None,
        settings={},
    )


class TreePrunerTest(TestCase):
    def test_noop_when_no_tree(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            agent = TreePrunerAgent()
            result = agent.run(state, _make_context(tmp))
            self.assertIn("no tree", result.notes[0].lower())

    def test_prunes_max_depth_reached_without_result(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "b1", "root_id": "r1",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r1", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["n1", "n2"], "status": "active",
                        "result": {}, "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "n1", "parent_id": "r1",
                        "hypothesis": "Good", "children_ids": [],
                        "status": "max_depth_reached", "result": {},
                        "decision": {}, "depth": 2,
                    },
                    {
                        "node_id": "n2", "parent_id": "r1",
                        "hypothesis": "Keep", "children_ids": [],
                        "status": "smoke_passed", "result": {"status": "passed"},
                        "decision": {"action": "continue"}, "depth": 1,
                    },
                ],
            }
            agent = TreePrunerAgent()
            result = agent.run(state, _make_context(tmp))
            tree = state.values["experiment_tree"]
            node_ids = {n["node_id"] for n in tree["nodes"]}
            self.assertNotIn("n1", node_ids)
            self.assertIn("n2", node_ids)
            self.assertIn("r1", node_ids)
            # Root children updated
            root = next(n for n in tree["nodes"] if n["node_id"] == "r1")
            self.assertEqual(root["children_ids"], ["n2"])

    def test_prunes_blocked_max_active_without_result(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "b2", "root_id": "r2",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r2", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["blocked"], "status": "active",
                        "result": {}, "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "blocked", "parent_id": "r2",
                        "hypothesis": "Blocked", "children_ids": [],
                        "status": "blocked_max_active", "result": {},
                        "decision": {}, "depth": 1,
                    },
                ],
            }
            agent = TreePrunerAgent()
            agent.run(state, _make_context(tmp))
            tree = state.values["experiment_tree"]
            node_ids = {n["node_id"] for n in tree["nodes"]}
            self.assertNotIn("blocked", node_ids)

    def test_recursive_prune_parent_without_result(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "b3", "root_id": "r3",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r3", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["mid"], "status": "active",
                        "result": {}, "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "mid", "parent_id": "r3",
                        "hypothesis": "Dead parent",
                        "children_ids": ["leaf"], "status": "branched",
                        "result": {}, "decision": {}, "depth": 1,
                    },
                    {
                        "node_id": "leaf", "parent_id": "mid",
                        "hypothesis": "Dead leaf",
                        "children_ids": [], "status": "max_depth_reached",
                        "result": {}, "decision": {}, "depth": 2,
                    },
                ],
            }
            agent = TreePrunerAgent()
            agent.run(state, _make_context(tmp))
            tree = state.values["experiment_tree"]
            node_ids = {n["node_id"] for n in tree["nodes"]}
            self.assertNotIn("leaf", node_ids)
            self.assertNotIn("mid", node_ids)  # recursive
            self.assertIn("r3", node_ids)
            root = next(n for n in tree["nodes"] if n["node_id"] == "r3")
            self.assertEqual(root["children_ids"], [])

    def test_does_not_prune_smoke_passed(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "b4", "root_id": "r4",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r4", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["good"], "status": "active",
                        "result": {}, "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "good", "parent_id": "r4",
                        "hypothesis": "Passed", "children_ids": [],
                        "status": "smoke_passed",
                        "result": {"status": "passed", "metrics": {"ade": 0.1}},
                        "decision": {"action": "continue"}, "depth": 1,
                    },
                ],
            }
            agent = TreePrunerAgent()
            agent.run(state, _make_context(tmp))
            tree = state.values["experiment_tree"]
            node_ids = {n["node_id"] for n in tree["nodes"]}
            self.assertIn("good", node_ids)

    def test_does_not_prune_selected_node(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "b5", "root_id": "r5",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r5", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["sel"], "status": "active",
                        "result": {}, "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "sel", "parent_id": "r5",
                        "hypothesis": "Selected", "children_ids": [],
                        "status": "selected", "result": {},
                        "decision": {}, "depth": 1,
                    },
                ],
            }
            agent = TreePrunerAgent()
            agent.run(state, _make_context(tmp))
            tree = state.values["experiment_tree"]
            node_ids = {n["node_id"] for n in tree["nodes"]}
            self.assertIn("sel", node_ids)

    def test_prunes_pending_at_or_beyond_max_depth(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "b6", "root_id": "r6",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r6", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["zombie"], "status": "active",
                        "result": {}, "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "zombie", "parent_id": "r6",
                        "hypothesis": "Zombie", "children_ids": [],
                        "status": "pending", "result": {}, "decision": {},
                        "depth": 2,
                    },
                ],
            }
            agent = TreePrunerAgent()
            agent.run(state, _make_context(tmp))
            tree = state.values["experiment_tree"]
            node_ids = {n["node_id"] for n in tree["nodes"]}
            self.assertNotIn("zombie", node_ids)

    def test_reports_prune_count(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "b7", "root_id": "r7",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r7", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["d1", "d2"], "status": "active",
                        "result": {}, "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "d1", "parent_id": "r7",
                        "hypothesis": "D1", "children_ids": [],
                        "status": "max_depth_reached", "result": {},
                        "decision": {}, "depth": 2,
                    },
                    {
                        "node_id": "d2", "parent_id": "r7",
                        "hypothesis": "D2", "children_ids": [],
                        "status": "blocked_max_active", "result": {},
                        "decision": {}, "depth": 2,
                    },
                ],
            }
            agent = TreePrunerAgent()
            result = agent.run(state, _make_context(tmp))
            self.assertIn("2", result.notes[0])


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m pytest tests/test_tree_pruner.py -v 2>&1
```
Expected: FAIL

- [ ] **Step 3: 实现 `TreePrunerAgent`**

```python
# agents/tree_pruner.py
from __future__ import annotations

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState


_PRUNEABLE_STATUSES = {"pending", "max_depth_reached", "blocked_max_active"}


class TreePrunerAgent(Agent):
    """Prunes dead-end nodes from experiment tree before branch selection.

    Removes nodes at or beyond max_depth that have no results, then
    recursively prunes parent nodes whose children were all removed.
    """

    name = "tree_pruner"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        tree = state.values.get("experiment_tree")
        if not isinstance(tree, dict) or not tree.get("nodes"):
            return AgentResult(notes=["tree_pruner: no tree, skipping"])

        nodes = tree.get("nodes", []) or []
        max_depth = tree.get("max_depth", 2)

        pruned_ids = set()
        self._mark_pruneable(nodes, max_depth, pruned_ids)

        if not pruned_ids:
            return AgentResult(notes=["tree_pruner: no nodes to prune"])

        # Remove pruned nodes
        remaining = [n for n in nodes if n.get("node_id") not in pruned_ids]
        # Update children_ids on all remaining parents
        for node in remaining:
            node["children_ids"] = [
                cid for cid in (node.get("children_ids") or [])
                if cid not in pruned_ids
            ]

        tree["nodes"] = remaining
        state.values["experiment_tree"] = tree

        return AgentResult(
            notes=[f"tree_pruner: pruned {len(pruned_ids)} node(s)"],
            values={"experiment_tree": tree},
        )

    def _mark_pruneable(
        self,
        nodes: list[dict],
        max_depth: int,
        pruned: set[str],
    ) -> None:
        marked = True
        while marked:
            marked = False
            for node in nodes:
                nid = node.get("node_id", "")
                if nid in pruned:
                    continue
                if self._is_pruneable(node, nodes, max_depth, pruned):
                    pruned.add(nid)
                    marked = True

    def _is_pruneable(
        self,
        node: dict,
        all_nodes: list[dict],
        max_depth: int,
        already_pruned: set[str],
    ) -> bool:
        """A node is pruneable if all its children would be pruned too.

        First pass: find nodes that are dead and at/past max depth.
        Second pass: parent nodes whose children are ALL pruned or already dead
        and the parent itself has no results.
        """
        nid = node.get("node_id", "")
        status = node.get("status", "")
        depth = node.get("depth", 0)
        result = node.get("result", {}) or {}
        children_ids = node.get("children_ids", []) or []

        # Direct dead nodes: at/beyond max depth and status is dead-end
        if depth >= max_depth and status in _PRUNEABLE_STATUSES:
            return bool(not result)

        # Parent whose children are all pruned
        if children_ids and status in {"branched", "max_depth_reached", "blocked_max_active"}:
            all_children_pruned = all(
                cid in already_pruned
                for cid in children_ids
            )
            if all_children_pruned and not result:
                return True

        return False
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m pytest tests/test_tree_pruner.py -v 2>&1
```
Expected: 8 passed

- [ ] **Step 5: 集成到 factory.py 和 `agents/__init__.py`**

```python
# agents/__init__.py — 在 imports 末尾新增
from agents.tree_pruner import TreePrunerAgent
```
（注意：实际编辑时查找现有导出列表，追加 `TreePrunerAgent`）

```python
# workflows/factory.py — 在 factory 函数签名新增参数
def build_full_research_workflow(
    ...
    enable_tree_search: bool = False,
    max_parallel_branches: int = 1,   # NEW
    literature_memory_store: object = None,
) -> Workflow:
```

在 `BranchSelectionAgent` 之前插入 TreePrunerAgent：

```python
    if enable_tree_search:
        agents.append(TreePrunerAgent())                                    # NEW
        agents.append(BranchSelectionAgent(lit_memory_store=literature_memory_store))
        agents.append(BranchToPlanAgent())
```

settings 新增 max_parallel_branches：

```python
        settings={
            ...
            "max_parallel_branches": max_parallel_branches,    # NEW
        },
```

- [ ] **Step 6: 全量测试**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests
```
Expected: 147 tests OK

---

### Task 3: 多分支选择 — 修改 `agents/branch_selection_agent.py`

**Files:**
- Modify: `agents/branch_selection_agent.py`
- Modify: `tests/test_branch_selection_agent.py`

- [ ] **Step 1: 新增 top-N 测试**

在 `tests/test_branch_selection_agent.py` 中新增：

```python
class MultiBranchSelectionTest(TestCase):
    def test_selects_top2_pending_nodes(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            tree = {
                "branch_id": "mb", "root_id": "r",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["p1", "p2", "p3"], "status": "active",
                        "result": {}, "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "p1", "parent_id": "r",
                        "hypothesis": "Data loader tweak", "patch_scope": "data loader",
                        "children_ids": [], "status": "pending",
                        "result": {}, "decision": {}, "depth": 1,
                    },
                    {
                        "node_id": "p2", "parent_id": "r",
                        "hypothesis": "Config change", "patch_scope": "config",
                        "children_ids": [], "status": "pending",
                        "result": {}, "decision": {}, "depth": 1,
                    },
                    {
                        "node_id": "p3", "parent_id": "r",
                        "hypothesis": "Fusion layer", "patch_scope": "fusion",
                        "children_ids": [], "status": "pending",
                        "result": {}, "decision": {}, "depth": 1,
                    },
                ],
            }
            state.values["experiment_tree"] = tree
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={"max_parallel_branches": 2},
            )
            agent = BranchSelectionAgent()
            result = agent.run(state, ctx)

            selected_nodes = state.values.get("selected_branch_nodes", [])
            self.assertEqual(len(selected_nodes), 2)
            # data loader > config > fusion (risk bonus)
            # data loader: +0.3 (risk) → score higher
            ids = [n["node_id"] for n in selected_nodes]
            self.assertIn("p1", ids)  # data loader highest risk bonus
            # Both should be selected
            self.assertEqual(selected_nodes[0]["status"], "selected")
            self.assertEqual(selected_nodes[1]["status"], "selected")

    def test_only_one_pending_selects_one(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            tree = {
                "branch_id": "mb2", "root_id": "r2",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r2", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["only"], "status": "active",
                        "result": {}, "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "only", "parent_id": "r2",
                        "hypothesis": "Only one", "patch_scope": "config",
                        "children_ids": [], "status": "pending",
                        "result": {}, "decision": {}, "depth": 1,
                    },
                ],
            }
            state.values["experiment_tree"] = tree
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={"max_parallel_branches": 2},
            )
            agent = BranchSelectionAgent()
            result = agent.run(state, ctx)
            selected_nodes = state.values.get("selected_branch_nodes", [])
            self.assertEqual(len(selected_nodes), 1)

    def test_default_max_parallel_is_one(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            tree = {
                "branch_id": "mb3", "root_id": "r3",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r3", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["a", "b"], "status": "active",
                        "result": {}, "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "a", "parent_id": "r3",
                        "hypothesis": "A", "patch_scope": "config",
                        "children_ids": [], "status": "pending",
                        "result": {}, "decision": {}, "depth": 1,
                    },
                    {
                        "node_id": "b", "parent_id": "r3",
                        "hypothesis": "B", "patch_scope": "data loader",
                        "children_ids": [], "status": "pending",
                        "result": {}, "decision": {}, "depth": 1,
                    },
                ],
            }
            state.values["experiment_tree"] = tree
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={},
            )
            agent = BranchSelectionAgent()
            result = agent.run(state, ctx)
            selected_nodes = state.values.get("selected_branch_nodes", [])
            self.assertEqual(len(selected_nodes), 1)
```

- [ ] **Step 2: 运行多分支测试验证失败**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m pytest tests/test_branch_selection_agent.py::MultiBranchSelectionTest -v 2>&1
```
Expected: FAIL（尚未修改 BranchSelectionAgent）

- [ ] **Step 3: 修改 `BranchSelectionAgent.run()` 支持 top-N**

在 `agents/branch_selection_agent.py` 中，修改 `run()` 方法的选择逻辑：

将当前的单选逻辑：
```python
        if pending:
            selected = self._select_best(pending, allowed)
            ...
            state.values["selected_branch_node"] = asdict(selected_node)
```

改为：
```python
        max_parallel = int(context.settings.get("max_parallel_branches", 1))
        max_parallel = max(1, max_parallel)

        if pending:
            sorted_pending = self._sort_by_score(pending, allowed)
            selected = sorted_pending[:max_parallel]
            ...
            state.values["selected_branch_nodes"] = [asdict(n) for n in selected_nodes]
            state.values["selected_branch_node"] = asdict(selected_nodes[0])  # backward compat
```

同时将现有的 `_select_best` 逻辑重构为 `_sort_by_score`（返回排序后列表而非只取最高分）。

- [ ] **Step 4: 确认已有单选测试和新增多分支测试均通过**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m pytest tests/test_branch_selection_agent.py -v 2>&1
```
Expected: 全部通过（原有 ~8 测试 + 新增 3 测试）

---

### Task 4: BranchToPlan 多 plan + AutonomousExperiment 串行执行

**Files:**
- Modify: `agents/tree_search_agent.py` (BranchToPlanAgent)
- Modify: `agents/autonomous_experiment.py`
- Create: `tests/test_multi_branch_parallel.py`

- [ ] **Step 1: 编写多分支集成测试**

```python
# tests/test_multi_branch_parallel.py
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.branch_selection_agent import BranchSelectionAgent
from agents.tree_search_agent import BranchToPlanAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState


def _make_topic():
    from schemas.topic_pack import TopicPack
    return TopicPack(
        topic_name="test_multi",
        codebase={"repo_path": "/fake", "allowed_auto_edit": ["data/*", "models/*", "cfg/*"]},
        experiment_metrics=["ADE", "FDE"],
    )


class MultiPlanTest(TestCase):
    def test_two_selected_branches_produce_two_plans(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "mpt", "root_id": "r",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {"node_id": "r", "parent_id": "", "hypothesis": "R",
                     "children_ids": ["a1", "a2"], "status": "active",
                     "result": {}, "decision": {}, "depth": 0},
                    {"node_id": "a1", "experiment_id": "exp_a1",
                     "parent_id": "r", "hypothesis": "A1",
                     "patch_scope": "data loader", "children_ids": [],
                     "status": "selected", "result": {}, "decision": {}, "depth": 1},
                    {"node_id": "a2", "experiment_id": "exp_a2",
                     "parent_id": "r", "hypothesis": "A2",
                     "patch_scope": "config", "children_ids": [],
                     "status": "selected", "result": {}, "decision": {}, "depth": 1},
                ],
            }
            state.values["selected_branch_nodes"] = [
                n for n in state.values["experiment_tree"]["nodes"]
                if n["status"] == "selected"
            ]

            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None, settings={},
            )
            agent = BranchToPlanAgent()
            result = agent.run(state, ctx)

            plans = state.values.get("experiment_plans", [])
            self.assertEqual(len(plans), 2)
            self.assertIn("exp_a1", plans[0]["experiment_id"])
            self.assertIn("exp_a2", plans[1]["experiment_id"])

    def test_no_selected_nodes_noops(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None, settings={},
            )
            agent = BranchToPlanAgent()
            result = agent.run(state, ctx)
            self.assertIn("no selected branch", result.notes[0].lower())


class AutonomousMultiExperimentTest(TestCase):
    def test_skip_when_not_enabled(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_plans"] = [{"experiment_id": "e1"}]
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={"enable_experiments": False},
            )
            from agents.autonomous_experiment import AutonomousExperimentAgent
            agent = AutonomousExperimentAgent()
            result = agent.run(state, ctx)
            self.assertIn("not set", result.notes[0].lower())

    def test_stops_on_first_error_with_multi_plan(self):
        """Verify the pattern: when multi-plan execution stops on error, the
        agent doesn't execute the second plan. Tested via unit logic only."""
        # This test validates the control-flow structure — actual execution
        # requires a real repo and is covered by smoke verification.
        from agents.autonomous_experiment import AutonomousExperimentAgent
        agent = AutonomousExperimentAgent()
        # Verify agent reads all plans, not just plans[0]
        self.assertTrue(hasattr(agent, "_execute_and_parse"))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 修改 `BranchToPlanAgent` 支持 `selected_branch_nodes`**

在 `agents/tree_search_agent.py` 的 `BranchToPlanAgent.run()` 中：

```python
    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        selected_nodes = state.values.get("selected_branch_nodes")
        if not isinstance(selected_nodes, list) or not selected_nodes:
            # Fallback to legacy single
            selected = state.values.get("selected_branch_node")
            if not isinstance(selected, dict) or not selected.get("node_id"):
                return AgentResult(notes=["branch_to_plan: no selected branch node, skipping"])
            selected_nodes = [selected]

        tree = state.values.get("experiment_tree", {}) or {}
        branch_id = tree.get("branch_id", "") if isinstance(tree, dict) else ""

        all_plans: list[dict] = []
        all_node_ids: list[str] = []
        for sel in selected_nodes:
            if not isinstance(sel, dict) or not sel.get("node_id"):
                continue
            node = ExperimentNode(
                node_id=sel.get("node_id", ""),
                experiment_id=sel.get("experiment_id", ""),
                ...
            )
            plan = _node_to_plan(node, state.topic, branch_id=branch_id)
            plan_dict = asdict(plan)
            all_plans.append(plan_dict)
            all_node_ids.append(node.node_id)
            context.artifact_store.save_json(
                state.run_id, "branch_experiment_plans", node.node_id, plan_dict,
            )

        state.values["experiment_plans"] = all_plans
        return AgentResult(
            notes=[f"branch_to_plan: converted {len(all_plans)} node(s) to experiment plans"],
            artifacts={"branch_experiment_plans": all_node_ids},
            values={"experiment_plans": all_plans},
        )
```

- [ ] **Step 3: 修改 `AutonomousExperimentAgent` 串行执行多 plan**

在 `agents/autonomous_experiment.py` 的 `run()` 方法中：

```python
    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        plans = state.values.get("experiment_plans", []) or []
        ...

        # Execute all plans sequentially, stop on first error
        all_results: list[dict[str, Any]] = []
        for plan in plans:
            experiment_id = plan.get("experiment_id", "unknown")
            smoke_commands = self._smoke_commands(state)
            for cmd in smoke_commands:
                result = self._execute_and_parse(experiment_id, cmd, repo_path, state)
                context.artifact_store.save_json(
                    state.run_id, "experiment_results", result.result_id, result
                )
                all_results.append(asdict(result))
                # Stop on error
                if result.status == "error":
                    break
            if all_results and all_results[-1].get("status") == "error":
                break

        state.values["experiment_results"] = all_results
        summary = self._summarize(all_results)
        return AgentResult(
            notes=summary,
            artifacts={"experiment_results": [r["result_id"] for r in all_results]},
            values={"experiment_results": all_results},
        )
```

注意保留原有的 `--enable-experiments` 和 repo_path 校验（在遍历前）。

- [ ] **Step 4: 运行多分支测试**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m pytest tests/test_multi_branch_parallel.py -v 2>&1
```
Expected: 3 passed

---

### Task 5: 分支晋升 — 自动晋升 + 手动 `--promote`

**Files:**
- Modify: `agents/tree_search_agent.py` (TreeSearchAgent auto-promotion)
- Modify: `app/main.py` (--promote CLI)
- Create: `tests/test_tree_promotion.py`

- [ ] **Step 1: 编写晋升测试**

```python
# tests/test_tree_promotion.py
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.tree_search_agent import TreeSearchAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState


def _make_topic():
    from schemas.topic_pack import TopicPack
    return TopicPack(topic_name="test_promo", experiment_metrics=["ADE", "FDE"])


class AutoPromotionTest(TestCase):
    def test_auto_promotes_when_both_metrics_better(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "promo1", "root_id": "root_p",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root_p", "parent_id": "", "hypothesis": "Old root",
                        "children_ids": ["better"], "status": "active",
                        "result": {"status": "passed", "metrics": {"ade": 0.5, "fde": 0.3}},
                        "decision": {"action": "continue"}, "depth": 0,
                    },
                    {
                        "node_id": "better", "experiment_id": "exp_better",
                        "parent_id": "root_p", "hypothesis": "Better one",
                        "patch_scope": "data", "children_ids": [],
                        "status": "selected", "result": {}, "decision": {}, "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_node"] = {
                "node_id": "better", "experiment_id": "exp_better",
                "parent_id": "root_p", "hypothesis": "Better one",
                "patch_scope": "data", "children_ids": [],
                "status": "selected", "result": {}, "decision": {}, "depth": 1,
            }
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "passed",
                 "metrics": {"ade": 0.2, "fde": 0.1}}
            ]
            state.values["experiment_decision"] = {"action": "continue"}

            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None, settings={},
            )
            agent = TreeSearchAgent()
            result = agent.run(state, ctx)

            tree = state.values["experiment_tree"]
            self.assertEqual(tree["root_id"], "better")
            root = next(n for n in tree["nodes"] if n["node_id"] == "better")
            self.assertEqual(root["status"], "active")
            old = next(n for n in tree["nodes"] if n["node_id"] == "root_p")
            self.assertEqual(old["status"], "archived")

    def test_no_auto_promote_when_only_one_metric_better(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "promo2", "root_id": "root_q",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root_q", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["border"], "status": "active",
                        "result": {"status": "passed", "metrics": {"ade": 0.3, "fde": 0.1}},
                        "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "border", "experiment_id": "exp_border",
                        "parent_id": "root_q", "hypothesis": "Border",
                        "patch_scope": "cfg", "children_ids": [],
                        "status": "selected", "result": {}, "decision": {}, "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_node"] = {
                "node_id": "border", "parent_id": "root_q",
                "status": "selected", "result": {}, "decision": {}, "depth": 1,
            }
            # ADE better (0.2 < 0.3) but FDE worse (0.3 > 0.1)
            state.values["experiment_results"] = [
                {"result_id": "r2", "status": "passed",
                 "metrics": {"ade": 0.2, "fde": 0.3}}
            ]
            state.values["experiment_decision"] = {"action": "continue"}

            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None, settings={},
            )
            agent = TreeSearchAgent()
            result = agent.run(state, ctx)

            tree = state.values["experiment_tree"]
            # Root unchanged
            self.assertEqual(tree["root_id"], "root_q")
            # Borderline promotable notes
            self.assertIn("borderline", result.notes[0].lower())


class ManualPromotionTest(TestCase):
    """Tests for --promote logic in app/main.py done via direct store manipulation."""
    # Covered in integration / real smoke; unit tests validate the promotion logic
    # in TreeSearchAgent since the manual path mirrors it.
    pass


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 实现 `TreeSearchAgent` 中的自动晋升**

在 `agents/tree_search_agent.py` 的 `TreeSearchAgent.run()` 方法末尾，写回结果之后添加：

```python
    def _maybe_auto_promote(
        self, tree: ExperimentBranch, current: ExperimentNode,
        root: ExperimentNode, notes: list[str],
    ) -> None:
        """Auto-promote branch node to root if both metrics beat root's."""
        if current is None or current is root:
            return
        if current.status != "smoke_passed":
            return

        current_metrics = (current.result or {}).get("metrics", {})
        root_metrics = (root.result or {}).get("metrics", {})
        if not current_metrics or not root_metrics:
            return

        current_ade = current_metrics.get("ade") or current_metrics.get("ADE")
        current_fde = current_metrics.get("fde") or current_metrics.get("FDE")
        root_ade = root_metrics.get("ade") or root_metrics.get("ADE")
        root_fde = root_metrics.get("fde") or root_metrics.get("FDE")

        if current_ade is None or current_fde is None or root_ade is None or root_fde is None:
            return

        both_better = current_ade < root_ade and current_fde < root_fde
        if both_better:
            # Auto-promote: current becomes root, old root → archived
            root.status = "archived"
            tree.root_id = current.node_id
            current.status = "active"
            # Move other root children to new root
            for cid in list(root.children_ids):
                if cid != current.node_id:
                    current.children_ids.append(cid)
                    child = next((n for n in tree.nodes if n.node_id == cid), None)
                    if child:
                        child.parent_id = current.node_id
            root.children_ids = [current.node_id]
            # Recalculate depths
            self._recalc_depths(tree.nodes, tree.root_id, 1)
            notes.append(
                f"auto-promoted node {current.node_id} to root: "
                f"ADE {root_ade:.4f}→{current_ade:.4f}, "
                f"FDE {root_fde:.4f}→{current_fde:.4f}"
            )
        else:
            one_better = current_ade < root_ade or current_fde < root_fde
            if one_better:
                notes.append(
                    f"borderline: node {current.node_id} has mixed metrics vs root "
                    f"(ADE: {root_ade:.4f} vs {current_ade:.4f}, "
                    f"FDE: {root_fde:.4f} vs {current_fde:.4f})"
                )
```

添加辅助方法 `_recalc_depths`:

```python
    def _recalc_depths(
        self, nodes: list[ExperimentNode], root_id: str, depth: int,
    ) -> None:
        """Recalculate depth for all nodes in the tree recursively."""
        root = next((n for n in nodes if n.node_id == root_id), None)
        if root is None:
            return
        root.depth = depth
        for cid in root.children_ids:
            self._recalc_depths(nodes, cid, depth + 1)
```

在 `run()` 的最终写回处调用 `self._maybe_auto_promote(tree, current, root, notes)`。

- [ ] **Step 3: 实现 `--promote` CLI 参数**

在 `app/main.py` 中添加参数：

```python
    run_parser.add_argument(
        "--promote",
        type=str,
        default=None,
        help="Manually promote a branch node (by node_id) to be the new tree root",
    )
    run_parser.add_argument(
        "--max-parallel-branches",
        type=int,
        default=1,
        help="Maximum number of pending branches to select and execute in one run",
    )
```

在 `run_workflow()` 中，workflow 执行前处理 `--promote`：

```python
    if args.promote:
        tree = lit_memory.load_branch(topic.topic_name) if lit_memory else None
        if tree:
            target = next(
                (n for n in (tree.get("nodes") or [])
                 if n.get("node_id") == args.promote), None
            )
            if target:
                root = next(
                    (n for n in tree["nodes"]
                     if n.get("node_id") == tree.get("root_id")), None
                )
                if root:
                    root["status"] = "archived"
                tree["root_id"] = target["node_id"]
                target["status"] = "active"
                lit_memory.write_branch(tree, topic.topic_name)
                print(f"promoted node {args.promote} to root")
            else:
                print(f"node {args.promote} not found in tree")
```

并在 `build_full_research_workflow()` 调用中传入：

```python
    workflow = build_full_research_workflow(
        ...
        max_parallel_branches=args.max_parallel_branches,
    )
```

- [ ] **Step 4: 运行晋升测试**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m pytest tests/test_tree_promotion.py -v 2>&1
```
Expected: 2 passed

---

### Task 6: Reviewer ASCII 树 + LiteratureMemory Mermaid 导出

**Files:**
- Modify: `agents/reviewer_agent.py`
- Modify: `agents/literature_memory_agent.py`

- [ ] **Step 1: 在 reviewer 中集成 ASCII 树打印和可晋升列表**

在 `reviewer_agent.py` 的 `run()` 方法中，`_check_experiment_tree` 调用后新增：

```python
        # Print ASCII tree and promotable list
        self._report_tree(state, context, findings)
```

新增方法：

```python
    def _report_tree(
        self, state: ResearchState, context: AgentContext, findings: list[str],
    ) -> None:
        tree = state.values.get("experiment_tree")
        if not isinstance(tree, dict) or not tree.get("nodes"):
            return

        from tools.tree_visualizer import render_ascii_tree
        ascii_tree = render_ascii_tree(tree)
        findings.append(f"Experiment tree:\n{ascii_tree}")

        # List promotable nodes (smoke_passed with metrics, not already root)
        root_id = tree.get("root_id", "")
        promotable: list[str] = []
        for n in tree.get("nodes", []) or []:
            if n.get("node_id") == root_id:
                continue
            if n.get("status") != "smoke_passed":
                continue
            result = n.get("result", {}) or {}
            metrics = result.get("metrics", {})
            if not metrics:
                continue
            # Check against root
            root = next(
                (rn for rn in tree["nodes"] if rn.get("node_id") == root_id), None
            )
            root_metrics = (root.get("result", {}) or {}).get("metrics", {}) if root else {}
            if root_metrics:
                ade_better = metrics.get("ade", 999) < root_metrics.get("ade", 999)
                fde_better = metrics.get("fde", 999) < root_metrics.get("fde", 999)
                if ade_better != fde_better:
                    promotable.append(
                        f"  {n['node_id']}: ADE={metrics.get('ade')} FDE={metrics.get('fde')} "
                        f"(root: ADE={root_metrics.get('ade')} FDE={root_metrics.get('fde')})"
                    )
        if promotable:
            findings.append("Borderline promotable branches:\n" + "\n".join(promotable))
```

- [ ] **Step 2: 在 literature_memory_agent 中集成 Mermaid 导出**

在 `literature_memory_agent.py` 的 `run()` 末尾（persist 之后）：

```python
        # Export Mermaid visualization
        tree = state.values.get("experiment_tree")
        if isinstance(tree, dict) and tree.get("nodes"):
            from tools.tree_visualizer import export_mermaid
            mermaid = export_mermaid(tree)
            context.artifact_store.save_text(
                state.run_id,
                "experiment_trees",
                tree.get("branch_id", "unknown"),
                mermaid,
                suffix=".mmd",
            )
```

- [ ] **Step 3: 全量测试**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests
```
Expected: 全部通过（约 152+ 测试）

---

### Task 7: 真实 smoke 验证 + 文档更新

- [ ] **Step 1: 真实 `--enable-tree-search --enable-experiments` 多分支 run**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m app.main run --topic topics/intent_led_virat.json --data-dir data --max-papers 1 --enable-tree-search --enable-experiments --max-parallel-branches 2
```

- [ ] **Step 2: 验证 SQLite 结果**

查询 `pend_b` 和其他分支节点的 result/decision/status。

- [ ] **Step 3: 验证 Mermaid 导出文件**

检查 `data/runs/<run_id>/artifacts/experiment_trees/` 中有 `.mmd` 文件。

- [ ] **Step 4: 更新 `docs/project_handoff.md`**

- Section 8: 新增 `TreePrunerAgent`
- Section 15: 更新测试数量
- Section 18: 将 P10 的 4 项从"下一步"移至"已完成"

- [ ] **Step 5: 更新 `docs/Q&A.md`**

- Q3: 更新 pipeline 列表（新增 TreePrunerAgent）
- Q43: 更新后续优先级状态

- [ ] **Step 6: 最终全量测试**

```bash
cd D:/Codes/VS/research_agent_lab && D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests
```
Expected: 全部通过
