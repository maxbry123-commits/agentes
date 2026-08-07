"""Policy Engine + DSL."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any
from ..evo_ir import EvoIR

POLICIES = {
    "default": {"cognitive": "preserve", "execution": "adapt", "control": "subordinate", "state": "adapt", "presentation": "isolate", "unknown": "adapt"},
    "code_agent": {"cognitive": "preserve", "execution": "adapt", "control": "subordinate", "state": "adapt", "presentation": "isolate", "unknown": "adapt"},
    "workflow_engine": {"cognitive": "adapt", "execution": "absorb", "control": "subordinate", "state": "adapt", "presentation": "isolate", "unknown": "adapt"},
    "skill": {"cognitive": "compile", "execution": "compile", "control": "subordinate", "state": "adapt", "presentation": "ignore", "unknown": "compile"},
    "dataset": {"cognitive": "ignore", "execution": "ignore", "control": "ignore", "state": "import", "presentation": "ignore", "unknown": "import"},
}

@dataclass
class TransformAction:
    component: str
    authority: str
    action: str
    reason: str = ""
    def to_dict(self): return asdict(self)

@dataclass
class TransformationPlan:
    source_id: str
    strategy: str
    policy_id: str
    actions: list = field(default_factory=list)
    capabilities_out: list = field(default_factory=list)
    preserved_cognitive: list = field(default_factory=list)
    subordinated_control: list = field(default_factory=list)
    isolated: list = field(default_factory=list)
    rejected: list = field(default_factory=list)
    def to_dict(self):
        return {"source_id": self.source_id, "strategy": self.strategy, "policy_id": self.policy_id, "actions": [a.to_dict() for a in self.actions], "capabilities_out": self.capabilities_out, "preserved_cognitive": self.preserved_cognitive, "subordinated_control": self.subordinated_control, "isolated": self.isolated, "rejected": self.rejected}

def select_policy(source_type, fingerprint=None):
    fp = fingerprint or {}
    if source_type == "skill": return "skill"
    if source_type == "dataset": return "dataset"
    if source_type == "software" and fp.get("has_workflow"): return "workflow_engine"
    if source_type in ("agent", "code_agent") or fp.get("has_code_gen") or fp.get("has_tools"): return "code_agent"
    return "default"

def build_plan(ir: EvoIR) -> TransformationPlan:
    policy_id = select_policy(ir.source_type, ir.fingerprint)
    policy = POLICIES[policy_id]
    actions, preserved, subordinated, isolated, rejected = [], [], [], [], []
    for c in ir.components:
        action = policy.get(c.authority, c.action or "adapt")
        if action == "compile" and ir.source_type != "skill": action = "adapt"
        actions.append(TransformAction(c.name, c.authority, action, f"policy:{policy_id}"))
        if action == "preserve": preserved.append(c.name)
        elif action == "subordinate": subordinated.append(c.name)
        elif action == "isolate": isolated.append(c.name)
        elif action == "reject": rejected.append(c.name)
    caps = [c.id for c in ir.capabilities]
    if not caps:
        for c in ir.components:
            if c.authority in ("cognitive", "execution") and c.action != "subordinate":
                caps.append(f"{ir.identity}.{c.name}")
    strategy = {"skill": "compile", "dataset": "import", "adapter": "adapt", "software": "absorb", "agent": "absorb", "code_agent": "absorb"}.get(ir.source_type, "absorb")
    return TransformationPlan(ir.identity, strategy, policy_id, actions, sorted(set(caps))[:50], preserved, subordinated, isolated, rejected)
