"""Shared Daytona credential and client construction helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


def resolve_api_key(
    *,
    api_key: str | None = None,
    api_key_env: str = "DAYTONA_API_KEY",
    secrets_file: str | None = None,
    fallback_env_vars: Iterable[str] = (),
) -> str:
    """Resolve a Daytona key from an explicit value, environment, or env file."""
    if api_key:
        return api_key

    env_vars = (api_key_env, *fallback_env_vars)
    for env_var in env_vars:
        value = os.environ.get(env_var)
        if value:
            return value

    if secrets_file:
        from dotenv import dotenv_values

        values = dotenv_values(Path(secrets_file).expanduser())
        for env_var in env_vars:
            value = values.get(env_var)
            if value:
                return value

    sources = ", ".join(f"${env_var}" for env_var in env_vars)
    raise ValueError(
        f"Daytona API key not found. Pass --api-key, export one of {sources}, "
        "or provide --secrets-file."
    )


def create_client(*, api_key: str, api_url: str | None = None):
    """Construct an authenticated Daytona SDK client without exposing credentials."""
    from daytona import Daytona, DaytonaConfig

    config = {"api_key": api_key}
    if api_url:
        config["api_url"] = api_url
    return Daytona(DaytonaConfig(**config))
