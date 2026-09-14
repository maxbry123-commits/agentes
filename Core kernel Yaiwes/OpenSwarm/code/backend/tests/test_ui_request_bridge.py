"""The AskUI bridge: early clicks are held, stops release zombies, answers land (ENG-232)."""

import asyncio

import pytest

from backend.apps.agents.ui_request_bridge import (
    cancel_session_waits,
    reset_ui_bridge,
    respond_to_ui_request,
    wait_for_ui_response,
)


@pytest.fixture(autouse=True)
def fresh_bridge():
    reset_ui_bridge()
    yield
    reset_ui_bridge()


@pytest.mark.asyncio
async def test_answer_reaches_a_parked_wait():
    task = asyncio.ensure_future(wait_for_ui_response("s1", "q1", 5.0))
    await asyncio.sleep(0.05)
    assert respond_to_ui_request("s1", "q1", {"action": "select", "value": "a"}) == "delivered"
    assert await task == {"action": "select", "value": "a"}


@pytest.mark.asyncio
async def test_click_before_the_wait_parks_is_held_not_dropped():
    """The card is clickable before the wait registers; that click used to be discarded."""
    assert respond_to_ui_request("s1", "q1", {"action": "confirm"}) == "buffered"
    assert await wait_for_ui_response("s1", "q1", 5.0) == {"action": "confirm"}
    # Consumed exactly once: the next wait for the same id parks and times out instead of replaying it.
    assert await wait_for_ui_response("s1", "q1", 0.1) is None


@pytest.mark.asyncio
async def test_stop_releases_parked_waits_so_they_cannot_eat_later_clicks():
    task = asyncio.ensure_future(wait_for_ui_response("s1", "q1", 30.0))
    other = asyncio.ensure_future(wait_for_ui_response("s2", "q1", 30.0))
    await asyncio.sleep(0.05)
    assert cancel_session_waits("s1") == 1
    assert await task is None
    # The other session's wait is untouched and still answerable.
    assert respond_to_ui_request("s2", "q1", {"action": "x"}) == "delivered"
    assert await other == {"action": "x"}


@pytest.mark.asyncio
async def test_stop_also_drops_buffered_answers():
    assert respond_to_ui_request("s1", "q1", {"action": "confirm"}) == "buffered"
    cancel_session_waits("s1")
    assert await wait_for_ui_response("s1", "q1", 0.1) is None


@pytest.mark.asyncio
async def test_a_stale_buffered_answer_expires(monkeypatch):
    import backend.apps.agents.ui_request_bridge as B
    monkeypatch.setattr(B, "EARLY_ANSWER_TTL_SECONDS", 0.0)
    assert respond_to_ui_request("s1", "q1", {"action": "confirm"}) == "buffered"
    # TTL zero: the next wait prunes it and parks instead of replaying a dead click.
    assert await wait_for_ui_response("s1", "q1", 0.2) is None
