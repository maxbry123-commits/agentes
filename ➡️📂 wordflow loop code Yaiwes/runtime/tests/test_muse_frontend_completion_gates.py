from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

RUNTIME = Path(__file__).resolve().parents[1]
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from src.core.completion_gate import (  # noqa: E402
    CompletionGateError,
    evaluate_completion,
    require_completion,
)
from src.core.kernel import Kernel, KernelError  # noqa: E402
from src.core.structured_action_gate import (  # noqa: E402
    evaluate_action,
    normalize_action,
)


def _frontend_contract() -> dict:
    return {
        "profile": "frontend",
        "goal": "render and interact with the requested UI",
        "acceptance": ["ui_visible", "primary_action_works"],
    }


def _frontend_full_result() -> dict:
    return {
        "acceptance": {"ui_visible": True, "primary_action_works": True},
        "evidence": {
            "source_code_pass": True,
            "build_pass": True,
            "runtime_pass": True,
            "browser_pass": True,
            "interaction_pass": True,
            "console_checked": True,
            "dom_or_visual_evidence": True,
            "mobile_touch_pass": True,
        },
    }


def test_frontend_source_and_build_are_not_enough():
    result = {
        "acceptance": {"ui_visible": True, "primary_action_works": False},
        "evidence": {"source_code_pass": True, "build_pass": True},
    }
    decision = evaluate_completion(_frontend_contract(), result)
    assert decision.passed is False
    assert "primary_action_works" in decision.missing_acceptance
    assert "runtime_pass" in decision.missing_evidence
    assert "browser_pass" in decision.missing_evidence
    assert "interaction_pass" in decision.missing_evidence
    assert "mobile_touch_pass" in decision.missing_evidence
    with pytest.raises(CompletionGateError):
        require_completion(_frontend_contract(), result)


def test_frontend_full_runtime_browser_touch_evidence_passes():
    decision = require_completion(_frontend_contract(), _frontend_full_result())
    assert decision.passed is True
    assert decision.acceptance_passed == decision.acceptance_total == 2


def test_backend_profile_has_a_different_evidence_contract():
    contract = {
        "profile": "backend",
        "goal": "execute backend change",
        "acceptance": ["api_behavior_correct"],
    }
    result = {
        "acceptance": {"api_behavior_correct": True},
        "evidence": {
            "source_code_pass": True,
            "execution_pass": True,
            "tests_pass": True,
            "output_captured": True,
        },
    }
    assert require_completion(contract, result).passed is True


def test_structured_action_has_stable_retry_identity():
    payload = {
        "action": "analyze_file",
        "actor": "LLM",
        "arguments": {"path": "src/app.py"},
        "side_effect": False,
    }
    first = normalize_action(payload)
    retry = normalize_action(payload)
    assert first.command_id == retry.command_id
    assert evaluate_action(first).execution_authorized is True


def test_llm_side_effect_cannot_bypass_sheriff_boundary():
    proposal = normalize_action(
        {
            "action": "draft_code",
            "actor": "LLM",
            "arguments": {"path": "src/app.py"},
            "side_effect": True,
        }
    )
    decision = evaluate_action(proposal, sheriff_approved=True)
    assert decision.execution_authorized is False
    assert decision.reason == "LLM_SIDE_EFFECT_FORBIDDEN"


def test_deterministic_side_effect_requires_sheriff():
    action = normalize_action(
        {
            "action": "persist_checkpoint",
            "actor": "DETERMINISTIC_RUNTIME",
            "arguments": {"node": "N-1"},
            "side_effect": True,
        }
    )
    assert evaluate_action(action, sheriff_approved=False).execution_authorized is False
    assert evaluate_action(action, sheriff_approved=True).execution_authorized is True


class _Bus:
    def __init__(self) -> None:
        self.events = []

    async def publish(self, name, data):
        self.events.append((name, data))


class _State:
    def __init__(self) -> None:
        self.states = {}

    async def transition(self, node_id, state):
        self.states[node_id] = state
        return state


class _Dag:
    def topological_order(self, manifest):
        return list(manifest.get("nodes", {}))


def test_kernel_opt_in_completion_contract_blocks_false_done():
    async def scenario():
        bus = _Bus()
        state = _State()
        kernel = Kernel(bus, _Dag(), state)

        async def incomplete(_payload):
            return {
                "acceptance": {"ui_visible": True, "primary_action_works": False},
                "evidence": {"source_code_pass": True, "build_pass": True},
            }

        kernel.register_node("frontend", incomplete)
        payload = {"completion_contract": _frontend_contract()}
        with pytest.raises(KernelError):
            await kernel.run_node("frontend", payload, "m-frontend")
        assert state.states["frontend"] == "FAILED"
        assert any(name == "node.failed" for name, _ in bus.events)

    asyncio.run(scenario())


def test_kernel_marks_done_only_after_completion_gate_passes():
    async def scenario():
        bus = _Bus()
        state = _State()
        kernel = Kernel(bus, _Dag(), state)

        async def complete(_payload):
            return _frontend_full_result()

        kernel.register_node("frontend", complete)
        payload = {"completion_contract": _frontend_contract()}
        result = await kernel.run_node("frontend", payload, "m-frontend")
        assert result["evidence"]["browser_pass"] is True
        assert state.states["frontend"] == "DONE"
        assert any(name == "node.completion_verified" for name, _ in bus.events)
        assert any(name == "node.done" for name, _ in bus.events)

    asyncio.run(scenario())
