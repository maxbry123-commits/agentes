"""Cognithor agent pack plugin system.

Public API:

- ``AgentPack`` — abstract base class packs inherit from
- ``PackManifest`` — validated manifest model
- ``PackContext`` — facade exposing the subset of Gateway state a pack may touch
- ``PackLoader`` — discovers + loads packs from ``~/.cognithor/packs/``
- ``PackInstaller`` — installs/upgrades/removes packs from zip files or URLs
- ``PackLoadError``, ``PackInstallError``, ``PackValidationError`` — exception types
"""

from __future__ import annotations

from cognithor.packs.errors import (
    PackError,
    PackInstallError,
    PackLoadError,
    PackValidationError,
)
from cognithor.packs.installer import PackInstaller
from cognithor.packs.interface import (
    AgentPack,
    PackContext,
    PackManifest,
    PricingTier,
    Publisher,
    RevenueShare,
)
from cognithor.packs.loader import PackLoader

__all__ = [
    "AgentPack",
    "PackContext",
    "PackError",
    "PackInstallError",
    "PackInstaller",
    "PackLoadError",
    "PackLoader",
    "PackManifest",
    "PackValidationError",
    "PricingTier",
    "Publisher",
    "RevenueShare",
]
