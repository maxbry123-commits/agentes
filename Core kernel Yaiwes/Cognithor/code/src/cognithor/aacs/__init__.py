"""Agent Access Control System (AACS) for Cognithor."""

from __future__ import annotations

from cognithor.aacs.config import AACS_CONFIG, AACSConfig, AACSFeatureFlags
from cognithor.aacs.exceptions import (
    AACSError,
    DelegationDepthExceededError,
    DualSignatureRequiredError,
    InsufficientPermissionError,
    MemoryTierAccessDeniedError,
    PrivilegeEscalationError,
    ReplayAttackDetectedError,
    TokenExpiredError,
    TokenInvalidSignatureError,
    TokenRevokedError,
)

__all__ = [
    "AACS_CONFIG",
    "AACSConfig",
    "AACSError",
    "AACSFeatureFlags",
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
