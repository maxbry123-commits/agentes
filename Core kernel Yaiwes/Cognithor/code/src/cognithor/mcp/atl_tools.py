"""ATL MCP Tools -- status, goals, journal.

Provides three tools for inspecting and managing the Autonomous Thinking Loop:
  - atl_status:  Overview of ATL config, cycle count, and active goals
  - atl_goals:   List / add / pause / resume / complete goals
  - atl_journal:  Read daily ATL journal entries
"""

from __future__ import annotations

from typing import Any

from cognithor.i18n import t
from cognithor.utils.logging import get_logger

log = get_logger(__name__)

# These will be set by gateway wiring via set_atl_context()
_goal_manager: Any = None
_atl_journal: Any = None
_atl_config: Any = None
_evolution_loop: Any = None


def set_atl_context(
    goal_manager: Any,
    journal: Any,
    config: Any,
    loop: Any,
) -> None:
    """Set ATL context for MCP tools.  Called during gateway init."""
    global _goal_manager, _atl_journal, _atl_config, _evolution_loop
    _goal_manager = goal_manager
    _atl_journal = journal
    _atl_config = config
    _evolution_loop = loop


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def atl_status(**_kwargs: Any) -> str:
    """Return ATL status summary."""
    parts: list[str] = []

    if _atl_config:
        parts.append(f"ATL enabled: {_atl_config.enabled}")
        parts.append(f"Interval: {_atl_config.interval_minutes} min")
        parts.append(f"Risk ceiling: {_atl_config.risk_ceiling}")
    else:
        parts.append("ATL not configured")

    if _evolution_loop and hasattr(_evolution_loop, "stats"):
        s = _evolution_loop.stats()
        parts.append(f"Thinking cycles: {s.get('atl_thinking_cycles', 0)}")

    if _goal_manager:
        goals = _goal_manager.active_goals()
        parts.append(f"Active goals: {len(goals)}")
        for g in goals[:5]:
            parts.append(f"  - {g.id}: {g.title} ({g.progress:.0%}) [P{g.priority}]")

    return "\n".join(parts)


async def atl_goals(
    action: str = "list",
    title: str = "",
    description: str = "",
    goal_id: str = "",
    **_kwargs: Any,
) -> str:
    """Manage ATL goals.  Actions: list, add, pause, resume, complete."""
    if not _goal_manager:
        return "ATL GoalManager not initialized."

    if action == "list":
        goals = _goal_manager.active_goals()
        if not goals:
            return t("tools.atl_no_goals")
        lines: list[str] = []
        for g in goals:
            lines.append(f"- {g.id}: {g.title} ({g.progress:.0%}) [P{g.priority}, {g.source}]")
            if g.success_criteria:
                for sc in g.success_criteria:
                    lines.append(f"    * {sc}")
        return "\n".join(lines)

    if action == "add":
        if not title:
            return t("tools.atl_title_required")
        from cognithor.evolution.goal_manager import Goal

        goal = Goal(title=title, description=description or title, priority=3, source="user")
        _goal_manager.add_goal(goal)
        return t("tools.atl_goal_created", id=goal.id, title=goal.title)

    if action == "pause" and goal_id:
        if not _goal_manager.get_goal(goal_id):
            return t("tools.atl_goal_not_found", id=goal_id)
        _goal_manager.pause_goal(goal_id)
        return t("tools.atl_goal_paused", id=goal_id)

    if action == "resume" and goal_id:
        if not _goal_manager.get_goal(goal_id):
            return t("tools.atl_goal_not_found", id=goal_id)
        _goal_manager.resume_goal(goal_id)
        return t("tools.atl_goal_resumed", id=goal_id)

    if action == "complete" and goal_id:
        if not _goal_manager.get_goal(goal_id):
            return t("tools.atl_goal_not_found", id=goal_id)
        _goal_manager.complete_goal(goal_id)
        return t("tools.atl_goal_completed", id=goal_id)

    return t("tools.atl_unknown_action", action=action)


async def atl_journal(days: int = 1, **_kwargs: Any) -> str:
    """Read ATL journal entries."""
    if not _atl_journal:
        return "ATL Journal not initialized."

    if days <= 1:
        content = _atl_journal.today()
        return content or t("tools.atl_no_journal_today")

    entries = _atl_journal.recent(days=days)
    if not entries:
        return t("tools.atl_no_journal_days", days=days)
    return "\n\n---\n\n".join(entries)


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------


def register_atl_tools(mcp_client: Any) -> None:
    """Register ATL tools with the MCP client."""
    mcp_client.register_builtin_handler(
        "atl_status",
        atl_status,
        description="Show ATL status: config, cycle count, active goals.",
        input_schema={"type": "object", "properties": {}},
    )

    mcp_client.register_builtin_handler(
        "atl_goals",
        atl_goals,
        description=(
            "Manage ATL goals. Actions: list (default), add (needs title), "
            "pause/resume/complete (needs goal_id)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "add", "pause", "resume", "complete"],
                    "description": "Action to perform (default: list)",
                },
                "title": {
                    "type": "string",
                    "description": "Goal title (required for 'add')",
                },
                "description": {
                    "type": "string",
                    "description": "Goal description (optional, for 'add')",
                },
                "goal_id": {
                    "type": "string",
                    "description": "Goal ID (required for pause/resume/complete)",
                },
            },
        },
    )

    mcp_client.register_builtin_handler(
        "atl_journal",
        atl_journal,
        description="Read ATL journal entries. Default: today only. Set days > 1 for history.",
        input_schema={
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to read (default: 1 = today only)",
                },
            },
        },
    )

    log.info("atl_mcp_tools_registered", tools=["atl_status", "atl_goals", "atl_journal"])
