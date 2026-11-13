#!/usr/bin/env python3
"""
Daytona SNAPSHOT management / auditing utility.

A multi-dataset datagen sweep builds one per-environment Daytona snapshot per
task-environment hash (``harbor__<hash>__snapshot``). The org has a HARD cap of
60 snapshots. This tool gives visibility into how close we are to that cap and a
*safe* way to reclaim stale snapshots — it ONLY audits and DELETES (reclaims).
It never creates snapshots and never raises caps.

Snapshots are a DIFFERENT Daytona resource from sandboxes. They live under
``client.snapshot`` (a ``SnapshotService``):

    client.snapshot.list(page=N, limit=M) -> PaginatedSnapshots
        .items        list[Snapshot]
        .total        int  (total snapshot count in the org)
        .page         int
        .total_pages  int
    client.snapshot.get(name) -> Snapshot
    client.snapshot.delete(snapshot: Snapshot) -> None     # takes the OBJECT, not an id

Snapshot object fields (from the installed `daytona` SDK, pydantic model):
    id, name, organization_id, general, image_name
    state           SnapshotState enum: building | pending | pulling | active |
                    inactive | error | build_failed | removing
    size, cpu, gpu, mem, disk
    error_reason
    created_at      datetime  (always present)
    updated_at      datetime  (always present)
    last_used_at    Optional[datetime]   primary staleness signal; falls back to
                                          created_at when null (snapshot never used)
    build_info, region_ids, initial_runner_id, ref

Staleness
---------
A snapshot is STALE when it is idle (last activity older than --stale-days) AND
not in a protected state. Protected = BUILDING / PENDING / PULLING / REMOVING —
the transitional states where deleting mid-build/mid-removal is unsafe. 'active'
is NOT protected: for snapshots it is the normal resting state of a built,
available snapshot, so an idle active snapshot is the reclaim target. ERROR /
BUILD_FAILED snapshots become deletable only once also idle past --stale-days.

Usage
-----
    # Audit (default, READ-ONLY) against the datagen org
    python daytona_snapshot_manager.py --api-key-env DAYTONA_DATA_API_KEY

    # JSON output
    python daytona_snapshot_manager.py --api-key-env DAYTONA_DATA_API_KEY --json

    # Custom staleness threshold
    python daytona_snapshot_manager.py --stale-days 7

    # Dry-run delete (still READ-ONLY — shows what WOULD be deleted)
    python daytona_snapshot_manager.py --delete-stale          # WAIT: see below

    # Actually delete stale snapshots (prompts unless --yes)
    python daytona_snapshot_manager.py --delete-stale --yes

Auth
----
API key resolution order:
    1. --api-key VALUE
    2. environment variable named by --api-key-env (default DAYTONA_DATA_API_KEY)
    3. that same variable read from a secrets file
       (--secrets-file, default $DC_AGENT_SECRET_ENV; see .agents/secret.md)

Exit codes
----------
    0  success
    1  runtime / API error
    2  CLI / auth error (no key, bad args)
    3  --delete-stale requested but user declined the confirmation prompt
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

try:
    from .daytona_client import create_client, resolve_api_key
except ImportError:
    from daytona_client import create_client, resolve_api_key

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HARD_CAP = 60  # org-wide snapshot hard limit (never raised by this tool)
DEFAULT_STALE_DAYS = 14
DEFAULT_SECRETS_FILE = os.environ.get("DC_AGENT_SECRET_ENV", "")
PAGE_LIMIT = 100  # snapshots per page when paging through the org

# Snapshot states that must never be flagged or deleted: in-flight / transitional.
# 'active' is NOT protected — for snapshots it is the normal resting state of a
# built, available snapshot. An idle active snapshot past the threshold is the
# reclaim target, governed purely by idle time.
PROTECTED_STATES = {"building", "pending", "pulling", "removing"}
# Error-ish states eligible only when ALSO past the stale window.
ERROR_STATES = {"error", "build_failed"}


# ---------------------------------------------------------------------------
# Snapshot fetch
# ---------------------------------------------------------------------------
def list_all_snapshots(client) -> list:
    """Fetch every snapshot in the org by paging through SnapshotService.list()."""
    snapshots: list = []
    page = 1
    total_pages = 1
    while page <= total_pages:
        result = client.snapshot.list(page=page, limit=PAGE_LIMIT)
        snapshots.extend(result.items)
        total_pages = result.total_pages or 1
        page += 1
    return snapshots


# ---------------------------------------------------------------------------
# Staleness analysis
# ---------------------------------------------------------------------------
def _as_aware(dt) -> datetime | None:
    """Return a timezone-aware datetime (assume UTC if naive). None passes through."""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def analyze(snapshots: list, stale_days: float, name_prefix: str = "") -> list[dict]:
    """Compute per-snapshot age / idle metrics and staleness verdict.

    Returns a list of dicts (one per snapshot) sorted most-stale-first.

    ``name_prefix`` restricts the STALE (deletable) verdict to snapshots whose
    name starts with it — the datagen/eval/RL per-environment snapshots are all
    ``harbor__<hash>__snapshot``, so the default guards the shared base/template
    images (``daytonaio/sandbox:*``, ``daytona-*``, ``windows-*``) from ever
    being flagged. Pass ``""`` to consider every snapshot (audit only).
    """
    now = datetime.now(timezone.utc)
    threshold_seconds = stale_days * 86400.0
    rows: list[dict] = []

    for s in snapshots:
        state = getattr(s.state, "value", str(s.state)).lower()
        created = _as_aware(getattr(s, "created_at", None))
        last_used = _as_aware(getattr(s, "last_used_at", None))
        updated = _as_aware(getattr(s, "updated_at", None))

        # Idle reference: prefer last_used_at; fall back to created_at and flag it.
        if last_used is not None:
            idle_ref = last_used
            idle_basis = "last_used_at"
        else:
            idle_ref = created
            idle_basis = "created_at (never used — fallback)"

        age_seconds = (now - created).total_seconds() if created else None
        idle_seconds = (now - idle_ref).total_seconds() if idle_ref else None

        protected = state in PROTECTED_STATES
        is_idle = idle_seconds is not None and idle_seconds > threshold_seconds
        name_ok = (not name_prefix) or s.name.startswith(name_prefix)

        # Stale = matches the reclaim prefix AND idle past threshold AND not
        # protected. Error/build_failed states are eligible only when ALSO idle
        # past the window. Base/template images (name_ok False) are never stale.
        stale = name_ok and is_idle and not protected

        # Reason annotation for the report.
        if not name_ok:
            reason = f"kept (not {name_prefix})"
        elif protected:
            reason = f"protected (state={state})"
        elif not is_idle:
            reason = "fresh (within window)"
        elif state in ERROR_STATES:
            reason = f"STALE (errored + idle {idle_seconds / 86400:.1f}d)"
        else:
            reason = f"STALE (idle {idle_seconds / 86400:.1f}d)"

        rows.append(
            {
                "id": s.id,
                "name": s.name,
                "state": state,
                "created_at": created.isoformat() if created else None,
                "updated_at": updated.isoformat() if updated else None,
                "last_used_at": last_used.isoformat() if last_used else None,
                "idle_basis": idle_basis,
                "age_days": round(age_seconds / 86400, 2)
                if age_seconds is not None
                else None,
                "idle_days": round(idle_seconds / 86400, 2)
                if idle_seconds is not None
                else None,
                "protected": protected,
                "stale": stale,
                "reason": reason,
                "error_reason": getattr(s, "error_reason", None),
                "_obj": s,  # SDK object, used for deletion; stripped from JSON
            }
        )

    # Most-stale-first: stale rows first, then by idle_days desc.
    rows.sort(
        key=lambda r: (
            0 if r["stale"] else 1,
            -(r["idle_days"] if r["idle_days"] is not None else -1),
        )
    )
    return rows


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def _short(ts: str | None) -> str:
    """Render an ISO timestamp as 'YYYY-MM-DD HH:MM' or 'n/a'."""
    if not ts:
        return "n/a"
    return ts.replace("T", " ")[:16]


def print_audit_human(rows: list[dict], total_reported: int, stale_days: float) -> None:
    n_total = len(rows)
    used_fallback = any(r["idle_basis"].startswith("created_at") for r in rows)

    # State breakdown
    by_state: dict[str, int] = {}
    for r in rows:
        by_state[r["state"]] = by_state.get(r["state"], 0) + 1

    stale_rows = [r for r in rows if r["stale"]]
    protected_rows = [r for r in rows if r["protected"]]

    print("=" * 100)
    print("DAYTONA SNAPSHOT AUDIT (read-only)")
    print("=" * 100)
    print(f"Total snapshots (API total): {total_reported}")
    if n_total != total_reported:
        print(f"  (fetched {n_total} objects via pagination)")
    print(f"Staleness threshold: idle > {stale_days} day(s)")
    print()

    # Per-snapshot table
    hdr = (
        f"{'NAME':<42} {'STATE':<12} {'AGE(d)':>7} {'IDLE(d)':>8} "
        f"{'LAST USED':<17} {'CREATED':<17}"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        flag = "*" if r["stale"] else (" " if not r["protected"] else "P")
        last_used = _short(r["last_used_at"])
        if not r["last_used_at"]:
            last_used = "never"
        print(
            f"{flag}{r['name']:<41.41} {r['state']:<12} "
            f"{(r['age_days'] if r['age_days'] is not None else 0):>7.1f} "
            f"{(r['idle_days'] if r['idle_days'] is not None else 0):>8.1f} "
            f"{last_used:<17} {_short(r['created_at']):<17}"
        )

    print()
    print("STATE BREAKDOWN:")
    for state, count in sorted(by_state.items()):
        print(f"  {state:<14} {count}")

    print()
    headroom = HARD_CAP - total_reported
    print(
        f"CAP: {total_reported} / {HARD_CAP} used  ->  headroom = {headroom} snapshot(s)"
    )
    print(f"STALE (>{stale_days}d idle, deletable): {len(stale_rows)}")
    print(
        f"PROTECTED (building/pending/pulling/removing — transitional): {len(protected_rows)}"
    )
    if stale_rows:
        reclaimable_headroom = headroom + len(stale_rows)
        print(
            f"If all {len(stale_rows)} stale snapshots were reclaimed, headroom would "
            f"become {reclaimable_headroom}."
        )
    print()
    if used_fallback:
        print(
            "NOTE: one or more snapshots had no last_used_at; staleness for those rows "
            "is based on CREATED-AT AGE, not actual usage (they were built but never "
            "used). Those rows are labeled 'never' under LAST USED."
        )
    print(
        "Legend:  * = stale/deletable   P = protected (transitional)   (blank) = fresh/idle-but-within-window"
    )
    print("=" * 100)


def build_json(rows: list[dict], total_reported: int, stale_days: float) -> dict:
    by_state: dict[str, int] = {}
    for r in rows:
        by_state[r["state"]] = by_state.get(r["state"], 0) + 1
    stale_rows = [r for r in rows if r["stale"]]
    clean = []
    for r in rows:
        d = {k: v for k, v in r.items() if k != "_obj"}
        clean.append(d)
    return {
        "hard_cap": HARD_CAP,
        "total_snapshots": total_reported,
        "headroom": HARD_CAP - total_reported,
        "stale_days_threshold": stale_days,
        "state_breakdown": by_state,
        "stale_count": len(stale_rows),
        "protected_count": sum(1 for r in rows if r["protected"]),
        "snapshots": clean,
    }


# ---------------------------------------------------------------------------
# Deletion
# ---------------------------------------------------------------------------
def delete_stale(
    client, stale_rows: list[dict], do_delete: bool, assume_yes: bool
) -> int:
    """Print would-delete / actually-delete stale snapshots. Returns exit code."""
    if not stale_rows:
        print("No stale snapshots to delete.")
        return 0

    print(f"\n{len(stale_rows)} snapshot(s) match the staleness criterion:")
    for r in stale_rows:
        print(
            f"  - {r['name']}  (state={r['state']}, idle={r['idle_days']}d)  {r['reason']}"
        )

    if not do_delete:
        print(
            f"\nDRY-RUN: would delete the {len(stale_rows)} snapshot(s) above. "
            f"Re-run with --delete-stale to actually reclaim them."
        )
        return 0

    if not assume_yes:
        try:
            resp = (
                input(f"\nDelete these {len(stale_rows)} snapshots? [y/N] ")
                .strip()
                .lower()
            )
        except EOFError:
            resp = ""
        if resp not in ("y", "yes"):
            print("Aborted — no snapshots deleted.")
            return 3

    print(f"\nDeleting {len(stale_rows)} stale snapshots ...")
    ok = failed = 0
    for i, r in enumerate(stale_rows, 1):
        try:
            client.snapshot.delete(r["_obj"])
            ok += 1
            print(f"  [{i}/{len(stale_rows)}] deleted {r['name']}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(
                f"  [{i}/{len(stale_rows)}] FAILED {r['name']}: {type(exc).__name__}: {exc}"
            )
        time.sleep(0.05)  # gentle rate-limit cushion

    print(f"\nDone. Reclaimed {ok}/{len(stale_rows)} snapshot(s).")
    if failed:
        print(f"  {failed} deletion(s) failed.")
        return 1
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="daytona_snapshot_manager.py",
        description=(
            "Audit and (optionally) reclaim stale Daytona snapshots in an org. "
            "Default mode is a READ-ONLY audit. This tool only audits and deletes; "
            "it never creates snapshots or raises caps."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Auth
    p.add_argument(
        "--api-key", default=None, help="Daytona org API key (overrides env/secrets)."
    )
    p.add_argument(
        "--api-key-env",
        default="DAYTONA_DATA_API_KEY",
        help="Env var (and secrets-file key) to read the API key from "
        "(default: DAYTONA_DATA_API_KEY).",
    )
    p.add_argument(
        "--secrets-file",
        default=DEFAULT_SECRETS_FILE,
        help=f"KEY=VALUE secrets file to read the key from (default: {DEFAULT_SECRETS_FILE}).",
    )
    p.add_argument(
        "--api-url",
        default=None,
        help="Override Daytona API URL (default: SDK default / DAYTONA_API_URL).",
    )
    # Staleness
    p.add_argument(
        "--stale-days",
        type=float,
        default=DEFAULT_STALE_DAYS,
        help=f"Idle days before a snapshot is stale (default: {DEFAULT_STALE_DAYS}).",
    )
    p.add_argument(
        "--name-prefix",
        default="harbor__",
        help="Only snapshots whose name starts with this prefix are eligible for the "
        "STALE/deletable verdict (default: harbor__). Guards shared base/template images "
        "(daytonaio/sandbox:*, daytona-*, windows-*) that do NOT rebuild-on-demand. "
        "Pass '' to audit every snapshot (never delete with an empty prefix).",
    )
    # Delete
    p.add_argument(
        "--delete-stale",
        action="store_true",
        help="Delete snapshots matching the staleness criterion (DEFAULT is dry-run).",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation prompt when deleting.",
    )
    # Output
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()

    try:
        api_key = resolve_api_key(
            api_key=args.api_key,
            api_key_env=args.api_key_env,
            secrets_file=args.secrets_file,
        )
        client = create_client(api_key=api_key, api_url=args.api_url)
    except Exception as exc:  # noqa: BLE001
        print(
            f"ERROR: failed to initialize Daytona client: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2

    try:
        snapshots = list_all_snapshots(client)
        total_reported = client.snapshot.list(page=1, limit=1).total
    except Exception as exc:  # noqa: BLE001
        print(
            f"ERROR: failed to list snapshots: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    rows = analyze(snapshots, args.stale_days, name_prefix=args.name_prefix)
    stale_rows = [r for r in rows if r["stale"]]

    if args.json:
        payload = build_json(rows, total_reported, args.stale_days)
        payload["delete_requested"] = bool(args.delete_stale)
        if args.delete_stale:
            # Perform deletion, then report results in JSON.
            deleted, failed = [], []
            if not args.yes:
                print(
                    "ERROR: --delete-stale with --json requires --yes "
                    "(no interactive prompt in JSON mode).",
                    file=sys.stderr,
                )
                return 2
            for r in stale_rows:
                try:
                    client.snapshot.delete(r["_obj"])
                    deleted.append(r["name"])
                except Exception as exc:  # noqa: BLE001
                    failed.append(
                        {"name": r["name"], "error": f"{type(exc).__name__}: {exc}"}
                    )
                time.sleep(0.05)
            payload["deleted"] = deleted
            payload["delete_failed"] = failed
        print(json.dumps(payload, indent=2, default=str))
        return 1 if (args.delete_stale and payload.get("delete_failed")) else 0

    # Human-readable
    print_audit_human(rows, total_reported, args.stale_days)
    return delete_stale(client, stale_rows, args.delete_stale, args.yes)


if __name__ == "__main__":
    sys.exit(main())
