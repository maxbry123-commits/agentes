"""Gateway Phase Modules: Modular initialization for the Cognithor Gateway.

Each phase module provides:
  - declare_*_attrs(config) -> PhaseResult: synchronous, returns attr defaults
  - init_*(config, ...) -> PhaseResult: async, returns initialized instances

PhaseResult is a dict mapping attribute names to values.
apply_phase() sets those attributes on the target object.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# PhaseResult type alias
# ---------------------------------------------------------------------------

PhaseResult = dict[str, Any]


def apply_phase(target: object, result: PhaseResult) -> None:
    """Apply a PhaseResult to *target* by setting _key = value for each entry."""
    for key, value in result.items():
        setattr(target, f"_{key}", value)


# ---------------------------------------------------------------------------
# Re-exports from all phase modules
# ---------------------------------------------------------------------------

from cognithor.gateway.phases.advanced import declare_advanced_attrs, init_advanced
from cognithor.gateway.phases.agents import declare_agents_attrs, init_agents
from cognithor.gateway.phases.compliance import declare_compliance_attrs, init_compliance
from cognithor.gateway.phases.core import declare_core_attrs, init_core
from cognithor.gateway.phases.memory import declare_memory_attrs, init_memory
from cognithor.gateway.phases.pge import declare_pge_attrs, init_pge
from cognithor.gateway.phases.security import declare_security_attrs, init_security
from cognithor.gateway.phases.tools import declare_tools_attrs, init_tools

__all__ = [
    "PhaseResult",
    "apply_phase",
    "declare_advanced_attrs",
    "declare_agents_attrs",
    "declare_compliance_attrs",
    "declare_core_attrs",
    "declare_memory_attrs",
    "declare_pge_attrs",
    "declare_security_attrs",
    "declare_tools_attrs",
    "init_advanced",
    "init_agents",
    "init_compliance",
    "init_core",
    "init_memory",
    "init_pge",
    "init_security",
    "init_tools",
]
