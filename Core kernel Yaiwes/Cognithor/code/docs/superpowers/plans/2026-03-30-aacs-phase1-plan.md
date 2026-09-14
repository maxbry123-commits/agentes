# AACS Phase 1 — Capability Token Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the cryptographic Capability Token system — the foundation of Cognithor's Agent Access Control System (AACS). Tokens are Ed25519-signed, short-lived, attenuation-only, and replay-protected.

**Architecture:** New `src/jarvis/aacs/` package with 7 modules: config, exceptions, capability_token (data model), token_issuer (creation + signing), token_validator (verification), nonce cache, and revoked token store. Uses `cryptography` library (already installed) for Ed25519. Feature-flagged so it can be enabled incrementally.

**Tech Stack:** Python 3.13, `cryptography.hazmat.primitives.asymmetric.ed25519`, `dataclasses`, existing `security/audit.py` patterns

---

## File Structure

```
src/jarvis/aacs/
├── __init__.py              # Package exports
├── config.py                # AACSConfig + AACSFeatureFlags
├── exceptions.py            # 8 exception classes
├── tokens/
│   ├── __init__.py          # Token sub-package exports
│   ├── capability_token.py  # CapabilityToken + Action + ActionVerb
│   ├── token_issuer.py      # TokenIssuer: create + sign tokens
│   ├── token_validator.py   # TokenValidator + NonceCache + RevokedTokenStore + DIDResolver
│   └── token_store.py       # ActiveTokenStore: in-memory token tracking

tests/test_aacs/
├── __init__.py
├── test_config.py
├── test_exceptions.py
├── test_capability_token.py
├── test_token_issuer.py
├── test_token_validator.py
└── test_integration.py
```

---

### Task 1: AACS Config + Exceptions

**Files:**
- Create: `src/jarvis/aacs/__init__.py`
- Create: `src/jarvis/aacs/config.py`
- Create: `src/jarvis/aacs/exceptions.py`
- Create: `tests/test_aacs/__init__.py`
- Test: `tests/test_aacs/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_aacs/__init__.py
# (empty)

# tests/test_aacs/test_config.py
"""Tests for AACS configuration."""
from __future__ import annotations

from jarvis.aacs.config import AACSConfig, AACSFeatureFlags


def test_config_defaults():
    cfg = AACSConfig()
    assert cfg.default_token_ttl == 300
    assert cfg.max_token_ttl == 3600
    assert cfg.min_token_ttl == 10
    assert cfg.max_delegation_depth == 5
    assert cfg.max_active_tokens_per_agent == 50
    assert cfg.trust_score_initial == 0.5


def test_config_validate_passes():
    cfg = AACSConfig()
    cfg.validate()  # should not raise


def test_config_memory_tiers():
    cfg = AACSConfig()
    assert cfg.memory_tiers[1] == "working"
    assert cfg.memory_tiers[5] == "system_config"
    assert len(cfg.memory_tiers) == 5


def test_feature_flags_defaults():
    flags = AACSFeatureFlags()
    assert flags.token_validation_enabled is False
    assert flags.enforcement_mode == "log_only"


def test_feature_flags_enforce():
    flags = AACSFeatureFlags(
        token_validation_enabled=True,
        enforcement_mode="enforce",
    )
    assert flags.token_validation_enabled
    assert flags.enforcement_mode == "enforce"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_aacs/test_config.py -v`

- [ ] **Step 3: Implement config.py and exceptions.py**

`src/jarvis/aacs/__init__.py`:
```python
"""Agent Access Control System (AACS) for Cognithor."""
from __future__ import annotations
```

`src/jarvis/aacs/config.py` — AACSConfig (frozen dataclass with validate()), AACSFeatureFlags, AACS_CONFIG singleton. Fields: token TTLs, delegation limits, nonce cache size, trust score bounds, memory tier definitions, key store path. Exactly as specified in the AACS spec Section 3.2.

`src/jarvis/aacs/exceptions.py` — 8 exception classes as specified in Section 3.3: AACSError (base), TokenExpiredError, TokenInvalidSignatureError, TokenRevokedError, PrivilegeEscalationError, DelegationDepthExceededError, InsufficientPermissionError, ReplayAttackDetectedError, MemoryTierAccessDeniedError, DualSignatureRequiredError.

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

### Task 2: Action and ActionVerb

