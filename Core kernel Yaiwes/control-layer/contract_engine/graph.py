"""Contract Graph Resolver · dependencias + detección de ciclos · 0% LLM."""
from __future__ import annotations

from typing import Dict, Iterable, List, Set, Tuple


class CycleError(Exception):
    """Dependencias de contratos forman un ciclo."""

    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        super().__init__(f"cycle_detected: {' -> '.join(cycle)}")


def expand_dependencies(
    contracts: Iterable[str],
    depends: Dict[str, List[str]],
) -> Set[str]:
    """Cierre transitivo de dependencias. Lanza CycleError si hay ciclo."""
    result: Set[str] = set(contracts)
    stack = list(contracts)
    visiting: Set[str] = set()
    path: List[str] = []

    def visit(node: str) -> None:
        if node in visiting:
            i = path.index(node) if node in path else 0
            raise CycleError(path[i:] + [node])
        if node in result and node not in depends:
            return
        visiting.add(node)
        path.append(node)
        for dep in depends.get(node, []):
            result.add(dep)
            visit(dep)
        path.pop()
        visiting.remove(node)

    for c in list(stack):
        visit(c)
    return result


def topological_order(contracts: Set[str], depends: Dict[str, List[str]]) -> List[str]:
    """Orden estable: deps antes que dependientes; desempate por id."""
    expanded = expand_dependencies(contracts, depends)
    indeg = {c: 0 for c in expanded}
    children: Dict[str, List[str]] = {c: [] for c in expanded}
    for c in expanded:
        for d in depends.get(c, []):
            if d in expanded:
                children[d].append(c)
                indeg[c] = indeg.get(c, 0) + 1
    ready = sorted([c for c, n in indeg.items() if n == 0])
    order: List[str] = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for ch in sorted(children.get(n, [])):
            indeg[ch] -= 1
            if indeg[ch] == 0:
                ready.append(ch)
                ready.sort()
    if len(order) != len(expanded):
        raise CycleError(["<unresolved_cycle>"])
    return order
