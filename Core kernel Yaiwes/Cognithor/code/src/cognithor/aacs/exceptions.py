"""AACS-specific exceptions."""

from __future__ import annotations

__all__ = [
    "AACSError",
    "DelegationDepthExceededError",
    "DualSignatureRequiredError",
    "InsufficientPermissionError",
    "MemoryTierAccessDeniedError",
    "PrivilegeEscalationError",
    "ReplayAttackDetectedError",
    "TokenExpiredError",
    "TokenInvalidSignatureError",
    "TokenRevokedError",
]


class AACSError(Exception):
    """Base exception for all AACS errors."""


class TokenExpiredError(AACSError):
    """Token has expired."""


class TokenInvalidSignatureError(AACSError):
    """Token signature is invalid."""


class TokenRevokedError(AACSError):
    """Token has been revoked."""


class PrivilegeEscalationError(AACSError):
    """Privilege escalation attempt detected."""


class DelegationDepthExceededError(AACSError):
    """Maximum delegation depth exceeded."""


class InsufficientPermissionError(AACSError):
    """Agent lacks the required permissions."""


class ReplayAttackDetectedError(AACSError):
    """Replay attack detected: nonce already used."""


class MemoryTierAccessDeniedError(AACSError):
    """Access to this memory tier denied."""


class DualSignatureRequiredError(AACSError):
    """Tier-5 access requires additional operator signature."""