**Files:**
- Create: `src/jarvis/aacs/tokens/__init__.py`
- Create: `src/jarvis/aacs/tokens/capability_token.py`
- Test: `tests/test_aacs/test_capability_token.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_aacs/test_capability_token.py
"""Tests for Capability Token data model."""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from jarvis.aacs.tokens.capability_token import (
    Action, ActionVerb, CapabilityToken,
)


# ── Action tests ──

def test_action_verb_values():
    assert ActionVerb.READ == "read"
    assert ActionVerb.EXECUTE == "execute"
    assert ActionVerb.DELEGATE == "delegate"


def test_action_exact_match():
    a = Action(resource="mcp.tool.web_search", verb=ActionVerb.EXECUTE)
    assert a.matches("mcp.tool.web_search", ActionVerb.EXECUTE)
    assert not a.matches("mcp.tool.web_fetch", ActionVerb.EXECUTE)
    assert not a.matches("mcp.tool.web_search", ActionVerb.READ)


def test_action_wildcard_match():
    a = Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE)
    assert a.matches("mcp.tool.web_search", ActionVerb.EXECUTE)
    assert a.matches("mcp.tool.run_python", ActionVerb.EXECUTE)
    assert not a.matches("memory.tier.1", ActionVerb.EXECUTE)


def test_action_star_matches_all():
    a = Action(resource="*", verb=ActionVerb.READ)
    assert a.matches("anything.at.all", ActionVerb.READ)
    assert not a.matches("anything", ActionVerb.WRITE)


def test_action_is_subset_of():
    parent = Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE)
    child = Action(resource="mcp.tool.web_search", verb=ActionVerb.EXECUTE)
    assert child.is_subset_of(parent)
    assert not parent.is_subset_of(child)


# ── CapabilityToken tests ──

def test_token_defaults():
    now = datetime.now(timezone.utc)
    t = CapabilityToken(
        token_id="t1",
        issuer_did="did:cognithor:planner",
        subject_did="did:cognithor:gk",
        allowed_actions=(
            Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE),
        ),
    )
    assert t.is_root_token
    assert not t.is_signed
    assert not t.is_expired
    assert t.delegation_depth == 0
    assert t.memory_tier_ceiling == 1


def test_token_expiry():
    t = CapabilityToken(
        token_id="t1",
        issuer_did="did:cognithor:planner",
        subject_did="did:cognithor:gk",
        allowed_actions=(),
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=10),
    )
    assert t.is_expired


def test_token_action_allowed():
    t = CapabilityToken(
        token_id="t1",
        issuer_did="did:cognithor:planner",
        subject_did="did:cognithor:gk",
        allowed_actions=(
            Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE),
        ),
        denied_actions=(
            Action(resource="mcp.tool.exec_command", verb=ActionVerb.EXECUTE),
        ),
    )
    assert t.check_action_allowed("mcp.tool.web_search", ActionVerb.EXECUTE)
    assert not t.check_action_allowed("mcp.tool.exec_command", ActionVerb.EXECUTE)
    assert not t.check_action_allowed("memory.tier.1", ActionVerb.READ)


def test_token_deny_overrides_allow():
    t = CapabilityToken(
        token_id="t1",
        issuer_did="did:cognithor:planner",
        subject_did="did:cognithor:gk",
        allowed_actions=(
            Action(resource="*", verb=ActionVerb.EXECUTE),
        ),
        denied_actions=(
            Action(resource="mcp.tool.exec_command", verb=ActionVerb.EXECUTE),
        ),
    )
    assert not t.check_action_allowed("mcp.tool.exec_command", ActionVerb.EXECUTE)
    assert t.check_action_allowed("mcp.tool.web_search", ActionVerb.EXECUTE)


def test_token_payload_bytes_deterministic():
    t = CapabilityToken(
        token_id="t1",
        issuer_did="did:cognithor:planner",
        subject_did="did:cognithor:gk",
        allowed_actions=(),
        nonce="fixed-nonce",
        issued_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        expires_at=datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc),
    )
    b1 = t.payload_bytes()
    b2 = t.payload_bytes()
    assert b1 == b2  # deterministic


def test_token_compute_hash():
    t = CapabilityToken(
        token_id="t1",
        issuer_did="did:cognithor:planner",
        subject_did="did:cognithor:gk",
        allowed_actions=(),
        nonce="fixed",
        issued_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    h = t.compute_hash()
    assert len(h) == 64  # SHA-256 hex
    assert h == t.compute_hash()  # stable


def test_token_can_delegate():
    t1 = CapabilityToken(
        token_id="t1", issuer_did="d", subject_did="d",
        allowed_actions=(), max_delegation_depth=2,
    )
    assert t1.can_delegate()

    t2 = CapabilityToken(
        token_id="t2", issuer_did="d", subject_did="d",
        allowed_actions=(), max_delegation_depth=0,
    )
    assert not t2.can_delegate()


def test_token_attenuation_valid():
    parent = CapabilityToken(
        token_id="p", issuer_did="d", subject_did="d",
        allowed_actions=(Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE),),
        max_delegation_depth=3,
        memory_tier_ceiling=3,
        expires_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    child = CapabilityToken(
        token_id="c", issuer_did="d", subject_did="d2",
        allowed_actions=(Action(resource="mcp.tool.web_search", verb=ActionVerb.EXECUTE),),
        max_delegation_depth=2,
        memory_tier_ceiling=2,
        delegation_depth=1,
        expires_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    assert parent.validate_subtokens_attenuation(child)


def test_token_attenuation_rejects_escalation():
    parent = CapabilityToken(
        token_id="p", issuer_did="d", subject_did="d",
        allowed_actions=(),
        max_delegation_depth=3,
        memory_tier_ceiling=2,
        expires_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    child = CapabilityToken(
        token_id="c", issuer_did="d", subject_did="d2",
        allowed_actions=(),
        max_delegation_depth=2,
        memory_tier_ceiling=4,  # ESCALATION
        delegation_depth=1,
        expires_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    assert not parent.validate_subtokens_attenuation(child)
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement capability_token.py**

Implement exactly as specified in the AACS spec Section 3.4: ActionVerb (StrEnum with READ/WRITE/EXECUTE/DELEGATE/DELETE/ADMIN), Action (frozen dataclass with matches() and is_subset_of()), CapabilityToken (frozen dataclass with all fields, payload_bytes(), compute_hash(), check_action_allowed(), can_delegate(), validate_subtokens_attenuation()).

Key implementation notes:
- Use `from cryptography.hazmat.primitives.asymmetric.ed25519` (already installed in this project)
- `payload_bytes()` must serialize to deterministic JSON (sort_keys=True, separators=(",",":"))
- `validate_subtokens_attenuation()` checks: memory tier ceiling, delegation depth, TTL not exceeding parent

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

### Task 3: Token Issuer

**Files:**
- Create: `src/jarvis/aacs/tokens/token_issuer.py`
- Test: `tests/test_aacs/test_token_issuer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_aacs/test_token_issuer.py
"""Tests for Token Issuer."""
from __future__ import annotations

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jarvis.aacs.tokens.token_issuer import TokenIssuer
from jarvis.aacs.tokens.capability_token import Action, ActionVerb
from jarvis.aacs.exceptions import (
    DelegationDepthExceededError,
    PrivilegeEscalationError,
)


