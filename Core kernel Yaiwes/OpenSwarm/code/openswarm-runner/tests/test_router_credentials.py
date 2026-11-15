"""The runner must be structurally unable to rotate a user's OAuth grant.

Every test here exists to make one class of bug unwritable: a refresh token reaching
9Router's db.json. Delete either wall in runner/seed/router_credentials.py and these go red.
"""

import json
import os
import stat
from datetime import datetime, timedelta, timezone

import pytest

from runner.run_spec import InvalidRunSpec, ProviderCredential, RunSpec, load_run_spec
from runner.seed.router_credentials import (
    RefreshTokenLeak,
    assert_no_refresh_token,
    router_db_payload,
    write_router_db,
)

NOW = datetime(2026, 7, 31, 12, 0, 0, tzinfo=timezone.utc)
ACCESS_TOKEN = "at-test-value-not-a-real-token"
REFRESH_TOKEN = "rt-test-value-not-a-real-token"


def spec_json(credential: dict) -> str:
    return json.dumps({
        "run_id": "run-1",
        "workflow": {"id": "wf-1", "title": "Test", "steps": [{"text": "say hi"}]},
        "credentials": [credential],
    })


def oauth_credential() -> ProviderCredential:
    return ProviderCredential(
        provider="claude",
        auth_type="oauth",
        access_token=ACCESS_TOKEN,
        expires_at=NOW + timedelta(hours=8),
    )


@pytest.mark.parametrize("key", ["refreshToken", "refresh_token", "Refresh-Token", "oauthRefreshToken"])
def test_a_spec_carrying_a_refresh_token_never_parses(key: str, tmp_path, monkeypatch) -> None:
    payload = {
        "provider": "claude",
        "auth_type": "oauth",
        "access_token": ACCESS_TOKEN,
        "expires_at": (NOW + timedelta(hours=8)).isoformat(),
        key: REFRESH_TOKEN,
    }
    monkeypatch.setenv("OPENSWARM_RUN_SPEC", spec_json(payload))
    with pytest.raises(InvalidRunSpec) as caught:
        load_run_spec()
    assert key in str(caught.value)
    assert not list(tmp_path.iterdir()), "a rejected spec must not leave anything on disk"


@pytest.mark.parametrize("key", ["refreshToken", "refresh_token", "Refresh-Token", "oauthRefreshToken"])
def test_the_writer_guard_rejects_a_poisoned_payload(key: str) -> None:
    payload = {"providerConnections": [{"provider": "claude", key: REFRESH_TOKEN}]}
    with pytest.raises(RefreshTokenLeak):
        assert_no_refresh_token(payload)


def test_the_guard_passes_a_clean_payload() -> None:
    assert_no_refresh_token(router_db_payload([oauth_credential()], NOW))


def test_written_db_carries_the_access_token_and_no_refresh_token(tmp_path) -> None:
    path = write_router_db(str(tmp_path / "9router"), [oauth_credential()], NOW)
    raw = open(path, "r", encoding="utf-8").read()

    # Without this the "no refresh token" assertion below would also pass on an empty file.
    assert ACCESS_TOKEN in raw
    connection = json.loads(raw)["providerConnections"][0]
    assert connection["provider"] == "claude"
    assert connection["isActive"] is True
    assert connection["expiresAt"] == "2026-07-31T20:00:00.000Z"

    assert "refresh" not in raw.lower()
    assert not any("refresh" in key.lower() for key in connection)


def test_the_db_and_its_directory_are_owner_only(tmp_path) -> None:
    path = write_router_db(str(tmp_path / "9router"), [oauth_credential()], NOW)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(os.path.dirname(path)).st_mode) == 0o700


def test_an_api_key_credential_never_reaches_the_router_db(tmp_path) -> None:
    credential = ProviderCredential(provider="anthropic", auth_type="api_key", api_key="sk-test-not-real")
    path = write_router_db(str(tmp_path / "9router"), [credential], NOW)
    assert json.loads(open(path, encoding="utf-8").read())["providerConnections"] == []


def test_an_oauth_credential_without_an_access_token_is_rejected() -> None:
    with pytest.raises(ValueError, match="no access_token"):
        ProviderCredential(provider="claude", auth_type="oauth", expires_at=NOW)


def test_an_expired_access_token_is_fatal_not_refreshable() -> None:
    spec = RunSpec.model_validate_json(spec_json({
        "provider": "claude",
        "auth_type": "oauth",
        "access_token": ACCESS_TOKEN,
        "expires_at": (NOW + timedelta(seconds=30)).isoformat(),
    }))
    assert [credential.provider for credential in spec.expired_credentials(NOW)] == ["claude"]
    assert spec.expired_credentials(NOW - timedelta(hours=1)) == []
