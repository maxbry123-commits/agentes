"""Contract Graph Resolver — dependencias y ciclos.
SOURCE: SALIDA_4 §14.6
"""
from __future__ import annotations

# Dependencias mínimas: si está C50 → activar C03, C31, C42 (ejemplo doc)
DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "C50": ("C03", "C31", "C42"),
    "C47": ("C45", "C48"),
    "C35": ("C34",),
    "C55": ("C52", "C53", "C54"),
}


def expand(contracts: list[str] | tuple[str, ...]) -> list[str]:
    result = set(contracts)
    changed = True
    while changed:
        changed = False
        for c in list(result):
            for dep in DEPENDENCIES.get(c, ()):
                if dep not in result:
                    result.add(dep)
                    changed = True
    return sorted(result)


def has_cycle(edges: dict[str, list[str]]) -> bool:
    visited: set[str] = set()
    stack: set[str] = set()

    def dfs(n: str) -> bool:
        visited.add(n)
        stack.add(n)
        for m in edges.get(n, []):
            if m not in visited:
                if dfs(m):
                    return True
            elif m in stack:
                return True
        stack.discard(n)
        return False

    return any(dfs(n) for n in edges if n not in visited)
