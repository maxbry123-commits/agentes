"""S28 · AST scanner Python determinista."""
from __future__ import annotations
import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class FunctionInfo:
    name: str
    lineno: int
    args: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    has_await: bool = False
    docstring: str = ""
    def to_dict(self):
        return asdict(self)

@dataclass
class ClassInfo:
    name: str
    lineno: int
    methods: list[str] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)
    def to_dict(self):
        return asdict(self)

@dataclass
class FileInventory:
    path: str
    imports: list[str] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    entrypoints: list[str] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)
    error: str = ""
    def to_dict(self):
        return {"path": self.path, "imports": self.imports, "functions": [f.to_dict() for f in self.functions], "classes": [c.to_dict() for c in self.classes], "entrypoints": self.entrypoints, "side_effects": self.side_effects, "error": self.error}

_SIDE = {"subprocess": "subprocess", "os": "os", "socket": "network", "requests": "network", "httpx": "network", "pathlib": "filesystem", "shutil": "filesystem", "sqlite3": "database", "docker": "docker"}

def _expr_name(node):
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute):
        b = _expr_name(node.value)
        return f"{b}.{node.attr}" if b else node.attr
    return ""

class AstScanner:
    def scan_file(self, path: Path) -> FileInventory:
        inv = FileInventory(path=str(path))
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
        except Exception as e:
            inv.error = str(e); return inv
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module or ""] + [a.name for a in node.names])
                for n in names:
                    if n and n not in inv.imports: inv.imports.append(n)
                    root = (n or "").split(".")[0]
                    if root in _SIDE and _SIDE[root] not in inv.side_effects: inv.side_effects.append(_SIDE[root])
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                calls = [_expr_name(s.func) for s in ast.walk(node) if isinstance(s, ast.Call)]
                inv.functions.append(FunctionInfo(node.name, node.lineno, [a.arg for a in node.args.args], [c for c in calls if c], isinstance(node, ast.AsyncFunctionDef), (ast.get_docstring(node) or "")[:200]))
                if node.name in ("main", "run", "execute", "serve", "cli", "worker", "start"): inv.entrypoints.append(node.name)
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                bases = [_expr_name(b) for b in node.bases]
                inv.classes.append(ClassInfo(node.name, node.lineno, methods, bases))
                if any(k in node.name.lower() for k in ("agent", "planner", "worker", "tool", "memory", "scheduler")): inv.entrypoints.append(f"class:{node.name}")
        return inv

    def scan_tree(self, root: Path, max_files: int = 200):
        out = []
        if not root.exists(): return out
        n = 0
        for p in sorted(root.rglob("*.py")):
            if any(x in p.parts for x in (".git", "venv", ".venv", "node_modules", "__pycache__")): continue
            out.append(self.scan_file(p)); n += 1
            if n >= max_files: break
        return out
