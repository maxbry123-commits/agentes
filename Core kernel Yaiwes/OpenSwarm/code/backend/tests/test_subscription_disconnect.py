"""Disconnecting a subscription reports the VERIFIED end state, never the attempt.

The shipped bug this pins: 9Router answers a bad id with a 404 and a JSON error body, and the old
code counted every DELETE it managed to send as a removal, so the UI said "disconnected" for a lane
that was still live and the next connect stacked on a stale row.
"""

import asyncio
from typing import Dict, List, Optional

import backend.apps.agents.disconnect_subscription as ds


class FakeResponse:
    def __init__(self, status_code: int, payload: Optional[Dict] = None):
        self.status_code = status_code
        self.p_payload = payload or {}

    def json(self) -> Dict:
        return self.p_payload


class FakeRouter:
    """A 9Router whose rows only disappear when `deletable` allows the delete to succeed."""

    def __init__(self, rows: List[Dict], deletable: bool = True, readable: bool = True):
        self.rows = list(rows)
        self.deletable = deletable
        self.readable = readable
        self.deletes: List[str] = []

    def client(self, **kwargs) -> "FakeClient":
        return FakeClient(self)


class FakeClient:
    def __init__(self, router: FakeRouter):
        self.router = router

    async def __aenter__(self) -> "FakeClient":
        return self

    async def __aexit__(self, *exc) -> None:
        return None

    async def get(self, url: str, **kw) -> FakeResponse:
        if not self.router.readable:
            return FakeResponse(503, {"error": "router down"})
        return FakeResponse(200, {"connections": self.router.rows})

    async def delete(self, url: str, **kw) -> FakeResponse:
        conn_id = url.rsplit("/", 1)[-1]
        self.router.deletes.append(conn_id)
        if not self.router.deletable:
            return FakeResponse(404, {"error": "Connection not found"})
        self.router.rows = [r for r in self.router.rows if r["id"] != conn_id]
        return FakeResponse(200, {"message": "Connection deleted successfully"})


CLAUDE_AND_CODEX = [
    {"id": "c1", "provider": "claude", "name": "Account 1"},
    {"id": "x1", "provider": "codex", "name": "Account 1"},
    {"id": "x2", "provider": "codex", "name": "Account 2"},
]


def p_install(monkeypatch, router: FakeRouter) -> None:
    monkeypatch.setattr(ds, "is_running", lambda: True)
    monkeypatch.setattr(ds.httpx, "AsyncClient", lambda **kw: router.client(**kw))
    monkeypatch.setattr(ds, "invalidate_health_cache", lambda: None)
    monkeypatch.setattr(ds, "sync_settings_state", lambda: None)


def test_disconnect_clears_every_row_of_the_lane(monkeypatch):
    router = FakeRouter(CLAUDE_AND_CODEX)
    p_install(monkeypatch, router)
    result = asyncio.run(ds.disconnect_subscription("codex"))
    assert result.ok and result.removed == 2 and result.error == ""
    assert [r["provider"] for r in router.rows] == ["claude"]


def test_a_refused_delete_is_never_reported_as_success(monkeypatch):
    router = FakeRouter(CLAUDE_AND_CODEX, deletable=False)
    p_install(monkeypatch, router)
    result = asyncio.run(ds.disconnect_subscription("claude"))
    assert not result.ok
    assert result.removed == 0
    assert result.error
    assert len(router.rows) == 3  # the lane really is still there


def test_an_unreadable_router_cannot_confirm(monkeypatch):
    router = FakeRouter(CLAUDE_AND_CODEX, readable=False)
    p_install(monkeypatch, router)
    result = asyncio.run(ds.disconnect_subscription("claude"))
    assert not result.ok and result.error


def test_disconnect_is_idempotent_when_the_lane_is_already_clear(monkeypatch):
    router = FakeRouter([{"id": "c1", "provider": "claude"}])
    p_install(monkeypatch, router)
    result = asyncio.run(ds.disconnect_subscription("codex"))
    assert result.ok and result.removed == 0
    assert router.deletes == []


def test_google_lanes_cascade_together(monkeypatch):
    router = FakeRouter([
        {"id": "g1", "provider": "gemini-cli"},
        {"id": "a1", "provider": "antigravity"},
        {"id": "c1", "provider": "claude"},
    ])
    p_install(monkeypatch, router)
    result = asyncio.run(ds.disconnect_subscription("gemini-cli"))
    assert result.ok and result.removed == 2
    assert [r["provider"] for r in router.rows] == ["claude"]
    # One-directional: dropping antigravity must NOT take gemini-cli with it.
    assert ds.PROVIDER_CASCADE_REMOVES.get("antigravity") is None


def test_router_down_fails_closed(monkeypatch):
    router = FakeRouter(CLAUDE_AND_CODEX)
    p_install(monkeypatch, router)
    monkeypatch.setattr(ds, "is_running", lambda: False)
    result = asyncio.run(ds.disconnect_subscription("claude"))
    assert not result.ok and result.error
    assert router.deletes == []
