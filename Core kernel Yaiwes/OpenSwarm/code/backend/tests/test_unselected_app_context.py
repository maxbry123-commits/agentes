"""An agent that cannot see an app must still know it exists.

Selecting an App card is what grants edit access, and that gate is deliberate. But a user who has
not learned the ritual just sees an agent behaving as though their app was never built, and the
agent cannot explain the problem because it was never told the app was there either. So with
nothing selected we name the apps and nothing more: enough to say "select it and I can edit it",
not enough to start editing something the user never pointed at.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_unselected_app_context.py -v
"""

from __future__ import annotations

from backend.apps.agents.manager.prompt import prompt_context
from backend.apps.outputs.models import Output


def p_app(name: str, workspace_id: str = "ws") -> Output:
    return Output(name=name, workspace_id=workspace_id)


def test_names_the_apps_when_nothing_is_selected(monkeypatch):
    monkeypatch.setattr(prompt_context, "load_all", lambda: [p_app("Budget Tracker")], raising=False)
    monkeypatch.setattr(
        "backend.apps.outputs.workspace_io.load_all",
        lambda: [p_app("Budget Tracker"), p_app("Habit Log")],
    )

    out = prompt_context.build_unselected_app_context()

    assert out is not None
    assert "Budget Tracker" in out and "Habit Log" in out


def test_tells_the_agent_to_ask_for_a_selection(monkeypatch):
    """The whole point: the agent has to hand the user the next step, not stonewall them."""
    monkeypatch.setattr("backend.apps.outputs.workspace_io.load_all", lambda: [p_app("Budget Tracker")])

    out = prompt_context.build_unselected_app_context() or ""

    assert "select" in out.lower()
    assert "does not exist" in out, "must explicitly forbid claiming the app is missing"


def test_leaks_no_paths(monkeypatch):
    """Names only. A path here would let the agent edit an app the user never pointed at, which is
    exactly the access the selection gate exists to withhold."""
    monkeypatch.setattr("backend.apps.outputs.workspace_io.load_all", lambda: [p_app("Budget Tracker")])

    out = prompt_context.build_unselected_app_context() or ""

    assert "/" not in out.replace("</available_apps>", ""), "no filesystem paths may appear"
    assert "workspace" not in out.lower()


def test_silent_when_the_user_has_no_apps(monkeypatch):
    monkeypatch.setattr("backend.apps.outputs.workspace_io.load_all", lambda: [])
    assert prompt_context.build_unselected_app_context() is None


def test_skips_apps_with_no_workspace(monkeypatch):
    """A row without a workspace is not a real app the user can select."""
    monkeypatch.setattr(
        "backend.apps.outputs.workspace_io.load_all",
        lambda: [Output(name="Ghost", workspace_id=None)],
    )
    assert prompt_context.build_unselected_app_context() is None


def test_caps_a_long_list(monkeypatch):
    many = [p_app(f"App {i}") for i in range(30)]
    monkeypatch.setattr("backend.apps.outputs.workspace_io.load_all", lambda: many)

    out = prompt_context.build_unselected_app_context() or ""

    assert "App 0" in out
    assert "App 29" not in out, "an uncapped list burns prompt tokens on every turn"
    assert "more" in out, "the user must still learn there are others"


def test_a_broken_store_does_not_break_the_turn(monkeypatch):
    def p_boom():
        raise OSError("disk gone")

    monkeypatch.setattr("backend.apps.outputs.workspace_io.load_all", p_boom)
    assert prompt_context.build_unselected_app_context() is None


def test_selection_still_wins(monkeypatch):
    """With a real selection the rich block must be used; this fallback must not shadow it."""
    monkeypatch.setattr("backend.apps.outputs.workspace_io.load_all", lambda: [p_app("Budget Tracker")])
    selected = prompt_context.build_selected_app_context(None)
    assert selected is None, "no ids means no rich block, which is what triggers the fallback"


def test_the_block_actually_reaches_the_composed_prompt(monkeypatch):
    """The one that matters. Every test above passes even with the builder unwired from the prompt,
    so without this the feature could ship doing nothing at all."""
    from backend.apps.agents.core.models import AgentSession
    from backend.apps.agents.manager.prompt.compose_turn_system_prompt import compose_turn_system_prompt

    monkeypatch.setattr("backend.apps.outputs.workspace_io.load_all", lambda: [p_app("Budget Tracker")])
    session = AgentSession(id="s1", name="t", model="sonnet", mode="agent")

    composed = compose_turn_system_prompt(
        session=session,
        mode_sys_prompt=None,
        default_system_prompt=None,
        selected_browser_ids=None,
        selected_app_output_ids=None,
        selected_setting_ids=None,
    ) or ""

    assert "Budget Tracker" in composed
    assert "<available_apps>" in composed
