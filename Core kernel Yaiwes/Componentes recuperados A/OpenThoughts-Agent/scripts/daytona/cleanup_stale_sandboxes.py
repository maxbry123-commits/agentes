#!/usr/bin/env python3
"""
Reap leaked Daytona sandboxes — TWO buckets:
  1. STALE-STARTED — running sandboxes idle past the threshold (orphaned active sandboxes).
  2. TERMINAL-DEAD — ERROR / BUILD_FAILED sandboxes that never self-clear on the
     non-snapshot (non-ephemeral, auto_delete_interval=0) eval path. Reaped by
     default; --no-reap-dead to skip.

Uses the official Daytona Python SDK (`daytona` package, v0.180+). Deleting a sandbox
INSTANCE never touches its `harbor__*` snapshot TEMPLATE, so the dead-reap is cap-safe.

Usage:
    # Dry run (default) — shows what would be deleted
    python cleanup_stale_sandboxes.py

    # Actually delete
    python cleanup_stale_sandboxes.py --delete

    # Custom threshold (minutes)
    python cleanup_stale_sandboxes.py --delete --threshold 120

Environment:
    DAYTONA_API_KEY     — API key for the target organization (default)
    DAYTONA_RL_API_KEY  — Fallback API key (or set in secrets.env)
"""

import argparse
import os
import time
from datetime import datetime, timezone

from daytona import (
    Daytona,
    ListSandboxesQuery,
    SandboxListSortDirection,
    SandboxListSortField,
    SandboxState,
)

try:
    from .daytona_client import create_client, resolve_api_key
except ImportError:
    from daytona_client import create_client, resolve_api_key

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PAGE_LIMIT = 100  # per-page fetch size; SDK pages through automatically
DEFAULT_THRESHOLD_MINUTES = 60

# Terminal-dead states: failed sandboxes that never self-clear on the non-snapshot
# (auto_delete_interval=0) eval path. Terminal state ⇒ no active trial ⇒ safe to
# delete; instance deletion never touches the `harbor__*` snapshot template (cap-safe).
# Built robustly from whatever the SDK enum exposes (member names drift across versions).
_DEAD_STATE_NAMES = ("ERROR", "BUILD_FAILED", "BUILDFAILED")
DEAD_STATES = [
    getattr(SandboxState, n) for n in _DEAD_STATE_NAMES if hasattr(SandboxState, n)
]

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def _last_seen_ts(sb) -> str | None:
    """Pick the freshest activity timestamp available on a Sandbox object."""
    return getattr(sb, "last_activity_at", None) or getattr(sb, "updated_at", None)


def list_started_sandboxes(client: Daytona) -> list:
    """Fetch all sandboxes in 'started' state, sorted by last activity desc."""
    query = ListSandboxesQuery(
        states=[SandboxState.STARTED],
        sort=SandboxListSortField.LASTACTIVITYAT,
        order=SandboxListSortDirection.DESC,
        limit=PAGE_LIMIT,
    )
    return list(client.list(query))


def list_dead_sandboxes(client: Daytona) -> list:
    """Fetch all sandboxes in terminal-dead states (ERROR / BUILD_FAILED).

    No staleness filter is applied — a terminal state already means the sandbox is dead.
    """
    if not DEAD_STATES:
        return []
    query = ListSandboxesQuery(states=DEAD_STATES, limit=PAGE_LIMIT)
    return list(client.list(query))


def delete_sandbox(sb) -> bool:
    """Delete a single sandbox. Returns True on success."""
    try:
        sb.delete()
        return True
    except Exception as e:  # noqa: BLE001
        print(f"    error: {type(e).__name__}: {e}")
        return False