@pytest.fixture
def planner_key():
    return Ed25519PrivateKey.generate()


@pytest.fixture
def issuer(planner_key):
    return TokenIssuer(
        agent_did="did:cognithor:planner-001",
        signing_key=planner_key,
    )


def test_issue_root_token(issuer):
    token = issuer.issue_root_token(
        subject_did="did:cognithor:gatekeeper-001",
        allowed_actions=[
            Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE),
        ],
        max_delegation_depth=2,
        memory_tier_ceiling=3,
        ttl_seconds=120,
    )
    assert token.is_signed
    assert token.is_root_token
    assert token.issuer_did == "did:cognithor:planner-001"
    assert token.subject_did == "did:cognithor:gatekeeper-001"
    assert token.delegation_depth == 0
    assert len(token.signature) > 0


def test_issue_root_token_ttl_clamped(issuer):
    token = issuer.issue_root_token(
        subject_did="did:cognithor:gk",
        allowed_actions=[],
        ttl_seconds=1,  # below minimum (10)
    )
    assert (token.expires_at - token.issued_at).total_seconds() >= 10


def test_delegate_creates_child(issuer):
    root = issuer.issue_root_token(
        subject_did="did:cognithor:gk",
        allowed_actions=[
            Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE),
        ],
        max_delegation_depth=3,
        memory_tier_ceiling=3,
        ttl_seconds=300,
    )
    child = issuer.delegate(
        parent_token=root,
        subject_did="did:cognithor:executor-001",
        allowed_actions=[
            Action(resource="mcp.tool.web_search", verb=ActionVerb.EXECUTE),
        ],
        max_delegation_depth=1,
        memory_tier_ceiling=2,
    )
    assert child.is_signed
    assert not child.is_root_token
    assert child.delegation_depth == 1
    assert child.parent_token_hash == root.compute_hash()
    assert child.memory_tier_ceiling == 2


