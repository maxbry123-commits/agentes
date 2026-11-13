"""Exception types for the pack system.

Loader errors are caught and logged — a broken pack must never crash Core.
Installer errors are surfaced to the CLI so the user sees what went wrong.
"""

from __future__ import annotations


class PackError(Exception):
    """Base class for all pack-system exceptions."""


class PackValidationError(PackError):
    """Raised when a manifest or bundle fails structural validation.

    Examples: missing required field, bad JSON, mismatched EULA hash,
    version range incompatibility.
    """


class PackLoadError(PackError):
    """Raised when a previously-installed pack fails to load at runtime.

    Never re-raised past the PackLoader boundary — always logged and
    swallowed so one broken pack can't stop Core from starting.
    """


class PackInstallError(PackError):
    """Raised by the installer when install/upgrade/remove fails.

    Surfaced to the CLI as a user-visible error with a hint.
    """
