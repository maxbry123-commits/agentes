"""Skills/transforms deterministas para D4 DAG.
SOURCE: research D4 · 0% LLM
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DagResult:
    ok: bool
    errors: tuple[str, ...]
    order: tuple[str, ...] = ()


def parse_dag_yaml(path: str | Path) -> dict[str, Any]:
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _edges(nodes: list[dict[str, Any]]) -> dict[str, list[str]]:
    g: dict[str, list[str]] = {n["id"]: list(n.get("depends_on") or []) for n in nodes}
    return g


def has_cycle(nodes: list[dict[str, Any]]) -> bool:
    deps = _edges(nodes)
    # reverse: node -> children
    children: dict[str, list[str]] = {n: [] for n in deps}
    for n, ds in deps.items():
        for d in ds:
            children.setdefault(d, []).append(n)
    indeg = {n: len(deps.get(n, [])) for n in deps}
    for d in list(indeg):
        for c in children.get(d, []):
            indeg.setdefault(c, 0)
    q = [n for n, i in indeg.items() if i == 0]
    seen = 0
    while q:
        n = q.pop()
        seen += 1
        for c in children.get(n, []):
            indeg[c] -= 1
            if indeg[c] == 0:
                q.append(c)
    return seen != len(indeg)


def topo_sort(nodes: list[dict[str, Any]]) -> list[str]:
    deps = _edges(nodes)
    children: dict[str, list[str]] = {n: [] for n in deps}
    for n, ds in deps.items():
        for d in ds:
            children.setdefault(d, []).append(n)
    indeg = {n: len(deps.get(n, [])) for n in deps}
    for d in list(indeg):
        for c in children.get(d, []):
            indeg.setdefault(c, 0)
    q = sorted(n for n, i in indeg.items() if i == 0)
    order: list[str] = []
    while q:
        n = q.pop(0)
        order.append(n)
        for c in sorted(children.get(n, [])):
            indeg[c] -= 1
            if indeg[c] == 0:
                q.append(c)
                q.sort()
    return order


def validate_dag(data: dict[str, Any], known_caps: set[str] | None = None) -> DagResult:
    errors: list[str] = []
    nodes = data.get("nodes") or []
    if not nodes:
        return DagResult(False, ("empty nodes",))
    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)):
        errors.append("duplicate node id")
    for n in nodes:
        for d in n.get("depends_on") or []:
            if d not in ids:
                errors.append(f"depends_on unknown: {d}")
        if known_caps is not None:
            for c in n.get("required_capabilities") or []:
                if c not in known_caps:
                    errors.append(f"unknown capability: {c}")
    if has_cycle(nodes):
        errors.append("cycle detected")
    rules = data.get("rules") or {}
    entry = rules.get("entry")
    if entry and entry not in ids:
        errors.append(f"entry not in nodes: {entry}")
    order = tuple(topo_sort(nodes)) if not errors else ()
    return DagResult(ok=len(errors) == 0, errors=tuple(errors), order=order)


def validate_dag_file(path: str | Path, known_caps: set[str] | None = None) -> DagResult:
    return validate_dag(parse_dag_yaml(path), known_caps)
