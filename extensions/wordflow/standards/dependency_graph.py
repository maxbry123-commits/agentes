"""DependencyGraph — cycle detection + import edges (RULE-003/004)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
from pathlib import Path
from .architecture_manifest import scan_file_imports

@dataclass
class DependencyGraph:
    nodes: Set[str] = field(default_factory=set)
    edges: Dict[str, Set[str]] = field(default_factory=dict)  # file -> imported roots

    def add_file(self, file_path: str, imports: Set[str]) -> None:
        self.nodes.add(file_path)
        self.edges[file_path] = set(imports)

    def build_from_paths(self, paths: List[Path]) -> None:
        for p in paths:
            if p.suffix == ".py" and p.is_file():
                self.add_file(str(p), scan_file_imports(p))

    def find_cycles_module_level(self) -> List[List[str]]:
        """Approximate cycles on module-root graph (not full AST call graph)."""
        # Build reverse: module -> modules that import it (among project files only)
        module_imports: Dict[str, Set[str]] = {}
        for f, imps in self.edges.items():
            mod = Path(f).stem
            module_imports.setdefault(mod, set()).update(imps)
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        stack: Set[str] = set()

        def dfs(node: str, path: List[str]) -> None:
            if node in stack:
                if node in path:
                    i = path.index(node)
                    cycles.append(path[i:] + [node])
                return
            if node in visited:
                return
            visited.add(node)
            stack.add(node)
            for dep in module_imports.get(node, set()):
                if dep in module_imports:  # only project-ish modules
                    dfs(dep, path + [node])
            stack.discard(node)

        for n in list(module_imports.keys()):
            dfs(n, [])
        return cycles

    def forbidden_hits(self, forbidden: List[str]) -> List[Tuple[str, str]]:
        hits: List[Tuple[str, str]] = []
        for f, imps in self.edges.items():
            for imp in imps:
                if imp in forbidden:
                    hits.append((f, imp))
        return hits
