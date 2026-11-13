"""EXTRA CG — text → DAG dict. Not a full lexer."""
from __future__ import annotations

from typing import Any


def text_to_dag(text: str) -> dict[str, Any]:
    lines = [ln.strip() for ln in str(text).splitlines() if ln.strip()]
    nodes = []
    edges = []
    prev = None
    for i, line in enumerate(lines, start=1):
        nid = f"n{i}"
        nodes.append({"id": nid, "label": line})
        if prev:
            edges.append({"from": prev, "to": nid})
        prev = nid
    if not nodes:
        nodes.append({"id": "n1", "label": str(text).strip() or "empty"})
    return {"ok": True, "type": "dag", "nodes": nodes, "edges": edges}


if __name__ == "__main__":
    dag = text_to_dag("intake\nnormalize\nlock")
    assert dag["ok"] and len(dag["nodes"]) == 3 and len(dag["edges"]) == 2
    print("ok", [n["id"] for n in dag["nodes"]])
