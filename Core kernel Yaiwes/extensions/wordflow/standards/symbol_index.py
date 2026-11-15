"""G-W3/U5 — índice AST. G-W3b = cache disco + cache en proceso."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SymbolHit:
    name: str
    kind: str
    path: str
    lineno: int


@dataclass
class SymbolIndex:
    by_name: dict[str, list[SymbolHit]] = field(default_factory=dict)

    def add(self, hit: SymbolHit) -> None:
        self.by_name.setdefault(hit.name, []).append(hit)

    def find(self, name: str) -> list[SymbolHit]:
        return list(self.by_name.get(name, []))

    def find_substring(self, partial: str) -> list[SymbolHit]:
        partial_l = partial.lower()
        out: list[SymbolHit] = []
        for name, hits in self.by_name.items():
            if partial_l in name.lower():
                out.extend(hits)
        return out

    def to_payload(self) -> dict:
        return {
            name: [
                {"name": h.name, "kind": h.kind, "path": h.path, "lineno": h.lineno}
                for h in hits
            ]
            for name, hits in self.by_name.items()
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "SymbolIndex":
        idx = cls()
        for name, hits in (payload or {}).items():
            for raw in hits:
                idx.add(
                    SymbolHit(
                        name=str(raw.get("name") or name),
                        kind=str(raw.get("kind") or ""),
                        path=str(raw.get("path") or ""),
                        lineno=int(raw.get("lineno") or 0),
                    )
                )
        return idx


_CACHE: dict[tuple[str, ...], SymbolIndex] = {}


def _kind(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, ast.FunctionDef):
        return "function"
    if isinstance(node, ast.AsyncFunctionDef):
        return "async_function"
    return None


def index_file(path: Path) -> list[SymbolHit]:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return []
    hits: list[SymbolHit] = []
    for node in tree.body:
        k = _kind(node)
        if k and hasattr(node, "name"):
            hits.append(SymbolHit(name=node.name, kind=k, path=str(path), lineno=getattr(node, "lineno", 0)))
    return hits


def _disk_cache_file(key: tuple[str, ...]) -> Path:
    env = os.environ.get("WORDFLOW_SYMBOL_CACHE")
    base = Path(env) if env else Path(tempfile.gettempdir()) / "wordflow_symbol_cache"
    digest = hashlib.sha256("|".join(key).encode("utf-8")).hexdigest()[:16]
    return base / f"symbols_{digest}.json"


def _load_disk(key: tuple[str, ...]) -> SymbolIndex | None:
    path = _disk_cache_file(key)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return SymbolIndex.from_payload(payload.get("by_name") or {})


def _save_disk(key: tuple[str, ...], idx: SymbolIndex) -> str:
    path = _disk_cache_file(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"by_name": idx.to_payload()}, indent=2) + "\n", encoding="utf-8")
    return str(path)


def build_symbol_index(
    roots: list[Path],
    limit_files: int = 500,
    *,
    use_cache: bool = True,
    use_disk: bool = True,
) -> SymbolIndex:
    key = tuple(sorted(str(r.resolve()) if r.exists() else str(r) for r in roots)) + (str(limit_files),)
    if use_cache and key in _CACHE:
        return _CACHE[key]
    if use_cache and use_disk:
        disk = _load_disk(key)
        if disk is not None:
            _CACHE[key] = disk
            return disk
    idx = SymbolIndex()
    n = 0
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            if n >= limit_files:
                if use_cache:
                    _CACHE[key] = idx
                    if use_disk:
                        _save_disk(key, idx)
                return idx
            for hit in index_file(p):
                idx.add(hit)
            n += 1
    if use_cache:
        _CACHE[key] = idx
        if use_disk:
            _save_disk(key, idx)
    return idx


def clear_symbol_cache() -> None:
    _CACHE.clear()
