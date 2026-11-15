"""StandardContract — DSL/schema del Advanced Engineering Standard V2."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional

class RuleId(str, Enum):
    FILE_LOC = "RULE-001"
    PROJECT_LOC_UNLIMITED = "RULE-002"
    NO_CIRCULAR = "RULE-003"
    NO_FORBIDDEN_IMPORTS = "RULE-004"
    DOMAIN_ISOLATED = "RULE-005"
    PORTS_ADAPTERS = "RULE-006"
    CONTRACTS_VERSIONED = "RULE-007"
    EVIDENCE_REQUIRED = "RULE-008"
    VERIFY_CRITICAL = "RULE-009"
    ARCH_MACHINE = "RULE-010"
    AGENT_AUTHORITY = "RULE-011"
    NO_DEFAULT_PROD = "RULE-012"
    NO_SECRETS = "RULE-013"
    DEPS_AUDITABLE = "RULE-014"
    IMPACT_ANALYSIS = "RULE-015"
    AI_NOT_PROOF = "RULE-016"
    DETERMINISTIC_FIRST = "RULE-017"
    SCALE_BY_MODULES = "RULE-018"
    STATE_OWNERSHIP = "RULE-019"
    CI_FAIL_CLOSED = "RULE-020"
    GAPS_100 = "RULE-021"
    NEVER_MVP = "RULE-022"

@dataclass
class StandardContract:
    version: str = "2.0.0"
    file_loc_preferred_max: int = 800
    file_loc_soft_min: int = 300
    project_loc_limit: Optional[int] = None  # None = unlimited
    never_mvp: bool = True
    gaps_must_be_100: bool = True
    ai_output_is_not_proof: bool = True
    deterministic_first: bool = True
    rules: List[RuleId] = field(default_factory=lambda: list(RuleId))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "file_loc_preferred_max": self.file_loc_preferred_max,
            "file_loc_soft_min": self.file_loc_soft_min,
            "project_loc_limit": self.project_loc_limit,
            "never_mvp": self.never_mvp,
            "gaps_must_be_100": self.gaps_must_be_100,
            "ai_output_is_not_proof": self.ai_output_is_not_proof,
            "deterministic_first": self.deterministic_first,
            "rules": [r.value for r in self.rules],
        }