def test_delegate_rejects_no_delegation_right(issuer):
    root = issuer.issue_root_token(
        subject_did="did:cognithor:gk",
        allowed_actions=[],
        max_delegation_depth=0,  # cannot delegate
    )
    with pytest.raises(DelegationDepthExceededError):
        issuer.delegate(
            parent_token=root,
            subject_did="did:cognithor:exec",
            allowed_actions=[],
        )


def test_delegate_rejects_tier_escalation(issuer):
    root = issuer.issue_root_token(
        subject_did="did:cognithor:gk",
        allowed_actions=[
            Action(resource="*", verb=ActionVerb.READ),
        ],
        max_delegation_depth=2,
        memory_tier_ceiling=2,
    )
    with pytest.raises(PrivilegeEscalationError):
        issuer.delegate(
            parent_token=root,
            subject_did="did:cognithor:exec",
            allowed_actions=[
                Action(resource="*", verb=ActionVerb.READ),
            ],
            max_delegation_depth=1,
            memory_tier_ceiling=5,  # ESCALATION
        )


def test_delegate_child_ttl_bounded_by_parent(issuer):
    root = issuer.issue_root_token(
        subject_did="did:cognithor:gk",
        allowed_actions=[],
        max_delegation_depth=2,
        ttl_seconds=60,
    )
    child = issuer.delegate(
        parent_token=root,
        subject_did="did:cognithor:exec",
        allowed_actions=[],
        ttl_seconds=3600,  # longer than parent
    )
    parent_remaining = (root.expires_at - child.issued_at).total_seconds()
    child_ttl = (child.expires_at - child.issued_at).total_seconds()
    assert child_ttl <= parent_remaining + 1  # +1 for clock skew
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement token_issuer.py**

Implement as specified in AACS spec Section 3.5. Use `cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey` (already in the project at `security/audit.py`). Key methods: `_sign_token()`, `issue_root_token()`, `delegate()`. Delegation validates: can_delegate(), max depth, attenuation.

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

### Task 4: Token Validator + NonceCache + RevokedTokenStore + DIDResolver

**Files:**
- Create: `src/jarvis/aacs/tokens/token_validator.py`
- Test: `tests/test_aacs/test_token_validator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_aacs/test_token_validator.py
"""Tests for Token Validator."""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jarvis.aacs.tokens.token_issuer import TokenIssuer
from jarvis.aacs.tokens.token_validator import (
    TokenValidator, DIDResolver, NonceCache, RevokedTokenStore,
    ValidationResult,
)
from jarvis.aacs.tokens.capability_token import Action, ActionVerb


@pytest.fixture
def key_pair():
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    return private, public


@pytest.fixture
def issuer(key_pair):
    private, _ = key_pair
    return TokenIssuer(
        agent_did="did:cognithor:planner",
        signing_key=private,
    )


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
        allowed_actions=[
            Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE),
        ],
        ttl_seconds=300,
    )


def test_validate_valid_token(validator, valid_token):
    result = validator.validate(valid_token)
    assert result.valid
    assert result.token == valid_token


def test_validate_expired_token(validator, issuer):
    from dataclasses import replace
    token = issuer.issue_root_token(
        subject_did="did:cognithor:gk",
        allowed_actions=[],
        ttl_seconds=10,
    )
    expired = replace(
        token,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=10),
        signature=token.signature,  # keep original sig
    )
    result = validator.validate(expired)
    assert not result.valid
    assert result.error_type == "EXPIRED"


def test_validate_unknown_issuer(validator, valid_token):
    from dataclasses import replace
    token = replace(valid_token, issuer_did="did:cognithor:unknown")
    result = validator.validate(token)
    assert not result.valid
    assert result.error_type == "UNKNOWN_ISSUER"


def test_validate_tampered_signature(validator, valid_token):
    from dataclasses import replace
    token = replace(valid_token, signature=b"\x00" * 64)
    result = validator.validate(token)
    assert not result.valid
    assert result.error_type == "INVALID_SIGNATURE"


def test_validate_replay_attack(validator, valid_token):
    r1 = validator.validate(valid_token)
    assert r1.valid
    r2 = validator.validate(valid_token)  # same nonce
    assert not r2.valid
    assert result.error_type == "REPLAY_ATTACK"


def test_validate_revoked_token(validator, valid_token):
    validator.revoke_token(valid_token.token_id)
    result = validator.validate(valid_token)
    assert not result.valid
    assert result.error_type == "REVOKED"


# ── NonceCache tests ──

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
    # Oldest should be evicted
    assert cache.check_and_store("n-0")  # re-usable after eviction


# ── DIDResolver tests ──

def test_did_resolver(key_pair):
    _, public = key_pair
    resolver = DIDResolver()
    resolver.register("did:cognithor:test", public)
    assert resolver.resolve("did:cognithor:test") is not None
    assert resolver.resolve("did:cognithor:unknown") is None
```

