"""Tests for AACS TokenIssuer."""

from __future__ import annotations

import unittest.mock as mock

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cognithor.aacs.exceptions import (
    DelegationDepthExceededError,
    PrivilegeEscalationError,
)
from cognithor.aacs.tokens.capability_token import Action, ActionVerb
from cognithor.aacs.tokens.token_issuer import TokenIssuer


@pytest.fixture()
def signing_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


@pytest.fixture()
def issuer(signing_key: Ed25519PrivateKey) -> TokenIssuer:
    return TokenIssuer(agent_did="did:jarvis:root", signing_key=signing_key)


@pytest.fixture()
def read_action() -> tuple[Action, ...]:
    return (Action(resource="mcp.tool.web_search", verb=ActionVerb.READ),)


# --------------------------------------------------------------------- #


def test_issue_root_token(
    issuer: TokenIssuer,
    signing_key: Ed25519PrivateKey,
    read_action: tuple[Action, ...],
) -> None:
    """Root token has correct fields and a valid Ed25519 signature."""
    token = issuer.issue_root_token(
        subject_did="did:jarvis:agent-1",
        allowed_actions=read_action,
        max_delegation_depth=2,
        memory_tier_ceiling=3,
    )

    assert token.issuer_did == "did:jarvis:root"
    assert token.subject_did == "did:jarvis:agent-1"
    assert token.is_root_token
    assert token.delegation_depth == 0
    assert token.max_delegation_depth == 2
    assert token.memory_tier_ceiling == 3
    assert token.is_signed

    # Verify Ed25519 signature (raises on failure)
    pub = signing_key.public_key()
    pub.verify(token.signature, token.payload_bytes())


def test_issue_root_token_ttl_clamped(
    issuer: TokenIssuer,
    read_action: tuple[Action, ...],
) -> None:
    """TTL below the configured minimum (10 s) gets clamped up."""
    token = issuer.issue_root_token(
        subject_did="did:jarvis:agent-2",
        allowed_actions=read_action,
        ttl_seconds=1,  # way below min_token_ttl=10
    )

    effective_ttl = (token.expires_at - token.issued_at).total_seconds()
    assert effective_ttl == pytest.approx(10.0, abs=1.0)


def test_delegate_creates_child(
    issuer: TokenIssuer,
    signing_key: Ed25519PrivateKey,
    read_action: tuple[Action, ...],
) -> None:
    """Delegated child token has correct depth, parent hash, and signature."""
    parent = issuer.issue_root_token(
        subject_did="did:jarvis:agent-1",
        allowed_actions=read_action,
        max_delegation_depth=2,
        memory_tier_ceiling=3,
        ttl_seconds=300,
    )

    child = issuer.delegate(
        parent_token=parent,
        subject_did="did:jarvis:agent-2",
        allowed_actions=read_action,
        max_delegation_depth=1,
        memory_tier_ceiling=2,
        ttl_seconds=60,
    )

    assert child.delegation_depth == 1
    assert child.parent_token_hash == parent.compute_hash()
    assert child.max_delegation_depth == 1
    assert child.memory_tier_ceiling == 2
    assert child.is_signed
    assert not child.is_root_token

    pub = signing_key.public_key()
    pub.verify(child.signature, child.payload_bytes())


def test_delegate_rejects_no_delegation_right(
    issuer: TokenIssuer,
    read_action: tuple[Action, ...],
) -> None:
    """Parent with max_delegation_depth=0 cannot delegate."""
    parent = issuer.issue_root_token(
        subject_did="did:jarvis:agent-1",
        allowed_actions=read_action,
        max_delegation_depth=0,
    )

    with pytest.raises(DelegationDepthExceededError):
        issuer.delegate(
            parent_token=parent,
            subject_did="did:jarvis:agent-2",
            allowed_actions=read_action,
        )


def test_delegate_rejects_tier_escalation(
    issuer: TokenIssuer,
    read_action: tuple[Action, ...],
) -> None:
    """Attenuation validation failure raises PrivilegeEscalationError.

    The issuer clamps tier to ``min(requested, parent)`` by construction,
    so we patch ``validate_subtokens_attenuation`` to simulate a scenario
    where the check detects privilege escalation.
    """
    parent = issuer.issue_root_token(
        subject_did="did:jarvis:agent-1",
        allowed_actions=read_action,
        max_delegation_depth=2,
        memory_tier_ceiling=3,
        ttl_seconds=300,
    )

    with mock.patch.object(
        type(parent),
        "validate_subtokens_attenuation",
        return_value=False,
    ):
        with pytest.raises(PrivilegeEscalationError):
            issuer.delegate(
                parent_token=parent,
                subject_did="did:jarvis:agent-2",
                allowed_actions=read_action,
                max_delegation_depth=1,
                memory_tier_ceiling=2,
                ttl_seconds=60,
            )


def test_delegate_child_ttl_bounded_by_parent(
    issuer: TokenIssuer,
    read_action: tuple[Action, ...],
) -> None:
    """Child TTL cannot exceed the parent's remaining lifetime."""
    parent = issuer.issue_root_token(
        subject_did="did:jarvis:agent-1",
        allowed_actions=read_action,
        max_delegation_depth=2,
        memory_tier_ceiling=3,
        ttl_seconds=30,  # parent lives for 30 s
    )

    child = issuer.delegate(
        parent_token=parent,
        subject_did="did:jarvis:agent-2",
        allowed_actions=read_action,
        max_delegation_depth=1,
        memory_tier_ceiling=2,
        ttl_seconds=3600,  # request way more than parent has left
    )

    child_ttl = (child.expires_at - child.issued_at).total_seconds()
    parent_remaining = (parent.expires_at - child.issued_at).total_seconds()

    # Child TTL must not exceed parent remaining (allow 2s tolerance for execution)
    assert child_ttl <= parent_remaining + 2.0
    # And it should be roughly 30s, not 3600
    assert child_ttl < 60
