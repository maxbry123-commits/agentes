"""Read-only runtime reports over the append-only event store."""

from __future__ import annotations

import json
import shutil
import sqlite3
from contextlib import ExitStack, closing, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Iterator, TypeVar

from .chain import head_sequence
from .completion import CompletionPolicyError, criteria_satisfy_completion
from .contract import ContractIssue
from .events import (
    EVENT_SCHEMA_ID,
    EVENT_TYPES,
    EventRowDecodeError,
    has_chain_columns,
    read_event_rows,
    store_user_version,
    validate_event,
)
from .paths import resolve_loop_paths
from .reducer import ChainBreakError, EventReplayError, reduce_events

_T = TypeVar("_T")


class RuntimeStoreError(RuntimeError):
    """The runtime store cannot be read well enough to construct a report."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _store_path(target: str | Path) -> Path:
    return resolve_loop_paths(target).loop_dir / "events.db"


def _open_read_only(path: Path, *, immutable: bool) -> sqlite3.Connection:
    """Open mode=ro, preferring immutable=1 when requested.

    immutable=1 assumes the file cannot change, so a live append can surface as
    SQLITE_CORRUPT; a failed immutable open falls back to plain mode=ro before the
    caller may conclude corruption: real corruption fails both."""
    uri = path.absolute().as_uri()
    if immutable:
        try:
            return sqlite3.connect(f"{uri}?mode=ro&immutable=1", uri=True)
        except sqlite3.DatabaseError:
            pass
    return sqlite3.connect(f"{uri}?mode=ro", uri=True)


def _copy_wal_store(path: Path, directory: Path) -> Path | None:
    """Copy the store then its WAL into `directory`; None when a checkpoint removed the WAL.

    Order is load-bearing: the copied WAL must be at least as new as the database it
    replays over. The -shm is deliberately never copied — it is a rebuildable index of
    the WAL, and a crash-left one may be stale garbage.
    """
    copy = directory / path.name
    shutil.copyfile(path, copy)
    try:
        shutil.copyfile(path.with_name(path.name + "-wal"), copy.with_name(copy.name + "-wal"))
    except FileNotFoundError:
        return None
    return copy


@contextmanager
def _read_only_connect(path: Path, *, immutable: bool = True) -> Iterator[sqlite3.Connection]:
    """Read-only connection that leaves the store's own directory byte-identical.

    A crash-left WAL is read through a temp-directory copy of the database and its WAL,
    because every in-place open makes SQLite create the -shm there to map the WAL.
    Reading the original with immutable=1 instead would silently skip the WAL frames,
    and checkpointing on open is a write. A torn WAL tail in the copy is safe: WAL frame
    checksums truncate it. If the WAL vanished mid-copy the writer checkpointed it, so
    the original is now a complete no-WAL store and is read directly.
    """
    with ExitStack() as stack:
        source = None
        if path.with_name(path.name + "-wal").exists():
            source = _copy_wal_store(path, Path(stack.enter_context(TemporaryDirectory())))
        if source is None:
            conn = _open_read_only(path, immutable=immutable)
        else:
            conn = _open_read_only(source, immutable=False)
        yield stack.enter_context(closing(conn))


def _read_store(path: Path, read: Callable[[sqlite3.Connection], _T]) -> _T:
    """Run one read; a lost immutable=1 race retries plainly before counting as corruption."""
    try:
        with _read_only_connect(path) as conn:
            return read(conn)
    except (OSError, sqlite3.DatabaseError):
        pass
    try:
        with _read_only_connect(path, immutable=False) as conn:
            return read(conn)
    except (OSError, sqlite3.DatabaseError) as exc:
        raise RuntimeStoreError("corrupt_store", f"cannot read event store: {exc}") from exc


def _read_events_readonly(path: Path, run_id: str) -> list[dict[str, Any]]:
    """Read the EventStore row shape without invoking its write-capable connector."""
    try:
        return _read_store(path, lambda conn: read_event_rows(conn, run_id))
    except EventRowDecodeError as exc:
        raise RuntimeStoreError("corrupt_store", f"cannot read event store: {exc}") from exc


def _discover_run_id(path: Path) -> str:
    if not path.exists():
        raise RuntimeStoreError("missing_store", f"event store does not exist: {path}")
    rows = _read_store(
        path, lambda conn: conn.execute("SELECT DISTINCT run_id FROM events ORDER BY run_id ASC").fetchall())
    if not rows:
        raise RuntimeStoreError("empty_store", f"event store is empty: {path}")
    if len(rows) != 1:
        raise RuntimeStoreError("ambiguous_run_id", f"event store has ambiguous run_id values: {path}")
    run_id = rows[0][0]
    if not isinstance(run_id, str):
        raise RuntimeStoreError("corrupt_store", f"event store has invalid run_id: {path}")
    return run_id


def _events(target: str | Path, mode: str | None) -> tuple[Path, str, list[dict[str, Any]], dict[str, Any]]:
    path = _store_path(target)
    run_id = _discover_run_id(path)
    events = _read_events_readonly(path, run_id)
    validation: dict[str, Any] | None = None
    for event in events:
        validation = validate_event(event, mode=mode)
        if not validation["ok"]:
            raise RuntimeStoreError("invalid_event",
                                    f"event store contains invalid event: {validation['issues']}")
    if validation is None:
        raise RuntimeStoreError("empty_store", f"event store is empty: {path}")
    return path, run_id, events, validation


def _state_divergence(paths: Any, projection: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        state = json.loads(paths.state.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = None
    if not isinstance(state, dict):
        return [ContractIssue("state_field_mismatch", "state.json is missing or is not an object")]
    expected = {
        "state": projection["state"],
        "iteration_id": projection["iteration_id"],
        "active_task": projection["active_task"],
        "terminal_state": projection["terminal"].get("state") if projection["terminal"] else None,
        "paused": projection["paused"],
        "pause_reason": projection["pause_reason"],
        "pending_approval": projection["pending_approval"],
    }
    issues: list[dict[str, Any]] = []
    for field, value in expected.items():
        if state.get(field, False if field == "paused" else None) != value:
            issues.append(ContractIssue("state_field_mismatch", f"state.json {field!r} differs from event projection"))
    return issues


def _completion_satisfied(terminal: dict[str, Any] | None) -> bool | None:
    if terminal is None:
        return None
    if terminal.get("state") != "Succeeded":
        return False
    try:
        return criteria_satisfy_completion(terminal.get("criteria_met", {}), terminal.get("completion_policy"))
    except CompletionPolicyError:
        return False


def status_report(target: str | Path, *, mode: str | None = None) -> dict[str, Any]:
    """Project a single event stream and reconcile it with live state.json."""
    _, run_id, events, validation = _events(target, mode)
    paths = resolve_loop_paths(target)
    degraded = {"state": None, "iteration_id": None, "active_task": None, "terminal": None,
                "chain_head": None, "unchained_prefix": 0}
    try:
        projection = reduce_events(events)
        divergence = _state_divergence(paths, projection)
    except ChainBreakError as exc:
        projection = degraded
        divergence = [ContractIssue("event_chain_broken", str(exc))]
    except EventReplayError as exc:
        projection = degraded
        divergence = [ContractIssue("illegal_event_sequence", str(exc))]
    return {
        "ok": not divergence,
        "validation_mode": validation["validation_mode"], "requested_mode": validation["requested_mode"],
        "schemas_checked": [EVENT_SCHEMA_ID], "run_id": run_id, "event_count": len(events),
        "state": projection["state"], "iteration_id": projection["iteration_id"],
        "active_task": projection["active_task"], "terminal": projection["terminal"],
        "completion_satisfied": _completion_satisfied(projection["terminal"]),
        "chain_head": projection.get("chain_head"),
        "unchained_prefix": projection.get("unchained_prefix", 0),
        "state_json_agrees": not divergence, "divergence": divergence,
    }


def _terminal_desync(paths: Any, projection: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    event_terminal = projection["terminal"]
    try:
        disk_terminal = json.loads(paths.terminal.read_text(encoding="utf-8")) if paths.terminal.exists() else None
    except (OSError, json.JSONDecodeError):
        disk_terminal = None
    if event_terminal is None and disk_terminal is None:
        return None, []
    if event_terminal is None or disk_terminal is None:
        return {"event": event_terminal, "file": disk_terminal}, [
            ContractIssue("desynced_terminal_window", "terminal event and terminal_state.json disagree on presence")
        ]
    if not isinstance(disk_terminal, dict) or disk_terminal.get("state") != event_terminal.get("state"):
        return {"event": event_terminal, "file": disk_terminal}, [
            ContractIssue("desynced_terminal_window", "terminal_state.json differs from event projection")
        ]
    for field in ("criteria_met", "evidence", "false_completion", "completion_policy"):
        if field in disk_terminal and disk_terminal.get(field) != event_terminal.get(field):
            return {"event": event_terminal, "file": disk_terminal}, [
                ContractIssue("terminal_state_mismatch", f"terminal_state.json {field!r} differs from event projection")
            ]
    return None, []


def replay_report(target: str | Path, *, mode: str | None = None) -> dict[str, Any]:
    """Double-fold an event stream and check terminal-window synchronization."""
    _, run_id, events, validation = _events(target, mode)
    paths = resolve_loop_paths(target)
    findings: list[dict[str, Any]] = []
    deterministic = True
    legal_sequence = True
    projection: dict[str, Any] | None = None
    try:
        first = reduce_events(events)
        second = reduce_events(events)
        deterministic = first == second
        projection = first
        if not deterministic:
            findings.append(ContractIssue("nondeterministic_replay", "two event folds produced different projections"))
    except ChainBreakError as exc:
        legal_sequence = False
        findings.append(ContractIssue("event_chain_broken", str(exc)))
    except EventReplayError as exc:
        legal_sequence = False
        findings.append(ContractIssue("illegal_event_sequence", str(exc)))
    terminal_desync = None
    if projection is not None:
        terminal_desync, terminal_findings = _terminal_desync(paths, projection)
        findings.extend(terminal_findings)
    return {
        "ok": not findings,
        "validation_mode": validation["validation_mode"], "requested_mode": validation["requested_mode"],
        "schemas_checked": [EVENT_SCHEMA_ID], "run_id": run_id, "event_count": len(events),
        "deterministic": deterministic, "legal_sequence": legal_sequence,
        "chain_head": (projection or {}).get("chain_head"),
        "unchained_prefix": (projection or {}).get("unchained_prefix", 0),
        "terminal_desync": terminal_desync, "findings": findings,
    }


def _store_declares_chain_without_columns(path: Path) -> bool:
    """True when the store still declares generation 2 but its chain columns are gone.

    PRAGMA-only probe, routed through _read_store so a lost immutable=1 race
    retries plainly instead of being mistaken for corruption (the D4 hole).
    """
    return _read_store(path, lambda conn: store_user_version(conn) >= 2 and not has_chain_columns(conn))


def _anchor_mismatch(message: str) -> dict[str, Any]:
    return ContractIssue("chain_anchor_mismatch", message)


def _not_ancestor(message: str) -> dict[str, Any]:
    """Deliberately NOT a reuse of chain_anchor_mismatch (D3).

    "your current head is not what I expected" and "the head you anchored is not in
    my history at all" are different facts, and doctor issue codes are the population
    verdict.doctor.issue_codes is drawn from — a permanent, public log. One shared
    code would collapse them there forever.
    """
    return ContractIssue("chain_anchor_not_ancestor", message)


def _ancestry(target: str | Path, mode: str | None, expect_chain_ancestor: str) -> int | None:
    """Sequence at which the anchored head was the head, by replay.

    A fourth read-only fold of the store, in the same tradition as
    _bound_evidence_issues (repo-os-contract.md #22).
    """
    _, _run_id, events, _validation = _events(target, mode)
    return head_sequence(events, expect_chain_ancestor)


def event_consistency_issues(
    target: str | Path, *, mode: str | None = None, expect_chain_head: str | None = None,
    expect_chain_ancestor: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return event-store health and the existing status/replay findings."""
    path = _store_path(target)
    if not path.exists():
        absent_issues: list[dict[str, Any]] = []
        residue = [suffix for suffix in ("-wal", "-shm")
                   if path.with_name(path.name + suffix).exists()]
        if residue:
            absent_issues.append(ContractIssue(
                "missing_event_store",
                "events.db is absent but SQLite sidecar files remain — the store was deleted"))
        if expect_chain_head is not None:
            absent_issues.append(_anchor_mismatch(
                "an anchored chain head was supplied but no event store is present"))
        if expect_chain_ancestor is not None:
            # D5: an absent store with an ancestor supplied FAILS. It never skips —
            # otherwise deleting the store is a gate bypass.
            absent_issues.append(_not_ancestor(
                "an anchored chain ancestor was supplied but no event store is present"))
        if absent_issues:
            return {"present": False, "sidecar_residue": bool(residue)}, absent_issues
        return {"present": False}, []
    try:
        status = status_report(target, mode=mode)
        replay = replay_report(target, mode=mode)
        declares_chain_without_columns = _store_declares_chain_without_columns(path)
        # Inside the guard with its two siblings: this is a THIRD independent read, and a
        # store that becomes unreadable between reads must surface as a typed finding
        # rather than an untyped traceback out of doctor_report (R007).
        bound_issues = _bound_evidence_issues(target, mode)
        # Inside the same guard, for the same R007 reason: the ancestry replay is a
        # FOURTH independent read, and a store that becomes unreadable between reads
        # must surface as a typed finding rather than a traceback out of doctor_report.
        ancestor_sequence = (_ancestry(target, mode, expect_chain_ancestor)
                             if expect_chain_ancestor is not None else None)
    except RuntimeStoreError as exc:
        unreadable_issues = [ContractIssue(exc.code, str(exc))]
        if expect_chain_head is not None:
            unreadable_issues.append(_anchor_mismatch(
                "an anchored chain head was supplied but the event store cannot be read"))
        if expect_chain_ancestor is not None:
            unreadable_issues.append(_not_ancestor(
                "an anchored chain ancestor was supplied but the event store cannot be read"))
        return {"present": True, "readable": False, "error_code": exc.code}, unreadable_issues
    issues = list(status["divergence"]) + list(replay["findings"])
    issues.extend(bound_issues)
    if declares_chain_without_columns:
        issues.append(ContractIssue(
            "chain_columns_missing",
            "store declares user_version >= 2 but the chain columns are absent — "
            "the chain was dropped (this check only catches the lazy downgrade; "
            "an anchored head is the real control)"))
    if expect_chain_head is not None:
        actual = (status["chain_head"] or {}).get("event_hash")
        if actual != expect_chain_head:
            issues.append(_anchor_mismatch(
                f"chain head {actual!r} does not match expected {expect_chain_head!r}"))
    if expect_chain_ancestor is not None and ancestor_sequence is None:
        issues.append(_not_ancestor(
            f"anchored chain head {expect_chain_ancestor!r} was never the head of this "
            "chain at any sequence — established by replay, so a row bearing the "
            "anchored digest without a matching recomputed hash does not satisfy it"))
    report = {
        "present": True,
        "readable": True,
        "run_id": status["run_id"],
        "event_count": status["event_count"],
        "state_json_agrees": status["state_json_agrees"],
        "deterministic": replay["deterministic"],
        "legal_sequence": replay["legal_sequence"],
        "chain": {"head": status["chain_head"], "unchained_prefix": status["unchained_prefix"]},
    }
    if expect_chain_ancestor is not None:
        # Only when asked: with no ancestor supplied the report stays byte-identical
        # to the pre-4b shape (the #22 habit).
        report["anchor"] = {"expected": expect_chain_ancestor, "sequence": ancestor_sequence}
    return report, issues


def _bound_evidence_issues(target: str | Path, mode: str | None) -> list[dict[str, Any]]:
    """Re-hash every artifact an event bound into the chain.

    Driven by what each event DECLARES: a legacy event carries an empty
    artifact_hashes list and is silent by construction, because the append-only
    triggers make a retroactive binding impossible (repo-os-contract.md #22).

    A declared path is attacker-nameable — event@1 constrains it only to a non-empty
    string, and the chain covers a binding rather than vouching for it. Every path is
    therefore containment-checked BEFORE anything is opened and hashed under a cap
    (``loop.evidence.hash_bound_artifact``); an escaping path is reported as
    ``bound_evidence_escape``, never read.
    """
    from .evidence import hash_bound_artifact

    _, _run_id, events, _validation = _events(target, mode)
    workspace = resolve_loop_paths(target).workspace
    issues: list[dict[str, Any]] = []
    for event in events:
        for entry in event.get("artifact_hashes") or []:
            code, detail = hash_bound_artifact(workspace, entry["path"])
            if code == "escape":
                issues.append(ContractIssue(
                    "bound_evidence_escape",
                    f"event {event['event_id']} (sequence {event['sequence']}) bound "
                    f"{entry['path']!r}, which {detail} — a bound path that does not "
                    f"resolve inside the workspace is a finding, not something to read"))
                continue
            if code == "unreadable":
                issues.append(ContractIssue(
                    "missing_bound_evidence",
                    f"event {event['event_id']} (sequence {event['sequence']}) bound "
                    f"{entry['path']} into the chain but it {detail}"))
                continue
            actual = detail
            if actual != entry["sha256"]:
                issues.append(ContractIssue(
                    "evidence_chain_mismatch",
                    f"{entry['path']} does not match the digest bound at sequence "
                    f"{event['sequence']}: expected {entry['sha256']}, found {actual} — "
                    f"the original bytes may remain at "
                    f".loop/artifacts/objects/{entry['sha256'][:2]}/{entry['sha256']}"))
    return issues


def bound_artifact_digests(target: str | Path,
                           mode: str | None = None) -> dict[str, tuple[str, ...]] | None:
    """{workspace-relative POSIX path: every DISTINCT sha256 an event bound it at}.

    Conflict-aware by construction. A dict-comprehension keyed on path would collapse
    repeat bindings LAST-WINS, which is not a summary but a laundering channel: an
    append-only forge that re-binds a tampered path at its new digest would look bound
    to this write-time view while ``_bound_evidence_issues`` — which checks PER EVENT —
    still reports ``evidence_chain_mismatch`` on the same tree. Returning the full
    conflict set keeps the two views in agreement on every tree; the strict bar refuses
    a path carrying more than one digest, because ambiguous is not proof.

    Digests are in first-bound order and de-duplicated, so the ordinary case (the same
    path bound repeatedly at the same bytes) stays a one-element tuple.

    None means there is no event store, and the caller MUST degrade explicitly and say
    so (decision 14) rather than treat absence as satisfaction. An empty dict means a
    store exists and bound nothing. An unreadable store raises RuntimeStoreError — an
    errored check fails, it never skips (R007).
    """
    if not (resolve_loop_paths(target).loop_dir / "events.db").is_file():
        return None
    _, _run_id, events, _validation = _events(target, mode)
    digests: dict[str, list[str]] = {}
    for event in events:
        for entry in event.get("artifact_hashes") or []:
            seen = digests.setdefault(entry["path"], [])
            if entry["sha256"] not in seen:
                seen.append(entry["sha256"])
    return {path: tuple(seen) for path, seen in digests.items()}
