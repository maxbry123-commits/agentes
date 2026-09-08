"""One event-sourced, crash-resumable execute-task dispatch step."""

from __future__ import annotations

import json
import shlex
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import emit
from .completion import DEFAULT_COMPLETION_MODE, VERIFIED_EVIDENCE_MODE
from .contract import _strict_evidence_failure
from .events import (EventRowDecodeError, EventStoreOperationalError, SQLiteEventStore,
                    read_event_rows, validate_event)
from .paths import EVIDENCE_DIR_NAME, resolve_loop_paths
from .reducer import ChainBreakError, reduce_events
from .runtime import RuntimeStoreError, _read_store, bound_artifact_digests
from .verifier import executed_verifier_identity, injected_verifier_identity


class RunnerError(RuntimeError):
    """A dispatch request could not be attempted."""


class NotReadyError(RunnerError):
    """The event projection has not reached execute-task."""


class VerifierNotImplementedError(RunnerError):
    """A selected task has no declared verification command."""


class VerifierExecutionError(RunnerError):
    """The declared verifier command could not be launched."""


class RunModeNotImplementedError(RunnerError):
    """A requested run mode is not implemented."""


@dataclass(frozen=True)
class VerifyOutcome:
    passed: bool
    summary: str = ""


Verifier = Callable[[dict[str, Any], Path], VerifyOutcome]

_VERIFY_TIMEOUT_SECONDS = 300


def done_task_ids(tasks: list[dict], projection: dict) -> set[str]:
    """Return declaratively done tasks plus durable successful dispatches."""
    done = {task["id"] for task in tasks if task.get("status") == "done"}
    done.update(
        entry["task_id"]
        for entry in projection.get("runlog_entries", [])
        if entry.get("outcome") == "task_passed" and isinstance(entry.get("task_id"), str)
    )
    return done


def select_next_task(tasks: list[dict], projection: dict) -> dict | None:
    """Select the first pending task whose declared dependencies are done."""
    done = done_task_ids(tasks, projection)
    for task in tasks:
        if task.get("status") != "pending" or task.get("id") in done:
            continue
        if all(dependency in done for dependency in task.get("depends_on", [])):
            return task
    return None


def _default_verifier(task: dict[str, Any], workspace: Path) -> VerifyOutcome:
    return _subprocess_verifier(task, workspace)


def _subprocess_verifier(task: dict[str, Any], workspace: Path) -> VerifyOutcome:
    """Run the task's declared verifier in a separate, bounded process."""
    cmd = task.get("verify")
    if not isinstance(cmd, str) or not cmd.strip():
        raise VerifierNotImplementedError(
            f"no verify command declared for task {task.get('id')!r}; "
            "add a non-empty TASKS.json `verify` field"
        )
    try:
        argv = shlex.split(cmd, posix=True)
    except ValueError as exc:
        raise VerifierExecutionError(f"cannot parse verify command {cmd!r}: {exc}") from exc
    try:
        proc = subprocess.run(
            argv, cwd=str(workspace), shell=False, timeout=_VERIFY_TIMEOUT_SECONDS,
            capture_output=True, text=True, errors="replace",
        )
    except subprocess.TimeoutExpired:
        return VerifyOutcome(False, summary=f"verify command timed out after {_VERIFY_TIMEOUT_SECONDS}s")
    except OSError as exc:
        raise VerifierExecutionError(f"cannot execute verify command {cmd!r}: {exc}") from exc
    return VerifyOutcome(proc.returncode == 0, summary=(proc.stdout + proc.stderr)[-2000:])


