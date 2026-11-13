"""Render experiment trees as ASCII art or Mermaid flowcharts."""

from __future__ import annotations


def render_ascii_tree(tree: dict) -> str:
    """Render an experiment tree as terminal-friendly ASCII art.

    Parameters
    ----------
    tree : dict
        Experiment tree with keys: branch_id, root_id, status, max_depth,
        max_active_nodes, nodes (list of node dicts).

    Returns
    -------
    str
        ASCII art representation of the tree.
    """
    nodes = tree.get("nodes", [])
    if not nodes:
        return "(empty tree)"

    root_id = tree.get("root_id", "")
    if not root_id:
        return "(no root node)"

    node_map = {n["node_id"]: n for n in nodes}
    root = node_map.get(root_id)
    if root is None:
        return "(no root node)"

    lines: list[str] = []
    _render_ascii_node(root, node_map, "", True, lines)
    return "\n".join(lines)


def _render_ascii_node(
    node: dict,
    node_map: dict,
    prefix: str,
    is_last: bool,
    lines: list[str],
    visited: set[str] | None = None,
) -> None:
    """Recursively render a single node and its children into *lines*."""
    if visited is None:
        visited = set()
    nid = node.get("node_id", "")
    if nid in visited:
        lines.append(prefix + ("└── " if is_last else "├── ") + f"{nid} [cycle, skipping]")
        return
    visited.add(nid)

    connector = "└── " if is_last else "├── "
    lines.append(prefix + connector + _format_ascii_label(node))

    children_ids = node.get("children_ids", [])
    if not children_ids:
        return

    children = [node_map[cid] for cid in children_ids if cid in node_map]
    child_prefix = prefix + ("    " if is_last else "│   ")
    for idx, child in enumerate(children):
        _render_ascii_node(child, node_map, child_prefix, idx == len(children) - 1, lines, visited)


def _format_ascii_label(node: dict) -> str:
    """Build the display string for a single ASCII tree node."""
    parts = [f'{node["node_id"]} [{node["status"]}]']

    hypothesis = (node.get("hypothesis") or "").replace("\n", " ").replace("\r", "")
    if hypothesis:
        if len(hypothesis) > 40:
            hypothesis = hypothesis[:37] + "..."
        parts.append(f'"{hypothesis}"')

    result = node.get("result", {})
    metrics = result.get("metrics", {})
    if metrics:
        metric_strs = [f"{k}={v}" for k, v in metrics.items()]
        parts.append(f"({', '.join(metric_strs)})")

    return " ".join(parts)


def export_mermaid(tree: dict) -> str:
    """Export an experiment tree as a Mermaid flowchart (graph TD).

    Parameters
    ----------
    tree : dict
        Experiment tree with the same format as *render_ascii_tree*.

    Returns
    -------
    str
        Mermaid flowchart syntax.
    """
    nodes = tree.get("nodes", [])
    if not nodes:
        return "graph TD\n    empty[No nodes]"

    root_id = tree.get("root_id", "")
    if not root_id:
        return "graph TD\n    empty[No nodes]"

    node_map = {n["node_id"]: n for n in nodes}
    root = node_map.get(root_id)
    if root is None:
        return "graph TD\n    empty[No nodes]"

    lines = ["graph TD"]
    id_counter = 0
    id_map: dict[str, str] = {}

    def _mermaid_id(node_id: str) -> str:
        nonlocal id_counter
        if node_id not in id_map:
            id_map[node_id] = f"N{id_counter}"
            id_counter += 1
        return id_map[node_id]

    def _mermaid_shape(status: str) -> tuple[str, str]:
        shapes = {
            "active": ("[", "]"),
            "smoke_passed": ("(", ")"),
            "pending": ("{", "}"),
            "selected": ("{{", "}}"),
            "branched": ("[\\", "\\]"),
            "max_depth_reached": ("[", "]"),
            "blocked_max_active": ("[", "]"),
            "archived": ("[(", ")]"),
        }
        return shapes.get(status, ("[", "]"))

    def _traverse(node: dict, visited: set[str] | None = None) -> None:
        if visited is None:
            visited = set()
        nid = _mermaid_id(node["node_id"])
        raw_id = node.get("node_id", "")
        if raw_id in visited:
            return
        visited.add(raw_id)

        # Build label: node_id + status on separate lines, plus metrics if available
        label_parts = [f"{node['node_id']}<br/>{node['status']}"]
        result = node.get("result", {})
        metrics = result.get("metrics", {})
        if metrics:
            metric_strs = [f"{k}={v}" for k, v in metrics.items()]
            label_parts.append("<br/>" + ", ".join(metric_strs))

        label = "".join(label_parts).replace('"', "'")

        open_ch, close_ch = _mermaid_shape(node["status"])
        lines.append(f"    {nid}{open_ch}{label}{close_ch}")

        for cid in node.get("children_ids", []):
            if cid in node_map:
                cnid = _mermaid_id(cid)
                lines.append(f"    {nid} --> {cnid}")
                _traverse(node_map[cid], visited)

    _traverse(root)
    return "\n".join(lines)
