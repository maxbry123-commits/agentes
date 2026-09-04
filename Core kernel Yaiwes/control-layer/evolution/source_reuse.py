"""EVO.10 · Source Reuse Contract · OS antes de from-scratch."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SourceRef:
    id: str
    repo_url: str
    ref: str
    sha256: str
    path: str
    license: str = "unknown"
    method: str = "git-archive"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceReuseDecision:
    must_search_os: bool
    sources_found: list[SourceRef] = field(default_factory=list)
    allow_from_scratch: bool = False
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "must_search_os": self.must_search_os,
            "sources_found": [s.to_dict() for s in self.sources_found],
            "allow_from_scratch": self.allow_from_scratch,
            "reason": self.reason,
        }


class SourceReuseContract:
    def __init__(self, manifest: list[SourceRef] | None = None) -> None:
        self.manifest = list(manifest or [])

    def register(self, ref: SourceRef) -> None:
        self.manifest = [m for m in self.manifest if m.id != ref.id]
        self.manifest.append(ref)

    def find(self, capability_hint: str) -> list[SourceRef]:
        hint = capability_hint.lower()
        return [m for m in self.manifest if hint in m.id.lower() or hint in m.path.lower()]

    def decide(self, capability_hint: str, *, force_scratch_reason: str = "") -> SourceReuseDecision:
        found = self.find(capability_hint)
        if found:
            return SourceReuseDecision(True, found, False, "source_in_manifest")
        if force_scratch_reason:
            return SourceReuseDecision(True, [], True, f"explicit_scratch:{force_scratch_reason}")
        return SourceReuseDecision(True, [], False, "no_source_search_required_before_scratch")
