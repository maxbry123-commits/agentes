"""Tests for AACS Capability Token data model."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cognithor.aacs.tokens.capability_token import (
    Action,
    ActionVerb,
    CapabilityToken,
)

# ---- ActionVerb -----------------------------------------------------------


def test_action_verb_values():
    assert set(ActionVerb) == {
        ActionVerb.READ,
        ActionVerb.WRITE,
        ActionVerb.EXECUTE,
        ActionVerb.DELEGATE,
        ActionVerb.DELETE,
        ActionVerb.ADMIN,
    }
    # StrEnum means the value *is* the string
    assert ActionVerb.READ == "READ"


# ---- Action matching -------------------------------------------------------


def test_action_exact_match():
    action = Action(resource="mcp.tool.web_search", verb=ActionVerb.EXECUTE)
    assert action.matches("mcp.tool.web_search", ActionVerb.EXECUTE) is True
    assert action.matches("mcp.tool.web_search", ActionVerb.READ) is False
    assert action.matches("mcp.tool.other", ActionVerb.EXECUTE) is False


def test_action_wildcard_match():
    action = Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE)
    assert action.matches("mcp.tool.web_search", ActionVerb.EXECUTE) is True
    assert action.matches("mcp.tool", ActionVerb.EXECUTE) is True
    assert action.matches("mcp.memory", ActionVerb.EXECUTE) is False


def test_action_star_matches_all():
    action = Action(resource="*", verb=ActionVerb.READ)
    assert action.matches("anything.at.all", ActionVerb.READ) is True
    assert action.matches("anything.at.all", ActionVerb.WRITE) is False


def test_action_is_subset_of():
    parent = Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE)
    child = Action(resource="mcp.tool.web_search", verb=ActionVerb.EXECUTE)
    assert child.is_subset_of(parent) is True

    unrelated = Action(resource="mcp.memory.read", verb=ActionVerb.EXECUTE)
    assert unrelated.is_subset_of(parent) is False


# ---- CapabilityToken defaults ----------------------------------------------


def test_token_defaults():
    token = CapabilityToken(
        token_id="tok-1",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(Action(resource="*", verb=ActionVerb.READ),),
    )
    assert token.is_root_token is True
    assert token.delegation_depth == 0
    assert token.max_delegation_depth == 0
    assert token.memory_tier_ceiling == 1
    assert token.is_signed is False
    assert len(token.nonce) == 32  # token_hex(16) -> 32 hex chars
    assert token.issued_at.tzinfo is not None


# ---- Expiry ----------------------------------------------------------------


def test_token_expiry():
    past = datetime.now(UTC) - timedelta(seconds=10)
    future = datetime.now(UTC) + timedelta(hours=1)

    expired = CapabilityToken(
        token_id="tok-exp",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(),
        expires_at=past,
    )
    assert expired.is_expired is True

    valid = CapabilityToken(
        token_id="tok-val",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(),
        expires_at=future,
    )
    assert valid.is_expired is False

    no_expiry = CapabilityToken(
        token_id="tok-ne",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(),
    )
    assert no_expiry.is_expired is False


# ---- Action authorisation ---------------------------------------------------


def test_token_action_allowed():
    token = CapabilityToken(
        token_id="tok-a",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE),),
    )
    assert token.check_action_allowed("mcp.tool.web_search", ActionVerb.EXECUTE) is True
    assert token.check_action_allowed("mcp.memory", ActionVerb.EXECUTE) is False


def test_token_deny_overrides_allow():
    token = CapabilityToken(
        token_id="tok-d",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE),),
        denied_actions=(Action(resource="mcp.tool.shell_exec", verb=ActionVerb.EXECUTE),),
    )
    assert token.check_action_allowed("mcp.tool.web_search", ActionVerb.EXECUTE) is True
    assert token.check_action_allowed("mcp.tool.shell_exec", ActionVerb.EXECUTE) is False


# ---- Payload determinism & hashing -----------------------------------------


def test_token_payload_bytes_deterministic():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    kwargs = dict(
        token_id="tok-det",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(Action(resource="*", verb=ActionVerb.READ),),
        issued_at=now,
        nonce="fixed-nonce",
    )
    t1 = CapabilityToken(**kwargs)
    t2 = CapabilityToken(**kwargs)
    assert t1.payload_bytes() == t2.payload_bytes()


def test_token_compute_hash():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    token = CapabilityToken(
        token_id="tok-hash",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(),
        issued_at=now,
        nonce="hash-nonce",
    )
    h = token.compute_hash()
    assert isinstance(h, str)
    assert len(h) == 64  # SHA-256 hex


# ---- Delegation ------------------------------------------------------------


def test_token_can_delegate():
    no_del = CapabilityToken(
        token_id="tok-nd",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(),
        max_delegation_depth=0,
    )
    assert no_del.can_delegate() is False

    can_del = CapabilityToken(
        token_id="tok-cd",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(),
        max_delegation_depth=3,
    )
    assert can_del.can_delegate() is True


# ---- Attenuation validation ------------------------------------------------


def test_token_attenuation_valid():
    now = datetime.now(UTC)
    parent_exp = now + timedelta(hours=2)
    child_exp = now + timedelta(hours=1)

    parent = CapabilityToken(
        token_id="tok-parent",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(),
        max_delegation_depth=3,
        memory_tier_ceiling=3,
        delegation_depth=0,
        expires_at=parent_exp,
    )

    child = CapabilityToken(
        token_id="tok-child",
        issuer_did="did:jarvis:agent-1",
        subject_did="did:jarvis:agent-2",
        allowed_actions=(),
        max_delegation_depth=2,
        memory_tier_ceiling=2,
        delegation_depth=1,
        expires_at=child_exp,
        parent_token_hash=parent.compute_hash(),
    )

    assert parent.validate_subtokens_attenuation(child) is True


def test_token_attenuation_rejects_escalation():
    now = datetime.now(UTC)
    parent_exp = now + timedelta(hours=1)

    parent = CapabilityToken(
        token_id="tok-parent",
        issuer_did="did:jarvis:root",
        subject_did="did:jarvis:agent-1",
        allowed_actions=(),
        max_delegation_depth=2,
        memory_tier_ceiling=2,
        delegation_depth=0,
        expires_at=parent_exp,
    )

    # Escalated tier ceiling
    bad_tier = CapabilityToken(
        token_id="tok-bad-tier",
        issuer_did="did:jarvis:agent-1",
        subject_did="did:jarvis:agent-2",
        allowed_actions=(),
        max_delegation_depth=1,
        memory_tier_ceiling=5,
        delegation_depth=1,
        expires_at=parent_exp,
    )
    assert parent.validate_subtokens_attenuation(bad_tier) is False

    # Wrong delegation depth
    bad_depth = CapabilityToken(
        token_id="tok-bad-depth",
        issuer_did="did:jarvis:agent-1",
        subject_did="did:jarvis:agent-2",
        allowed_actions=(),
        max_delegation_depth=1,
        memory_tier_ceiling=2,
        delegation_depth=0,  # should be 1
        expires_at=parent_exp,
    )
    assert parent.validate_subtokens_attenuation(bad_depth) is False

    # max_delegation_depth not reduced
    bad_max = CapabilityToken(
        token_id="tok-bad-max",
        issuer_did="did:jarvis:agent-1",
        subject_did="did:jarvis:agent-2",
        allowed_actions=(),
        max_delegation_depth=2,  # same as parent, should be less
        memory_tier_ceiling=2,
        delegation_depth=1,
        expires_at=parent_exp,
    )
    assert parent.validate_subtokens_attenuation(bad_max) is False

    # Expires after parent
    bad_exp = CapabilityToken(
        token_id="tok-bad-exp",
        issuer_did="did:jarvis:agent-1",
        subject_did="did:jarvis:agent-2",
        allowed_actions=(),
        max_delegation_depth=1,
        memory_tier_ceiling=2,
        delegation_depth=1,
        expires_at=parent_exp + timedelta(hours=1),
    )
    assert parent.validate_subtokens_attenuation(bad_exp) is False
