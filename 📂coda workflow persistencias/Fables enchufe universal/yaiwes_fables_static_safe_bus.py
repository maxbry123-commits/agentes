from __future__ import annotations
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List

@dataclass(frozen=True)
class StaticSymbol:
    name: str
    kind: str

def extract_python_symbols(source: str) -> List[StaticSymbol]:
    tree = ast.parse(source)
    symbols: List[StaticSymbol] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(StaticSymbol(node.name, "function"))
        elif isinstance(node, ast.ClassDef):
            symbols.append(StaticSymbol(node.name, "class"))
    return symbols

def inspect_file(path: str | Path) -> List[StaticSymbol]:
    return extract_python_symbols(Path(path).read_text(encoding="utf-8"))

def compatible(expone: dict, consume: dict) -> bool:
    return bool(expone) and expone.get("datatype") == consume.get("datatype")
