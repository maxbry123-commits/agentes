"""ApplicabilityEngine — decide tags deterministas; el agente NO puede bajar required."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Dict, Any
from .programming_points_catalog import points_for_tags, ProgPoint, CATALOG_VERSION

@dataclass
class ApplicabilityResult:
    tags: Set[str]
    required_ids: List[str]
    conditional_ids: List[str]
    advisory_ids: List[str]
    catalog_version: str = CATALOG_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tags": sorted(self.tags),
            "required_ids": self.required_ids,
            "conditional_ids": self.conditional_ids,
            "advisory_ids": self.advisory_ids,
            "catalog_version": self.catalog_version,
        }

class ApplicabilityEngine:
    def classify(
        self,
        *,
        files: List[str] | None = None,
        action: str = "GENERATE",
        has_external_api: bool = False,
        has_db: bool = False,
        has_concurrency: bool = False,
        has_ai_agent: bool = False,
        has_ui: bool = False,
        new_dependency: bool = False,
        security_sensitive: bool = False,
        public_api: bool = False,
        side_effects: bool = False,
    ) -> ApplicabilityResult:
        files = files or []
        tags: Set[str] = {"always"}
        if len(files) > 1:
            tags.add("multi_file")
        if has_external_api:
            tags.add("external_api")
        if has_db:
            tags.add("db")
        if has_concurrency:
            tags.add("concurrency")
        if has_ai_agent:
            tags.add("ai_agent")
        if has_ui:
            tags.add("ui")
        if new_dependency:
            tags.add("new_dep")
        if security_sensitive:
            tags.add("security")
        if public_api:
            tags.add("public_api")
        if side_effects:
            tags.add("side_effects")
        if action in ("COPY", "ADAPT", "GENERATE"):
            tags.add("always")

        pts = points_for_tags(tags)
        required = [p.id for p in pts if p.enforcement in ("CORE", "CONDITIONAL")]
        conditional = [p.id for p in pts if p.enforcement == "CONDITIONAL"]
        advisory = [p.id for p in pts if p.enforcement == "ADVISORY"]
        return ApplicabilityResult(tags, required, conditional, advisory)
