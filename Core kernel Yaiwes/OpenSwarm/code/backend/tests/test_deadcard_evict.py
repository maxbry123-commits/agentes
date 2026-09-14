"""The recovery-card wedge fix: when a card is declared dead, its webview must be
torn down (renderer unmount + layout removal) BEFORE recovery spawns a fresh card,
so two heavy pages never co-exist and starve the renderer. Pins evict_dead_card."""
import asyncio
from datetime import datetime, timedelta

import backend.apps.agents.browser.browser_agent as ba


class FakeLayout:
    def __init__(self, cards):
        self.browser_cards = cards


class FakeDash:
    def __init__(self, cards):
        self.layout = FakeLayout(cards)
        self.updated_at = None


def p_patch(monkeypatch, cards):
    broadcasts = []
    saved = []

    async def fake_broadcast(event, data):
        broadcasts.append((event, data))

    dash = FakeDash(cards)
    monkeypatch.setattr(ba, "P_EVICT_SETTLE_S", 0, raising=True)  # don't pay the renderer-settle wait in a unit test
    monkeypatch.setattr(ba.ws_manager, "broadcast_global", fake_broadcast, raising=True)
    import backend.apps.dashboards.dashboards as dmod
    monkeypatch.setattr(dmod, "load", lambda did: dash, raising=True)
    monkeypatch.setattr(dmod, "save", lambda d: saved.append(d), raising=True)
    return broadcasts, saved, dash


def test_evict_broadcasts_unmount_and_removes_from_layout(monkeypatch):
    broadcasts, saved, dash = p_patch(monkeypatch, {"browser-dead": FakeCard("sess-1"), "browser-keep": FakeCard("sess-1")})
    ba.ACTIVE_AGENT_CARDS.add("browser-dead")
    asyncio.run(ba.evict_dead_card("dash-1", "browser-dead"))
    # the renderer is told to unmount exactly the dead card
    assert ("dashboard:browser_card_evict", {"dashboard_id": "dash-1", "browser_id": "browser-dead"}) in broadcasts
    # it's gone from the persisted layout, its neighbor is untouched
    assert "browser-dead" not in dash.layout.browser_cards
    assert "browser-keep" in dash.layout.browser_cards
    assert saved  # the layout was persisted
    assert "browser-dead" not in ba.ACTIVE_AGENT_CARDS


def test_evict_without_a_dashboard_deletes_nothing(monkeypatch):
    # No dashboard = ownership unverifiable = fail SAFE: never unmount or delete
    # what might be the user's card; the reuse-skip alone handles it.
    broadcasts, saved, _ = p_patch(monkeypatch, {})
    asyncio.run(ba.evict_dead_card("", "browser-x"))
    assert not broadcasts and not saved


class FakeCard:
    def __init__(self, spawned_by=None, created_at=None):
        self.spawned_by = spawned_by
        self.created_at = created_at


def test_user_card_is_never_evicted(monkeypatch):
    """A wedged USER card (no spawned_by) must never be deleted out from under the
    user; reuse-skip is the whole remedy. Only agent-spawned cards evict."""
    broadcasts, saved, dash = p_patch(monkeypatch, {"browser-user": FakeCard(None)})
    asyncio.run(ba.evict_dead_card("dash-1", "browser-user"))
    assert not broadcasts and not saved
    assert "browser-user" in dash.layout.browser_cards


# --- the idle-card reaper: cards a FINISHED run left behind ------------------------------------
# The frontend's fade-and-remove is owned by the card's own component, so a dashboard switch or a
# quit strands it. These pin the backend bound that holds no matter what the UI did.

def p_born(n):
    return datetime(2026, 1, 1) + timedelta(minutes=n)


def p_reap_patch(monkeypatch, cards, running=()):
    broadcasts, saved, dash = p_patch(monkeypatch, cards)

    class FakeSession:
        def __init__(self, status):
            self.status = status

    class FakeManager:
        def get_session(self, sid):
            return FakeSession("running") if sid in running else FakeSession("completed")

    import backend.apps.agents.agent_manager as am
    monkeypatch.setattr(am, "agent_manager", FakeManager(), raising=True)
    return broadcasts, saved, dash


def test_idle_agent_cards_are_reaped_down_to_the_newest_few(monkeypatch):
    cards = {f"browser-{i}": FakeCard("sess-old", p_born(i)) for i in range(8)}
    broadcasts, saved, dash = p_reap_patch(monkeypatch, cards)
    assert asyncio.run(ba.reap_idle_agent_cards("dash-1", keep=3)) == 5
    # the newest three survive, the five older ones are gone and the renderer was told about each
    assert sorted(dash.layout.browser_cards) == ["browser-5", "browser-6", "browser-7"]
    assert len([b for b in broadcasts if b[0] == "dashboard:browser_card_evict"]) == 5
    assert saved


def test_reaper_never_touches_user_cards_or_live_runs(monkeypatch):
    cards = {
        "browser-user": FakeCard(None, p_born(0)),           # the user's own, oldest of all
        "browser-live": FakeCard("sess-live", p_born(1)),    # its agent is still running
        "browser-driving": FakeCard("sess-old", p_born(2)),  # being driven RIGHT NOW
        "browser-idle-a": FakeCard("sess-old", p_born(3)),
        "browser-idle-b": FakeCard("sess-old", p_born(4)),
    }
    _, _, dash = p_reap_patch(monkeypatch, cards, running=("sess-live",))
    ba.ACTIVE_AGENT_CARDS.add("browser-driving")
    try:
        # keep=0 is the harshest possible sweep: anything that survives is protected by rule, not luck
        assert asyncio.run(ba.reap_idle_agent_cards("dash-1", keep=0)) == 2
    finally:
        ba.ACTIVE_AGENT_CARDS.discard("browser-driving")
    assert sorted(dash.layout.browser_cards) == ["browser-driving", "browser-live", "browser-user"]


def test_cards_from_before_created_at_existed_reap_first(monkeypatch):
    # An older build's cards have no timestamp. They are the oldest thing on the canvas, so they
    # must go before anything stamped, never outlive it on a technicality.
    cards = {
        "browser-legacy": FakeCard("sess-old", None),
        "browser-new": FakeCard("sess-old", p_born(1)),
    }
    _, _, dash = p_reap_patch(monkeypatch, cards)
    assert asyncio.run(ba.reap_idle_agent_cards("dash-1", keep=1)) == 1
    assert list(dash.layout.browser_cards) == ["browser-new"]


def test_reaper_is_quiet_when_there_is_nothing_to_collect(monkeypatch):
    cards = {"browser-a": FakeCard("sess-old", p_born(1))}
    broadcasts, saved, dash = p_reap_patch(monkeypatch, cards)
    assert asyncio.run(ba.reap_idle_agent_cards("dash-1", keep=3)) == 0
    assert not broadcasts and not saved
    assert "browser-a" in dash.layout.browser_cards
