"""B01 · determinismo ContractSet / Sentinela · mismo input → mismo hash."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contract_engine.compiler import compile_contract_set
from contract_engine.sentinela_router import route

CASES = [
    ("READ_LOCAL", {"path": "README.md"}),
    ("WRITE_LOCAL", {"path": "out.txt", "content": "hola"}),
    ("LLM_CALL", {"prompt": "explica X"}),
    ("DELETE", {"path": "tmp.bin"}),
    ("NETWORK_CALL", {"url": "https://example.com"}),
    ("EXTENSION_MOUNT", {}),
]


def test_compile_stable_across_calls():
    for op, payload in CASES:
        a = compile_contract_set(op_type=op, payload=payload, strict_reverse=False)
        b = compile_contract_set(op_type=op, payload=payload, strict_reverse=False)
        assert a.set_hash == b.set_hash, op
        assert a.fingerprint_hash == b.fingerprint_hash, op
        assert a.contracts == b.contracts, op


def test_route_stable_across_calls():
    for op, payload in CASES:
        a = route(op_type=op, payload=payload, strict_reverse=False)
        b = route(op_type=op, payload=payload, strict_reverse=False)
        assert a.set_hash == b.set_hash, op
        assert a.fingerprint_hash == b.fingerprint_hash, op
        assert a.active_contracts == b.active_contracts, op
        assert a.process_plan == b.process_plan, op


def test_order_independent_payload_keys():
    p1 = {"path": "a", "content": "x"}
    p2 = {"content": "x", "path": "a"}
    a = compile_contract_set(op_type="WRITE_LOCAL", payload=p1, strict_reverse=False)
    b = compile_contract_set(op_type="WRITE_LOCAL", payload=p2, strict_reverse=False)
    assert a.fingerprint_hash == b.fingerprint_hash
    assert a.set_hash == b.set_hash


if __name__ == "__main__":
    test_compile_stable_across_calls()
    test_route_stable_across_calls()
    test_order_independent_payload_keys()
    print("B01 OK")