Note: there's a bug in `test_validate_replay_attack` — it references `result` instead of `r2`. Fix: change the last assert to `assert r2.error_type == "REPLAY_ATTACK"`.

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement token_validator.py**

Implement as specified in AACS spec Section 3.6: NonceCache (LRU with expiry), RevokedTokenStore (in-memory set), DIDResolver (dict-based did→public_key mapping), ValidationResult dataclass, TokenValidator with validate() (checks: signature, expiry, nonce, revocation in fail-fast order).

Use `cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey` for signature verification. Note: `public_key.verify(signature, data)` — signature first, then data (opposite of nacl).

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

### Task 5: Feature Flags + Package Exports + Integration Test

**Files:**
- Modify: `src/jarvis/aacs/config.py` (add AACSFeatureFlags if not already present)
- Modify: `src/jarvis/aacs/__init__.py` (clean exports)
- Modify: `src/jarvis/aacs/tokens/__init__.py` (clean exports)
- Test: `tests/test_aacs/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_aacs/test_integration.py
"""Integration test: full PGE token flow."""
from __future__ import annotations

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jarvis.aacs.tokens.token_issuer import TokenIssuer
from jarvis.aacs.tokens.token_validator import (
    TokenValidator, DIDResolver,
)
from jarvis.aacs.tokens.capability_token import Action, ActionVerb


def test_full_pge_token_flow():
    """Simulate: Planner issues root → Gatekeeper delegates → Executor validates."""

    # Generate keys for 3 agents
    planner_key = Ed25519PrivateKey.generate()
    gk_key = Ed25519PrivateKey.generate()

    # Set up DID resolver with public keys
    resolver = DIDResolver()
    resolver.register("did:cognithor:planner", planner_key.public_key())
    resolver.register("did:cognithor:gatekeeper", gk_key.public_key())

    validator = TokenValidator(did_resolver=resolver)

    # Step 1: Planner issues root token to Gatekeeper
    planner_issuer = TokenIssuer(
        agent_did="did:cognithor:planner",
        signing_key=planner_key,
    )
    root_token = planner_issuer.issue_root_token(
        subject_did="did:cognithor:gatekeeper",
        allowed_actions=[
            Action(resource="mcp.tool.*", verb=ActionVerb.EXECUTE),
            Action(resource="memory.tier.1", verb=ActionVerb.READ),
            Action(resource="memory.tier.2", verb=ActionVerb.READ),
        ],
        denied_actions=[
            Action(resource="mcp.tool.exec_command", verb=ActionVerb.EXECUTE),
        ],
        max_delegation_depth=2,
        memory_tier_ceiling=3,
        ttl_seconds=300,
    )

    # Validate root token
    result = validator.validate(root_token)
    assert result.valid, f"Root token invalid: {result.error}"

    # Step 2: Gatekeeper delegates scoped sub-token to Executor
    gk_issuer = TokenIssuer(
        agent_did="did:cognithor:gatekeeper",
        signing_key=gk_key,
    )
    exec_token = gk_issuer.delegate(
        parent_token=root_token,
        subject_did="did:cognithor:executor-042",
        allowed_actions=[
            Action(resource="mcp.tool.web_search", verb=ActionVerb.EXECUTE),
            Action(resource="mcp.tool.web_fetch", verb=ActionVerb.EXECUTE),
        ],
        max_delegation_depth=0,  # Executor cannot delegate further
        memory_tier_ceiling=2,
        ttl_seconds=60,
    )

    # Validate executor token
    result2 = validator.validate(exec_token)
    assert result2.valid, f"Exec token invalid: {result2.error}"

    # Step 3: Check executor permissions
    assert exec_token.check_action_allowed(
        "mcp.tool.web_search", ActionVerb.EXECUTE
    )
    assert not exec_token.check_action_allowed(
        "mcp.tool.exec_command", ActionVerb.EXECUTE
    )
    assert not exec_token.check_action_allowed(
        "memory.tier.3", ActionVerb.READ
    )

    # Step 4: Executor cannot delegate further
    assert not exec_token.can_delegate()

    # Step 5: Revoke root token → exec token should still validate
    # (revocation is per-token, not chain-based in Phase 1)
    validator.revoke_token(root_token.token_id)
    result3 = validator.validate(exec_token)
    assert result3.valid  # exec token still valid on its own
```

