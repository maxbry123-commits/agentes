"""Deterministic bridge from architecture output (Chat 1/A) to execution packet (Chat 2/B).

The architecture document is immutable input. This bridge validates and normalizes
it into an executor packet; it does not redesign, reprioritize, or add tasks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

ARCHITECT_ALIASES = {"Chat 1", "Chat A"}
EXECUTOR_ALIASES = {"Chat 2", "Chat B"}


class ArchitectureBridgeError(ValueError):
    pass


@dataclass(frozen=True)
class ArchitecturePackage:
    architecture_version: str
    architect: str
    executor: str
    task_id: str
    objective: str
    target_files: Tuple[str, ...]
    dependencies: Tuple[str, ...]
    constraints: Tuple[str, ...]
    source_refs: Tuple[str, ...]


@dataclass(frozen=True)
class ExecutionPacket:
    contract: str
    task_id: str
    objective: str
    target_files: Tuple[str, ...]
    dependencies: Tuple[str, ...]
    constraints: Tuple[str, ...]
    source_refs: Tuple[str, ...]
    mode: str
    architecture_mutation_allowed: bool
    llm_execution_authority: bool


def convert_architecture_to_execution(package: ArchitecturePackage) -> ExecutionPacket:
    if package.architect not in ARCHITECT_ALIASES:
        raise ArchitectureBridgeError("ARCHITECT_ROLE_MISMATCH")
    if package.executor not in EXECUTOR_ALIASES:
        raise ArchitectureBridgeError("EXECUTOR_ROLE_MISMATCH")
    if not package.architecture_version.strip():
        raise ArchitectureBridgeError("ARCHITECTURE_VERSION_REQUIRED")
    if not package.task_id.strip() or not package.objective.strip():
        raise ArchitectureBridgeError("TASK_ID_AND_OBJECTIVE_REQUIRED")
    if not package.target_files:
        raise ArchitectureBridgeError("TARGET_FILES_REQUIRED")
    if not package.source_refs:
        raise ArchitectureBridgeError("SOURCE_REFS_REQUIRED")
    if any(".." in path.replace("\\", "/").split("/") for path in package.target_files):
        raise ArchitectureBridgeError("UNSAFE_TARGET_PATH")

    fixed_constraints = (
        "NO_REPLAN",
        "NO_ARCHITECTURE_MUTATION",
        "REUSE_PATCH_ADAPT_GENERATE",
        "SANDBOX_REQUIRED",
        "INDEPENDENT_REVIEW_REQUIRED",
        "EVIDENCE_REQUIRED",
    )
    return ExecutionPacket(
        contract="yaiwes.architecture_execution_bridge/v1",
        task_id=package.task_id,
        objective=package.objective,
        target_files=package.target_files,
        dependencies=package.dependencies,
        constraints=tuple(dict.fromkeys(package.constraints + fixed_constraints)),
        source_refs=package.source_refs,
        mode="DETERMINISTIC_EXECUTOR",
        architecture_mutation_allowed=False,
        llm_execution_authority=False,
    )
