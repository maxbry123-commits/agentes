"""EVO-IR · Intermediate Representation de cualquier fuente.

Agent/Software/Skill/Dataset/Adapter → EVO-IR → Transform → UniversalPlugin
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ComponentIR:
    name: str
    path: str = ""
    kind_hint: str = ""  # class|function|module|entrypoint
    authority: str = "unknown"  # cognitive|execution|control|state|presentation
    reusable: bool = True
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0  # CERTAIN≈1.0 INFERRED≈0.5 UNKNOWN≈0
    side_effects: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CapabilityIR:
    id: str
    origin_component: str = ""
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    authority: str = "execution"
    action: str = "adapt"  # preserve|adapt|absorb|subordinate|isolate|ignore|reject

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvoIR:
    identity: str
    source_type: str  # agent|software|skill|dataset|adapter|plugin|workflow
    source_repo: str = ""
    source_ref: str = ""
    source_sha256: str = ""
    language: str = ""
    components: list[ComponentIR] = field(default_factory=list)
    capabilities: list[CapabilityIR] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    entrypoints: list[str] = field(default_factory=list)
    fingerprint: dict[str, bool] = field(default_factory=dict)
    decision_layer_detected: bool = False
    execution_layer_detected: bool = False
    memory_layer_detected: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "source_type": self.source_type,
            "source_repo": self.source_repo,
            "source_ref": self.source_ref,
            "source_sha256": self.source_sha256,
            "language": self.language,
            "components": [c.to_dict() for c in self.components],
            "capabilities": [c.to_dict() for c in self.capabilities],
            "interfaces": self.interfaces,
            "dependencies": self.dependencies,
            "entrypoints": self.entrypoints,
            "fingerprint": self.fingerprint,
            "decision_layer_detected": self.decision_layer_detected,
            "execution_layer_detected": self.execution_layer_detected,
            "memory_layer_detected": self.memory_layer_detected,
            "meta": self.meta,
        }
