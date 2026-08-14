# -*- coding: utf-8 -*-
"""MemoryPort — T0p. Interface + Fake Hermes. No network. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Protocol, runtime_checkable

from ..cognitive_registers import merge_memory_pack


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_memory_pack(
    lock_id: str,
    *,
    engine_id: str = "fake",
    facts: list[str] | None = None,
    open_loops: list[str] | None = None,
    constraints_echo: list[str] | None = None,
    checkpoint_ref: str | None = None,
    state: str | None = None,
) -> dict[str, Any]:
    if engine_id not in ("hermes", "fake", "unknown"):
        raise ValueError(f"invalid engine_id={engine_id}")
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "pack_id": f"mp_{uuid.uuid4().hex[:12]}",
        "lock_id": lock_id or "",
        "engine_id": engine_id,
        "facts": [str(f) for f in (facts or [])],
        "open_loops": [str(x) for x in (open_loops or [])],
        "constraints_echo": [str(c) for c in (constraints_echo or [])],
        "checkpoint_ref": checkpoint_ref,
        "state": state,
    }
    body["pack_hash"] = _hash({k: v for k, v in body.items() if k != "pack_hash"})
    return body


@runtime_checkable
class MemoryPort(Protocol):
    engine_id: str

    def refresh(
        self,
        lock: dict[str, Any],
        *,
        current_step: str | None = None,
        last_output: str | None = None,
        checkpoint_ref: str | None = None,
    ) -> dict[str, Any]:
        """Return MemoryPack."""
        ...


class FakeHermesMemory:
    """Deterministic memory refresh from lock + step."""

    engine_id = "hermes"

    def refresh(
        self,
        lock: dict[str, Any],
        *,
        current_step: str | None = None,
        last_output: str | None = None,
        checkpoint_ref: str | None = None,
    ) -> dict[str, Any]:
        facts = [
            f"objective={lock.get('objective')}",
            f"lock_id={lock.get('lock_id')}",
        ]
        if current_step:
            facts.append(f"step={current_step}")
        if last_output:
            facts.append(f"last_output_len={len(last_output)}")
        open_loops = []
        if current_step:
            open_loops.append(f"continuar:{current_step}")
        return make_memory_pack(
            lock.get("lock_id") or "",
            engine_id="hermes",
            facts=facts,
            open_loops=open_loops,
            constraints_echo=list(lock.get("constraints") or []),
            checkpoint_ref=checkpoint_ref,
            state="RUNNING",
        )


def apply_memory_to_registers(
    registers_file: dict[str, Any],
    pack: dict[str, Any],
) -> dict[str, Any]:
    """Merge pack into registers; R0 must stay objective from lock seed."""
    if pack.get("lock_id") and registers_file.get("lock_id"):
        if pack["lock_id"] != registers_file["lock_id"]:
            raise ValueError("lock_id mismatch pack vs registers")
    return merge_memory_pack(registers_file, pack)
