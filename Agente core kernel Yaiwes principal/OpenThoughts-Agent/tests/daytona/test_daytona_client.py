from __future__ import annotations

import pytest

from scripts.daytona.daytona_client import resolve_api_key


def test_resolve_api_key_prefers_explicit_environment_then_secret_file(
    tmp_path, monkeypatch
):
    secrets_file = tmp_path / "secrets.env"
    secrets_file.write_text("DAYTONA_API_KEY=from-file\n")

    assert (
        resolve_api_key(api_key="explicit", secrets_file=str(secrets_file))
        == "explicit"
    )

    monkeypatch.setenv("DAYTONA_API_KEY", "from-environment")
    assert resolve_api_key(secrets_file=str(secrets_file)) == "from-environment"

    monkeypatch.delenv("DAYTONA_API_KEY")
    assert resolve_api_key(secrets_file=str(secrets_file)) == "from-file"


def test_resolve_api_key_uses_configured_fallback_and_rejects_missing_credentials(
    monkeypatch,
):
    monkeypatch.delenv("DAYTONA_API_KEY", raising=False)
    monkeypatch.setenv("DAYTONA_RL_API_KEY", "fallback")
    assert resolve_api_key(fallback_env_vars=("DAYTONA_RL_API_KEY",)) == "fallback"

    monkeypatch.delenv("DAYTONA_RL_API_KEY")
    with pytest.raises(ValueError, match="Daytona API key not found"):
        resolve_api_key()
