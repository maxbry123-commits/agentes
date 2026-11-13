"""RequestHumanIntervention is opt-in for the model, never injected by code: the gate removes the
tool for workflow runs and when the settings toggle says deny, and the scrubber guarantees no prompt
copy anywhere still advertises a tool the run does not have (ENG-198)."""

from backend.apps.agents.browser import browser_schema
from backend.apps.agents.browser.browser_loop import (
    LOOP_WARNING_TEXT,
    STAGNATION_MAX,
    stagnation_nudge,
)
from backend.apps.agents.browser.human_intervention_allowed import human_intervention_allowed
from backend.apps.agents.browser.intervention_copy import (
    INTERVENTION_SECTION,
    strip_intervention_copy,
)
from backend.apps.agents.browser.seed_playbooks import SEED_PLAYBOOKS
from backend.apps.agents.core.models import AgentSession


def p_session(sid: str, parent: str | None = None, workflow: str | None = None) -> AgentSession:
    return AgentSession(id=sid, name="t", model="m", mode="browser-agent",
                        parent_session_id=parent, workflow_run_id=workflow)


def test_allowed_by_default():
    assert human_intervention_allowed({}, None, {})


def test_toggle_deny_removes_it():
    assert not human_intervention_allowed({"RequestHumanIntervention": "deny"}, None, {})


def test_ask_policy_keeps_it():
    assert human_intervention_allowed({"RequestHumanIntervention": "ask"}, None, {})


def test_workflow_parent_removes_it():
    sessions = {"p": p_session("p", workflow="wf1")}
    assert not human_intervention_allowed({}, "p", sessions)


def test_workflow_grandparent_removes_it_through_the_chain():
    sessions = {"p": p_session("p", parent="gp"), "gp": p_session("gp", workflow="wf1")}
    assert not human_intervention_allowed({}, "p", sessions)


def test_chat_parent_keeps_it():
    sessions = {"p": p_session("p")}
    assert human_intervention_allowed({}, "p", sessions)


def test_unknown_parent_degrades_to_allowed():
    assert human_intervention_allowed({}, "ghost", {})


def test_a_parent_chain_cycle_cannot_hang():
    sessions = {"a": p_session("a", parent="b"), "b": p_session("b", parent="a")}
    assert human_intervention_allowed({}, "a", sessions)


def test_intervention_section_is_really_in_the_system_prompt():
    # strip_intervention_copy works by exact replace; if the prompt copy drifts away from the
    # constant, this is the test that fails before the scrub silently stops matching.
    assert INTERVENTION_SECTION in browser_schema.SYSTEM_PROMPT


def test_scrubbed_copy_never_names_the_tool():
    seeds = [line for lines in SEED_PLAYBOOKS.values() for line in lines]
    for text in (
        browser_schema.SYSTEM_PROMPT,
        browser_schema.APP_SYSTEM_PROMPT,
        LOOP_WARNING_TEXT.format(count=3),
        stagnation_nudge(STAGNATION_MAX),
        "💡 Suggested next step: call RequestHumanIntervention now.",
        *seeds,
    ):
        assert "RequestHumanIntervention" not in strip_intervention_copy(text)


def test_interactive_tool_list_still_offers_it():
    names = [t["name"] for t in browser_schema.MODEL_VISIBLE_TOOLS]
    assert "RequestHumanIntervention" in names
