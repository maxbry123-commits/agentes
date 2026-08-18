"""COPY-FIRST + catalog + multi-repo + AST symbols (G-W3)."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib
import json
import os

from .symbol_index import build_symbol_index, SymbolHit

@dataclass
class SourceHit:
    path: str
    reason: str
    sha256_prefix: str = ""

@dataclass
class CopyPlan:
    action: str
    sources: List[SourceHit] = field(default_factory=list)
    dest: str = ""
    notes: str = ""

@dataclass
class CopyFirstResult:
    plan: CopyPlan
    blocked_generate: bool
    message: str

def default_multi_repo_roots() -> List[Path]:
    roots: List[Path] = []
    env = os.environ.get("WORDFLOW_SCAN_ROOTS", "")
    if env:
        for part in env.split(os.pathsep):
            p = Path(part.strip())
            if p.exists():
                roots.append(p)
    wf = Path(__file__).resolve().parents[1]
    roots.append(wf)
    kernel = wf.parent / "wordflow_kernel"
    if kernel.exists():
        roots.append(kernel)
    seen, out = set(), []
    for r in roots:
        s = str(r.resolve())
        if s not in seen:
            seen.add(s)
            out.append(r)
    return out

class ExistingCodeScanner:
    def __init__(self, roots: Optional[List[Path]] = None):
        self.roots = roots if roots is not None else default_multi_repo_roots()
        self._symbol_index = None

    def _hash_prefix(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12]

    def symbols(self):
        if self._symbol_index is None:
            self._symbol_index = build_symbol_index(self.roots)
        return self._symbol_index

    def find_by_name(self, stem: str) -> List[SourceHit]:
        hits: List[SourceHit] = []
        for root in self.roots:
            if not root.exists():
                continue
            for p in root.rglob("*.py"):
                if p.stem == stem or stem in p.stem:
                    try:
                        data = p.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        data = ""
                    hits.append(SourceHit(str(p), f"name_match:{stem}", self._hash_prefix(data)))
        return hits

    def find_by_symbol(self, name: str) -> List[SourceHit]:
        hits: List[SourceHit] = []
        for sh in self.symbols().find(name) + self.symbols().find_substring(name):
            hits.append(SourceHit(sh.path, f"ast:{sh.kind}:{sh.name}:{sh.lineno}", ""))
        return hits

    def find_in_catalog(self, stem: str) -> List[SourceHit]:
        hits: List[SourceHit] = []
        for root in self.roots:
            cat = root / "component_catalog.json"
            if not cat.exists():
                continue
            try:
                data = json.loads(cat.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for comp in data.get("components", []):
                cid = str(comp.get("id", ""))
                path = str(comp.get("path", ""))
                if stem in cid or stem in path:
                    hits.append(SourceHit(path, f"catalog:{cid}", ""))
        return hits

    def plan(self, *, symbol_or_stem: str, dest: str, force_generate: bool = False) -> CopyFirstResult:
        hits = (
            self.find_by_name(symbol_or_stem)
            + self.find_in_catalog(symbol_or_stem)
            + self.find_by_symbol(symbol_or_stem)
        )
        seen, uniq = set(), []
        for h in hits:
            if h.path not in seen:
                seen.add(h.path)
                uniq.append(h)
        if uniq and not force_generate:
            return CopyFirstResult(CopyPlan("ADAPT", uniq, dest, "existing found"), True, "GENERATE blocked")
        if force_generate:
            return CopyFirstResult(CopyPlan("GENERATE", [], dest, "force"), False, "GENERATE allowed")
        return CopyFirstResult(CopyPlan("GENERATE", [], dest, "no match"), False, "GENERATE last")


def copy_file_deterministic(src: Path, dest: Path) -> Dict[str, Any]:
    text = src.read_text(encoding="utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    meta = {"source": str(src), "dest": str(dest), "sha256": h, "action": "COPY", "bytes": len(text.encode("utf-8"))}
    side = dest.parent / f"{dest.stem}.copy_evidence.json"
    side.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    meta["evidence_sidecar"] = str(side)
    return meta
