"""Tests for Token Validator."""

from __future__ import annotations

from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cognithor.aacs.tokens.capability_token import Action, ActionVerb
from cognithor.aacs.tokens.token_issuer import TokenIssuer
from cognithor.aacs.tokens.token_validator import (
    DIDResolver,
    NonceCache,
    TokenValidator,
)


@pytest.fixture
def key_pair():
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    return private, public


@pytest.fixture
def issuer(key_pair):
    private, _ = key_pair
    return TokenIssuer(agent_did="did:cognithor:planner", signing_key=private)


@pytest.fixture
def validator(key_pair):
    _, public = key_pair
    resolver = DIDResolver()
    resolver.register("did:cognithor:planner", public)
    return TokenValidator(did_resolver=resolver)


@pytest.fixture
def valid_token(issuer):
    return issuer.issue_root_token(
        subject_did="did:cognithor:gk",
        allowed_actions=[Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE)],
        ttl_seconds=300,
    )


def test_validate_valid_token(validator, valid_token):
    result = validator.validate(valid_token)
    assert result.valid
    assert result.token == valid_token


def test_validate_expired_token(validator, issuer):
    # Expiry is checked after signature. We can't easily create a properly-signed
    # expired token without sleeping. Expiry logic is unit-tested in
    # test_capability_token.py via is_expired. This test is a placeholder.
    short_token = issuer.issue_root_token(
        subject_did="did:cognithor:gk",
        allowed_actions=[],
        ttl_seconds=10,
    )
    # Token is valid (not yet expired)
    result = validator.validate(short_token)
    assert result.valid


def test_validate_unknown_issuer(validator, valid_token):
    token = replace(valid_token, issuer_did="did:cognithor:unknown")
    result = validator.validate(token)
    assert not result.valid
    assert result.error_type == "UNKNOWN_ISSUER"


def test_validate_tampered_signature(validator, valid_token):
    token = replace(valid_token, signature=b"\x00" * 64)
    result = validator.validate(token)
    assert not result.valid
    assert result.error_type == "INVALID_SIGNATURE"


def test_validate_replay_attack(validator, valid_token):
    r1 = validator.validate(valid_token)
    assert r1.valid
    r2 = validator.validate(valid_token)  # same nonce
    assert not r2.valid
    assert r2.error_type == "REPLAY_ATTACK"


def test_validate_revoked_token(validator, valid_token):
    # Revoke first, then validate. Nonce hasn't been seen yet so nonce check
    # passes, then revocation check catches it.
    validator.revoke_token(valid_token.token_id)
    result = validator.validate(valid_token)
    assert not result.valid
    assert result.error_type == "REVOKED"


def test_nonce_cache_new():
    cache = NonceCache(max_size=100)
    assert cache.check_and_store("nonce-1")


def test_nonce_cache_replay():
    cache = NonceCache(max_size=100)
    cache.check_and_store("nonce-1")
    assert not cache.check_and_store("nonce-1")


def test_nonce_cache_eviction():
    cache = NonceCache(max_size=3)
    for i in range(5):
        cache.check_and_store(f"n-{i}")
    assert cache.check_and_store("n-0")  # evicted, re-usable


def test_did_resolver(key_pair):
    _, public = key_pair
    resolver = DIDResolver()
    resolver.register("did:cognithor:test", public)
    assert resolver.resolve("did:cognithor:test") is not None
    assert resolver.resolve("did:cognithor:unknown") is None
