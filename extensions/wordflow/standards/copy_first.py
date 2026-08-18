"""COPY-FIRST — scanner por nombre + component_catalog (mejora índice)."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib
import json

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

class ExistingCodeScanner:
    def __init__(self, roots: Optional[List[Path]] = None):
        self.roots = roots or []

    def _hash_prefix(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12]

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

    def find_in_catalog(self, stem: str) -> List[SourceHit]:
        hits: List[SourceHit] = []
        for root in self.roots:
            cat = root / "component_catalog.json"
            if not cat.exists():
                # wordflow root catalog
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
        # also fixed path used by list_connections
        fixed = Path(__file__).resolve().parents[1] / "component_catalog.json"
        if fixed.exists():
            try:
                data = json.loads(fixed.read_text(encoding="utf-8"))
                for comp in data.get("components", []):
                    cid = str(comp.get("id", ""))
                    path = str(comp.get("path", ""))
                    if stem in cid or stem in path:
                        hits.append(SourceHit(path, f"catalog:{cid}", ""))
            except (OSError, json.JSONDecodeError):
                pass
        return hits

    def plan(self, *, symbol_or_stem: str, dest: str, force_generate: bool = False) -> CopyFirstResult:
        hits = self.find_by_name(symbol_or_stem) + self.find_in_catalog(symbol_or_stem)
        # dedupe by path
        seen = set()
        uniq: List[SourceHit] = []
        for h in hits:
            if h.path not in seen:
                seen.add(h.path)
                uniq.append(h)
        if uniq and not force_generate:
            plan = CopyPlan(action="ADAPT", sources=uniq, dest=dest, notes="existing code found")
            return CopyFirstResult(plan, True, "GENERATE blocked: existing sources found")
        if force_generate:
            return CopyFirstResult(CopyPlan("GENERATE", [], dest, "force_generate"), False, "GENERATE allowed")
        return CopyFirstResult(CopyPlan("GENERATE", [], dest, "no match"), False, "no existing match — GENERATE last")


def copy_file_deterministic(src: Path, dest: Path) -> Dict[str, Any]:
    text = src.read_text(encoding="utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {"source": str(src), "dest": str(dest), "sha256": h, "action": "COPY", "bytes": len(text.encode("utf-8"))}
