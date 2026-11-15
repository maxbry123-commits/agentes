"""AACS Token Issuer — creates and Ed25519-signs Capability Tokens."""

from __future__ import annotations

import typing
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from cognithor.aacs.config import AACS_CONFIG
from cognithor.aacs.exceptions import (
    DelegationDepthExceededError,
    PrivilegeEscalationError,
)
from cognithor.aacs.tokens.capability_token import Action, CapabilityToken

if typing.TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

__all__ = ["TokenIssuer"]


class TokenIssuer:
    """Creates and signs :class:`CapabilityToken` instances."""

    def __init__(self, agent_did: str, signing_key: Ed25519PrivateKey) -> None:
        self._agent_did = agent_did
        self._signing_key = signing_key

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign_token(self, token: CapabilityToken) -> CapabilityToken:
        """Sign *token* with Ed25519. Uses ``dataclasses.replace`` since frozen."""
        payload = token.payload_bytes()
        signature = self._signing_key.sign(payload)
        return replace(token, signature=signature)

    @staticmethod
    def _clamp_ttl(requested: int | None) -> int:
        """Clamp *requested* TTL to config bounds, defaulting when ``None``."""
        cfg = AACS_CONFIG
        if requested is None:
            return cfg.default_token_ttl
        return max(cfg.min_token_ttl, min(requested, cfg.max_token_ttl))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def issue_root_token(
        self,
        subject_did: str,
        allowed_actions: tuple[Action, ...],
        denied_actions: tuple[Action, ...] = (),
        max_delegation_depth: int = 0,
        memory_tier_ceiling: int = 1,
        resource_patterns: tuple[str, ...] = (),
        ttl_seconds: int | None = None,
    ) -> CapabilityToken:
        """Create a root token (no parent). TTL clamped to config min/max."""
        ttl = self._clamp_ttl(ttl_seconds)
        now = datetime.now(UTC)

        token = CapabilityToken(
            token_id=str(uuid.uuid4()),
            issuer_did=self._agent_did,
            subject_did=subject_did,
            allowed_actions=allowed_actions,
            denied_actions=denied_actions,
            max_delegation_depth=max_delegation_depth,
            memory_tier_ceiling=memory_tier_ceiling,
            resource_patterns=resource_patterns,
            issued_at=now,
            expires_at=now + timedelta(seconds=ttl),
            delegation_depth=0,
            parent_token_hash=None,
        )
        return self._sign_token(token)

    def delegate(
        self,
        parent_token: CapabilityToken,
        subject_did: str,
        allowed_actions: tuple[Action, ...],
        denied_actions: tuple[Action, ...] = (),
        max_delegation_depth: int = 0,
        memory_tier_ceiling: int | None = None,
        resource_patterns: tuple[str, ...] = (),
        ttl_seconds: int | None = None,
    ) -> CapabilityToken:
        """Create a child token by delegation from *parent_token*.

        Raises
        ------
        DelegationDepthExceededError
            If the parent cannot delegate (``max_delegation_depth == 0``).
        PrivilegeEscalationError
            If the child token is not a proper attenuation of the parent.
        """
        if not parent_token.can_delegate():
            raise DelegationDepthExceededError(
                "Parent token does not permit further delegation "
                f"(max_delegation_depth={parent_token.max_delegation_depth})."
            )

        # --- TTL: clamp to config, then bound by parent remaining time ---
        ttl = self._clamp_ttl(ttl_seconds)
        now = datetime.now(UTC)
        if parent_token.expires_at is not None:
            parent_remaining = (parent_token.expires_at - now).total_seconds()
            ttl = max(1, min(ttl, int(parent_remaining)))

        # --- Memory tier: bounded by parent ---
        requested_tier = (
            memory_tier_ceiling
            if memory_tier_ceiling is not None
            else parent_token.memory_tier_ceiling
        )
        child_tier = min(requested_tier, parent_token.memory_tier_ceiling)

        # --- Delegation depth ---
        child_max_depth = min(max_delegation_depth, parent_token.max_delegation_depth - 1)

        child = CapabilityToken(
            token_id=str(uuid.uuid4()),
            issuer_did=self._agent_did,
            subject_did=subject_did,
            allowed_actions=allowed_actions,
            denied_actions=denied_actions,
            max_delegation_depth=child_max_depth,
            memory_tier_ceiling=child_tier,
            resource_patterns=resource_patterns,
            issued_at=now,
            expires_at=now + timedelta(seconds=ttl),
            delegation_depth=parent_token.delegation_depth + 1,
            parent_token_hash=parent_token.compute_hash(),
        )

        if not parent_token.validate_subtokens_attenuation(child):
            raise PrivilegeEscalationError(
                "Child token is not a proper attenuation of parent token."
            )

        return self._sign_token(child)