def _store_append(store: SQLiteEventStore, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Keep an unusable store (schema drift, lock) inside the typed runtime family."""
    try:
        return store.append(*args, **kwargs)
    except EventStoreOperationalError as exc:
        raise RuntimeStoreError("event_store_unusable", str(exc)) from exc


def _load_tasks(paths: Any) -> list[dict]:
    try:
        raw = json.loads(paths.tasks.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError(f"cannot read TASKS.json: {exc}") from exc
    tasks = raw.get("tasks") if isinstance(raw, dict) else None
    if not isinstance(tasks, list) or not all(isinstance(task, dict) for task in tasks):
        raise RunnerError("TASKS.json must contain a tasks array of objects")
    return tasks


def _projection(target: str | Path, mode: str | None) -> tuple[str, dict[str, Any]]:
    """Read through the shared read path so a dispatch attempt writes nothing and never
    mistakes a lost race with a live appender for a corrupt store (design change D4)."""
    path = resolve_loop_paths(target).loop_dir / "events.db"
    if not path.exists():
        raise RuntimeStoreError("missing_store", f"event store does not exist: {path}")

    def read_stream(conn: sqlite3.Connection) -> tuple[str, list[dict[str, Any]]]:
        run_ids = conn.execute("SELECT DISTINCT run_id FROM events ORDER BY run_id ASC").fetchall()
        if not run_ids:
            raise RuntimeStoreError("empty_store", f"event store is empty: {path}")
        if len(run_ids) != 1:
            raise RuntimeStoreError("ambiguous_run_id", f"event store has ambiguous run_id values: {path}")
        run_id = run_ids[0][0]
        return run_id, read_event_rows(conn, run_id)

    try:
        run_id, events = _read_store(path, read_stream)
    except EventRowDecodeError as exc:
        raise RuntimeStoreError("corrupt_store", f"cannot read event store: {exc}") from exc
    for event in events:
        report = validate_event(event, mode=mode)
        if not report["ok"]:
            raise RuntimeStoreError("invalid_event", f"event store contains invalid event: {report['issues']}")
    try:
        return run_id, reduce_events(events)
    except ChainBreakError as exc:
        raise RuntimeStoreError("event_chain_broken", str(exc)) from exc
    except ValueError as exc:
        raise RuntimeStoreError("invalid_event_stream", str(exc)) from exc


def _reconcile_legacy_iteration(target: str | Path, projection: dict[str, Any]) -> None:
    """Materialize every event-log iteration not yet reflected in state.json."""
    paths = resolve_loop_paths(target)
    try:
        state = json.loads(paths.state.read_text(encoding="utf-8"))
        current_id = state.get("iteration_id") if isinstance(state, dict) else None
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError(f"cannot read state.json: {exc}") from exc
    if not isinstance(current_id, int):
        raise RunnerError("state.json iteration_id must be an integer")
    for entry in projection["runlog_entries"]:
        iteration_id = entry.get("iteration_id")
        if isinstance(iteration_id, int) and iteration_id > current_id:
            emit.append_iteration(
                target,
                iteration_id=iteration_id,
                outcome=entry["outcome"],
                state=entry.get("state"),
                task_id=entry.get("task_id", ""),
                notes=entry.get("summary", ""),
            )
            current_id = iteration_id


def _evidence_records_by_task(paths: Any, projection: dict[str, Any]) -> dict[str, list[str]]:
    """Map each task id to the evidence records this run's passing iterations left on disk."""
    records: dict[str, list[str]] = {}
    for entry in projection.get("runlog_entries", []):
        if entry.get("outcome") != "task_passed":
            continue
        task_id, iteration_id = entry.get("task_id"), entry.get("iteration_id")
        if not isinstance(task_id, str) or not isinstance(iteration_id, int):
            continue
        record = paths.loop_dir / EVIDENCE_DIR_NAME / f"evidence-iter{iteration_id}.json"
        if record.is_file():
            records.setdefault(task_id, []).append(record.relative_to(paths.workspace).as_posix())
    return records


def _unmet_strict_bar(paths: Any, cited: list[str]) -> str | None:
    """Why the cited records cannot back the strict mode, or ``None`` when they can.

    The SAME predicate ``emit.terminate`` enforces, evaluated against the very records
    the payload would cite.  Existence is not satisfaction: adopting the strict mode
    because a file is present would overstate the bar (decision 7) and would re-open the
    committed-then-refused seam this slice closes (decision 2), because the writer runs
    the predicate afterwards and raises once the event is already durable.
    """
    try:
        bound = bound_artifact_digests(paths.workspace)
    except RuntimeStoreError as exc:
        return (f"the event store could not be read ({exc}), so chain-boundness is "
                f"unestablished — and unestablished is not proof")
    for entry in cited:
        detail = _strict_evidence_failure(entry, paths, bound)
        if detail is not None:
            return f"{entry} {detail}"
    return None


def _auto_terminal_payload(paths: Any, tasks: list[dict], projection: dict[str, Any]) -> dict[str, Any]:
    """Adopt the verified-evidence mode only when this run can honestly satisfy it.

    Choosing the weaker policy silently would be a self-serving downgrade, so the
    all_required branch always says WHY — distinguishing a task that produced no record
    at all from a record that is present but fails the bar.
    """
    payload: dict[str, Any] = {
        "state": "Succeeded", "criteria_met": {task["id"]: True for task in tasks},
        "evidence": ["RUNLOG.md"], "false_completion": False,
        "completion_policy": {"mode": DEFAULT_COMPLETION_MODE},
        "iteration_id": projection["iteration_id"],
    }
    records = _evidence_records_by_task(paths, projection)
    missing = sorted(str(task.get("id")) for task in tasks if task.get("id") not in records)
    if missing:
        payload["reason"] = "tasks with no evidence record: " + ", ".join(missing)
        return payload
    cited = sorted({record for task in tasks for record in records[task["id"]]})
    unmet = _unmet_strict_bar(paths, cited)
    if unmet is not None:
        payload["reason"] = "evidence records do not meet the verified-evidence bar: " + unmet
        return payload
    payload["evidence"] = cited
    payload["completion_policy"] = {"mode": VERIFIED_EVIDENCE_MODE}
    return payload


def _reconcile_legacy_terminal(target: str | Path, projection: dict[str, Any]) -> None:
    """Replay the terminal's already-recorded payload into existing emit APIs."""
    terminal = projection.get("terminal")
    if terminal is None:
        return
    paths = resolve_loop_paths(target)
    if not paths.terminal.exists():
        reason = terminal.get("reason")
        emit.terminate(
            target,
            state=terminal["state"],
            criteria_met=terminal["criteria_met"],
            evidence=terminal["evidence"],
            reason=reason if isinstance(reason, str) else "",
            false_completion=terminal["false_completion"],
            iteration_id=terminal.get("iteration_id"),
            completion_policy=terminal.get("completion_policy"),
        )
    try:
        state = json.loads(paths.state.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError(f"cannot read state.json: {exc}") from exc
    if not isinstance(state, dict) or state.get("state") != "terminal" or state.get("terminal_state") != terminal["state"]:
        emit.sync_state_to_terminal(target)


def dispatch_once(
    target: str | Path, *, verifier: Verifier | None = None, mode: str | None = None,
    executor: str | None = None, verifier_identity: str | None = None,
) -> dict[str, Any]:
    """Run at most one durable selection/verification/recording dispatch."""
    run_id, projection = _projection(target, mode)
    # Safe only because each dispatch_once invocation appends at most one event.
    if projection.get("terminal") is not None:
        _reconcile_legacy_terminal(target, projection)
        return {"ok": True, "action": "noop_terminal", "run_id": run_id}
    if projection.get("state") != "execute-task":
        raise NotReadyError(f"dispatch requires state 'execute-task', got {projection.get('state')!r}")

    _reconcile_legacy_iteration(target, projection)
    paths = resolve_loop_paths(target)
    tasks = _load_tasks(paths)
    task = select_next_task(tasks, projection)
    if task is None:
        done = done_task_ids(tasks, projection)
        if all(task.get("id") in done for task in tasks):
            iteration_id = projection["iteration_id"]
            payload = _auto_terminal_payload(paths, tasks, projection)
            store = SQLiteEventStore(paths.loop_dir / "events.db")
            _store_append(store, run_id, "terminal_written", payload, actor="loop.run",
                          expected_sequence=projection["last_sequence"] + 1)
            _reconcile_legacy_terminal(target, {**projection, "terminal": payload})
            return {"ok": True, "action": "terminal_written", "iteration_id": iteration_id, "run_id": run_id}
        return {"ok": False, "action": "blocked", "run_id": run_id}

    # Identity of what is ABOUT TO RUN. Built here, not in the writer: only this
    # frame knows whether the declared command or an injected callable will execute,
    # and hashing before execution keeps a self-modifying verify script honest.
    code_identity = (
        injected_verifier_identity() if verifier is not None
        else executed_verifier_identity(task.get("verify"), paths.workspace)
    )
    attempt = 1 + sum(
        1 for entry in projection["runlog_entries"] if entry.get("task_id") == task["id"]
    )
    outcome = (verifier or _default_verifier)(task, paths.workspace)
    if not isinstance(outcome, VerifyOutcome):
        raise RunnerError("verifier must return VerifyOutcome")
    iteration_id = projection["iteration_id"] + 1
    payload = {
        "iteration_id": iteration_id,
        "outcome": "task_passed" if outcome.passed else "task_failed",
        "task_id": task["id"],
        "summary": outcome.summary,
    }
    # Rendered BEFORE the append and written AFTER it. Building first is what lets
    # the event carry the digests of the very bytes that will land; the builder
    # writes nothing, so a SIGKILL at the pre-commit COMMIT still leaves the tree
    # byte-identical (test_crash_injection_before_iteration_event_commit_...).
    try:
        built = emit.build_verify_evidence(
            target, run_id=run_id, iteration_id=iteration_id, task=task,
            passed=outcome.passed, summary=outcome.summary, code_identity=code_identity,
            executor=executor, verifier_identity=verifier_identity, attempt=attempt,
        )
    except emit.EmitError as exc:
        raise RunnerError(
            f"cannot build the verify evidence for iteration {iteration_id}: {exc}"
        ) from exc
    store = SQLiteEventStore(paths.loop_dir / "events.db")
    _store_append(store, run_id, "iteration_appended", payload, actor="loop.run",
                  artifact_hashes=list(built.artifact_hashes),
                  expected_sequence=projection["last_sequence"] + 1)
    try:
        written = emit.write_verify_evidence(
            target, run_id=run_id, iteration_id=iteration_id, task=task,
            passed=outcome.passed, summary=outcome.summary, code_identity=code_identity,
            executor=executor, verifier_identity=verifier_identity, attempt=attempt,
            built=built,
        )
    except (OSError, emit.EmitError) as exc:
        raise RunnerError(
            f"iteration {iteration_id} is committed to the event log but its verify "
            f"bundle could not be written: {exc}"
        ) from exc
    emit.append_iteration(target, iteration_id=iteration_id, outcome=payload["outcome"],
                          task_id=payload["task_id"], notes=payload["summary"])
    return {"ok": True, "action": "dispatched", "task_id": task["id"],
            "outcome": payload["outcome"], "iteration_id": iteration_id, "run_id": run_id,
            "evidence": str(written["evidence"]), "object": str(written["object"])}
