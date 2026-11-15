import pytest

from extensions.wordflow.engine.evidence_packet import (
    EvidencePacketError,
    build_evidence_packet,
    chain_packets,
    verify_packet_chain,
)


def test_chain_preserves_source_timestamp_and_verifies_integrity():
    first = build_evidence_packet(task_id="T07", claim_status="PARTIAL", timestamp=1.0)
    second = build_evidence_packet(task_id="T07", claim_status="COMPLETED", timestamp=2.0)
    chained = chain_packets([first, second])
    assert verify_packet_chain(chained["packets"])["ok"] is True
    assert chained["packets"][0]["ts"] == 1.0
    assert chained["packets"][1]["parent_hash"] == chained["packets"][0]["packet_hash"]


def test_chain_rejects_tampered_source_packet():
    packet = build_evidence_packet(task_id="T07", timestamp=1.0)
    packet["notes"] = "tampered"
    with pytest.raises(EvidencePacketError, match="INVALID_SOURCE_PACKET"):
        chain_packets([packet])


def test_chain_verifier_rejects_broken_parent_link():
    packet = build_evidence_packet(task_id="T07", timestamp=1.0)
    packet["parent_hash"] = "broken"
    # The packet hash remains valid only if the mutation is reflected in the hash;
    # verify_packet_chain must still reject the non-root parent link.
    packet["packet_hash"] = build_evidence_packet(
        task_id="T07", timestamp=1.0, parent_hash="broken"
    )["packet_hash"]
    result = verify_packet_chain([packet])
    assert result["ok"] is False
    assert result["reason"] == "PARENT_HASH_MISMATCH"
