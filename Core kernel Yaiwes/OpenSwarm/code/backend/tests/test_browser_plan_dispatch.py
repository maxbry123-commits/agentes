"""Code-side plan dispatch: the aux's JSON plan is parsed fail-open and the
irreversible wall holds in the PARSER (before anything could ever run)."""
from backend.apps.agents.browser import browser_plan_dispatch as pd


def test_parse_valid_plan():
    steps = pd.parse_plan('[{"action":"click","target":"Options","role":"button"},'
                          '{"action":"fill","target":"Search","text":"cats"}]')
    assert [s.kind for s in steps] == ["click", "fill"]
    assert steps[1].text == "cats"


def test_parse_stops_at_irreversible_and_drops_the_rest():
    steps = pd.parse_plan('[{"action":"click","target":"Options"},'
                          '{"action":"click","target":"Send message"},'
                          '{"action":"click","target":"Home"}]')
    assert [s.target for s in steps] == ["Options"]  # Send refused, Home never reached


def test_parse_malformed_and_junk_fail_open():
    assert pd.parse_plan("I think you should click Options") == []
    assert pd.parse_plan('{"action":"click"}') == []
    assert pd.parse_plan("[]") == []
    assert pd.parse_plan('[{"action":"hover","target":"X"},{"action":"click","target":""}]') == []


def test_parse_caps_at_six_steps():
    plan = "[" + ",".join('{"action":"click","target":"B%d"}' % i for i in range(9)) + "]"
    assert len(pd.parse_plan(plan)) == 6


def test_parse_carries_the_chosen_flag():
    # The planner may PICK among similar rows (the disambiguation turn-collapser); the
    # flag must survive parsing so the handoff note can mark the pick for review.
    steps = pd.parse_plan(
        '[{"action":"click","target":"Tyler Chen · 1st · Irvine, CA","chosen":true},'
        '{"action":"click","target":"Message","role":"button"}]')
    assert [s.chosen for s in steps] == [True, False]


def test_chosen_cannot_smuggle_an_irreversible_click():
    # A chosen pick relaxes WHICH row gets clicked, never WHAT may be clicked: the
    # irreversible wall still breaks the chain even on a chosen step.
    steps = pd.parse_plan(
        '[{"action":"click","target":"Options","chosen":true},'
        '{"action":"click","target":"Send now","chosen":true},'
        '{"action":"click","target":"Home"}]')
    assert [s.target for s in steps] == ["Options"]
