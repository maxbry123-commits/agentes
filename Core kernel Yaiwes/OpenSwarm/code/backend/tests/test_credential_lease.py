"""Custody handover of a rotating credential, ordered so two holders is unrepresentable.

Providers issue a new refresh token on every refresh and treat a replayed one as theft, revoking
the whole grant family. So the invariant under test is not "the happy path works", it is: at no
point does BOTH this device and the cloud hold a token that can rotate.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_credential_lease.py -v
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx
import pytest

import backend.apps.nine_router.credential_lease as lease
import backend.apps.nine_router.credential_store as store
from backend.apps.nine_router import process

P_CONNECTION = {
    "id": "conn-1",
    "provider": "claude",
    "authType": "oauth",
    "accessToken": "access-old",
    "refreshToken": "refresh-live",
    "expiresAt": "2026-08-01T00:00:00.000Z",
    "isActive": True,
}


@pytest.fixture
def p_device(tmp_path, monkeypatch):
    """A stopped-on-demand router with one oauth connection, and a signed-in cloud identity."""
    data_dir = tmp_path / "9router"
    data_dir.mkdir()
    (data_dir / "db.json").write_text(json.dumps({"providerConnections": [dict(P_CONNECTION)]}))
    monkeypatch.setattr(process, "nine_router_data_dir", lambda: str(data_dir))

    state = {"running": True}
    monkeypatch.setattr(process, "stop", lambda: state.__setitem__("running", False))
    monkeypatch.setattr(process, "is_running", lambda: state["running"])

    async def p_ensure() -> None:
        state["running"] = True

    async def p_no_http() -> None:
        return None

    monkeypatch.setattr(process, "ensure_running", p_ensure)
    monkeypatch.setattr(store, "request_shutdown", p_no_http)
    monkeypatch.setattr(lease, "p_cloud", lambda: ("bearer-xyz", "https://api.example.test"))
    return state


def p_local() -> Dict[str, Any]:
    db = json.loads(open(store.db_path(), encoding="utf-8").read())
    return next(c for c in db["providerConnections"] if c["id"] == "conn-1")


class FakeClient:
    """Records calls and replays scripted responses; never touches the network."""

    def __init__(self, script: List[Any], calls: List[Dict[str, Any]]):
        self.script = script
        self.calls = calls

    async def __aenter__(self) -> "FakeClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None

    def p_next(self, method: str, url: str, kwargs: Dict[str, Any]) -> Any:
        self.calls.append({"method": method, "url": url, **kwargs})
        outcome = self.script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def post(self, url: str, **kwargs: Any) -> Any:
        return self.p_next("POST", url, kwargs)

    async def get(self, url: str, **kwargs: Any) -> Any:
        return self.p_next("GET", url, kwargs)


def p_response(status: int, body: Dict[str, Any] | None = None) -> Any:
    return httpx.Response(status, json=body if body is not None else {})


async def p_already_leased(harness: Dict[str, Any]) -> None:
    """Put the device in the post-handover state: cloud owns the refresh token, device does not."""
    harness["script"].append(p_response(200, {}))
    await lease.lease_to_cloud("conn-1")
    harness["script"].clear()
    harness["calls"].clear()


@pytest.fixture
def p_cloud_calls(monkeypatch):
    calls: List[Dict[str, Any]] = []
    script: List[Any] = []

    def p_factory(*args: Any, **kwargs: Any) -> FakeClient:
        return FakeClient(script, calls)

    monkeypatch.setattr(lease.httpx, "AsyncClient", p_factory)
    return {"calls": calls, "script": script}


@pytest.mark.asyncio
async def test_lease_strips_locally_and_uploads(p_device, p_cloud_calls):
    p_cloud_calls["script"].append(p_response(200, {"owner": "cloud"}))

    result = await lease.lease_to_cloud("conn-1")

    assert result.status == "leased"
    assert "refreshToken" not in p_local(), "the device must not keep a token it could rotate"
    assert p_local()["accessToken"] == "access-old", "the access token still has to work locally"
    sent = p_cloud_calls["calls"][0]["json"]
    assert sent["refresh_token"] == "refresh-live"
    assert sent["provider"] == "claude"


@pytest.mark.asyncio
async def test_device_is_stripped_before_the_upload_is_attempted(p_device, p_cloud_calls, monkeypatch):
    """The ordering IS the safety property. If the upload could run first, a failed strip would
    leave two live rotators, which is the incident this design exists to prevent."""
    observed: List[bool] = []

    def p_factory(*args: Any, **kwargs: Any) -> FakeClient:
        observed.append("refreshToken" in p_local())
        return FakeClient(p_cloud_calls["script"], p_cloud_calls["calls"])

    p_cloud_calls["script"].append(p_response(200, {}))
    monkeypatch.setattr(lease.httpx, "AsyncClient", p_factory)

    await lease.lease_to_cloud("conn-1")

    assert observed == [False], "the local token was still present when the upload began"


@pytest.mark.asyncio
async def test_rejected_upload_restores_the_local_token(p_device, p_cloud_calls):
    p_cloud_calls["script"].append(p_response(500, {}))

    result = await lease.lease_to_cloud("conn-1")

    assert result.status == "cloud_rejected"
    assert p_local()["refreshToken"] == "refresh-live", "custody never moved, so it must come back"


@pytest.mark.asyncio
async def test_ambiguous_upload_asks_who_owns_it_before_restoring(p_device, p_cloud_calls):
    """A timeout can mean the server committed anyway. Restoring blindly would recreate exactly the
    two-holder state, so ownership is checked rather than assumed."""
    p_cloud_calls["script"].append(httpx.ReadTimeout("boom"))
    p_cloud_calls["script"].append(
        p_response(200, {"leases": [{"connection_id": "conn-1", "owner": "cloud"}]})
    )

    result = await lease.lease_to_cloud("conn-1")

    assert result.status == "leased"
    assert "refreshToken" not in p_local(), "the cloud owns it; putting it back makes two rotators"


@pytest.mark.asyncio
async def test_ambiguous_upload_restores_when_the_cloud_does_not_have_it(p_device, p_cloud_calls):
    p_cloud_calls["script"].append(httpx.ReadTimeout("boom"))
    p_cloud_calls["script"].append(p_response(200, {"leases": []}))

    result = await lease.lease_to_cloud("conn-1")

    assert result.status == "cloud_rejected"
    assert p_local()["refreshToken"] == "refresh-live"


@pytest.mark.asyncio
async def test_unknown_ownership_leaves_the_token_off_the_device(p_device, p_cloud_calls):
    """Fail safe: when we cannot learn who owns it, the safe guess is 'not us'. Worst case the user
    reconnects; the alternative risks revoking their whole grant."""
    p_cloud_calls["script"].append(httpx.ReadTimeout("boom"))
    p_cloud_calls["script"].append(httpx.ReadTimeout("also boom"))

    result = await lease.lease_to_cloud("conn-1")

    assert result.status == "ownership_unknown"
    assert "refreshToken" not in p_local()


@pytest.mark.asyncio
async def test_release_brings_the_refresh_token_home(p_device, p_cloud_calls):
    await p_already_leased(p_cloud_calls)
    p_cloud_calls["script"].append(
        p_response(200, {"access_token": "access-new", "refresh_token": "refresh-rotated"})
    )

    result = await lease.release_to_device("conn-1")

    assert result.status == "released"
    assert p_local()["refreshToken"] == "refresh-rotated", "must be the CURRENT token, not the old one"
    assert p_local()["accessToken"] == "access-new"


@pytest.mark.asyncio
async def test_release_conflict_does_not_write_a_doomed_token(p_device, p_cloud_calls):
    """409 means a refresh is mid-exchange. Taking that token would hand the device one the provider
    is about to invalidate."""
    await p_already_leased(p_cloud_calls)
    p_cloud_calls["script"].append(p_response(409, {}))

    result = await lease.release_to_device("conn-1")

    assert result.status == "cloud_rejected"
    assert "refreshToken" not in p_local()


@pytest.mark.asyncio
async def test_pull_access_token_updates_only_the_access_token(p_device, p_cloud_calls):
    await p_already_leased(p_cloud_calls)
    p_cloud_calls["script"].append(p_response(200, {"access_token": "access-fresh"}))

    result = await lease.pull_access_token("conn-1")

    assert result.status == "refreshed"
    assert p_local()["accessToken"] == "access-fresh"
    assert "refreshToken" not in p_local(), "pulling a token must never re-arm local rotation"


@pytest.mark.asyncio
async def test_api_key_connection_is_not_leasable(p_device, p_cloud_calls):
    """No rotating secret means nothing to hand over, and no reason to touch the row."""
    await p_already_leased(p_cloud_calls)

    result = await lease.lease_to_cloud("conn-1")

    assert result.status == "not_rotatable"
    assert p_cloud_calls["calls"] == [], "a row with nothing to rotate must not be uploaded at all"


@pytest.mark.asyncio
async def test_signed_out_device_does_nothing(p_device, monkeypatch):
    monkeypatch.setattr(lease, "p_cloud", lambda: None)
    result = await lease.lease_to_cloud("conn-1")
    assert result.status == "not_signed_in"
    assert p_local()["refreshToken"] == "refresh-live"


def test_expiry_converts_to_unix_ms():
    assert lease.expires_ms("2026-08-01T00:00:00.000Z") == 1785542400000
    assert lease.expires_ms("garbage") == 0, "an unreadable clock must read as expired, not valid"
    assert lease.expires_ms(None) == 0
