from __future__ import annotations

from typing import Any

from .contracts import sha256


def append_event(ledger: list[dict[str, Any]], event: dict[str, Any]) -> dict[str, Any]:
    prev_hash = ledger[-1]["hash"] if ledger else "0" * 64
    row = {"seq": len(ledger) + 1, "prev_hash": prev_hash, "event": event}
    row["hash"] = sha256(row)
    ledger.append(row)
    return row


def verify_ledger(ledger: list[dict[str, Any]]) -> bool:
    prev_hash = "0" * 64
    for expected_seq, row in enumerate(ledger, start=1):
        raw = {k: v for k, v in row.items() if k != "hash"}
        if row.get("seq") != expected_seq:
            return False
        if row.get("prev_hash") != prev_hash:
            return False
        if row.get("hash") != sha256(raw):
            return False
        prev_hash = row["hash"]
    return True
