"""ArchitectureManifest — boundaries + allowed/forbidden deps (ARCH rules)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any
from pathlib import Path
import ast
import re

@dataclass
class ModulePolicy:
    name: str
    paths: List[str]
    allowed_dependencies: List[str] = field(default_factory=list)
    forbidden_dependencies: List[str] = field(default_factory=list)

@dataclass
class ArchitectureManifest:
    modules: Dict[str, ModulePolicy] = field(default_factory=dict)
    forbidden_global_imports: List[str] = field(default_factory=lambda: [
        # placeholders; extend per repo
    ])

    def add_module(self, policy: ModulePolicy) -> None:
        self.modules[policy.name] = policy

    def module_for_path(self, path: str) -> str | None:
        norm = path.replace("\\", "/")
        for name, pol in self.modules.items():
            for p in pol.paths:
                if norm.startswith(p.rstrip("*").rstrip("/")) or re.match(
                    p.replace("**", ".*").replace("*", "[^/]*"), norm
                ):
                    return name
        return None


def default_wordflow_manifest() -> ArchitectureManifest:
    m = ArchitectureManifest()
    m.add_module(ModulePolicy(
        name="domain",
        paths=["extensions/wordflow_kernel/", "extensions/wordflow/engine/"],
        allowed_dependencies=["stdlib", "extensions/wordflow/standards"],
        forbidden_dependencies=["github", "requests", "boto3", "openai"],
    ))
    m.add_module(ModulePolicy(
        name="adapters",
        paths=["extensions/wordflow/connectors/", "extensions/github_deploy/"],
        allowed_dependencies=["stdlib", "domain", "ports"],
        forbidden_dependencies=[],
    ))
    m.forbidden_global_imports = ["openai", "anthropic"]  # LLM only via gateway
    return m


def extract_imports(py_source: str) -> Set[str]:
    """Top-level and from-import module roots."""
    roots: Set[str] = set()
    try:
        tree = ast.parse(py_source)
    except SyntaxError:
        return roots
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                roots.add(node.module.split(".")[0])
    return roots


def scan_file_imports(path: Path) -> Set[str]:
    if not path.exists() or path.suffix != ".py":
        return set()
    return extract_imports(path.read_text(encoding="utf-8", errors="replace"))
