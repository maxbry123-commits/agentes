"""COPY-FIRST — obligatorio antes de GENERATE (ejecutor + forense)."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib

@dataclass
class SourceHit:
    path: str
    reason: str
    sha256_prefix: str = ""

@dataclass
class CopyPlan:
    action: str  # COPY | LINK | PATCH | ADAPT | GENERATE
    sources: List[SourceHit] = field(default_factory=list)
    dest: str = ""
    notes: str = ""

    def allows_generate(self) -> bool:
        return self.action == "GENERATE" and len(self.sources) == 0

@dataclass
class CopyFirstResult:
    plan: CopyPlan
    blocked_generate: bool
    message: str

class ExistingCodeScanner:
    """Busca code existente; si hay match → COPY/ADAPT, no GENERATE desde 0."""

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

    def plan(
        self,
        *,
        symbol_or_stem: str,
        dest: str,
        force_generate: bool = False,
    ) -> CopyFirstResult:
        hits = self.find_by_name(symbol_or_stem)
        if hits and not force_generate:
            plan = CopyPlan(action="ADAPT", sources=hits, dest=dest, notes="existing code found — COPY/ADAPT required")
            return CopyFirstResult(plan, blocked_generate=True, message="GENERATE blocked: existing sources found")
        if force_generate:
            plan = CopyPlan(action="GENERATE", sources=[], dest=dest, notes="force_generate explicit")
            return CopyFirstResult(plan, blocked_generate=False, message="GENERATE allowed by force flag")
        plan = CopyPlan(action="GENERATE", sources=[], dest=dest, notes="no existing match")
        return CopyFirstResult(plan, blocked_generate=False, message="no existing match — GENERATE last resort")


def copy_file_deterministic(src: Path, dest: Path) -> Dict[str, Any]:
    """Copia literal source→dest; retorna evidencia."""
    text = src.read_text(encoding="utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "source": str(src),
        "dest": str(dest),
        "sha256": h,
        "action": "COPY",
        "bytes": len(text.encode("utf-8")),
    }