def _delete_bucket(sandboxes: list, label: str) -> tuple[int, int]:
    """Delete every sandbox in a bucket; return (success, failed). Rate-limited."""
    print(f"\nDeleting {len(sandboxes)} {label} sandboxes …")
    success = failed = 0
    for i, sb in enumerate(sandboxes, 1):
        if delete_sandbox(sb):
            success += 1
        else:
            failed += 1
            print(f"  FAILED to delete {sb.id}")
        if i % 50 == 0 or i == len(sandboxes):
            print(f"  Progress: {i}/{len(sandboxes)}  (ok={success}, fail={failed})")
        time.sleep(0.05)  # avoid rate-limiting
    return success, failed


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def find_stale_sandboxes(sandboxes: list, threshold_minutes: int) -> list:
    """Return sandboxes whose last-activity timestamp is older than threshold_minutes ago."""
    now = datetime.now(timezone.utc)
    stale = []

    for sb in sandboxes:
        updated_str = _last_seen_ts(sb)
        if not updated_str:
            continue
        # Parse ISO-8601 timestamp (with or without trailing Z)
        updated_str = updated_str.replace("Z", "+00:00")
        try:
            updated_at = datetime.fromisoformat(updated_str)
        except ValueError:
            continue
        age_minutes = (now - updated_at).total_seconds() / 60.0
        if age_minutes > threshold_minutes:
            # Attach for the report; using a plain attribute since these are
            # SDK Sandbox instances, not dicts.
            sb._age_minutes = round(age_minutes, 1)
            stale.append(sb)

    return stale


def main():
    parser = argparse.ArgumentParser(description="Clean up stale Daytona RL sandboxes")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete stale sandboxes (default is dry-run)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD_MINUTES,
        help=f"Minutes of inactivity before a sandbox is considered stale (default: {DEFAULT_THRESHOLD_MINUTES})",
    )
    parser.add_argument(
        "--api-key",
        help="Daytona API key. Prefer the environment variable in normal use.",
    )
    parser.add_argument(
        "--api-key-env",
        type=str,
        default="DAYTONA_API_KEY",
        help="Environment variable name containing the API key (default: DAYTONA_API_KEY)",
    )
    parser.add_argument(
        "--secrets-file",
        default=os.environ.get("DC_AGENT_SECRET_ENV"),
        help="Optional env file. Defaults to $DC_AGENT_SECRET_ENV.",
    )
    parser.add_argument(
        "--no-reap-dead",
        action="store_true",
        help="Skip reaping terminal-dead (ERROR/BUILD_FAILED) sandboxes (reaped by default).",
    )
    args = parser.parse_args()

    try:
        api_key = resolve_api_key(
            api_key=args.api_key,
            api_key_env=args.api_key_env,
            secrets_file=args.secrets_file,
            fallback_env_vars=("DAYTONA_RL_API_KEY",),
        )
        client = create_client(api_key=api_key)
    except ValueError as exc:
        parser.error(str(exc))

    # 1. STALE-STARTED bucket: running sandboxes idle past the threshold (orphaned).
    print("Fetching all started sandboxes …")
    started = list_started_sandboxes(client)
    print(f"  Found {len(started)} started sandboxes.")
    stale = find_stale_sandboxes(started, args.threshold)
    print(f"  {len(stale)} are stale (no event in >{args.threshold} min).")

    # 2. DEAD bucket: terminal ERROR/BUILD_FAILED sandboxes.
    dead = [] if args.no_reap_dead else list_dead_sandboxes(client)
    if not args.no_reap_dead:
        print(
            f"  Found {len(dead)} terminal-dead sandboxes (ERROR/BUILD_FAILED) to reap."
        )
    print()

    if not stale and not dead:
        print("Nothing to clean up.")
        return

    # 3. Report
    if stale:
        print(f"STALE-STARTED ({len(stale)}):")
        print(f"  {'ID':<40} {'Age (min)':>10}  {'Created':<26} {'Last Activity':<26}")
        print("  " + "-" * 108)
        for sb in stale:
            print(
                f"  {sb.id:<40} {sb._age_minutes:>10.1f}  {sb.created_at or 'n/a':<26} {_last_seen_ts(sb) or 'n/a':<26}"
            )
    if dead:
        from collections import Counter

        by_state = Counter(str(getattr(sb, "state", "?")) for sb in dead)
        print(
            f"DEAD ({len(dead)}): " + ", ".join(f"{s}={n}" for s, n in by_state.items())
        )

    if not args.delete:
        print(
            f"\nDry run — pass --delete to actually remove {len(stale)} stale + {len(dead)} dead sandboxes."
        )
        return

    # 4. Delete both buckets
    total_ok = total_fail = 0
    for bucket, label in ((stale, "stale-started"), (dead, "terminal-dead")):
        if not bucket:
            continue
        ok, failed = _delete_bucket(bucket, label)
        total_ok += ok
        total_fail += failed

    print(
        f"\nDone. Deleted {total_ok} sandboxes ({len(stale)} stale + {len(dead)} dead)."
    )
    if total_fail:
        print(f"  {total_fail} deletions failed.")


if __name__ == "__main__":
    main()
