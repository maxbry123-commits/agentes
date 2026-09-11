import pytest

from runtime.src.core.crazywall_claim_gate import (
    InvalidTransition,
    OwnershipConflict,
    VersionConflict,
    claim_node,
    detect_claim_drift,
    release_node,
)


def node(status="PENDING", owner=None, version=1):
    return {
        "id": "G-030",
        "status": status,
        "claimed_by": owner,
        "version": version,
        "steps": [
            {"id": "1_RESEARCH", "status": "PENDING"},
            {"id": "2_MOTOR", "status": "PENDING"},
            {"id": "3_WIRE_TEST", "status": "PENDING"},
        ],
    }


def test_claim_pending_node_and_increment_version():
    result = claim_node(node(), actor="SOL_1", expected_version=1, idempotency_key="claim-1")
    assert result.changed is True
    assert result.node["status"] == "CLAIMED"
    assert result.node["claimed_by"] == "SOL_1"
    assert result.node["version"] == 2
    assert result.node["steps"][0]["status"] == "RUNNING"


def test_claim_is_idempotent_for_same_key():
    first = claim_node(node(), actor="SOL_1", expected_version=1, idempotency_key="claim-1").node
    replay = claim_node(first, actor="SOL_1", expected_version=2, idempotency_key="claim-1")
    assert replay.changed is False
    assert replay.node == first


def test_foreign_owner_fails_closed():
    with pytest.raises(OwnershipConflict):
        claim_node(node("CLAIMED", "SOL_2", 2), actor="SOL_1", expected_version=2, idempotency_key="claim-x")


def test_stale_version_fails_closed():
    with pytest.raises(VersionConflict):
        claim_node(node(version=3), actor="SOL_1", expected_version=2, idempotency_key="claim-x")


def test_different_key_cannot_reclaim_same_owned_node():
    claimed = claim_node(node(), actor="SOL_1", expected_version=1, idempotency_key="claim-1").node
    with pytest.raises(InvalidTransition):
        claim_node(claimed, actor="SOL_1", expected_version=2, idempotency_key="claim-2")


def test_release_requires_same_owner_and_resets_research():
    claimed = claim_node(node(), actor="SOL_1", expected_version=1, idempotency_key="claim-1").node
    released = release_node(claimed, actor="SOL_1", expected_version=2, idempotency_key="release-1")
    assert released.node["status"] == "PENDING"
    assert released.node["claimed_by"] is None
    assert released.node["version"] == 3
    assert released.node["steps"][0]["status"] == "PENDING"


def test_foreign_release_fails_closed():
    with pytest.raises(OwnershipConflict):
        release_node(node("CLAIMED", "SOL_2", 2), actor="SOL_1", expected_version=2, idempotency_key="release-x")


def test_detects_checkpoint_task_owner_drift():
    task = node("CLAIMED", "SOL_2", 2)
    task["id"] = "G-018"
    checkpoint = {"claimed_by": "SOL_1", "verified_this_cycle": {"gap": "G-018"}}
    drift = detect_claim_drift(task, checkpoint)
    assert drift["drift"] is True
    assert drift["decision"] == "FAIL_CLOSED_RECONCILE"
