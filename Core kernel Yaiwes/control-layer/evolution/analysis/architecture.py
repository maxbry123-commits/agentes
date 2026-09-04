"""Architecture Analyzer."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from .ast_scanner import AstScanner, FileInventory

@dataclass
class ArchitectureMap:
    root: str
    components: list[dict[str, Any]] = field(default_factory=list)
    fingerprint: dict[str, bool] = field(default_factory=dict)
    imports_global: list[str] = field(default_factory=list)
    entrypoints: list[str] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)
    file_count: int = 0
    def to_dict(self): return asdict(self)

_FP = {
    "has_agent_loop": ("agent_loop", "run_agent", "autonomous"),
    "has_planner": ("planner", "plan_next"),
    "has_tools": ("tool", "tools", "tool_router"),
    "has_workers": ("worker", "workers", "queue"),
    "has_memory": ("memory", "vectorstore", "embedding"),
    "has_code_gen": ("generate_code", "code_gen", "apply_patch"),
    "has_workflow": ("workflow", "n8n", "dag", "pipeline"),
    "has_browser": ("playwright", "selenium", "browser"),
    "has_git": ("git", "repo"),
    "has_llm": ("openai", "anthropic", "llm"),
}

class ArchitectureAnalyzer:
    def __init__(self):
        self.scanner = AstScanner()
    def analyze_path(self, root):
        root_p = Path(root)
        return self.analyze_inventories(str(root_p), self.scanner.scan_tree(root_p))
    def analyze_inventories(self, root, invs):
        am = ArchitectureMap(root=root, file_count=len(invs))
        blob = []
        for inv in invs:
            am.imports_global.extend(inv.imports)
            am.entrypoints.extend(inv.entrypoints)
            for s in inv.side_effects:
                if s not in am.side_effects: am.side_effects.append(s)
            for fn in inv.functions:
                am.components.append({"name": fn.name, "path": inv.path, "kind": "function", "calls": fn.calls[:20], "side_effects": inv.side_effects, "lineno": fn.lineno})
                blob += [fn.name.lower()] + [c.lower() for c in fn.calls]
            for cls in inv.classes:
                am.components.append({"name": cls.name, "path": inv.path, "kind": "class", "methods": cls.methods, "bases": cls.bases, "side_effects": inv.side_effects})
                blob += [cls.name.lower()] + [m.lower() for m in cls.methods]
        text = " ".join(blob + [i.lower() for i in am.imports_global])
        for k, tokens in _FP.items():
            am.fingerprint[k] = any(t in text for t in tokens)
        am.imports_global = sorted(set(am.imports_global))[:200]
        am.entrypoints = sorted(set(am.entrypoints))
        return am
