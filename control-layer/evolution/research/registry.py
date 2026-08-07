"""Research Registry · candidatos a evolve_path."""
from __future__ import annotations
import json, re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class ResearchCandidate:
    identity: str
    source_type: str
    repo_url: str = ""
    ref: str = "main"
    local_path: str = ""
    evidence_level: str = "E0"
    evidence: list = field(default_factory=list)
    score: float = 0.0
    meta: dict = field(default_factory=dict)
    def to_dict(self): return asdict(self)

class ResearchRegistry:
    def __init__(self, store_path="evolution/research_registry.json"):
        self.path = Path(store_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.candidates = []
        self._load()
    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.candidates = [ResearchCandidate(**c) for c in data.get("candidates", [])]
            except Exception:
                self.candidates = []
    def save(self):
        self.path.write_text(json.dumps({"candidates": [c.to_dict() for c in self.candidates]}, indent=2), encoding="utf-8")
    def add_local(self, identity, path, source_type="agent"):
        c = ResearchCandidate(identity, source_type, local_path=path, evidence_level="E0", evidence=[f"local:{path}"], score=0.9)
        self.candidates.append(c); self.save(); return c
    def add_git(self, identity, repo_url, ref="main", source_type="agent", evidence_level="E1"):
        c = ResearchCandidate(identity, source_type, repo_url=repo_url, ref=ref, evidence_level=evidence_level, evidence=[f"git:{repo_url}@{ref}"], score=0.8)
        self.candidates.append(c); self.save(); return c
    def parse_query_hints(self, query):
        out = []
        for m in re.finditer(r"https?://github\.com/([\w\-\.]+)/([\w\-\.]+)", query):
            owner, repo = m.group(1), m.group(2).rstrip("/").removesuffix(".git")
            out.append(ResearchCandidate(repo.lower().replace("-", "_"), "software", repo_url=f"https://github.com/{owner}/{repo}", evidence_level="E1", evidence=[f"query_url:{m.group(0)}"], score=0.75))
        kw = {"n8n": ("n8n", "https://github.com/n8n-io/n8n", "software"), "graphiti": ("graphiti", "https://github.com/getzep/graphiti", "software"), "playwright": ("playwright", "https://github.com/microsoft/playwright", "software")}
        low = query.lower()
        for key, (ident, url, st) in kw.items():
            if key in low:
                out.append(ResearchCandidate(ident, st, repo_url=url, evidence_level="E1", evidence=[f"keyword:{key}"], score=0.7))
        for c in out: self.candidates.append(c)
        if out: self.save()
        return out
    def list_candidates(self, min_score=0.0):
        return [c.to_dict() for c in self.candidates if c.score >= min_score]
    def to_evolve_kwargs(self, candidate):
        if isinstance(candidate, dict):
            candidate = ResearchCandidate(**{k: candidate[k] for k in ResearchCandidate.__dataclass_fields__ if k in candidate})
        kw = {"identity": candidate.identity, "source_type": candidate.source_type, "repo_url": candidate.repo_url, "ref": candidate.ref}
        if candidate.local_path: kw["path"] = candidate.local_path
        return kw
