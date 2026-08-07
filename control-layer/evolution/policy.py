"""Policy Engine + Policy DSL · transformación determinista.

CODE_AGENT_POLICY: preserve cognitive, adapt I/O, subordinate global control.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .authority import DEFAULT_POLICY, AuthorityNode
from .evo_ir import CapabilityIR, ComponentIR, EvoIR


@dataclass
class TransformAction:
    component: str
    authority: str
    action: str  # preserve|adapt|absorb|subordinate|isolate|ignore|reject
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TransformationPlan:
    source_id: str
    strategy: str  # absorb|adapt|compile|wrap|import|reject
    actions: list[TransformAction] = field(default_factory=list)
    capabilities_out: list[str] = field(default_factory=list)
    removed_control: list[str] = field(default_factory=list)
    preserved_cognitive: list[str] = field(default_factory=list)
    policy_id: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "strategy": self.strategy,
            "actions": [a.to_dict() for a in self.actions],
            "capabilities_out": self.capabilities_out,
            "removed_control": self.removed_control,
            "preserved_cognitive": self.preserved_cognitive,
            "policy_id": self.policy_id,
        }


# Políticas declarativas por tipo de fuente
POLICIES: dict[str, dict[str, str]] = {
    "default": dict(DEFAULT_POLICY),
    "code_agent": {
        "cognitive": "preserve",
        "execution": "adapt",
        "control": "subordinate",
        "state": "adapt",
        "presentation": "isolate",
        "unknown": "adapt",
    },
    "workflow_engine": {
        "cognitive": "adapt",
        "execution": "absorb",
        "control": "subordinate",  # scheduler al TEAM scheduler
        "state": "adapt",
        "presentation": "isolate",
        "unknown": "adapt",
    },
    "skill": {
        "cognitive": "compile",
        "execution": "compile",
        "control": "subordinate",
        "state": "adapt",
        "presentation": "ignore",
        "unknown": "compile",
    },
}


def select_policy(source_type: str, fingerprint: dict[str, bool] | None = None) -> str:
    fp = fingerprint or {}
    if source_type == "skill":
        return "skill"
    if source_type == "software" and fp.get("has_workflow"):
        return "workflow_engine"
    if source_type == "agent" and (fp.get("has_code_gen") or fp.get("has_tools")):
        return "code_agent"
    return "default"


def build_plan(ir: EvoIR, authority_nodes: list[AuthorityNode]) -> TransformationPlan:
    policy_id = select_policy(ir.source_type, ir.fingerprint)
    policy = POLICIES.get(policy_id, POLICIES["default"])
    actions: list[TransformAction] = []
    removed: list[str] = []
    preserved: list[str] = []
    caps: list[str] = []

    by_name = {n.component: n for n in authority_nodes}
    for c in ir.components:
        node = by_name.get(c.name) or AuthorityNode(c.name, c.authority, policy.get(c.authority, "adapt"))
        action = policy.get(node.authority, node.action)
        # map compile → absorb for non-skill
        if action == "compile" and ir.source_type != "skill":
            action = "adapt"
        actions.append(TransformAction(c.name, node.authority, action, reason=f"policy:{policy_id}"))
        if action == "subordinate" and node.authority == "control":
            removed.append(c.name)
        if action == "preserve" and node.authority == "cognitive":
            preserved.append(c.name)

    for cap in ir.capabilities:
        caps.append(cap.id)

    strategy = "compile" if ir.source_type == "skill" else "absorb"
    if ir.source_type == "dataset":
        strategy = "import"
    if ir.source_type == "adapter":
        strategy = "adapt"

    return TransformationPlan(
        source_id=ir.identity,
        strategy=strategy,
        actions=actions,
        capabilities_out=caps,
        removed_control=removed,
        preserved_cognitive=preserved,
        policy_id=policy_id,
    )
