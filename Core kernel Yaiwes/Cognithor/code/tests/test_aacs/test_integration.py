"""Integration test: full PGE token flow."""

from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cognithor.aacs.tokens.capability_token import Action, ActionVerb
from cognithor.aacs.tokens.token_issuer import TokenIssuer
from cognithor.aacs.tokens.token_validator import (
    DIDResolver,
    TokenValidator,
)


def test_full_pge_token_flow():
    """Planner issues root -> Gatekeeper delegates -> Executor validates."""

    planner_key = Ed25519PrivateKey.generate()
    gk_key = Ed25519PrivateKey.generate()

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
        max_delegation_depth=0,
        memory_tier_ceiling=2,
        ttl_seconds=60,
    )

    result2 = validator.validate(exec_token)
    assert result2.valid, f"Exec token invalid: {result2.error}"

    # Step 3: Check executor permissions
    assert exec_token.check_action_allowed("mcp.tool.web_search", ActionVerb.EXECUTE)
    assert not exec_token.check_action_allowed("mcp.tool.exec_command", ActionVerb.EXECUTE)
    assert not exec_token.check_action_allowed("memory.tier.3", ActionVerb.READ)

    # Step 4: Executor cannot delegate further
    assert not exec_token.can_delegate()

    # Step 5: Revoke root -> exec still valid (per-token revocation)
    validator.revoke_token(root_token.token_id)
    # Use a fresh validator sharing the same revoked store but with a new
    # nonce cache so the second validate() of exec_token isn't flagged as
    # replay.  This isolates the test to revocation semantics only.
    validator2 = TokenValidator(
        did_resolver=resolver,
        revoked_store=validator._revoked_store,
    )
    result3 = validator2.validate(exec_token)
    assert result3.valid
