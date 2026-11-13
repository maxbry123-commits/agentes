"""AACS Capability Token data model."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

__all__ = ["Action", "ActionVerb", "CapabilityToken"]


class ActionVerb(StrEnum):
    """Verbs that describe what an action permits."""

    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    DELEGATE = "DELEGATE"
    DELETE = "DELETE"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class Action:
    """A single (resource, verb) permission entry."""

    resource: str
    verb: ActionVerb

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def matches(self, requested_resource: str, requested_verb: ActionVerb) -> bool:
        """Return True if this action covers the requested resource+verb."""
        if self.verb != requested_verb:
            return False
        return self._resource_matches(self.resource, requested_resource)

    def is_subset_of(self, parent: Action) -> bool:
        """Return True if *this* action's rights are <= *parent*'s."""
        if not parent._resource_matches(parent.resource, self.resource):
            return False
        if self.verb != parent.verb and parent.verb != ActionVerb.ADMIN:
            return False
        return True

    @staticmethod
    def _resource_matches(pattern: str, target: str) -> bool:
        """Wildcard-aware resource matching.

        Rules:
        - ``"*"`` matches everything.
        - ``"mcp.tool.*"`` matches ``"mcp.tool"`` and anything beneath it
          (e.g. ``"mcp.tool.web_search"``).
        - Otherwise exact match.
        """
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]  # strip ".*"
            return target == prefix or target.startswith(prefix + ".")
        return pattern == target


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_nonce() -> str:
    return secrets.token_hex(16)


@dataclass(frozen=True)
class CapabilityToken:
    """Immutable capability token carrying permissions for one agent."""

    token_id: str
    issuer_did: str
    subject_did: str

    allowed_actions: tuple[Action, ...]
    denied_actions: tuple[Action, ...] = ()

    max_delegation_depth: int = 0
    memory_tier_ceiling: int = 1
    resource_patterns: tuple[str, ...] = ()

    issued_at: datetime = field(default_factory=_utcnow)
    expires_at: datetime | None = None
    nonce: str = field(default_factory=_new_nonce)

    parent_token_hash: str | None = None
    delegation_depth: int = 0
    signature: bytes = b""

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_root_token(self) -> bool:
        """True when this token has no parent."""
        return self.parent_token_hash is None

    @property
    def is_expired(self) -> bool:
        """True when the token's expiry has passed."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) >= self.expires_at

    @property
    def is_signed(self) -> bool:
        """True when the token carries a non-empty signature."""
        return len(self.signature) > 0

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def payload_bytes(self) -> bytes:
        """Deterministic JSON serialization of all fields except *signature*."""
        data = {
            "allowed_actions": [
                {"resource": a.resource, "verb": str(a.verb)} for a in self.allowed_actions
            ],
            "delegation_depth": self.delegation_depth,
            "denied_actions": [
                {"resource": a.resource, "verb": str(a.verb)} for a in self.denied_actions
            ],
            "expires_at": (self.expires_at.isoformat() if self.expires_at is not None else None),
            "issued_at": self.issued_at.isoformat(),
            "issuer_did": self.issuer_did,
            "max_delegation_depth": self.max_delegation_depth,
            "memory_tier_ceiling": self.memory_tier_ceiling,
            "nonce": self.nonce,
            "parent_token_hash": self.parent_token_hash,
            "resource_patterns": list(self.resource_patterns),
            "subject_did": self.subject_did,
            "token_id": self.token_id,
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def compute_hash(self) -> str:
        """SHA-256 hex digest of :meth:`payload_bytes`."""
        return hashlib.sha256(self.payload_bytes()).hexdigest()

    # ------------------------------------------------------------------
    # Authorisation checks
    # ------------------------------------------------------------------

    def check_action_allowed(self, resource: str, verb: ActionVerb) -> bool:
        """Return True only if allowed and not denied.  Default deny."""
        for denied in self.denied_actions:
            if denied.matches(resource, verb):
                return False
        return any(allowed.matches(resource, verb) for allowed in self.allowed_actions)

    def can_delegate(self) -> bool:
        """True when delegation is permitted."""
        return self.max_delegation_depth > 0

    def validate_subtokens_attenuation(self, child: CapabilityToken) -> bool:
        """Validate that *child* is a proper attenuation of this token.

        Requirements:
        - child.memory_tier_ceiling <= parent.memory_tier_ceiling
        - child.delegation_depth == parent.delegation_depth + 1
        - child.max_delegation_depth < parent.max_delegation_depth
        - child.expires_at <= parent.expires_at (if parent has one)
        - Every child allowed_action must be a subset of parent allowed_actions
        """
        if child.memory_tier_ceiling > self.memory_tier_ceiling:
            return False
        if child.delegation_depth != self.delegation_depth + 1:
            return False
        if child.max_delegation_depth >= self.max_delegation_depth:
            return False
        if self.expires_at is not None and (
            child.expires_at is None or child.expires_at > self.expires_at
        ):
            return False
        # Every child action must be covered by at least one parent action
        for child_action in child.allowed_actions:
            if not any(child_action.is_subset_of(pa) for pa in self.allowed_actions):
                return False
        return True
