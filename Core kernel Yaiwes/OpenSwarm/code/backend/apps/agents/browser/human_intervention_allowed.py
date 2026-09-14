"""The one decision for whether a browser run may ASK a human for help. Code never fires
RequestHumanIntervention itself; this gate only controls whether the model is offered the tool."""

from typing import Dict, Optional, Set

from typeguard import typechecked

from backend.apps.agents.core.models import AgentSession


@typechecked
def human_intervention_allowed(
    builtin_perms: Dict[str, str],
    parent_session_id: Optional[str],
    sessions: Dict[str, AgentSession],
) -> bool:
    if builtin_perms.get("RequestHumanIntervention") == "deny":
        return False
    # A workflow run anywhere up the parent chain means nobody is watching the screen. The visited
    # set means a corrupt chain degrades to "allowed" instead of hanging the spawn.
    seen: Set[str] = set()
    sid = parent_session_id
    while sid and sid not in seen:
        seen.add(sid)
        parent = sessions.get(sid)
        if parent is None:
            return True
        if parent.workflow_run_id:
            return False
        sid = parent.parent_session_id
    return True
