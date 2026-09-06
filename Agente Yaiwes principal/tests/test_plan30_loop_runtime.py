"""Deterministic tests for PLAN30 T10-T14 adapters/guards."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_serial_dispatch_selects_first_runnable_and_only_once():
    mod = _load(
        "yaiwes_serial_dispatch",
        "execution-orchestration/deterministic-execution/serial_dispatch.py",
    )
    tasks = [
        {"task_id": "A", "status": "DONE"},
        {"task_id": "B", "status": "PENDING", "depends_on": ["A"]},
        {"task_id": "C", "status": "PENDING", "depends_on": ["A"]},
    ]
    calls = []
    result = mod.dispatch_once(tasks, lambda task: calls.append(task["task_id"]) or "ok")
    assert result["task_id"] == "B"
    assert calls == ["B"]


def test_serial_dispatch_blocks_when_dependency_missing():
    mod = _load(
        "yaiwes_serial_dispatch_blocked",
        "execution-orchestration/deterministic-execution/serial_dispatch.py",
    )
    tasks = [{"task_id": "B", "status": "PENDING", "depends_on": ["A"]}]
    assert mod.select_next_task(tasks) is None


def test_resume_identity_preserves_literal_input_and_checkpoint():
    mod = _load(
        "yaiwes_resume_identity",
        "state-events-durability/checkpoint-recovery/resume_identity.py",
    )
    original = {"INPUT_BLOCK": "literal", "contract": "tel.workflow/v3"}
    ident = mod.ResumeIdentity.from_literal_input(
        run_id="run-1", node_id="N01", input_block=original, checkpoint_id="ckpt-1"
    )
    resumed = ident.resume(node_id="N01", input_block=original, checkpoint_id="ckpt-1")
    assert resumed.attempt == 1
    assert resumed.input_hash == ident.input_hash

    with pytest.raises(mod.ResumeIdentityError):
        ident.resume(node_id="N01", input_block={"INPUT_BLOCK": "changed"}, checkpoint_id="ckpt-1")
    with pytest.raises(mod.ResumeIdentityError):
        ident.resume(node_id="N02", input_block=original, checkpoint_id="ckpt-1")
    with pytest.raises(mod.ResumeIdentityError):
        ident.resume(node_id="N01", input_block=original, checkpoint_id="ckpt-2")


def test_strategy_delta_rejects_repeated_strategy_or_delta():
    mod = _load(
        "yaiwes_strategy_delta_guard",
        "control-governance/strategy_delta_guard.py",
    )
    delta = {"query": "candidate B", "top_k": 10}
    fingerprint = mod.delta_hash(delta)
    assert not mod.validate_strategy_delta(
        strategy_id="s1", delta=delta, attempted_strategies=["s1"]
    ).allowed
    assert not mod.validate_strategy_delta(
        strategy_id="s2", delta=delta, failed_delta_hashes=[fingerprint]
    ).allowed
    assert mod.validate_strategy_delta(strategy_id="s3", delta={"query": "candidate C"}).allowed


class _MemoryStore:
    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def checkpoint(self, block_id, payload):
        key = f"ckpt:{block_id}"
        self.data[key] = dict(payload)
        return key


def test_pause_resume_requires_exact_checkpoint():
    mod = _load(
        "yaiwes_run_control",
        "state-events-durability/checkpoint-recovery/run_control_adapter.py",
    )
    store = _MemoryStore()
    paused = mod.pause_run(store, "run-1", iteration_id=7, reason="manual check")
    assert paused.paused is True
    with pytest.raises(mod.RunControlError):
        mod.resume_run(store, "run-1", expected_checkpoint_id="wrong")
    resumed = mod.resume_run(store, "run-1", expected_checkpoint_id=paused.checkpoint_id)
    assert resumed.paused is False
    assert resumed.iteration_id == 7