- [ ] **Step 2: Ensure clean package exports**

`src/jarvis/aacs/__init__.py`:
```python
"""Agent Access Control System (AACS) for Cognithor."""
from __future__ import annotations

from jarvis.aacs.config import AACSConfig, AACSFeatureFlags, AACS_CONFIG
from jarvis.aacs.exceptions import (
    AACSError,
    DelegationDepthExceededError,
    InsufficientPermissionError,
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
    "InsufficientPermissionError",
    "PrivilegeEscalationError",
    "ReplayAttackDetectedError",
    "TokenExpiredError",
    "TokenInvalidSignatureError",
    "TokenRevokedError",
]
```

`src/jarvis/aacs/tokens/__init__.py`:
```python
"""AACS Token sub-package."""
from __future__ import annotations

from jarvis.aacs.tokens.capability_token import Action, ActionVerb, CapabilityToken
from jarvis.aacs.tokens.token_issuer import TokenIssuer
from jarvis.aacs.tokens.token_validator import (
    DIDResolver,
    NonceCache,
    RevokedTokenStore,
    TokenValidator,
    ValidationResult,
)

__all__ = [
    "Action",
    "ActionVerb",
    "CapabilityToken",
    "DIDResolver",
    "NonceCache",
    "RevokedTokenStore",
    "TokenIssuer",
    "TokenValidator",
    "ValidationResult",
]
```

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest tests/test_aacs/ -v`
Expected: ALL PASS

- [ ] **Step 4: Run ruff lint**

Run: `ruff check src/jarvis/aacs/ tests/test_aacs/`
Expected: 0 errors

- [ ] **Step 5: Commit**

---

## Spec Coverage Check

| Spec Section | Covered by Task |
|-------------|-----------------|
| 3.2 AACSConfig | Task 1 |
| 3.2 AACSFeatureFlags | Task 1 + Task 5 |
| 3.3 Exceptions (10 classes) | Task 1 |
| 3.4 ActionVerb, Action, CapabilityToken | Task 2 |
| 3.4 payload_bytes(), compute_hash() | Task 2 |
| 3.4 check_action_allowed(), can_delegate() | Task 2 |
| 3.4 validate_subtokens_attenuation() | Task 2 |
| 3.5 TokenIssuer.issue_root_token() | Task 3 |
| 3.5 TokenIssuer.delegate() | Task 3 |
| 3.5 Attenuation enforcement | Task 3 |
| 3.6 NonceCache | Task 4 |
| 3.6 RevokedTokenStore | Task 4 |
| 3.6 DIDResolver | Task 4 |
| 3.6 TokenValidator.validate() | Task 4 |
| 3.6 ValidationResult | Task 4 |
| 10.2 Feature Flags | Task 5 |
| Full PGE flow integration | Task 5 |

## Test Summary

| Task | Tests |
|------|-------|
| 1: Config + Exceptions | 5 |
| 2: CapabilityToken | 13 |
| 3: TokenIssuer | 6 |
| 4: TokenValidator | 10 |
| 5: Integration | 1 |
| **Total** | **~35** |
