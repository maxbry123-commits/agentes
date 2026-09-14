import pytest

from runtime.src.core.file_audit_contract import FileAuditContract, SourceDescriptor
from runtime.src.core.unsafe_behavior_gate import (
    NeutralizationEvidence,
    UnsafeBehaviorGate,
    UnsafeBehaviorGateError,
)


def audit(name: str, text: str):
    return FileAuditContract().audit_text(
        SourceDescriptor(source_id=name, filename=name, provenance="test"), text
    )


def test_risky_original_safe_candidate_passes_pre_execution_gate_only():
    original = audit("unsafe.py", "def run(x):\n    return eval(x)\n")
    candidate = audit("safe.py", "def run(x):\n    return x\n")
    decision = UnsafeBehaviorGate().evaluate(
        original,
        candidate,
        [NeutralizationEvidence("DANGEROUS_CALL:eval", "return validated value", "remove dynamic evaluation")],
    )
    assert decision.pre_execution_gate_pass is True
    assert decision.execution_authorized is False
    assert decision.requires_sandbox_review is True
    assert decision.neutralized_risks == ("DANGEROUS_CALL:eval",)


def test_missing_justification_fails_closed():
    original = audit("unsafe.py", "def run(x):\n    return eval(x)\n")
    candidate = audit("safe.py", "def run(x):\n    return x\n")
    with pytest.raises(UnsafeBehaviorGateError, match="NEUTRALIZATION_EVIDENCE_INCOMPLETE"):
        UnsafeBehaviorGate().evaluate(
            original,
            candidate,
            [NeutralizationEvidence("DANGEROUS_CALL:eval", "return x", "")],
        )


def test_candidate_that_remains_risky_is_rejected():
    original = audit("unsafe.py", "def run(x):\n    return eval(x)\n")
    candidate = audit("still_unsafe.py", "def run(x):\n    return compile(x, '<x>', 'eval')\n")
    decision = UnsafeBehaviorGate().evaluate(
        original,
        candidate,
        [NeutralizationEvidence("DANGEROUS_CALL:eval", "compile expression", "replacement candidate")],
    )
    assert decision.pre_execution_gate_pass is False
    assert decision.reason == "CANDIDATE_STILL_RISKY"
    assert decision.execution_authorized is False


def test_unchanged_risky_source_fails_closed():
    original = audit("unsafe.py", "def run(x):\n    return eval(x)\n")
    with pytest.raises(UnsafeBehaviorGateError, match="RISKY_SOURCE_NOT_CHANGED"):
        UnsafeBehaviorGate().evaluate(
            original,
            original,
            [NeutralizationEvidence("DANGEROUS_CALL:eval", "return x", "remove eval")],
        )


def test_every_original_risk_requires_evidence():
    original = audit("unsafe.py", "import os\ndef run(x):\n    os.system(x)\n    return eval(x)\n")
    candidate = audit("safe.py", "def run(x):\n    return x\n")
    with pytest.raises(UnsafeBehaviorGateError, match="NEUTRALIZATION_EVIDENCE_MISSING"):
        UnsafeBehaviorGate().evaluate(
            original,
            candidate,
            [NeutralizationEvidence("DANGEROUS_CALL:eval", "return x", "remove eval")],
        )
