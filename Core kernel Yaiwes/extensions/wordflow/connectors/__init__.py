"""Connectors for external accounts (Cuenta B software store, etc.)."""
from .github_external import (
    ExternalGitHubConfig,
    GitHubExternalConnector,
    config_from_mapping,
    resolve_credential,
)

__all__ = [
    "ExternalGitHubConfig",
    "GitHubExternalConnector",
    "config_from_mapping",
    "resolve_credential",
]
