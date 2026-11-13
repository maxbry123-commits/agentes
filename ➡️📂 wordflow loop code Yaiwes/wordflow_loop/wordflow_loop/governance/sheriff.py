from __future__ import annotations

from ..contracts import NodeContract, sha256


def check(node: NodeContract) -> list[str]:
    errors: list[str] = []
    if not node.node_id or not node.layer or not node.literal:
        errors.append("missing_identity_or_literal")
    if node.literal_sha256 != sha256(node.literal):
        errors.append("literal_hash_mismatch")
    if node.timeout_ms <= 0:
        errors.append("invalid_timeout")
    if node.mutation and not node.authorization:
        errors.append("mutation_without_authorization")
    if node.mutation and not node.allowed_paths:
        errors.append("mutation_without_allowed_paths")
    return errors
