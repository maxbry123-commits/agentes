from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from . import fsm
from .chain import ChainHashError
from .completion import (
    VERIFIED_EVIDENCE_MODE,
    CompletionPolicyError,
    criteria_satisfy_completion,
    evidence_entry_is_record_shaped,
    normalize_completion_policy,
    policy_requires_verified_evidence,
    unmet_required_criteria,
)
from .paths import ARTIFACTS_DIR_NAME, EVIDENCE_DIR_NAME, LoopPaths, resolve_loop_paths

TERMINAL_STATES = (
    "Succeeded",
    "FailedUnverifiable",
    "FailedBlocked",
    "FailedBudget",
    "FailedSafety",
    "FailedSpecGap",
    "AbortedByHuman",
)

VALIDATION_MODES = ("basic", "strict", "release")

SCHEMA_IDS = (
    "loop-engineer/manifest@1",
    "loop-engineer/state@1",
    "loop-engineer/tasks@1",
    "loop-engineer/terminal@1",
)


class ValidationModeError(RuntimeError):
    """Raised when an explicit validation mode cannot be honored."""


class ContractIssue(dict):
    def __init__(self, code: str, message: str, path: Path | None = None):
        super().__init__(code=code, message=message)
        if path is not None:
            self["path"] = str(path)


def _read_json(path: Path, issues: list[dict]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(ContractIssue("missing_file", f"missing {path.name}", path))
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        # Same rule as _validate_jsonl: undecodable bytes fail the file closed
        # with a typed finding, never a traceback out of doctor_report (#107).
        issues.append(ContractIssue("invalid_encoding", f"{path.name}: not valid UTF-8: {exc}", path))
        return None
    except json.JSONDecodeError as exc:
        issues.append(ContractIssue("invalid_json", f"{path.name}: {exc}", path))
        return None
    if not isinstance(data, dict):
        issues.append(ContractIssue("invalid_json", f"{path.name}: expected object", path))
        return None
    return data


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "null":
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _strip_comment(raw: str) -> str:
    """Drop a trailing ``#`` comment, but only when the ``#`` is unquoted.

    A ``#`` inside a single- or double-quoted scalar is data (``"reach #1"``),
    not a comment; and — like YAML — a ``#`` only opens a comment at line start
    or after whitespace, so an unquoted ``reach#1`` is left intact.
    """

    in_single = in_double = False
    for i, ch in enumerate(raw):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double and (i == 0 or raw[i - 1] in " \t"):
            return raw[:i]
    return raw


def _fallback_yaml(text: str) -> dict[str, Any]:
    """Small YAML subset parser for the manifest shapes this project emits.

    It supports top-level scalars, one-level mappings, and one-level lists. When
    PyYAML is available, `read_manifest` uses it instead.
    """

    root: dict[str, Any] = {}
    current_key: str | None = None
    for raw in text.splitlines():
        line = _strip_comment(raw).rstrip()
        if not line:
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                root[key] = _parse_scalar(value)
                current_key = None
            else:
                root[key] = {}
                current_key = key
            continue
        if current_key is None:
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            if not isinstance(root[current_key], list):
                root[current_key] = []
            root[current_key].append(_parse_scalar(stripped[2:]))
        elif ":" in stripped:
            if not isinstance(root[current_key], dict):
                root[current_key] = {}
            key, value = stripped.split(":", 1)
            root[current_key][key.strip()] = _parse_scalar(value)
    return root


def read_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Undecodable bytes are malformed content: fail safe to {} exactly like
        # the malformed-YAML branch below, never propagate a traceback (#107).
        return {}
    try:
        import yaml  # type: ignore
    except Exception:
        data = _fallback_yaml(text)
    else:
        # The manifest may come from an untrusted/foreign loop dir; a malformed
        # document must fail safe to {} (parseable-as-empty), mirroring the
        # json.JSONDecodeError guard in _read_json — never propagate a traceback.
        try:
            loaded = yaml.safe_load(text)
        except yaml.YAMLError:
            loaded = None
        data = loaded if isinstance(loaded, dict) else {}
    return data


def _require_schema(data: dict[str, Any] | None, expected: str, path: Path, issues: list[dict]) -> None:
    if data is None:
        return
    if data.get("schema") != expected:
        issues.append(
            ContractIssue(
                "schema_mismatch",
                f"{path.name}: expected schema {expected!r}, got {data.get('schema')!r}",
                path,
            )
        )


def _validate_state(data: dict[str, Any] | None, path: Path, issues: list[dict]) -> None:
    _require_schema(data, "loop-engineer/state@1", path, issues)
    if data is None:
        return
    for key in ("iteration_id", "state", "plan_version", "budget_remaining"):
        if key not in data:
            issues.append(ContractIssue("missing_state_field", f"state missing {key}", path))

    if "iteration_id" in data:
        iteration_id = data.get("iteration_id")
        canonical_integer = (
            isinstance(iteration_id, int)
            and not isinstance(iteration_id, bool)
            and iteration_id >= 0
        )
        legacy_decimal = (
            isinstance(iteration_id, str)
            and (
                iteration_id == "0"
                or (
                    iteration_id.isascii()
                    and iteration_id.isdigit()
                    and not iteration_id.startswith("0")
                )
            )
        )
        if not (canonical_integer or legacy_decimal):
            issues.append(
                ContractIssue(
                    "invalid_state",
                    "iteration_id must be a non-negative integer "
                    "(legacy canonical decimal strings remain read-compatible)",
                    path,
                )
            )

    terminal = data.get("terminal_state")
    if terminal is not None and terminal not in TERMINAL_STATES:
        issues.append(ContractIssue("invalid_terminal_state", f"invalid terminal_state {terminal!r}", path))

def _check_tasks_semantics(data: dict[str, Any] | None, path: Path, issues: list[dict]) -> None:
    """Cross-task rules JSON Schema cannot express: id uniqueness and the
    evidence-before-done invariant. Runs in both validation modes."""

    if not isinstance(data, dict):
        return
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return
    seen: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = task.get("id")
        if isinstance(task_id, str) and task_id:
            if task_id in seen:
                issues.append(ContractIssue("duplicate_task", f"duplicate task id {task_id!r}", path))
            seen.add(task_id)
        if task.get("status") == "done" and not task.get("evidence"):
            issues.append(ContractIssue("done_without_evidence", f"task {task_id!r} done without evidence", path))


def _check_state_vocabulary(
    state: dict[str, Any] | None,
    manifest: dict[str, Any] | None,
    path: Path,
    issues: list[dict],
) -> None:
    """Reject undeclared state names in both validation modes."""
    if not isinstance(state, dict):
        return
    extra_states = manifest.get("extra_states") if isinstance(manifest, dict) else None
    declared = (
        tuple(value for value in extra_states if isinstance(value, str))
        if isinstance(extra_states, list)
        else ()
    )
    value = state.get("state")
    if value not in fsm.ALL_STATES + declared:
        issues.append(ContractIssue("unknown_state", f"unknown state {value!r}", path))


def _validate_tasks(data: dict[str, Any] | None, path: Path, issues: list[dict]) -> None:
    _require_schema(data, "loop-engineer/tasks@1", path, issues)
    if data is None:
        return
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        issues.append(ContractIssue("invalid_tasks", "tasks must be a list", path))
        return
    for task in tasks:
        if not isinstance(task, dict):
            issues.append(ContractIssue("invalid_task", "task must be an object", path))
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            issues.append(ContractIssue("invalid_task", "task id must be a non-empty string", path))
    _check_tasks_semantics(data, path, issues)


def _check_terminal_contradiction(
    data: dict[str, Any] | None,
    path: Path,
    issues: list[dict],
) -> None:
    """G1: a Succeeded terminal must prove every required criterion.

    This semantic rule runs in both validation modes because JSON Schema cannot
    express the relationship between the completion policy, criteria map,
    false-completion flag, and evidence list.
    """
    if not isinstance(data, dict) or data.get("state") != "Succeeded":
        return

    try:
        policy = normalize_completion_policy(data.get("completion_policy"))
    except CompletionPolicyError as exc:
        issues.append(
            ContractIssue(
                "invalid_completion_policy",
                f"Succeeded terminal has invalid completion_policy: {exc}",
                path,
            )
        )
        return

    if data.get("false_completion") is True:
        issues.append(
            ContractIssue(
                "contradictory_terminal",
                "Succeeded terminal declares false_completion=true",
                path,
            )
        )

    criteria = data.get("criteria_met")
    if not isinstance(criteria, dict) or not criteria_satisfy_completion(criteria, policy):
        unmet = unmet_required_criteria(criteria) if isinstance(criteria, dict) else ()
        detail = ", ".join(unmet) if unmet else "no criteria were declared"
        issues.append(
            ContractIssue(
                "contradictory_terminal",
                "Succeeded terminal criteria_met does not prove every required criterion: " + detail,
                path,
            )
        )

    evidence = data.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        issues.append(
            ContractIssue(
                "contradictory_terminal",
                "Succeeded terminal has empty evidence[] (G1)",
                path,
            )
        )

def _validate_terminal(data: dict[str, Any] | None, path: Path, issues: list[dict]) -> None:
    _require_schema(data, "loop-engineer/terminal@1", path, issues)
    if data is None:
        return
    if data.get("state") not in TERMINAL_STATES:
        issues.append(ContractIssue("invalid_terminal_state", f"invalid state {data.get('state')!r}", path))

    criteria = data.get("criteria_met")
    if not isinstance(criteria, dict):
        issues.append(ContractIssue("invalid_terminal", "criteria_met must be an object", path))
    else:
        if not all(isinstance(key, str) and key.strip() for key in criteria):
            issues.append(
                ContractIssue(
                    "invalid_terminal",
                    "criteria_met keys must be non-empty strings",
                    path,
                )
            )
        if not all(isinstance(value, bool) for value in criteria.values()):
            issues.append(
                ContractIssue(
                    "invalid_terminal",
                    "criteria_met values must be booleans",
                    path,
                )
            )

    try:
        normalize_completion_policy(data.get("completion_policy"))
    except CompletionPolicyError as exc:
        issues.append(
            ContractIssue(
                "invalid_terminal",
                f"completion_policy is invalid: {exc}",
                path,
            )
        )

    evidence = data.get("evidence")
    if not isinstance(evidence, list):
        issues.append(ContractIssue("invalid_terminal", "evidence must be a list", path))
    else:
        all_strings = all(isinstance(item, str) for item in evidence)
        if not all_strings or any(not item.strip() for item in evidence):
            issues.append(
                ContractIssue(
                    "invalid_terminal",
                    "evidence entries must be non-empty strings",
                    path,
                )
            )
        if all_strings and len(set(evidence)) != len(evidence):
            issues.append(
                ContractIssue(
                    "invalid_terminal",
                    "evidence entries must be unique",
                    path,
                )
            )

    iteration_id = data.get("iteration_id")
    if iteration_id is not None and (
        not isinstance(iteration_id, int)
        or isinstance(iteration_id, bool)
        or iteration_id < 0
    ):
        issues.append(
            ContractIssue(
                "invalid_terminal",
                "iteration_id must be a non-negative integer",
                path,
            )
        )

    if not isinstance(data.get("false_completion"), bool):
        issues.append(ContractIssue("invalid_terminal", "false_completion must be bool", path))
    _check_terminal_contradiction(data, path, issues)

def _validate_manifest(data: dict[str, Any] | None, path: Path, issues: list[dict]) -> None:
    if data is None:
        issues.append(ContractIssue("missing_file", "missing manifest.yaml", path))
        return
    if data.get("schema") != "loop-engineer/manifest@1":
        issues.append(
            ContractIssue(
                "schema_mismatch",
                f"manifest.yaml: expected schema 'loop-engineer/manifest@1', got {data.get('schema')!r}",
                path,
            )
        )
    policies = data.get("policies")
    if not isinstance(policies, dict):
        issues.append(ContractIssue("invalid_manifest", "policies must be an object", path))
    elif not isinstance(policies.get("plan_then_execute"), bool):
        issues.append(ContractIssue("invalid_manifest", "policies.plan_then_execute must be bool", path))
    states = data.get("terminal_states")
    if states is not None and list(states) != list(TERMINAL_STATES):
        issues.append(ContractIssue("invalid_terminal_states", "terminal_states must match canonical 7", path))


def _verify_script_paths(paths: LoopPaths) -> list[Path]:
    scripts = paths.workspace / "scripts"
    return [scripts / "verify-fast", scripts / "verify-fast.sh", scripts / "verify-full", scripts / "verify-full.sh"]


def _task_verify_values(tasks: dict[str, Any] | None) -> list[str]:
    """Non-empty ``verify`` strings declared by the tasks, in order."""
    if not isinstance(tasks, dict):
        return []
    task_list = tasks.get("tasks")
    if not isinstance(task_list, list):
        return []
    values: list[str] = []
    for task in task_list:
        if isinstance(task, dict):
            verify = task.get("verify")
            if isinstance(verify, str) and verify.strip():
                values.append(verify.strip())
    return values


def _check_verify_surface(paths: LoopPaths, tasks: dict[str, Any] | None, issues: list[dict]) -> None:
    """Every loop needs a verification surface, and a declared one must resolve.

    (a) If NO verify-* script exists AND no task declares a verify command, the
        contract can never gate anything — ``missing_verify_surface``.
    (b) A task ``verify`` whose first whitespace token is path-shaped (contains
        "/") must resolve relative to the workspace — a dangling script path is
        ``unresolved_task_verify``. A plain command (``pytest -q``) is not a path
        and is not existence-checked.

    Runs in both validation modes.
    """
    any_script = any(p.is_file() for p in _verify_script_paths(paths))
    verify_values = _task_verify_values(tasks)
    if not any_script and not verify_values:
        issues.append(
            ContractIssue(
                "missing_verify_surface",
                "no verify-* script exists and no task declares a verify command",
                paths.tasks,
            )
        )
    for value in verify_values:
        first = value.split()[0]
        if "/" not in first:
            continue
        if not (paths.workspace / first).exists():
            issues.append(
                ContractIssue(
                    "unresolved_task_verify",
                    f"task verify path {first!r} does not resolve under the workspace",
                    paths.tasks,
                )
            )


def _check_stub_verify_scripts(paths: LoopPaths, issues: list[dict]) -> None:
    """Flag verify-* scripts that still carry the scaffold's stub markers.

    The ``stub:`` / ``replace with real command`` markers are an OPT-IN
    convention: a loop that wants doctor to refuse an un-filled gate leaves them
    in until the real command lands. The templates ship WITHOUT them so a fresh
    scaffold is doctor-clean — the presence of a marker is a deliberate signal,
    never the default state.
    """
    for script in _verify_script_paths(paths):
        if not script.exists() or not script.is_file():
            continue
        text = script.read_text(encoding="utf-8", errors="ignore").lower()
        if "stub:" in text or "replace with real command" in text:
            issues.append(ContractIssue("stub_verify_script", f"{script.name} still contains stub markers", script))


_SCHEMA_FILES = {
    "manifest": "manifest.schema.json",
    "state": "state.schema.json",
    "tasks": "tasks.schema.json",
    "terminal": "terminal.schema.json",
}


def _schemas_dir() -> Path:
    # Bundle-first (wheel package data), repo-relative editable-install fallback.
    from ._resources import schemas_dir

    return schemas_dir()


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((_schemas_dir() / _SCHEMA_FILES[name]).read_text(encoding="utf-8"))


def _validation_mode() -> str:
    try:
        import jsonschema  # type: ignore  # noqa: F401
    except Exception:
        return "structural-fallback"
    return "jsonschema"


def _resolve_requested_mode(mode: str | None) -> tuple[str, str]:
    """Resolve the caller-facing mode to the internal validation branch."""
    if mode is None:
        return "auto", _validation_mode()
    if mode not in VALIDATION_MODES:
        valid = ", ".join(VALIDATION_MODES)
        raise ValidationModeError(f"unknown validation mode {mode!r}; expected one of: {valid}")
    if mode == "basic":
        return mode, "structural-fallback"
    resolved = _validation_mode()
    if resolved != "jsonschema":
        raise ValidationModeError(
            f"validation mode {mode!r} requires the jsonschema package; "
            "install it or use --mode basic"
        )
    return mode, resolved


def _jsonschema_validate(data: dict[str, Any], name: str, path: Path, issues: list[dict]) -> None:
    import jsonschema  # type: ignore

    validator = jsonschema.Draft202012Validator(_load_schema(name))
    for err in validator.iter_errors(data):
        location = "/".join(str(p) for p in err.absolute_path) or "<root>"
        issues.append(ContractIssue("schema_violation", f"{path.name}: {location}: {err.message}", path))


# The FCR/RP evidentiary trail (M5): repair records and receipt/rollout ledgers.
# Validated OPTIONALLY — only when the files exist — so an in-flight loop that has
# not emitted them yet still passes, while a loop that ships malformed metric
# inputs can no longer pass validation with them unchecked.
_RECORD_SCHEMA_FILES = {
    "repair": "repair-record.schema.json",
    "rollout": "rollout-record.schema.json",
    "receipt": "receipt.schema.json",
}

# The $id each record schema publishes, reported under schemas_checked when the
# corresponding record files were present and validated (deterministic order).
_RECORD_SCHEMA_IDS = (
    ("repair", "loop-engineer/repair@1"),
    ("rollout", "loop-engineer/rollout@1"),
    ("receipt", "loop-engineer/receipt@1"),
    ("evidence", "loop-engineer/evidence@1"),
)


def _load_schema_file(filename: str) -> dict[str, Any]:
    return json.loads((_schemas_dir() / filename).read_text(encoding="utf-8"))


def _structural_record_check(data: dict[str, Any], schema: dict[str, Any], path: Path, issues: list[dict]) -> None:
    props = schema.get("properties", {})
    for key in schema.get("required", []):
        if key not in data:
            issues.append(ContractIssue("invalid_record", f"{path.name}: missing {key}", path))
    for key, sub in props.items():
        if key in data and isinstance(sub, dict) and "const" in sub and data[key] != sub["const"]:
            issues.append(ContractIssue("schema_mismatch", f"{path.name}: {key} != {sub['const']!r}", path))
    for vk in ("verification_before", "verification_after"):
        sub = props.get(vk)
        if isinstance(sub, dict) and "score" in sub.get("required", []) and vk in data:
            value = data[vk]
            score = value.get("score") if isinstance(value, dict) else None
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                issues.append(ContractIssue("invalid_record", f"{path.name}: {vk}.score must be numeric", path))


def _validate_record(data: dict[str, Any], schema_key: str, path: Path, mode: str, issues: list[dict]) -> None:
    filename = _RECORD_SCHEMA_FILES[schema_key]
    if mode == "jsonschema":
        import jsonschema  # type: ignore

        validator = jsonschema.Draft202012Validator(_load_schema_file(filename))
        for err in validator.iter_errors(data):
            location = "/".join(str(p) for p in err.absolute_path) or "<root>"
            issues.append(ContractIssue("schema_violation", f"{path.name}: {location}: {err.message}", path))
    else:
        _structural_record_check(data, _load_schema_file(filename), path, issues)


# The canonical rollout / candidate ledger file (scripts/rollout_ledger.py,
# schemas/rollout-record.schema.json). doctor validates THIS as a rollout ledger;
# any other .loop/*.jsonl is foreign and skipped rather than force-validated
# against the rollout schema.
ROLLOUT_LEDGER_NAMES = ("rollout.jsonl",)


def _validate_jsonl(path: Path, schema_key: str, mode: str, issues: list[dict]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        # A ledger that is not valid UTF-8 fails closed — decoding it lossily
        # (errors="ignore") would let a record with corrupt bytes validate clean.
        issues.append(ContractIssue("invalid_encoding", f"{path.name}: not valid UTF-8: {exc}", path))
        return
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(ContractIssue("invalid_json", f"{path.name}:{lineno}: {exc}", path))
            continue
        if not isinstance(data, dict):
            issues.append(ContractIssue("invalid_record", f"{path.name}:{lineno}: expected object", path))
            continue
        _validate_record(data, schema_key, path, mode, issues)


_RUNNER_BUNDLE_RE = re.compile(r"verify-iter([0-9]+)\.json")
_EVIDENCE_RECORD_RE = re.compile(r"evidence-iter([0-9]+)\.json")


def _self_verified(record: Mapping[str, Any]) -> bool:
    """True when a record DECLARES that its producer also verified it.

    Comparison is strip+casefold: it closes trivial case evasion with no realistic
    false positive. A genuine rename still evades — this surfaces DECLARED
    self-verification, it does not prove independence
    (reference/safety-and-approvals.md §5).
    """
    produced_by, verified_by = record.get("produced_by"), record.get("verified_by")
    if not isinstance(produced_by, dict) or not isinstance(verified_by, dict):
        return False
    executor, verifier = produced_by.get("executor"), verified_by.get("by")
    if not isinstance(executor, str) or not isinstance(verifier, str):
        return False
    normalized = executor.strip().casefold()
    return bool(normalized) and normalized == verifier.strip().casefold()


def _orphan_bundle_issues(paths: LoopPaths, issues: list[dict]) -> None:
    """A runner-written bundle with no matching record is detectable residue.

    Mirrors the shipped `missing_event_store` tripwire (repo-os-contract §22): the
    check fires ONLY when a bundle is present, so absent-everything stays
    byte-identical. Scoped to the runner's own `verify-iter<N>.json` name, so the
    shipped example bundles (`verify-T1.json`, `verify-T1-iter1.json`) never trip it.
    Deleting BOTH files remains undetectable — the honest residual, pinned by name.
    """
    artifacts_dir = paths.loop_dir / ARTIFACTS_DIR_NAME
    if not artifacts_dir.is_dir():
        return
    for bundle_path in sorted(artifacts_dir.glob("verify-iter*.json")):
        match = _RUNNER_BUNDLE_RE.fullmatch(bundle_path.name)
        if match is None:
            continue
        record_path = paths.loop_dir / EVIDENCE_DIR_NAME / f"evidence-iter{match.group(1)}.json"
        if not record_path.is_file():
            issues.append(ContractIssue(
                "missing_evidence_record",
                f"{bundle_path.name} has no matching evidence record at "
                f".loop/{EVIDENCE_DIR_NAME}/{record_path.name} — the bundle's provenance "
                f"record is absent or was removed",
                bundle_path))


def _policy_digest_issues(
    paths: LoopPaths,
    records: list[tuple[int | None, Path, dict]],
    issues: list[dict],
) -> None:
    """Compare the LATEST record per task against the live TASKS.json goalpost.

    Only the latest record backs the task's current claim; older records describe
    goalposts that were current when they were written, and comparing them would
    make every honest re-verification a permanent failure (repo-os-contract.md §17).
    "Latest" orders numbered ``evidence-iter<N>.json`` records by iteration and ranks
    every unnumbered record below all of them (ties by filename), so a task whose only
    record carries no iteration id is still compared — being unnumbered is not a way
    out of the comparison.

    A record naming a task that is no longer in TASKS.json is not compared at all —
    a renamed or removed task is a replan, not a forgery. A task that is present but
    cannot be canonicalized is reported rather than skipped: a comparison that cannot
    run has not passed.
    """
    from .verifier import verification_policy_digest

    tasks = _read_json(paths.tasks, [])   # already reported by the contract read
    declared = tasks.get("tasks") if isinstance(tasks, dict) else None
    entries = {t["id"]: t for t in (declared if isinstance(declared, list) else [])
               if isinstance(t, dict) and isinstance(t.get("id"), str)}
    latest: dict[str, tuple[tuple[int, int, str], Path, dict]] = {}
    for iteration_id, record_path, data in records:
        produced_by = data.get("produced_by")
        task_id = produced_by.get("task_id") if isinstance(produced_by, dict) else None
        if not isinstance(task_id, str) or task_id not in entries:
            continue
        # A record outside the runner's evidence-iter<N>.json name carries no position
        # in the run's order, so it sorts BELOW every numbered record (ties by
        # filename). Excluding it outright left a hole: the only record for a task is
        # still that task's latest, and skipping it meant a moved goalpost went
        # unreported for exactly the hand-written records most worth comparing.
        rank = ((1, iteration_id, record_path.name) if isinstance(iteration_id, int)
                else (0, 0, record_path.name))
        if task_id not in latest or rank > latest[task_id][0]:
            latest[task_id] = (rank, record_path, data)
    for task_id, (_rank, record_path, data) in sorted(latest.items()):
        verified_by = data.get("verified_by")
        recorded = verified_by.get("policy_digest") if isinstance(verified_by, dict) else None
        if not isinstance(recorded, str):
            continue
        try:
            live = verification_policy_digest(entries[task_id])
        except ChainHashError as exc:
            # Fail closed. Structural-fallback mode carries no tasks@1 type-check, so
            # skipping here would leave a stale goalpost reported by nothing at all.
            issues.append(ContractIssue(
                "policy_digest_mismatch",
                f"{record_path.name}: the goalpost recorded for task {task_id!r} "
                f"({recorded}) cannot be compared against the live TASKS.json entry, "
                f"because that entry is not canonicalizable ({exc}) — agreement is "
                f"unestablished, and unestablished is not agreement",
                record_path))
            continue
        if live != recorded:
            issues.append(ContractIssue(
                "policy_digest_mismatch",
                f"{record_path.name}: the goalpost recorded for task {task_id!r} "
                f"({recorded}) is not the live TASKS.json goalpost ({live}) — "
                f"the declared verify/criterion_ref/depends_on/id changed after this "
                f"verification; re-verify to record the current goalpost",
                record_path))


def _validate_evidence_records(paths: LoopPaths, mode: str, issues: list[dict]) -> bool:
    """Validate declared evidence@1 records, hash-verify what they reference, and
    surface declared self-verification.

    Declared location: `.loop/evidence/*.json` (repo-os-contract.md §17). An absent
    directory is a no-op, so a contract with no evidence produces a byte-identical
    report — the same rule §22 pins for an absent event store.
    """
    from .evidence import evidence_issues, verify_evidence  # local: loop.evidence imports this module

    _orphan_bundle_issues(paths, issues)
    evidence_dir = paths.loop_dir / EVIDENCE_DIR_NAME
    if not evidence_dir.is_dir():
        return False
    checked = False
    verifiable: list[tuple[int | None, Path, dict]] = []
    for record_path in sorted(evidence_dir.glob("*.json")):
        data = _read_json(record_path, issues)
        if data is None:
            continue
        checked = True
        record_issues = evidence_issues(data, resolved_mode=mode)
        for issue in record_issues:
            issues.append(ContractIssue(issue["code"], f"{record_path.name}: {issue['message']}", record_path))
        if not record_issues:
            # Guarded: verify_evidence() re-runs validate_evidence internally, so an
            # unconditional call would report a malformed record twice.
            result = verify_evidence(data, workspace_root=paths.workspace)
            for issue in result["issues"]:
                issues.append(ContractIssue(issue["code"], f"{record_path.name}: {issue['message']}", record_path))
            match = _EVIDENCE_RECORD_RE.fullmatch(record_path.name)
            verifiable.append((int(match.group(1)) if match else None, record_path, data))
        if _self_verified(data):
            issues.append(ContractIssue(
                "self_verified_evidence",
                f"{record_path.name}: produced_by.executor == verified_by.by "
                f"({data['produced_by']['executor']!r}) — the producer declares it verified its own work",
                record_path))
    _policy_digest_issues(paths, verifiable, issues)
    return checked


def _verdict_failure(record: Mapping[str, Any], paths: LoopPaths) -> str | None:
    """Why the record's artifact does not attest a PASS, or ``None`` when it does.

    Hash-verification proves the pointer resolves to the bytes the record committed
    to; it says nothing about what those bytes SAY.  A record backing ``Succeeded``
    must point at a green verdict, judged by the repo's one green-marker rule
    (``loop.evidence.verify_bundle_is_green``) — the same rule ``scripts/metrics.py``
    scores FCR with, so a bundle that reads RED to metrics can never read GREEN here.

    A record whose ``kind`` is anything other than ``verify-bundle`` carries no
    verdict this layer can read (evidence@1's ``kind`` is an open vocabulary — a log,
    a diff, a screenshot).  Such a record is REFUSED rather than waved through: the
    strict mode's claim is that completion is backed by a verification that passed,
    and an artifact with no verdict cannot make that claim.  Unreadable or
    unparseable is likewise a refusal, never a skip (R007).
    """
    from .evidence import VERIFY_BUNDLE_KIND, verify_bundle_is_green

    kind = record.get("kind")
    if kind != VERIFY_BUNDLE_KIND:
        return (f"is a {kind!r} record, not a {VERIFY_BUNDLE_KIND}: it carries no verdict, "
                f"so it cannot show that anything passed")
    uri = record["uri"]
    try:
        blob = (paths.workspace / uri).read_bytes()
    except (OSError, ValueError) as exc:
        return f"cites a verify bundle that cannot be read ({exc})"
    # Re-anchored to the digest the record declares, so the bytes judged here are the
    # bytes hash-verification just accepted rather than whatever landed since.
    if hashlib.sha256(blob).hexdigest() != record["sha256"]:
        return (f"cites a verify bundle whose bytes changed between hash verification "
                f"and the verdict read: {uri}")
    try:
        bundle = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return f"cites a verify bundle that is not UTF-8 JSON ({exc})"
    if not isinstance(bundle, dict):
        return "cites a verify bundle that is not a JSON object"
    if not verify_bundle_is_green(bundle):
        return (f"cites a verify bundle whose verdict is not a pass "
                f"(outcome={bundle.get('outcome')!r}, passed={bundle.get('passed')!r}) — "
                f"evidence of failure cannot back Succeeded")
    return None


def _strict_evidence_failure(entry: object, paths: LoopPaths,
                             bound: Mapping[str, tuple[str, ...]] | None) -> str | None:
    """The ONE definition of the verified-evidence bar (plan decision 14).

    Returns ``None`` when the cited entry can back ``Succeeded``, otherwise a detail
    string naming which of the four sub-checks failed:

    1. self-consistency — the entry is a readable evidence@1 record whose ``uri``
       resolves inside the workspace and hashes to the digest it declares;
    2. verdict — the artifact it points at is a verify bundle that says PASS.  An
       authentic record of a FAILING verification is still not proof of success;
    3. chain-boundness — some event bound this record's path AT its current bytes,
       and at exactly ONE digest.  A path bound at two or more different digests is
       ambiguous, and ambiguous is not proof.  ``bound is None`` means there is no
       event store at all, and the sub-check is skipped: the store-less writer-API
       path is a DOCUMENTED degradation, not a pass;
    4. goalpost agreement — when the record names a task still in TASKS.json, its
       recorded ``policy_digest`` equals the live one.  A goalpost that cannot even be
       computed is a FAILURE, not a skip: unestablished is not agreement (R007).

    ``emit.terminate`` imports this function rather than restating it.  Two hand-written
    copies of a three-part security check drift, and a drift here is a silent false
    completion.
    """
    from .evidence import validate_evidence, verify_evidence  # local: loop.evidence imports this module
    from .verifier import verification_policy_digest

    if not isinstance(entry, str) or not entry.strip():
        return "is not a workspace-relative evidence record path"
    if not evidence_entry_is_record_shaped(entry):
        # The pure layers reject this shape outright, so accepting it here would let a
        # terminal through the writer that its own replay would refuse.
        return ("is not verified evidence: not a workspace-relative "
                ".loop/evidence/*.json record path")
    try:
        blob = (paths.workspace / entry).read_bytes()
    except (OSError, ValueError) as exc:
        return f"is not verified evidence: the record cannot be read ({exc})"
    try:
        record = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return f"is not verified evidence: the record is not UTF-8 JSON ({exc})"
    if not isinstance(record, dict):
        return "is not verified evidence: the record is not a JSON object"
    validation = validate_evidence(record, mode="basic")
    if not validation["ok"]:
        return f"is not verified evidence: {[issue['message'] for issue in validation['issues']]}"
    verified = verify_evidence(record, workspace_root=paths.workspace)
    if not verified["ok"]:
        return f"is not verified evidence: {[issue['message'] for issue in verified['issues']]}"

    verdict = _verdict_failure(record, paths)
    if verdict is not None:
        return verdict

    if bound is not None:
        committed = bound.get(entry)
        if not committed:
            return ("is not bound into the event chain — no event committed this record's "
                    "digest, so no dispatch produced it")
        if len(committed) > 1:
            # Append-only forgery: a later ordinary event re-binds a tampered path at its
            # new digest. Collapsing the bindings would let the writer accept a tree the
            # doctor walk still reports, so an ambiguous binding is refused outright.
            return (f"is bound at {len(committed)} different digests "
                    f"({', '.join(committed)}) — an ambiguous binding is not proof")
        current = hashlib.sha256(blob).hexdigest()
        if committed[0] != current:
            return (f"is bound at a different digest: the chain committed {committed[0]}, "
                    f"the record now hashes to {current}")

    produced_by = record.get("produced_by")
    task_id = produced_by.get("task_id") if isinstance(produced_by, dict) else None
    if not isinstance(task_id, str):
        return None
    declared = _read_json(paths.tasks, [])   # already reported by the contract read
    entries = declared.get("tasks") if isinstance(declared, dict) else None
    live = next((task for task in (entries if isinstance(entries, list) else [])
                 if isinstance(task, dict) and task.get("id") == task_id), None)
    if live is None:
        # A renamed or removed task is a replan, not a forgery (decision 5).
        return None
    verified_by = record.get("verified_by")
    recorded = verified_by.get("policy_digest") if isinstance(verified_by, dict) else None
    try:
        current_goalpost = verification_policy_digest(live)
    except ChainHashError as exc:
        return (f"records a goalpost that cannot be compared against the live TASKS.json "
                f"goalpost for task {task_id!r}: that entry is not canonicalizable ({exc}), "
                f"so agreement is unestablished — and unestablished is not agreement")
    if recorded != current_goalpost:
        return (f"records a goalpost that is not the live TASKS.json goalpost for task "
                f"{task_id!r}: recorded {recorded!r}, live {current_goalpost!r}")
    return None


def _check_verified_evidence_terminal(terminal: Any, paths: LoopPaths, issues: list[dict]) -> None:
    """Read-time twin of emit.terminate's strict bar — one predicate, two callers."""
    if not isinstance(terminal, dict) or terminal.get("state") != "Succeeded":
        return
    try:
        if not policy_requires_verified_evidence(terminal.get("completion_policy")):
            return
    except CompletionPolicyError:
        return   # already reported by _validate_terminal / the terminal@1 schema
    from .runtime import RuntimeStoreError, bound_artifact_digests  # local: runtime imports this module

    try:
        bound = bound_artifact_digests(paths.workspace)
    except RuntimeStoreError as exc:
        issues.append(ContractIssue(
            "unverified_evidence_terminal",
            f"the terminal declares {VERIFIED_EVIDENCE_MODE} but the event store could not "
            f"be read ({exc}) — chain-boundness is unestablished, and unestablished is not "
            f"proof", paths.terminal))
        return
    evidence = terminal.get("evidence")
    for entry in evidence if isinstance(evidence, list) else []:
        detail = _strict_evidence_failure(entry, paths, bound)
        if detail is not None:
            issues.append(ContractIssue(
                "unverified_evidence_terminal",
                f"the terminal declares {VERIFIED_EVIDENCE_MODE} but {entry!r} {detail}",
                paths.terminal))


def _validate_optional_records(paths: LoopPaths, mode: str, issues: list[dict]) -> set[str]:
    """Validate record files that are present; return the set of record schema
    keys actually checked (``repair``/``rollout``/``receipt``/``evidence``) so ``doctor`` can
    report them under ``schemas_checked`` instead of under-counting its coverage."""
    checked: set[str] = set()
    repair_dir = paths.loop_dir / "repair"
    if repair_dir.is_dir():
        for record_path in sorted(repair_dir.glob("*.json")):
            data = _read_json(record_path, issues)
            if data is not None:
                _validate_record(data, "repair", record_path, mode, issues)
                checked.add("repair")
    for name in ROLLOUT_LEDGER_NAMES:
        ledger_path = paths.loop_dir / name
        if ledger_path.is_file():
            _validate_jsonl(ledger_path, "rollout", mode, issues)
            checked.add("rollout")
    receipts_dir = paths.loop_dir / "receipts"
    if receipts_dir.is_dir():
        for receipt_path in sorted(receipts_dir.glob("*.jsonl")):
            _validate_jsonl(receipt_path, "receipt", mode, issues)
            checked.add("receipt")
    if _validate_evidence_records(paths, mode, issues):
        checked.add("evidence")
    return checked


def _derive_lifecycle(state: Any, terminal: Any, terminal_exists: bool) -> str:
    """Report which lifecycle band a loop is in — additive reporting only, never
    an issue source. Total and pure: never raises.

    Per the ratified rule:
      1. state parsed with a non-null terminal_state, OR terminal_state.json
         present  → ``terminated:<X>`` where X is the terminal file's ``state``
         (dict + string) if available, else state.json's ``terminal_state`` if a
         string, else ``unknown``.
      2. state parsed and iteration_id is 0 / "0"  → ``planned``.
      3. state parsed  → ``running``.
      4. else  → ``unknown``.
    """
    state_is_dict = isinstance(state, dict)
    terminal_state_val = state.get("terminal_state") if state_is_dict else None
    if (state_is_dict and terminal_state_val is not None) or terminal_exists:
        if isinstance(terminal, dict) and isinstance(terminal.get("state"), str):
            resolved = terminal["state"]
        elif isinstance(terminal_state_val, str):
            resolved = terminal_state_val
        else:
            resolved = "unknown"
        return f"terminated:{resolved}"
    if state_is_dict:
        iteration_id = state.get("iteration_id")
        if iteration_id == 0 or iteration_id == "0":
            return "planned"
        return "running"
    return "unknown"


def validate_contract(target: str | Path, *, mode: str | None = None) -> dict[str, Any]:
    requested_mode, resolved_mode = _resolve_requested_mode(mode)
    paths = resolve_loop_paths(target)
    issues: list[dict] = []
    manifest = read_manifest(paths.manifest)
    state = _read_json(paths.state, issues)
    tasks = _read_json(paths.tasks, issues)
    if not paths.terminal.exists() and isinstance(state, dict) and state.get("terminal_state") is None:
        # In-flight loop: terminal_state.json is written once, at loop end. Its
        # absence is valid while state.json still declares terminal_state: null.
        terminal = None
    else:
        terminal = _read_json(paths.terminal, issues)

    mode = resolved_mode
    if mode == "jsonschema":
        if manifest is None:
            issues.append(ContractIssue("missing_file", "missing manifest.yaml", paths.manifest))
        else:
            _jsonschema_validate(manifest, "manifest", paths.manifest, issues)
        for data, name, path in (
            (state, "state", paths.state),
            (tasks, "tasks", paths.tasks),
            (terminal, "terminal", paths.terminal),
        ):
            if data is not None:
                _jsonschema_validate(data, name, path, issues)
        # Cross-field rules JSON Schema cannot express, run in both modes.
        _check_state_vocabulary(state, manifest, paths.state, issues)
        _check_tasks_semantics(tasks, paths.tasks, issues)
        _check_terminal_contradiction(terminal, paths.terminal, issues)
    else:
        _validate_manifest(manifest, paths.manifest, issues)
        _validate_state(state, paths.state, issues)
        _check_state_vocabulary(state, manifest, paths.state, issues)
        _validate_tasks(tasks, paths.tasks, issues)
        _validate_terminal(terminal, paths.terminal, issues)

    if not paths.runlog.exists():
        issues.append(ContractIssue("missing_file", "missing RUNLOG.md", paths.runlog))
    _check_stub_verify_scripts(paths, issues)
    _check_verify_surface(paths, tasks, issues)
    records_checked = _validate_optional_records(paths, mode, issues)
    if terminal is not None:
        _check_verified_evidence_terminal(terminal, paths, issues)

    schemas_checked = list(SCHEMA_IDS) + [
        schema_id for key, schema_id in _RECORD_SCHEMA_IDS if key in records_checked
    ]

    lifecycle = _derive_lifecycle(state, terminal, paths.terminal.exists())

    return {
        "ok": not issues,
        "paths": paths.to_json(),
        "validation_mode": mode,
        "requested_mode": requested_mode,
        "schemas_checked": schemas_checked,
        "lifecycle": lifecycle,
        "issues": issues,
    }


def doctor_report(target: str | Path, *, mode: str | None = None,
                  expect_chain_head: str | None = None,
                  expect_chain_ancestor: str | None = None) -> dict[str, Any]:
    report = validate_contract(target, mode=mode)
    from .runtime import event_consistency_issues

    event_store, event_issues = event_consistency_issues(
        target, mode=mode, expect_chain_head=expect_chain_head,
        expect_chain_ancestor=expect_chain_ancestor)
    issues = report["issues"] + list(event_issues) if event_issues else report["issues"]
    return {**report, "event_store": event_store, "issues": issues,
            "ok": report["ok"] and not event_issues}
