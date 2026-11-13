"""Pure hash-chain canonicalization and verification for event@1 records.

Stdlib-only and import-free of other loop modules: verify_chain() must work over
any ordered event list (a SQLite read or a JSONL export) so third parties can
re-verify a chain without this package's store code. Canonical form is
json.dumps(sort_keys, separators=(",",":"), ensure_ascii=False, allow_nan=False)
encoded UTF-8 — pinned normatively in reference/repo-os-contract.md #16.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Mapping

_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")

_PREIMAGE_FIELDS = (
    "schema", "run_id", "sequence", "event_id", "type", "actor", "ts",
    "causation_id", "correlation_id", "payload", "artifact_hashes",
    "prev_event_hash",
)


class ChainHashError(ValueError):
    """A value cannot be canonically hashed (non-JSON type, non-finite float, lone surrogate)."""


def canonical_json(value: Any) -> str:
    try:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ChainHashError(f"value is not canonically serializable: {exc}") from exc
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ChainHashError(f"value contains a lone surrogate: {exc}") from exc
    return text


def compute_event_hash(record: Mapping[str, Any]) -> str:
    preimage = {field: record.get(field) for field in _PREIMAGE_FIELDS}
    return hashlib.sha256(canonical_json(preimage).encode("utf-8")).hexdigest()


def link_issue(record: Mapping[str, Any], prev_head: Mapping[str, Any] | None) -> str | None:
    """One incremental chain check; None means record legally extends prev_head."""
    sequence = record.get("sequence")
    stored = record.get("event_hash")
    if stored is None:
        if prev_head is None:
            return None
        return (f"unchained event after chained prefix at sequence {sequence!r} "
                "(a pre-0.10.0 writer appended to a chained store, or the row was tampered)")
    expected_prev = prev_head["event_hash"] if prev_head is not None else None
    if record.get("prev_event_hash") != expected_prev:
        return f"prev_event_hash mismatch at sequence {sequence!r}"
    try:
        recomputed = compute_event_hash(record)
    except ChainHashError as exc:
        return f"unhashable record at sequence {sequence!r}: {exc}"
    if recomputed != stored:
        return f"event_hash mismatch at sequence {sequence!r}"
    return None


def head_sequence(events: Iterable[Mapping[str, Any]], digest: str) -> int | None:
    """Sequence at which `digest` WAS the chain head, or None if it never was.

    Established by REPLAY: every link is re-checked and every hash recomputed via
    link_issue/compute_event_hash. The stored event_hash column is never trusted —
    an adversary who can rewrite the store can also insert a row bearing the
    anchored digest, and only recomputation refuses that row.

    This is the cross-run check: --expect-chain-head is exact current-head equality,
    so it fails by construction on a store that legitimately grew. Sequence 0 is a
    legitimate answer, so callers must compare against None, never truthiness.

    Raises ValueError (deliberately NOT ChainHashError, which is scoped to
    canonicalization failures) when `digest` is not 64 lowercase hex characters: a
    silent None on a typo would read as "rewrite detected".
    """
    if not isinstance(digest, str) or _DIGEST_PATTERN.fullmatch(digest) is None:
        raise ValueError(f"digest must be 64 lowercase hex characters, got {digest!r}")
    head: dict[str, Any] | None = None
    for record in events:
        if link_issue(record, head) is not None:
            break
        stored = record.get("event_hash")
        if stored is None:
            continue
        if stored == digest:
            return record.get("sequence")
        head = {"sequence": record.get("sequence"), "event_hash": stored}
    return None


def verify_chain(events: Iterable[Mapping[str, Any]], *, expected_head: str | None = None) -> dict[str, Any]:
    """Verify a COMPLETE run stream's hash chain (sequence 0 onward); pure, I/O-free."""
    issues: list[str] = []
    unchained_prefix = 0
    chained_events = 0
    head: dict[str, Any] | None = None
    for record in events:
        issue = link_issue(record, head)
        if issue is not None:
            issues.append(issue)
            break
        if record.get("event_hash") is None:
            unchained_prefix += 1
            continue
        chained_events += 1
        head = {"sequence": record.get("sequence"), "event_hash": record["event_hash"]}
    if expected_head is not None and not issues:
        if head is None:
            issues.append("expected chain head, but the stream has no chained events")
        elif head["event_hash"] != expected_head:
            issues.append(f"chain head {head['event_hash']} does not match expected {expected_head}")
    return {"ok": not issues, "issues": issues, "chained_events": chained_events,
            "unchained_prefix": unchained_prefix, "head": head}
