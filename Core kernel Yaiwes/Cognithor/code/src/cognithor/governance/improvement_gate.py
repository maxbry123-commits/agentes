"""ImprovementGate: Safety layer for self-improvement features.

Controls WHICH domains are allowed to self-improve (SAFE_DOMAINS),
enforces cooldowns after failures, and rate-limits changes per hour.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import TYPE_CHECKING, Any

from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.config import ImprovementGovernanceConfig

logger = get_logger(__name__)


class ImprovementDomain(str, Enum):
    """Domains that can be self-improved."""

    PROMPT_TUNING = "prompt_tuning"
    TOOL_PARAMETERS = "tool_parameters"
    WORKFLOW_ORDER = "workflow_order"
    MEMORY_WEIGHTS = "memory_weights"
    MODEL_SELECTION = "model_selection"
    CODE_GENERATION = "code_generation"


class GateVerdict(str, Enum):
    """Verdict from the ImprovementGate."""

    ALLOWED = "allowed"
    NEEDS_APPROVAL = "needs_approval"
    BLOCKED = "blocked"
    COOLDOWN = "cooldown"


# Maps GovernanceAgent proposal categories to ImprovementDomains
CATEGORY_DOMAIN_MAP: dict[str, ImprovementDomain] = {
    "error_rate": ImprovementDomain.TOOL_PARAMETERS,
    "budget": ImprovementDomain.MODEL_SELECTION,
    "recurring_error": ImprovementDomain.WORKFLOW_ORDER,
    "tool_latency": ImprovementDomain.TOOL_PARAMETERS,
    "unused_tool": ImprovementDomain.TOOL_PARAMETERS,
    "prompt_evolution": ImprovementDomain.PROMPT_TUNING,
}


class ImprovementGate:
    """Gate that controls which self-improvement domains are allowed.

    Logic of ``check()``:
    1. Gate disabled? -> ALLOWED (everything passes)
    2. Domain in blocked_domains? -> BLOCKED
    3. Rate limit exceeded (max_changes_per_hour)? -> COOLDOWN
    4. Domain in cooldown (recent failure)? -> COOLDOWN
    5. Domain in auto_domains? -> ALLOWED
    6. Otherwise -> NEEDS_APPROVAL (HITL via ApprovalManager)
    """

    def __init__(self, config: ImprovementGovernanceConfig) -> None:
        self._config = config
        # Cooldown tracking: domain -> monotonic timestamp of last failure
        self._cooldowns: dict[ImprovementDomain, float] = {}
        # Rate-limit tracking: list of monotonic timestamps of recent changes
        self._change_timestamps: list[float] = []

    def check(
        self, domain: ImprovementDomain, proposal: dict[str, Any] | None = None
    ) -> GateVerdict:
        """Check whether a self-improvement action in the given domain is allowed.

        Args:
            domain: The improvement domain to check.
            proposal: Optional proposal metadata (currently unused, reserved).

        Returns:
            GateVerdict indicating whether the action is allowed.
        """
        if not self._config.enabled:
            return GateVerdict.ALLOWED

        domain_value = domain.value if isinstance(domain, ImprovementDomain) else domain

        # 1. Blocked?
        if domain_value in self._config.blocked_domains:
            logger.info("improvement_gate_blocked", domain=domain_value)
            return GateVerdict.BLOCKED

        # 2. Rate limit?
        now = time.monotonic()
        cutoff = now - 3600  # 1 hour
        self._change_timestamps = [t for t in self._change_timestamps if t > cutoff]
        if len(self._change_timestamps) >= self._config.max_changes_per_hour:
            logger.info(
                "improvement_gate_rate_limited",
                domain=domain_value,
                changes=len(self._change_timestamps),
            )
            return GateVerdict.COOLDOWN

        # 3. Cooldown after failure?
        if domain in self._cooldowns:
            elapsed = now - self._cooldowns[domain]
            cooldown_seconds = self._config.cooldown_minutes * 60
            if elapsed < cooldown_seconds:
                logger.info(
                    "improvement_gate_cooldown",
                    domain=domain_value,
                    remaining_s=round(cooldown_seconds - elapsed),
                )
                return GateVerdict.COOLDOWN

        # 4. Auto-allowed?
        if domain_value in self._config.auto_domains:
            return GateVerdict.ALLOWED

        # 5. Default: needs human approval
        return GateVerdict.NEEDS_APPROVAL

    def record_outcome(self, domain: ImprovementDomain, success: bool) -> None:
        """Record the outcome of a self-improvement action.

        On success: records timestamp for rate-limiting (no cooldown).
        On failure: sets a cooldown for the domain.
        """
        now = time.monotonic()
        if success:
            self._change_timestamps.append(now)
            # Clear cooldown on success
            self._cooldowns.pop(domain, None)
            logger.debug("improvement_gate_success", domain=domain.value)
        else:
            self._cooldowns[domain] = now
            logger.info(
                "improvement_gate_failure_cooldown",
                domain=domain.value,
                cooldown_min=self._config.cooldown_minutes,
            )
