"""Tests A03 · compiler determinista + elevación + reverse."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contract_engine.compiler import compile_contract_set
from contract_engine.reverse import ClassificationError


def test_compile_stable():
    a = compile_contract_set(op_type="READ_LOCAL", payload={"path": "a.md"}, strict_reverse=False)
    b = compile_contract_set(op_type="READ_LOCAL", payload={"path": "a.md"}, strict_reverse=False)
    assert a.set_hash == b.set_hash
    assert a.contracts == b.contracts


def test_credential_write_includes_c47():
    cs = compile_contract_set(
        op_type="WRITE_LOCAL",
        payload={"content": "api_key=sk-test"},
        strict_reverse=True,
    )
    assert cs.suggested_op_type == "CREDENTIAL_ACCESS"
    assert "C47" in cs.contracts
    assert cs.elevated is True


def test_llm_call_has_multiple_contracts():
    cs = compile_contract_set(op_type="LLM_CALL", payload={"prompt": "hi"}, strict_reverse=False)
    assert len(cs.contracts) >= 5
    assert "C43" in cs.contracts  # presupuesto


if __name__ == "__main__":
    test_compile_stable()
    test_credential_write_includes_c47()
    test_llm_call_has_multiple_contracts()
    print("A03 tests OK")
