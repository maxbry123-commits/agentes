import pytest

from runtime.src.core.architecture_chat_bridge import (
    ArchitectureBridgeError,
    ArchitecturePackage,
    convert_architecture_to_execution,
)


def _package(**overrides):
    values = {
        "architecture_version": "4.1.0-FINAL",
        "architect": "Chat 1",
        "executor": "Chat 2",
        "task_id": "T-001",
        "objective": "Build deterministic DAG core",
        "target_files": ("runtime/src/core/dag_engine.py",),
        "dependencies": (),
        "constraints": ("NO_SCOPE_CREEP",),
        "source_refs": ("PECP_MAXBRY_100x_ARQUITECTURA_v4.1.0_FINAL.md",),
    }
    values.update(overrides)
    return ArchitecturePackage(**values)


def test_chat1_to_chat2_is_normalized_without_architecture_mutation():
    packet = convert_architecture_to_execution(_package())
    assert packet.contract == "yaiwes.architecture_execution_bridge/v1"
    assert packet.mode == "DETERMINISTIC_EXECUTOR"
    assert packet.architecture_mutation_allowed is False
    assert packet.llm_execution_authority is False
    assert "NO_REPLAN" in packet.constraints


def test_chat_a_chat_b_aliases_are_accepted():
    packet = convert_architecture_to_execution(_package(architect="Chat A", executor="Chat B"))
    assert packet.task_id == "T-001"


def test_wrong_roles_or_unsafe_target_fail_closed():
    with pytest.raises(ArchitectureBridgeError, match="ARCHITECT_ROLE_MISMATCH"):
        convert_architecture_to_execution(_package(architect="Worker"))
    with pytest.raises(ArchitectureBridgeError, match="UNSAFE_TARGET_PATH"):
        convert_architecture_to_execution(_package(target_files=("../outside.py",)))
