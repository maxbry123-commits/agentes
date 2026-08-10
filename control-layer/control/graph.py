# -*- coding: utf-8 -*-
"""control/graph.py — Dependency Graph Builder 0% LLM.
Fuente: SALIDA 4 §14.5 · CAPA_CONTROL_1 A5
A → B (A requiere B). Orden topológico.
"""
from __future__ import annotations

from typing import Dict, List, Set


# deps mínimas seed (C_id → requiere)
DEFAULT_DEPS: Dict[str, List[str]] = {
    "C00": [],
    "C01": ["C00"],
    "C02": ["C00"],
    "C03": ["C00"],
    "C04": ["C03"],
    "C27": ["C03", "C04"],
    "C28": ["C03"],
    "C29": ["C27"],
    "C33": ["C03"],
    "C35": ["C27", "C29"],
    "C36": ["C33"],
    "C37": ["C36"],
    "C38": ["C36"],
    "C40": ["C33"],
    "C41": ["C03", "C28"],
    "C42": ["C40"],
    "C43": ["C41"],
    "C44": ["C41"],
    "C45": ["C03"],
    "C47": ["C45"],
    "C48": ["C45"],
    "C49": ["C48"],
    "C51": ["C00"],
    "C52": ["C51"],
    "C53": ["C51"],
    "C54": ["C52"],
    "C55": ["C53"],
    "C73": ["C41", "C49"],
    "C82": ["C51"],
    "C83": ["C82"],
    "C84": ["C82"],
    "C85": ["C83", "C84"],
}


def expand_deps(contracts: List[str], deps: Dict[str, List[str]] | None = None) -> Set[str]:
    """Cierra transitivamente el set de contratos con sus deps."""
    d = deps or DEFAULT_DEPS
    result: Set[str] = set(contracts)
    stack = list(contracts)
    while stack:
        c = stack.pop()
        for req in d.get(c, []):
            if req not in result:
                result.add(req)
                stack.append(req)
    return result


def topo_sort(contracts: Set[str], deps: Dict[str, List[str]] | None = None) -> List[str]:
    """Orden topológico Kahn. Ciclo → ValueError."""
    d = deps or DEFAULT_DEPS
    nodes = set(contracts)
    indeg: Dict[str, int] = {n: 0 for n in nodes}
    adj: Dict[str, List[str]] = {n: [] for n in nodes}
    for n in nodes:
        for req in d.get(n, []):
            if req in nodes:
                adj[req].append(n)
                indeg[n] += 1
    queue = sorted(n for n in nodes if indeg[n] == 0)
    order: List[str] = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for m in sorted(adj[n]):
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
                queue.sort()
    if len(order) != len(nodes):
        raise ValueError("ciclo en grafo de contratos")
    return order


def build_graph(contracts: List[str], deps: Dict[str, List[str]] | None = None) -> List[str]:
    """expand + topo. Mismo input → mismo orden."""
    closed = expand_deps(contracts, deps)
    return topo_sort(closed, deps)
