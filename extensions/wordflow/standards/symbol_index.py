"""G-W3 — índice de símbolos AST (defs) para reuse/COPY-FIRST."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import ast

@dataclass
class SymbolHit:
    name: str
    kind: str  # class | function | async_function
    path: str
    lineno: int

@dataclass
class SymbolIndex:
    by_name: Dict[str, List[SymbolHit]] = field(default_factory=dict)

    def add(self, hit: SymbolHit) -> None:
        self.by_name.setdefault(hit.name, []).append(hit)

    def find(self, name: str) -> List[SymbolHit]:
        return list(self.by_name.get(name, []))

    def find_substring(self, partial: str) -> List[SymbolHit]:
        partial_l = partial.lower()
        out: List[SymbolHit] = []
        for name, hits in self.by_name.items():
            if partial_l in name.lower():
                out.extend(hits)
        return out


def _kind(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, ast.FunctionDef):
        return "function"
    if isinstance(node, ast.AsyncFunctionDef):
        return "async_function"
    return None


def index_file(path: Path) -> List[SymbolHit]:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return []
    hits: List[SymbolHit] = []
    for node in tree.body:
        k = _kind(node)
        if k and hasattr(node, "name"):
            hits.append(SymbolHit(name=node.name, kind=k, path=str(path), lineno=getattr(node, "lineno", 0)))
    return hits


def build_symbol_index(roots: List[Path], limit_files: int = 500) -> SymbolIndex:
    idx = SymbolIndex()
    n = 0
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            if n >= limit_files:
                return idx
            for hit in index_file(p):
                idx.add(hit)
            n += 1
    return idx
