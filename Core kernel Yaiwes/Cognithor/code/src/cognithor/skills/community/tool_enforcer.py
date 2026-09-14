"""ToolEnforcer: Runtime tool allowlist for community skills.

Kern der architektonischen Sicherheit: Community-Skills duerfen NUR
die in ``tools_required`` deklarierten Tools nutzen.  Alle anderen
Tool-Calls werden geblockt, BEVOR der Gatekeeper sie sieht.

Einbindung:
  - Im PGE-Loop (gateway.py) vor ``Gatekeeper.evaluate()``
  - Gatekeeper ruft ``_enforce_skill_tools()`` als ersten Schritt

Bible reference: §3.2 (Gatekeeper), §6.2 (Skills), §11 (Security)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.models import PlannedAction
    from cognithor.skills.registry import Skill

log = get_logger(__name__)


# ============================================================================
# Datenmodelle
# ============================================================================


@dataclass(frozen=True)
class ToolEnforcementResult:
    """Result of a ToolEnforcer check."""

    allowed: bool
    tool: str
    skill_name: str
    declared_tools: list[str] = field(default_factory=list)
    reason: str = ""


# ============================================================================
# ToolEnforcer
# ============================================================================


class ToolEnforcer:
    """Runtime enforcement of the tool allowlist for community skills.

    Garantie: Ein Community-Skill kann NUR die Tools nutzen, die er
    in ``tools_required`` deklariert hat.  Alles andere wird geblockt.

    Fuer builtin-Skills (``source != "community"``) wird immer ALLOW
    zurueckgegeben — die bestehende Gatekeeper-Logik gilt unveraendert.

    Usage::

        enforcer = ToolEnforcer()
        result = enforcer.check(action, skill)
        if not result.allowed:
            # → BLOCK, Grund in result.reason
    """

    def __init__(self, *, max_tool_calls: int = 0) -> None:
        """Initialize the ToolEnforcer.

        Args:
            max_tool_calls: Globaler Default fuer max Tool-Calls pro
                Skill-Aufruf.  0 = kein Limit (Manifest-Wert gilt).
        """
        self._default_max_tool_calls = max_tool_calls

        # Pro-Session Call-Counter: session_id:skill_slug → count
        self._call_counts: dict[str, int] = {}

        # Statistiken
        self._stats = _EnforcerStats()

    # ====================================================================
    # Public API
    # ====================================================================

    def check(
        self,
        action: PlannedAction,
        skill: Skill | None,
    ) -> ToolEnforcementResult:
        """Check if a tool call is allowed for the active skill.

        Args:
            action: Die geplante Aktion mit Tool-Name.
            skill: Der aktive Skill (None = kein Skill aktiv).

        Returns:
            ToolEnforcementResult — ``allowed=True`` wenn OK.
        """
        self._stats.total_checks += 1

        # Kein Skill aktiv → kein Enforcement
        if skill is None:
            return ToolEnforcementResult(
                allowed=True,
                tool=action.tool,
                skill_name="<none>",
                reason="No skill active",
            )

        # Only builtin skills skip enforcement — community AND generated are checked
        source = getattr(skill, "source", "builtin")
        if source == "builtin":
            return ToolEnforcementResult(
                allowed=True,
                tool=action.tool,
                skill_name=skill.name,
                declared_tools=skill.tools_required,
                reason="Builtin skill, no enforcement needed",
            )

        # Community-Skill → tools_required enforcement
        declared = skill.tools_required
        if not declared:
            # Community-Skill ohne tools_required → BLOCK (Sicherheits-Default)
            self._stats.blocked += 1
            log.warning(
                "tool_enforcer_block",
                tool=action.tool,
                skill=skill.name,
                reason="Community skill without tools_required",
            )
            return ToolEnforcementResult(
                allowed=False,
                tool=action.tool,
                skill_name=skill.name,
                declared_tools=[],
                reason="Community skill has no tools_required declared — alle Tools geblockt",
            )

        if action.tool not in declared:
            self._stats.blocked += 1
            log.warning(
                "tool_enforcer_block",
                tool=action.tool,
                skill=skill.name,
                declared=declared,
            )
            return ToolEnforcementResult(
                allowed=False,
                tool=action.tool,
                skill_name=skill.name,
                declared_tools=declared,
                reason=f"Tool '{action.tool}' nicht in tools_required deklariert",
            )

        # Max-Tool-Calls Enforcement (aus Manifest)
        manifest = getattr(skill, "manifest", None)
        max_calls = (
            getattr(manifest, "max_tool_calls", 0) if manifest else self._default_max_tool_calls
        )
        if max_calls > 0:
            key = skill.slug
            current = self._call_counts.get(key, 0)
            if current >= max_calls:
                self._stats.blocked += 1
                return ToolEnforcementResult(
                    allowed=False,
                    tool=action.tool,
                    skill_name=skill.name,
                    declared_tools=declared,
                    reason=f"max_tool_calls ({max_calls}) fuer Skill '{skill.name}' erreicht",
                )
            self._call_counts[key] = current + 1

        self._stats.allowed += 1
        return ToolEnforcementResult(
            allowed=True,
            tool=action.tool,
            skill_name=skill.name,
            declared_tools=declared,
            reason="Tool in tools_required deklariert",
        )

    def reset_call_count(self, skill_slug: str) -> None:
        """Reset the call counter for a skill.

        Called at the end of a skill invocation.
        """
        self._call_counts.pop(skill_slug, None)

    @property
    def stats(self) -> dict[str, int]:
        """Enforcement statistics."""
        return {
            "total_checks": self._stats.total_checks,
            "allowed": self._stats.allowed,
            "blocked": self._stats.blocked,
        }


@dataclass
class _EnforcerStats:
    """Internal statistics."""

    total_checks: int = 0
    allowed: int = 0
    blocked: int = 0
