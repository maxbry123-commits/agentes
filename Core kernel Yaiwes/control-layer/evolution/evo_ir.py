"""EVO-IR."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class ComponentIR:
    name: str
    path: str = ""
    kind: str = ""
    authority: str = "unknown"
    action: str = "adapt"
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    certainty: str = "UNKNOWN"
    side_effects: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    def to_dict(self): return asdict(self)

@dataclass
class CapabilityIR:
    id: str
    origin: str = ""
    action: str = "adapt"
    authority: str = "execution"
    requires: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    def to_dict(self): return asdict(self)

@dataclass
class EvoIR:
    identity: str
    source_type: str
    source_path: str = ""
    source_repo: str = ""
    source_ref: str = ""
    source_sha256: str = ""
    license_spdx: str = ""
    license_verdict: str = ""
    components: list[ComponentIR] = field(default_factory=list)
    capabilities: list[CapabilityIR] = field(default_factory=list)
    fingerprint: dict[str, bool] = field(default_factory=dict)
    entrypoints: list[str] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    def to_dict(self):
        return {"identity": self.identity, "source_type": self.source_type, "source_path": self.source_path, "source_repo": self.source_repo, "source_ref": self.source_ref, "source_sha256": self.source_sha256, "license_spdx": self.license_spdx, "license_verdict": self.license_verdict, "components": [c.to_dict() for c in self.components], "capabilities": [c.to_dict() for c in self.capabilities], "fingerprint": self.fingerprint, "entrypoints": self.entrypoints, "side_effects": self.side_effects, "meta": self.meta}
