"""COPY-FIRST + auto evidence map SOURCE→DEST (G-W5)."""
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
        fixed = Path(__file__).resolve().parents[1] / "component_catalog.json"
        paths = [fixed]
        for root in self.roots:
            paths.append(root / "component_catalog.json")
        for cat in paths:
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
        hits = self.find_by_name(symbol_or_stem) + self.find_in_catalog(symbol_or_stem)
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
    meta = {
        "source": str(src),
        "dest": str(dest),
        "sha256": h,
        "action": "COPY",
        "bytes": len(text.encode("utf-8")),
    }
    # G-W5: side-car evidence map
    side = dest.parent / f"{dest.stem}.copy_evidence.json"
    side.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    meta["evidence_sidecar"] = str(side)
    return meta
