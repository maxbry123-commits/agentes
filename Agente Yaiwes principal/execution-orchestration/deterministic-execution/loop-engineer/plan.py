"""loop-engineer/plan@1 — the Loop Plan IR (ADR 0001).

Kernel-side schema + lint only: this module never dispatches an agent, tool,
or model provider, and it is not yet wired into `loop doctor` / a scaffolded
workspace's `.loop/` tree (see reference/repo-os-contract.md #15 for the
documented scope boundary). It exists so a plan document can be authored and
validated on its own, ahead of the execution-runtime milestone that will give
it an on-disk home.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .completion import CompletionPolicyError, normalize_completion_policy
from .contract import TERMINAL_STATES, ContractIssue, _resolve_requested_mode, _schemas_dir

PLAN_SCHEMA_ID = "loop-engineer/plan@1"
TASK_KINDS = ("agent", "tool", "gate", "approval", "join", "subloop", "human", "terminal")
MODEL_POLICY_ROLES = ("read", "reason", "write", "verify")
MODEL_CAPABILITIES = ("fast_low_cost", "deep_reasoning", "code_generation", "independent_review")

_KIND_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "agent": ("role", "verify"), "tool": ("tool_name", "verify"), "gate": ("verify",),
    "approval": ("approval_gate",), "join": ("join_on",), "subloop": ("subloop_ref",),
    "human": ("instructions",), "terminal": ("terminal_state",),
}


def _read_plan_json(path: Path, issues: list[dict]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(ContractIssue("missing_file", f"missing plan file: {path}", path))
        return None
    if path.is_dir():
        issues.append(ContractIssue("invalid_target", f"plan-lint target is a directory, not a file: {path}", path))
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(ContractIssue("invalid_json", f"{path.name}: {exc}", path))
        return None
    except UnicodeDecodeError as exc:
        issues.append(ContractIssue("invalid_encoding", f"{path.name}: not valid UTF-8: {exc}", path))
        return None
    if not isinstance(data, dict):
        issues.append(ContractIssue("invalid_json", f"{path.name}: expected object", path))
        return None
    return data


def _load_plan_schema() -> dict[str, Any]:
    return json.loads((_schemas_dir() / "plan.schema.json").read_text(encoding="utf-8"))


def _jsonschema_validate_plan(data: dict[str, Any], path: Path, issues: list[dict]) -> None:
    import jsonschema  # type: ignore
    validator = jsonschema.Draft202012Validator(_load_plan_schema())
    for err in validator.iter_errors(data):
        location = "/".join(str(p) for p in err.absolute_path) or "<root>"
        issues.append(ContractIssue("schema_violation", f"{path.name}: {location}: {err.message}", path))


def _structural_validate_plan(data: dict[str, Any], path: Path, issues: list[dict]) -> None:
    if data.get("schema") != PLAN_SCHEMA_ID:
        issues.append(ContractIssue("schema_mismatch", f"{path.name}: expected schema {PLAN_SCHEMA_ID!r}, got {data.get('schema')!r}", path))
    if not isinstance(data.get("goal"), str) or not data["goal"].strip():
        issues.append(ContractIssue("invalid_plan", "goal must be a non-empty string", path))
    criteria = data.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria:
        issues.append(ContractIssue("invalid_plan", "acceptance_criteria must be a non-empty array", path))
    else:
        for index, item in enumerate(criteria, start=1):
            if not isinstance(item, dict):
                issues.append(ContractIssue("invalid_plan", f"acceptance criterion #{index} must be an object", path))
                continue
            criterion_id = item.get("id")
            criterion_label = repr(criterion_id) if criterion_id is not None else f"#{index}"
            if not isinstance(criterion_id, str) or not criterion_id:
                issues.append(ContractIssue("invalid_plan", f"acceptance criterion {criterion_label} id must be a non-empty string", path))
            description = item.get("description")
            if not isinstance(description, str) or not description:
                issues.append(ContractIssue("invalid_plan", f"acceptance criterion {criterion_label} description must be a non-empty string", path))
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        issues.append(ContractIssue("invalid_plan", "tasks must be a non-empty array", path))
    else:
        for index, task in enumerate(tasks, start=1):
            if not isinstance(task, dict):
                issues.append(ContractIssue("invalid_task", "task must be an object", path))
                continue
            task_id = task.get("id")
            task_label = repr(task_id) if task_id is not None else f"#{index}"
            for key in ("id", "kind", "title", "depends_on"):
                if key not in task:
                    issues.append(ContractIssue("invalid_task", f"task {task_label} missing {key!r}", path))
            if not isinstance(task_id, str) or not task_id:
                issues.append(ContractIssue("invalid_task", f"task {task_label} id must be a non-empty string", path))
            title = task.get("title")
            if not isinstance(title, str) or not title:
                issues.append(ContractIssue("invalid_task", f"task {task_label} title must be a non-empty string", path))
            kind = task.get("kind")
            if not isinstance(kind, str):
                issues.append(ContractIssue("invalid_task", f"task {task_label} kind must be a string", path))
            elif kind not in TASK_KINDS:
                issues.append(ContractIssue("invalid_task_kind", f"task {task_label} has unknown kind {kind!r}", path))
            if not isinstance(task.get("depends_on"), list):
                issues.append(ContractIssue("invalid_task", f"task {task_label} depends_on must be an array", path))
    mapping = data.get("terminal_state_mapping")
    if not isinstance(mapping, dict) or not mapping:
        issues.append(ContractIssue("invalid_plan", "terminal_state_mapping must be a non-empty object", path))
    else:
        for key, value in mapping.items():
            if value not in TERMINAL_STATES:
                issues.append(ContractIssue("invalid_terminal_state", f"terminal_state_mapping[{key!r}] = {value!r} is not a canonical terminal state", path))
    model_policy = data.get("model_policy")
    if model_policy is not None:
        if not isinstance(model_policy, dict):
            issues.append(ContractIssue("invalid_plan", "model_policy must be an object", path))
        else:
            for role, capability in model_policy.items():
                if role not in MODEL_POLICY_ROLES:
                    issues.append(ContractIssue("invalid_model_policy", f"unknown model_policy role {role!r}", path))
                if capability not in MODEL_CAPABILITIES:
                    issues.append(ContractIssue("invalid_model_policy", f"unknown model_policy capability {capability!r} for role {role!r}", path))
    try:
        normalize_completion_policy(data.get("completion_policy"))
    except CompletionPolicyError as exc:
        issues.append(ContractIssue("invalid_plan", f"completion_policy is invalid: {exc}", path))


def _check_task_kind_fields(tasks: list[Any], path: Path, issues: list[dict]) -> None:
    for task in tasks:
        if not isinstance(task, dict):
            continue
        kind = task.get("kind")
        if kind not in _KIND_REQUIRED_FIELDS:
            continue
        task_id = task.get("id", "<unknown>")
        for field in _KIND_REQUIRED_FIELDS[kind]:
            if not task.get(field):
                issues.append(ContractIssue("missing_kind_field", f"task {task_id!r} (kind={kind!r}) missing required field {field!r}", path))
        if kind == "agent" and task.get("role") is not None and task["role"] not in MODEL_POLICY_ROLES:
            issues.append(ContractIssue("invalid_task_role", f"task {task_id!r} has unknown role {task['role']!r}", path))
        if kind == "terminal" and task.get("terminal_state") is not None and task["terminal_state"] not in TERMINAL_STATES:
            issues.append(ContractIssue("invalid_terminal_state", f"task {task_id!r} terminal_state {task['terminal_state']!r} is not canonical", path))
        if kind == "join":
            join_on = task.get("join_on")
            if isinstance(join_on, list) and len(join_on) < 2:
                issues.append(ContractIssue("invalid_join", f"task {task_id!r} join_on needs at least 2 upstream task ids", path))


def _check_task_ids_and_dependencies(tasks: list[Any], path: Path, issues: list[dict]) -> None:
    ids: list[str] = []
    seen: set[str] = set()
    edges: dict[str, list[str]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = task.get("id")
        task_label = repr(task_id) if task_id is not None else "<unknown>"
        depends_on = task.get("depends_on")
        if isinstance(depends_on, list):
            for dependency in depends_on:
                if not isinstance(dependency, str):
                    issues.append(ContractIssue("invalid_dependency_entry", f"task {task_label} depends_on contains non-string entry {dependency!r}", path))
        join_on = task.get("join_on")
        if isinstance(join_on, list):
            for dependency in join_on:
                if not isinstance(dependency, str):
                    issues.append(ContractIssue("invalid_dependency_entry", f"task {task_label} join_on contains non-string entry {dependency!r}", path))
        if not isinstance(task_id, str) or not task_id:
            continue
        if task_id in seen:
            issues.append(ContractIssue("duplicate_task_id", f"duplicate task id {task_id!r}", path))
        seen.add(task_id)
        ids.append(task_id)
        edges[task_id] = [d for d in depends_on if isinstance(d, str)] if isinstance(depends_on, list) else []
    known = set(ids)
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str):
            continue
        for dep in edges.get(task_id, []):
            if dep not in known:
                issues.append(ContractIssue("unknown_dependency", f"task {task_id!r} depends_on unknown task {dep!r}", path))
        join_on = task.get("join_on")
        if isinstance(join_on, list):
            for dep in join_on:
                if isinstance(dep, str) and dep not in known:
                    issues.append(ContractIssue("unknown_dependency", f"task {task_id!r} join_on unknown task {dep!r}", path))
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {task_id: WHITE for task_id in ids}
    cyclic: set[str] = set()
    for start in ids:
        if color[start] != WHITE:
            continue
        stack = [(start, iter(edges.get(start, [])))]
        color[start] = GRAY
        while stack:
            node, it = stack[-1]
            advanced = False
            for dep in it:
                if dep not in known:
                    continue
                if color[dep] == GRAY:
                    cyclic.add(node)
                    cyclic.add(dep)
                elif color[dep] == WHITE:
                    color[dep] = GRAY
                    stack.append((dep, iter(edges.get(dep, []))))
                    advanced = True
                    break
            if not advanced:
                color[node] = BLACK
                stack.pop()
    if cyclic:
        issues.append(ContractIssue("cyclic_dependency", "dependency graph has a cycle among tasks: " + ", ".join(sorted(cyclic)), path))


def _check_acceptance_criteria_ids(criteria: list[Any], path: Path, issues: list[dict]) -> None:
    seen: set[str] = set()
    for item in criteria:
        if not isinstance(item, dict):
            continue
        crit_id = item.get("id")
        if isinstance(crit_id, str) and crit_id:
            if crit_id in seen:
                issues.append(ContractIssue("duplicate_criterion_id", f"duplicate acceptance_criteria id {crit_id!r}", path))
            seen.add(crit_id)


def _check_approval_gates(data: dict[str, Any], tasks: list[Any], path: Path, issues: list[dict]) -> None:
    declared = data.get("approval_gates")
    declared_set = set(declared) if isinstance(declared, list) else set()
    approval_tasks = [t for t in tasks if isinstance(t, dict) and t.get("kind") == "approval"]
    if approval_tasks and not declared_set:
        issues.append(ContractIssue("missing_approval_gates", "plan has approval tasks but declares no top-level approval_gates", path))
        return
    for task in approval_tasks:
        gate = task.get("approval_gate")
        if isinstance(gate, str) and gate not in declared_set:
            issues.append(ContractIssue("unknown_approval_gate", f"task {task.get('id')!r} references undeclared approval_gate {gate!r}", path))


def validate_plan(target: str | Path, *, mode: str | None = None) -> dict[str, Any]:
    requested_mode, resolved_mode = _resolve_requested_mode(mode)
    path = Path(target)
    issues: list[dict] = []
    data = _read_plan_json(path, issues)
    if data is not None:
        if resolved_mode == "jsonschema":
            _jsonschema_validate_plan(data, path, issues)
        else:
            _structural_validate_plan(data, path, issues)
        tasks = data.get("tasks")
        if isinstance(tasks, list):
            _check_task_kind_fields(tasks, path, issues)
            _check_task_ids_and_dependencies(tasks, path, issues)
            _check_approval_gates(data, tasks, path, issues)
        criteria = data.get("acceptance_criteria")
        if isinstance(criteria, list):
            _check_acceptance_criteria_ids(criteria, path, issues)
    return {"ok": not issues, "path": str(path), "validation_mode": resolved_mode, "requested_mode": requested_mode, "schemas_checked": [PLAN_SCHEMA_ID], "issues": issues}
