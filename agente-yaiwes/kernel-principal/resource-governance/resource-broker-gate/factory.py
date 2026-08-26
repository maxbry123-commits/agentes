"""AdapterFactory — build ResourceContract plans; FETCH only when flag+policy."""
from __future__ import annotations

import os
from typing import Any

from .contract import ResourceContract
from .skill_loader import SkillLoader, SkillIR
from .dataset_loader import DatasetLoader, DatasetPlan
from .space_loader import SpaceAgentsLoader, SpaceContract
from .registry import ResourceRegistry
from wordflow_kernel.models import Resource


class AdapterFactory:
    def __init__(self, registry: ResourceRegistry | None = None):
        self.registry = registry or ResourceRegistry()
        self.skills = SkillLoader()
        self.datasets = DatasetLoader()
        self.spaces = SpaceAgentsLoader()

    def fetch_enabled(self) -> bool:
        return os.environ.get("FETCH_ENABLED", "false").lower() in ("1", "true", "yes")

    def from_skill_markdown(self, text: str, source_path: str | None = None) -> ResourceContract:
        ir = self.skills.load_text(text, source_path=source_path)
        contract = self.skills.to_contract(ir)
        self._register_model(contract)
        return contract

    def plan_dataset(self, contract: ResourceContract) -> DatasetPlan:
        return self.datasets.plan(contract)

    def from_agents_md(self, text: str, space_id: str) -> tuple[SpaceContract, ResourceContract]:
        space = self.spaces.parse(text, space_id=space_id)
        contract = self.spaces.to_resource_contract(space)
        self._register_model(contract)
        return space, contract

    def execute_plan(self, plan: DatasetPlan) -> dict[str, Any]:
        """Refuse download unless FETCH_ENABLED."""
        desc = self.datasets.describe_execution(plan)
        if not self.fetch_enabled():
            desc["executed"] = False
            desc["reason"] = "FETCH_ENABLED=false"
            return desc
        desc["executed"] = False
        desc["reason"] = "real_hf_download_deferred_to_runtime_policy"
        return desc

    def _register_model(self, contract: ResourceContract) -> None:
        try:
            self.registry.register(
                Resource(
                    resource_id=contract.resource_id,
                    kind=contract.kind,
                    source=contract.source_uri,
                    version=contract.version or contract.revision,
                    capabilities=contract.capabilities,
                )
            )
        except ValueError:
            pass  # already registered
