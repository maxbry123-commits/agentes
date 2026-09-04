#!/usr/bin/env python3
"""Analyze a completed Iris Harbor datagen or eval job from synced or remote history.

Log acquisition reads finelog directly. For a logical job we:

  1. Enumerate the authoritative attempt/generation set from the iris controller
     SQLite (``task_attempts`` joined through ``tasks``/``jobs`` on
     ``root_job_id``/``job_id``), with each attempt's ``[started, finished]``
     window.
  2. Fetch every matching ``log`` row by ``key`` prefix from BOTH the LIVE
     finelog server (recent, locally-resident segments) AND the GCS parquet
     archive (uploaded L>=1 segments), then union and dedup on the server-stamped
     monotonic ``seq``. Neither source alone is complete.
  3. Assert COVERAGE: every enumerated attempt window must contain log rows with
     no internal gap larger than ``--max-coverage-gap-seconds``. If any window is
     uncovered (e.g. live unavailable for the recent L0 tail AND GCS has not yet
     archived it) we FAIL LOUDLY, listing the missing ``(log_key, window)``,
     unless ``--allow-incomplete`` is passed.

The merged, filtered stream is cached to ``/tmp/iris_history_<job>.filtered.log``
(coverage result alongside in ``.coverage.json``) so re-runs are fast;
``--refresh`` re-fetches.

Three sections of stats are computed:
  §1 preemption count + time-to-preempt distribution
  §2 trace progress per cycle (from harbor GCS output)
  §3 serving throughput stats (full + warmup-excluded)

A markdown report is written to ``--output``; a JSON sidecar is written
alongside.

Run under the marin venv (``/Users/benjaminfeuer/Documents/marin/.venv/bin/
python``) so ``finelog``/``rigging``/``duckdb`` import. The LIVE path needs an
IAP session for the ``marin`` cluster (``marin-login login marin``); without it
the recent-L0 window is reported as uncovered rather than silently dropped.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from collections.abc import Callable, Iterator
from pathlib import Path

import os
import shutil

import duckdb
import fsspec
from finelog.client.log_client import LogClient
from finelog.deploy.cli import _register_namespace_views
from finelog.deploy.config import FinelogConfig, load_finelog_config, tunnel_target_for
from finelog.errors import StatsError
from rigging.auth import IapLoginRequired
from rigging.connect import IapAuth, connect, disconnect
from rigging.credentials import iap_edge_provider
from rigging.tunnel import open_tunnel

from hpc.iris.job_output_resolver import resolve_job_output_dir


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.iris.iris_ops import (  # noqa: E402
    DEFAULT_BUNDLE_ROOT,
    job_bundle,
    load_bundle_manifest,
    write_bundle_manifest,
)


def resolve_iris_bin() -> str:
    """Resolve a WORKING iris binary.

    Precedence: ``$IRIS_BIN`` env override → ``iris`` on ``$PATH`` → the otagent
    conda env's iris (drives CoreWeave ``cw-us-east-02a`` cleanly) → the marin
    ``.venv`` iris (TPU/marin cluster). The marin ``.venv`` iris has a broken
    ``kubernetes`` import and CANNOT drive CoreWeave, so it is deliberately LAST.
    """
    env_override = os.environ.get("IRIS_BIN")
    if env_override and Path(env_override).exists():
        return env_override
    on_path = shutil.which("iris")
    if on_path:
        return on_path
    candidates = [
        "/Users/benjaminfeuer/miniconda3/envs/otagent/bin/iris",
        "/Users/benjaminfeuer/Documents/marin/.venv/bin/iris",
    ]
    for cand in candidates:
        if Path(cand).exists():
            return cand
    return "iris"


# Resolved once at import; the ``--cluster`` is supplied per-invocation (default
# below). For CoreWeave pass ``--cluster cw-us-east-02a`` (needs KUBECONFIG set).
IRIS_BIN = resolve_iris_bin()
# Default cluster; overridable via --cluster. NOT hardcoded into the query/log
# helpers any longer — they read module-global CLUSTER, set from argv in main().
CLUSTER = "marin"

# Iris log line: "[HH:MM:SS] task=<task> | <content>"
LINE_RE = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\] task=(\S+) \| (.*)$")

# Cycle boundary on a given task: the tpu-inference-patch fires exactly once per
# attempt boot. We use task=/.../0 boundaries as the cycle marker.
PATCH_APPLIED_RE = re.compile(r"\[tpu-inference-patch\] APPLIED:")

# Rendezvous polling has an embedded epoch-seconds timestamp:
# "[start_vllm_iris_controller] Polling for rendezvous ... min written_at <epoch>)..."
RENDEZVOUS_RE = re.compile(r"min written_at (\d+)\)")

# result.json is harbor's large, continuously-updated status file; a `gsutil cat`
# that races a mid-write (or a truncated transfer) yields a JSONDecodeError. The
# read is the reader's only handle, so retry briefly before degrading gracefully.
HARBOR_FETCH_ATTEMPTS = 3
HARBOR_FETCH_BACKOFFS = (1, 2)

# Throughput line from vLLM's logger has an embedded MM-DD HH:MM:SS:
# "(APIServer pid=N) INFO 05-30 07:07:36 [loggers.py:271] Engine ...: Avg prompt
# throughput: X tokens/s, Avg generation throughput: Y tokens/s, Running: N reqs,
# Waiting: W reqs, ..."
THROUGHPUT_RE = re.compile(
    r"INFO (\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2}) .*?"
    r"Avg prompt throughput:\s+([0-9.]+) tokens/s,\s+"
    r"Avg generation throughput:\s+([0-9.]+) tokens/s,\s+"
    r"Running:\s+(\d+) reqs,\s+Waiting:\s+(\d+) reqs"
)

# Preempt-edge markers (any of these on any task signal a cycle ending soon).
# We separately count cycles from APPLIED markers on task=0; these are
# diagnostic only, useful for cross-checking.
PREEMPT_EDGE_RE = re.compile(
    r"(raylet\) Raylet is terminated|EngineCore died|worker_lost_spec|Preempted by /[^/]+/)"
)

# Filter regex used when pulling logs from iris (keep only lines we care about).
# We INCLUDE the iris control-plane lines (without a [HH:MM:SS] prefix) so we can
# detect the "tunnel ready" boundary; we filter those out at line-prefix-parse
# time later.
KEEP_RE = re.compile(
    r"(\[tpu-inference-patch\] APPLIED|"
    r"start_vllm_iris_controller\] Polling for rendezvous|"
    r"raylet\) Raylet is terminated|"
    r"EngineCore died|"
    r"worker_lost_spec|"
    r"Preempted by /[^/]+/|"
    r"Avg generation throughput)"
)

# Spinner / progress lines we definitely want to drop fast (these dominate the
# raw log volume). The KEEP_RE above already excludes them implicitly, so this
# is belt-and-suspenders / not used at the moment.
DROP_SUFFIX = ("running agent...", "[fd-monitor]")

# ---------- finelog acquisition tuning ----------

# Server-side substring filters that select exactly the lines KEEP_RE matches.
# These are LITERAL substrings of each KEEP_RE alternative; pushing them down as
# ``contains(data, ...)`` (trigram-indexed) shrinks the stats fetch from the full
# multi-million-row stream to a few thousand rows, while ``parse_log_lines`` still
# re-validates each line against the precise regexes.
FINELOG_CONTAINS_PATTERNS = (
    "[tpu-inference-patch] APPLIED",
    "Polling for rendezvous",
    "Raylet is terminated",
    "EngineCore died",
    "worker_lost_spec",
    "Preempted by /",
    "Avg generation throughput",
)

# The LIVE query deadline must cover a trigram scan over a multi-day job; the
# 10s client default times out on the long datagen jobs.
LIVE_TIMEOUT_MS = 180_000
# seq keyset page size. The server has no row cap but a 64MB transport limit per
# response; a 50k-row page of log lines stays well under it.
SEQ_PAGE_ROWS = 50_000
# Coverage is proven by a cheap per-minute GROUP BY over ALL rows (unfiltered):
# a bucket is "covered" if either source emitted >=1 row in that minute.
COVERAGE_BUCKET_MS = 60_000
# Portable floor-division to a minute bucket. The finelog server is
# Postgres-flavored (integer ``/``) while the GCS path is DuckDB (float ``/``);
# ``CAST(floor(epoch_ms / 60000.0) AS BIGINT)`` yields the same integer bucket on
# both, matching python's ``epoch_ms // COVERAGE_BUCKET_MS``.
BUCKET_EXPR = f"CAST(floor(epoch_ms / {COVERAGE_BUCKET_MS}.0) AS BIGINT)"
# GCS parquet prune padding (segment ``time_created`` is an upper bound on its
# rows' ``epoch_ms``): widen the window generously so L0->L1 compaction lag never
# prunes a segment that still holds in-window rows.
GCS_CREATED_SINCE_PAD_MS = 3_600_000  # 1h below the window floor
GCS_CREATED_UNTIL_PAD_MS = 6 * 3_600_000  # 6h above the window ceiling
# Default max run of consecutive empty minutes tolerated inside an attempt window
# before it is flagged uncovered.
DEFAULT_MAX_COVERAGE_GAP_SECONDS = 600.0


@dataclass
class Cycle:
    idx: int
    cycle_start: datetime
    cycle_end: datetime
    did_serve: bool
    time_to_first_serve_s: float | None
    duration_s: float
    serving_samples_in_cycle: int = 0
    non_empty_trials_in_cycle: int = 0


@dataclass
class ServingSample:
    ts: datetime
    prompt_tps: float
    gen_tps: float
    running: int
    waiting: int
    cycle_idx: int = -1
    elapsed_in_cycle_s: float = 0.0


@dataclass
class TrialStatus:
    trial_name: str
    has_trajectory: bool
    trajectory_mtime: datetime | None
    trajectory_size: int


@dataclass
class Attempt:
    """One row of ``task_attempts`` — an attempt of a task in some generation.

    ``log_key`` is the iris wire identity including the attempt suffix
    (``<task_id>:<attempt_id>``), which is the value of the finelog ``key``
    column. ``finished_at_ms`` is ``None`` while the attempt is still running, in
    which case its coverage window runs to ``now``.
    """

    log_key: str
    state: int
    started_at_ms: int | None
    finished_at_ms: int | None


@dataclass
class MissingWindow:
    """A coverage gap: an attempt window with a too-long run of empty minutes."""

    log_key: str
    window_start_ms: int
    window_end_ms: int
    gap_start_ms: int
    gap_end_ms: int
    gap_seconds: float


@dataclass
class LogAcquisition:
    """Result of the LIVE u GCS fetch + coverage assertion."""

    lines: list[str]
    logs_complete: bool
    missing_windows: list[MissingWindow]
    live_available: bool
    live_unavailable_reason: str | None
    live_rows: int
    gcs_rows: int
    merged_rows: int


@dataclass
class JobAnalysis:
    job_id: str
    job_name: str
    submitted_at: datetime
    started_at: datetime
    current_time: datetime
    total_runtime_s: float
    iris_preemption_count: int | None
    state: int

    # §1
    cycles: list[Cycle] = field(default_factory=list)
    preempt_count_from_log: int = 0

    # §2
    total_trial_dirs: int = 0
    non_empty_trials: int = 0
    harbor_n_completed: int = 0
    harbor_n_errored: int = 0
    harbor_n_running: int = 0
    harbor_n_pending: int = 0
    harbor_exception_stats: dict[str, int] = field(default_factory=dict)
    harbor_started_at: str | None = None
    harbor_updated_at: str | None = None
    harbor_n_total_trials: int = 0

    # §3
    serving_samples: list[ServingSample] = field(default_factory=list)

    # Completeness contract (see module docstring §3).
    logs_complete: bool = True
    missing_windows: list[MissingWindow] = field(default_factory=list)


# ---------- Iris CLI / subprocess helpers ----------


def run_iris_query(sql: str) -> list[dict[str, str]]:
    """Run ``iris query`` and parse CSV. iris prints I-level logs to stderr."""
    cmd = [IRIS_BIN, "--cluster", CLUSTER, "query", sql, "-f", "csv"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    lines = [line for line in proc.stdout.strip().splitlines() if line]
    if not lines:
        return []
    header = lines[0].split(",")
    return [dict(zip(header, line.split(","), strict=False)) for line in lines[1:]]


def get_job_metadata(job_id: str) -> dict[str, int | str]:
    sql = (
        "SELECT job_id, submitted_at_ms, started_at_ms, state "
        f"FROM jobs WHERE job_id='{job_id}'"
    )
    rows = run_iris_query(sql)
    if not rows:
        raise RuntimeError(f"no job row found for {job_id}")
    row = rows[0]
    return {
        "job_id": row["job_id"],
        "submitted_at_ms": int(row["submitted_at_ms"]),
        "started_at_ms": int(row["started_at_ms"]),
        "state": int(row["state"]),
    }


def get_job_summary_preemptions(job_id: str) -> int | None:
    cmd = [IRIS_BIN, "--cluster", CLUSTER, "job", "summary", job_id]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    # "State: running  exit=0  failures=0  preemptions=37"
    m = re.search(r"preemptions=(\d+)", proc.stdout)
    if not m:
        return None
    return int(m.group(1))


# ---------- finelog log acquisition (LIVE u GCS, dedup on seq) ----------


def _int_or_none(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def enumerate_attempts(job_id: str) -> tuple[list[Attempt], int]:
    """Enumerate every attempt of every generation of the logical job ``job_id``.

    Works whether ``job_id`` is a plain job, an executor coordinator, or a child:
    the WHERE clause unions ``root_job_id`` matches (all descendants/generations)
    with ``job_id`` matches (the job itself). Returns the attempt list plus
    ``window_lo_ms``, the earliest job/attempt timestamp seen (used to bound the
    GCS parquet prune). GC'd generations that survive only in finelog are still
    fetched by key prefix; they simply lack an enumerated coverage window.
    """
    esc = job_id.replace("'", "''")
    sql = (
        "SELECT ta.task_id || ':' || ta.attempt_id AS log_key, ta.state, "
        "ta.started_at_ms, ta.finished_at_ms "
        "FROM task_attempts ta "
        "JOIN tasks t ON t.task_id = ta.task_id "
        "JOIN jobs j ON j.job_id = t.job_id "
        f"WHERE j.root_job_id = '{esc}' OR j.job_id = '{esc}' "
        "ORDER BY ta.started_at_ms"
    )
    rows = run_iris_query(sql)
    attempts = [
        Attempt(
            log_key=r["log_key"],
            state=int(r["state"]) if r.get("state") else -1,
            started_at_ms=_int_or_none(r.get("started_at_ms")),
            finished_at_ms=_int_or_none(r.get("finished_at_ms")),
        )
        for r in rows
    ]
    job_sql = (
        "SELECT submitted_at_ms, started_at_ms FROM jobs "
        f"WHERE root_job_id = '{esc}' OR job_id = '{esc}'"
    )
    job_rows = run_iris_query(job_sql)
    candidates: list[int] = []
    for jr in job_rows:
        candidates += [
            _int_or_none(jr.get("submitted_at_ms")),
            _int_or_none(jr.get("started_at_ms")),
        ]
    for att in attempts:
        candidates += [att.started_at_ms, att.finished_at_ms]
    valid = [c for c in candidates if c]
    window_lo = min(valid) if valid else 0
    return attempts, window_lo


def _sql_str(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _key_predicate(prefix: str) -> str:
    """SQL predicate selecting every log row of ``prefix``'s job tree.

    Matches the exact ``prefix`` plus everything under ``<prefix>/`` (all tasks,
    attempts, and nested generations at any depth). ``%``/``_``/``\\`` in the
    prefix are escaped so a literal underscore in a job name cannot widen the
    match. Filtering is on ``key`` (wire identity), never ``source`` (stream).
    """
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    like_pat = escaped + "/%"
    return f"(key LIKE {_sql_str(like_pat)} ESCAPE '\\' OR key = {_sql_str(prefix)})"


def _data_predicate() -> str:
    return (
        "("
        + " OR ".join(
            f"contains(data, {_sql_str(p)})" for p in FINELOG_CONTAINS_PATTERNS
        )
        + ")"
    )


def _paginate(run_page: Callable[[int], list[dict]]) -> list[dict]:
    """Keyset-paginate by ``seq``: call ``run_page(last_seq)`` until a short page.

    ``run_page`` must return rows sorted ascending by ``seq``, at most
    ``SEQ_PAGE_ROWS`` of them, each a dict with a ``seq`` key.
    """
    out: list[dict] = []
    last_seq = -1
    while True:
        page = run_page(last_seq)
        out.extend(page)
        if len(page) < SEQ_PAGE_ROWS:
            return out
        last_seq = page[-1]["seq"]


def _data_page_sql(key_pred: str, data_pred: str, last_seq: int) -> str:
    return (
        "SELECT seq, key, source, epoch_ms, level, data FROM log "
        f"WHERE {key_pred} AND {data_pred} AND seq > {last_seq} "
        f"ORDER BY seq LIMIT {SEQ_PAGE_ROWS}"
    )


def _bucket_sql(key_pred: str) -> str:
    # Unfiltered per-minute presence over EVERY row (the coverage proof).
    return f"SELECT {BUCKET_EXPR} AS bkt, count(*) AS n FROM log WHERE {key_pred} GROUP BY 1 ORDER BY 1"


@contextmanager
def _open_live_client(cfg: FinelogConfig, finelog_name: str) -> "Iterator[LogClient]":
    """Yield a LogClient to the live finelog server, mirroring ``finelog query``.

    Uses the controller IAP proxy when ``client_url`` is set (the marin cluster),
    otherwise an SSH/k8s tunnel (e.g. cw-us-east-02a).
    """
    if cfg.client_url:
        provider = iap_edge_provider(finelog_name)
        if provider is None:
            raise IapLoginRequired(
                f"no cached IAP credentials for {finelog_name!r}; log in to {finelog_name!r} to refresh them"
            )
        client = connect(
            cfg.client_url,
            lambda ep: LogClient.connect(
                ep.url, interceptors=ep.interceptors, timeout_ms=LIVE_TIMEOUT_MS
            ),
            auth=IapAuth(provider),
            connect_timeout=60.0,
        )
        try:
            yield client
        finally:
            client.close()
            disconnect(client)
    else:
        target = tunnel_target_for(cfg)
        with open_tunnel(target, timeout=60.0) as url:
            client = LogClient.connect(url, timeout_ms=LIVE_TIMEOUT_MS)
            try:
                yield client
            finally:
                client.close()


def fetch_live(
    cfg: FinelogConfig, finelog_name: str, prefix: str
) -> tuple[list[dict], set[int], bool, str | None]:
    """Fetch filtered rows + per-minute coverage buckets from the LIVE server.

    Returns ``(rows, covered_buckets, available, reason)``. On any auth/transport
    failure the live source is reported UNAVAILABLE (empty rows/buckets) so the
    coverage check fails loudly for any window GCS does not also cover, rather
    than silently proceeding as if complete.
    """
    key_pred = _key_predicate(prefix)
    data_pred = _data_predicate()
    try:
        with _open_live_client(cfg, finelog_name) as client:
            rows = _paginate(
                lambda last: client.query(
                    _data_page_sql(key_pred, data_pred, last),
                    max_rows=SEQ_PAGE_ROWS + 10_000,
                ).to_pylist()
            )
            bucket_rows = client.query(
                _bucket_sql(key_pred), max_rows=2_000_000
            ).to_pylist()
            buckets = {int(r["bkt"]) for r in bucket_rows}
        return rows, buckets, True, None
    except (
        IapLoginRequired,
        StatsError,
        ConnectionError,
        OSError,
        TimeoutError,
    ) as exc:
        reason = f"{type(exc).__name__}: {exc}"
        print(
            f"[live] UNAVAILABLE: {reason}\n"
            "       (live finelog needs an IAP session: `marin-login login marin`)",
            file=sys.stderr,
        )
        return [], set(), False, reason


# finelog L0->L1->L2 compaction deletes superseded segments. A segment listed by
# the view builder can 404 by the time DuckDB reads it; re-listing picks up the
# superseding (higher-level) segment, whose rows carry the same ``seq`` — so a
# fresh attempt is consistent and completeness is preserved.
GCS_COMPACTION_RACE_ATTEMPTS = 5
GCS_COMPACTION_RACE_BACKOFF_SECONDS = 2.0


def _is_missing_segment_error(exc: Exception) -> bool:
    text = str(exc)
    return "FileNotFoundError" in text or "404" in text or "NoSuchKey" in text


def _fetch_gcs_once(
    cfg: FinelogConfig, prefix: str, window_lo_ms: int, window_hi_ms: int
) -> tuple[list[dict], set[int]]:
    fs, _ = fsspec.url_to_fs(cfg.remote_log_dir)
    conn = duckdb.connect()
    try:
        conn.register_filesystem(fs)
        _register_namespace_views(
            conn,
            cfg.remote_log_dir,
            ["log"],
            fs=fs,
            created_since_ms=window_lo_ms - GCS_CREATED_SINCE_PAD_MS,
            created_until_ms=window_hi_ms + GCS_CREATED_UNTIL_PAD_MS,
        )
        # _register_namespace_views skips the view entirely when the prune drops
        # every segment; referencing ``log`` then raises. Treat as nothing archived.
        if not conn.execute(
            "SELECT view_name FROM duckdb_views() WHERE view_name = 'log'"
        ).fetchall():
            return [], set()

        key_pred = _key_predicate(prefix)
        data_pred = _data_predicate()

        def run_page(last_seq: int) -> list[dict]:
            cur = conn.execute(_data_page_sql(key_pred, data_pred, last_seq))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

        rows = _paginate(run_page)
        cur = conn.execute(_bucket_sql(key_pred))
        buckets = {int(r[0]) for r in cur.fetchall()}
        return rows, buckets
    finally:
        conn.close()


def fetch_gcs(
    cfg: FinelogConfig, prefix: str, window_lo_ms: int, window_hi_ms: int
) -> tuple[list[dict], set[int]]:
    """Fetch filtered rows + per-minute coverage buckets from the GCS archive.

    Replicates ``finelog gcs-query`` in-process: a DuckDB ``log`` view over the
    archived parquet, time-pruned by object ``time_created`` (padded for L0->L1
    lag). Retries the compaction TOCTOU race (a listed segment 404s mid-read).
    Returns ``([], set())`` if no archived segments fall in the window.
    """
    if not cfg.remote_log_dir:
        return [], set()
    last_exc: Exception | None = None
    for attempt in range(GCS_COMPACTION_RACE_ATTEMPTS):
        try:
            return _fetch_gcs_once(cfg, prefix, window_lo_ms, window_hi_ms)
        except duckdb.Error as exc:
            if not _is_missing_segment_error(exc):
                raise
            last_exc = exc
            print(
                f"[gcs] segment vanished mid-read (compaction race), "
                f"retry {attempt + 1}/{GCS_COMPACTION_RACE_ATTEMPTS}",
                file=sys.stderr,
            )
            time.sleep(GCS_COMPACTION_RACE_BACKOFF_SECONDS)
    raise RuntimeError(
        f"GCS archive read kept racing finelog compaction after "
        f"{GCS_COMPACTION_RACE_ATTEMPTS} attempts: {last_exc}"
    )


def merge_dedup_rows(live_rows: list[dict], gcs_rows: list[dict]) -> list[dict]:
    """Union the two row sets, dedup on the monotonic ``seq``, sort by time.

    ``seq`` is identical in the live deque and its GCS-archived copy, so it is the
    canonical dedup key. Final order is ``(epoch_ms, seq)``.
    """
    by_seq: dict[int, dict] = {}
    for row in live_rows:
        by_seq[row["seq"]] = row
    for row in gcs_rows:
        by_seq.setdefault(row["seq"], row)
    return sorted(by_seq.values(), key=lambda r: (r["epoch_ms"], r["seq"]))


def _strip_attempt_suffix(key: str) -> str:
    """``/user/job/0:3`` -> ``/user/job/0`` (the task identity the parser expects).

    The trailing ``:<attempt_id>`` is what iris appends per attempt; the legacy
    ``iris job logs`` ``task=`` field carried the bare task id, so the downstream
    parser keys cycle detection on it.
    """
    head, _, tail = key.rpartition(":")
    if head and tail.isdigit():
        return head
    return key


def rows_to_filtered_lines(rows: list[dict]) -> list[str]:
    """Render merged finelog rows into the legacy ``[HH:MM:SS] task=<k> | <data>``.

    This is the exact text shape ``parse_log_lines`` consumes: the outer
    ``[HH:MM:SS]`` is ``epoch_ms`` in UTC, ``task=`` is the key with its attempt
    suffix stripped, and the body is the raw ``data``. Multi-line ``data`` is
    flattened so each emitted physical line still satisfies ``LINE_RE``.
    """
    out: list[str] = []
    for row in rows:
        ts = datetime.fromtimestamp(row["epoch_ms"] / 1000, tz=timezone.utc)
        task = _strip_attempt_suffix(row["key"])
        data = str(row["data"]).replace("\n", " ").replace("\r", " ")
        out.append(f"[{ts.strftime('%H:%M:%S')}] task={task} | {data}")
    return out


def check_coverage(
    attempts: list[Attempt],
    covered_buckets: set[int],
    now_ms: int,
    max_gap_seconds: float,
) -> list[MissingWindow]:
    """Assert each attempt window is covered with no empty run > ``max_gap_seconds``.

    A minute bucket is covered if EITHER source emitted a row in it. For a running
    attempt (``finished_at_ms`` is None) the window runs to ``now``, so a live
    outage that strands the recent-L0 tail (which GCS has not archived) surfaces
    as a trailing gap here.
    """
    missing: list[MissingWindow] = []
    for att in attempts:
        if att.started_at_ms is None:
            continue
        start = att.started_at_ms
        end = att.finished_at_ms if att.finished_at_ms is not None else now_ms
        if end <= start:
            continue
        lo_b = start // COVERAGE_BUCKET_MS
        hi_b = end // COVERAGE_BUCKET_MS
        worst_run = 0
        worst_span: tuple[int, int] | None = None
        run_start: int | None = None
        for b in range(lo_b, hi_b + 1):
            if b in covered_buckets:
                run_start = None
                continue
            if run_start is None:
                run_start = b
            run_len = b - run_start + 1
            if run_len > worst_run:
                worst_run = run_len
                worst_span = (run_start, b)
        if (
            worst_span is not None
            and worst_run * (COVERAGE_BUCKET_MS / 1000.0) > max_gap_seconds
        ):
            gap_start_ms = worst_span[0] * COVERAGE_BUCKET_MS
            gap_end_ms = (worst_span[1] + 1) * COVERAGE_BUCKET_MS
            missing.append(
                MissingWindow(
                    log_key=att.log_key,
                    window_start_ms=start,
                    window_end_ms=end,
                    gap_start_ms=gap_start_ms,
                    gap_end_ms=gap_end_ms,
                    gap_seconds=(gap_end_ms - gap_start_ms) / 1000.0,
                )
            )
    return missing


def acquire_complete_log(
    job_id: str,
    cluster: str,
    now_ms: int,
    cache_path: Path,
    coverage_cache_path: Path,
    refresh: bool,
    max_gap_seconds: float,
) -> LogAcquisition:
    """Fetch the COMPLETE filtered log + coverage verdict for ``job_id``.

    Caches the merged filtered lines and the coverage verdict so re-runs are
    instant; ``refresh`` re-fetches. The returned ``lines`` are in the legacy
    ``[HH:MM:SS] task=<key> | <data>`` shape ``parse_log_lines`` consumes.
    """
    if cache_path.exists() and coverage_cache_path.exists() and not refresh:
        print(f"[cache] reusing {cache_path}", file=sys.stderr)
        cov = json.loads(coverage_cache_path.read_text())
        return LogAcquisition(
            lines=cache_path.read_text().splitlines(),
            logs_complete=cov["logs_complete"],
            missing_windows=[MissingWindow(**w) for w in cov["missing_windows"]],
            live_available=cov["live_available"],
            live_unavailable_reason=cov.get("live_unavailable_reason"),
            live_rows=cov.get("live_rows", 0),
            gcs_rows=cov.get("gcs_rows", 0),
            merged_rows=cov.get("merged_rows", 0),
        )

    finelog_name = cluster  # finelog config name == iris cluster name
    cfg = load_finelog_config(finelog_name)
    prefix = job_id.rstrip("/")

    attempts, window_lo = enumerate_attempts(job_id)
    print(
        f"[enumerate] {len(attempts)} attempt(s) across the job tree; "
        f"window_lo={window_lo}",
        file=sys.stderr,
    )

    print("[live] fetching filtered rows + coverage buckets ...", file=sys.stderr)
    live_rows, live_buckets, live_available, live_reason = fetch_live(
        cfg, finelog_name, prefix
    )
    print(
        f"[live] available={live_available} filtered_rows={len(live_rows)} "
        f"buckets={len(live_buckets)}",
        file=sys.stderr,
    )

    print("[gcs] fetching filtered rows + coverage buckets ...", file=sys.stderr)
    gcs_rows, gcs_buckets = fetch_gcs(cfg, prefix, window_lo, now_ms)
    print(
        f"[gcs] filtered_rows={len(gcs_rows)} buckets={len(gcs_buckets)}",
        file=sys.stderr,
    )

    merged = merge_dedup_rows(live_rows, gcs_rows)
    covered_buckets = live_buckets | gcs_buckets
    print(
        f"[merge] live={len(live_rows)} + gcs={len(gcs_rows)} -> "
        f"deduped={len(merged)}; covered_minutes={len(covered_buckets)}",
        file=sys.stderr,
    )

    missing = check_coverage(attempts, covered_buckets, now_ms, max_gap_seconds)
    logs_complete = not missing
    if missing:
        print(
            f"[coverage] INCOMPLETE: {len(missing)} attempt window(s) uncovered",
            file=sys.stderr,
        )
        for w in missing:
            g0 = datetime.fromtimestamp(
                w.gap_start_ms / 1000, tz=timezone.utc
            ).isoformat()
            g1 = datetime.fromtimestamp(
                w.gap_end_ms / 1000, tz=timezone.utc
            ).isoformat()
            print(
                f"    {w.log_key}: {w.gap_seconds / 60:.1f}min gap [{g0} .. {g1}]",
                file=sys.stderr,
            )
    else:
        print(
            "[coverage] COMPLETE: every enumerated attempt window covered",
            file=sys.stderr,
        )

    lines = rows_to_filtered_lines(merged)
    cache_path.write_text("\n".join(lines) + ("\n" if lines else ""))
    coverage_cache_path.write_text(
        json.dumps(
            {
                "logs_complete": logs_complete,
                "missing_windows": [asdict(w) for w in missing],
                "live_available": live_available,
                "live_unavailable_reason": live_reason,
                "live_rows": len(live_rows),
                "gcs_rows": len(gcs_rows),
                "merged_rows": len(merged),
            },
            indent=2,
        )
    )
    return LogAcquisition(
        lines=lines,
        logs_complete=logs_complete,
        missing_windows=missing,
        live_available=live_available,
        live_unavailable_reason=live_reason,
        live_rows=len(live_rows),
        gcs_rows=len(gcs_rows),
        merged_rows=len(merged),
    )


# ---------- Log line parsing ----------


def parse_log_lines(
    filtered_lines: list[str], submitted_at: datetime
) -> tuple[list[tuple[datetime, str, str]], list[ServingSample]]:
    """Parse filtered lines into (timestamp, task, content) tuples + serving samples.

    The iris ``[HH:MM:SS]`` outer prefix has no date, so we walk lines in order
    and bump a day-counter whenever HH:MM:SS goes backwards. The starting day is
    ``submitted_at``'s UTC date.

    For lines containing the vLLM throughput emission, we use the embedded
    ``MM-DD HH:MM:SS`` as the authoritative timestamp (still year-less but
    dated).

    For lines containing the rendezvous-polling ``min written_at <epoch_s>``, we
    use that epoch.
    """
    parsed: list[tuple[datetime, str, str]] = []
    samples: list[ServingSample] = []
    cur_date = submitted_at.astimezone(timezone.utc).date()
    last_hms: tuple[int, int, int] | None = None

    for line in filtered_lines:
        m = LINE_RE.match(line)
        if not m:
            continue
        hh, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3))
        task = m.group(4)
        content = m.group(5)

        # day-rollover via monotonic HH:MM:SS
        hms = (hh, mm, ss)
        if last_hms is not None and hms < last_hms:
            # going backwards by > 12 hours => assume day-rollover. The iris log
            # stream isn't perfectly ordered task-to-task; small backward jumps
            # within a minute are normal. So only roll the day if we went
            # backward by a lot.
            secs_now = hh * 3600 + mm * 60 + ss
            secs_prev = last_hms[0] * 3600 + last_hms[1] * 60 + last_hms[2]
            if secs_prev - secs_now > 12 * 3600:
                cur_date = cur_date + timedelta(days=1)
        last_hms = hms

        outer_ts = datetime(
            cur_date.year,
            cur_date.month,
            cur_date.day,
            hh,
            mm,
            ss,
            tzinfo=timezone.utc,
        )

        # Prefer embedded epoch (rendezvous lines)
        ts = outer_ts
        rm = RENDEZVOUS_RE.search(content)
        if rm:
            ts = datetime.fromtimestamp(int(rm.group(1)), tz=timezone.utc)

        tm = THROUGHPUT_RE.search(content)
        if tm:
            # Use embedded MM-DD HH:MM:SS (no year). Anchor year to outer_ts.year
            # to disambiguate at year boundaries; that's the right year for both
            # of these jobs.
            mo, dy = int(tm.group(1)), int(tm.group(2))
            th, tmin, tsec = int(tm.group(3)), int(tm.group(4)), int(tm.group(5))
            try:
                ts = datetime(
                    outer_ts.year, mo, dy, th, tmin, tsec, tzinfo=timezone.utc
                )
            except ValueError:
                ts = outer_ts
            samples.append(
                ServingSample(
                    ts=ts,
                    prompt_tps=float(tm.group(6)),
                    gen_tps=float(tm.group(7)),
                    running=int(tm.group(8)),
                    waiting=int(tm.group(9)),
                )
            )

        parsed.append((ts, task, content))

    parsed.sort(key=lambda x: x[0])
    samples.sort(key=lambda s: s.ts)
    return parsed, samples


def build_cycles(
    job_id: str,
    parsed: list[tuple[datetime, str, str]],
    samples: list[ServingSample],
    end_time: datetime,
) -> list[Cycle]:
    """Build cycle list from APPLIED markers on task=0.

    Each task=0 'tpu-inference-patch] APPLIED:' line marks the boot of a fresh
    attempt on rank 0. There are several APPLIED lines per boot (one per patch
    applied); we take the FIRST per boot via clustering by proximity.
    """
    task0 = f"{job_id}/0"
    cycle_starts: list[datetime] = []
    last_boundary: datetime | None = None
    for ts, task, content in parsed:
        if task != task0:
            continue
        if not PATCH_APPLIED_RE.search(content):
            continue
        # cluster: only count the first APPLIED line within a 60s window
        if last_boundary is None or (ts - last_boundary).total_seconds() > 60:
            cycle_starts.append(ts)
        last_boundary = ts

    cycles: list[Cycle] = []
    for i, start in enumerate(cycle_starts):
        end = cycle_starts[i + 1] if i + 1 < len(cycle_starts) else end_time
        duration_s = (end - start).total_seconds()
        # serving samples in this cycle
        in_cycle = [s for s in samples if start <= s.ts < end]
        did_serve = len(in_cycle) > 0
        first_serve = None
        if did_serve:
            first_serve = (in_cycle[0].ts - start).total_seconds()
        cycles.append(
            Cycle(
                idx=i,
                cycle_start=start,
                cycle_end=end,
                did_serve=did_serve,
                time_to_first_serve_s=first_serve,
                duration_s=duration_s,
                serving_samples_in_cycle=len(in_cycle),
            )
        )

    # tag samples with cycle_idx + elapsed_in_cycle
    for sample in samples:
        for cycle in cycles:
            if cycle.cycle_start <= sample.ts < cycle.cycle_end:
                sample.cycle_idx = cycle.idx
                sample.elapsed_in_cycle_s = (
                    sample.ts - cycle.cycle_start
                ).total_seconds()
                break

    return cycles


# ---------- GCS / harbor trial parsing ----------


def list_trial_trajectories(job_name: str, job_output_dir: str) -> list[TrialStatus]:
    """Return TrialStatus for every trial dir (with or without trajectory.json).

    ``job_output_dir`` is the job's recorded OUTER ``.../ot-agent/<job>`` prefix
    (from :func:`resolve_job_output_dir`), so legacy multi-region jobs and new
    single-region jobs both read from the correct bucket. We do this in two passes:
      (a) list trial dirs (cheap, one listing)
      (b) list trajectory.json files with mtime+size (one recursive ls)
    Then we join.
    """
    root = f"{job_output_dir}/{job_name}"

    # (a) all trial dirs. Tolerate the dir not existing — that happens when
    # the job has never reached SERVING + harbor never wrote a single trial
    # (e.g., preempt-storm before first compile finishes). Treat as zero
    # trials.
    cmd = ["gsutil", "ls", f"{root}/"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        if "matched no objects" in (proc.stderr or "").lower():
            return []
        # Any other gsutil failure (auth, network) — surface it.
        raise subprocess.CalledProcessError(
            proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr
        )
    trial_dirs: list[str] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.endswith("/"):
            continue
        if line.endswith(f"/{job_name}/"):
            continue  # root self
        trial_name = line.rstrip("/").rsplit("/", 1)[-1]
        if trial_name.startswith("_"):
            continue
        trial_dirs.append(trial_name)

    # (b) trajectory.json files
    cmd = ["gsutil", "ls", "-l", f"{root}/**/agent/trajectory.json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    traj_info: dict[str, tuple[datetime, int]] = {}
    # gsutil ls -l format: "<size> <YYYY-MM-DDTHH:MM:SSZ> <gs://...>"
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3 or not parts[-1].startswith("gs://"):
            continue
        size_s, mtime_s, path = parts[0], parts[1], parts[-1]
        try:
            size = int(size_s)
        except ValueError:
            continue
        try:
            mtime = datetime.strptime(mtime_s, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
        # path like ../<trial_name>/agent/trajectory.json
        parts2 = path.split("/")
        if len(parts2) < 3:
            continue
        # find 'agent' index
        try:
            agent_idx = parts2.index("agent")
        except ValueError:
            continue
        trial_name = parts2[agent_idx - 1]
        traj_info[trial_name] = (mtime, size)

    out: list[TrialStatus] = []
    for name in trial_dirs:
        if name in traj_info:
            mtime, size = traj_info[name]
            out.append(TrialStatus(name, True, mtime, size))
        else:
            out.append(TrialStatus(name, False, None, 0))
    return out


def fetch_harbor_result(job_name: str, job_output_dir: str) -> dict | None:
    """Cat <job_output_dir>/<job_name>/result.json.

    ``job_output_dir`` is the job's recorded OUTER ``.../ot-agent/<job>`` prefix
    (from :func:`resolve_job_output_dir`). result.json is mutated in place by
    harbor on a remote worker; a `gsutil cat` that races a write can return a
    truncated payload that fails to parse. Retry briefly on the transient failure
    modes (gsutil non-zero exit, JSONDecodeError) and return None on persistent
    failure so the caller degrades without harbor stats rather than aborting the
    whole run.
    """
    path = f"{job_output_dir}/{job_name}/result.json"
    for attempt in range(HARBOR_FETCH_ATTEMPTS):
        proc = subprocess.run(["gsutil", "cat", path], capture_output=True, text=True)
        if proc.returncode == 0:
            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError:
                pass
        if attempt < len(HARBOR_FETCH_BACKOFFS):
            time.sleep(HARBOR_FETCH_BACKOFFS[attempt])
    print(
        f"[{job_name}] WARNING: result.json unreadable after {HARBOR_FETCH_ATTEMPTS} "
        "attempts (truncated/mid-update read or gsutil failure); skipping harbor stats",
        file=sys.stderr,
    )
    return None


# ---------- Stats helpers ----------


def pct(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * q
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def stats_dict(values: list[float]) -> dict[str, float]:
    if not values:
        return {
            k: float("nan")
            for k in (
                "n",
                "mean",
                "median",
                "p10",
                "p25",
                "p50",
                "p75",
                "p90",
                "p99",
                "min",
                "max",
            )
        }
    return {
        "n": float(len(values)),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p10": pct(values, 0.10),
        "p25": pct(values, 0.25),
        "p50": pct(values, 0.50),
        "p75": pct(values, 0.75),
        "p90": pct(values, 0.90),
        "p99": pct(values, 0.99),
        "min": min(values),
        "max": max(values),
    }


# ---------- Report rendering ----------


def fmt_duration(seconds: float) -> str:
    if seconds < 0 or seconds != seconds:  # NaN
        return "n/a"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:d}h{m:02d}m{s:02d}s"


def fmt_pct(x: float) -> str:
    if x != x:
        return "n/a"
    return f"{100 * x:.1f}%"


def render_markdown(a: JobAnalysis, warmup_seconds: float) -> str:
    lines: list[str] = []
    lines.append(f"# Iris job history analysis: `{a.job_id}`")
    lines.append("")
    lines.append(f"- **submitted_at**: {a.submitted_at.isoformat()}")
    lines.append(f"- **started_at**: {a.started_at.isoformat()}")
    lines.append(f"- **current_time** (analysis): {a.current_time.isoformat()}")
    lines.append(f"- **total_runtime**: {fmt_duration(a.total_runtime_s)}")
    lines.append(f"- **state**: {a.state} (3=RUNNING)")
    if a.logs_complete:
        lines.append("- **logs_complete**: true (every attempt window covered)")
    else:
        lines.append(
            f"- **logs_complete**: FALSE — {len(a.missing_windows)} uncovered "
            "window(s); stats below may be partial:"
        )
        for w in a.missing_windows:
            g0 = datetime.fromtimestamp(
                w.gap_start_ms / 1000, tz=timezone.utc
            ).isoformat()
            g1 = datetime.fromtimestamp(
                w.gap_end_ms / 1000, tz=timezone.utc
            ).isoformat()
            lines.append(
                f"    - `{w.log_key}`: {w.gap_seconds / 60:.1f}min gap [{g0} .. {g1}]"
            )
    lines.append("")

    # §1
    lines.append("## §1 Preemption analysis")
    lines.append("")
    n_cycles = len(a.cycles)
    n_serving = sum(1 for c in a.cycles if c.did_serve)
    n_dead_in_compile = n_cycles - n_serving
    lines.append(
        f"- **cycles detected (log-derived)**: {n_cycles} "
        f"(=> preempts from log = {a.preempt_count_from_log})"
    )
    lines.append(f"- **iris job summary preemptions=**: {a.iris_preemption_count}")
    if (
        a.iris_preemption_count is not None
        and a.iris_preemption_count != a.preempt_count_from_log
    ):
        lines.append(
            f"  - **discrepancy**: log shows {a.preempt_count_from_log}, "
            f"iris shows {a.iris_preemption_count} "
            f"(diff={a.preempt_count_from_log - a.iris_preemption_count})"
        )
    lines.append(f"- **cycles that reached SERVING**: {n_serving}")
    lines.append(
        f"- **cycles that died in compile (no throughput emission)**: {n_dead_in_compile}"
    )
    lines.append("")
    serving_durations = [c.duration_s for c in a.cycles if c.did_serve]
    first_serve = [
        c.time_to_first_serve_s
        for c in a.cycles
        if c.did_serve and c.time_to_first_serve_s is not None
    ]
    if serving_durations:
        sd_stats = stats_dict(serving_durations)
        lines.append("### Serving-cycle survival time (cycles that did_serve)")
        lines.append("")
        lines.append(f"- mean: {fmt_duration(sd_stats['mean'])}")
        lines.append(f"- median: {fmt_duration(sd_stats['median'])}")
        lines.append(
            f"- p25 / p75: {fmt_duration(sd_stats['p25'])} / {fmt_duration(sd_stats['p75'])}"
        )
        lines.append(f"- max: {fmt_duration(sd_stats['max'])}")
        lines.append("")
    if first_serve:
        fs_stats = stats_dict(first_serve)
        lines.append("### Time-to-first-serve (cold compile cost)")
        lines.append("")
        lines.append(f"- mean: {fmt_duration(fs_stats['mean'])}")
        lines.append(f"- median: {fmt_duration(fs_stats['median'])}")
        lines.append("")

    # cycle table (top 30 + bottom 5 if huge)
    lines.append("### Per-cycle table")
    lines.append("")
    lines.append(
        "| idx | cycle_start (UTC) | duration | did_serve | t_first_serve | samples | trials_finalized | cumulative_trials |"
    )
    lines.append(
        "|-----|--------------------|----------|-----------|---------------|---------|------------------|-------------------|"
    )
    cum_trials = 0
    for c in a.cycles:
        cum_trials += c.non_empty_trials_in_cycle
        tfs = (
            fmt_duration(c.time_to_first_serve_s)
            if c.time_to_first_serve_s is not None
            else "—"
        )
        lines.append(
            f"| {c.idx} | {c.cycle_start.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"{fmt_duration(c.duration_s)} | {c.did_serve} | {tfs} | "
            f"{c.serving_samples_in_cycle} | {c.non_empty_trials_in_cycle} | {cum_trials} |"
        )
    lines.append("")

    # §2
    lines.append("## §2 Trace progress")
    lines.append("")
    lines.append(f"- **harbor n_total_trials**: {a.harbor_n_total_trials}")
    lines.append(
        f"- **harbor n_completed_trials**: {a.harbor_n_completed} (includes errored)"
    )
    lines.append(f"- **harbor n_errored_trials**: {a.harbor_n_errored}")
    lines.append(f"- **harbor n_running_trials**: {a.harbor_n_running}")
    lines.append(f"- **harbor n_pending_trials**: {a.harbor_n_pending}")
    lines.append(f"- **harbor started_at**: {a.harbor_started_at}")
    lines.append(f"- **harbor updated_at**: {a.harbor_updated_at}")
    lines.append("")
    lines.append(f"- **trial dirs on GCS**: {a.total_trial_dirs}")
    lines.append(
        f"- **non-empty trials (trajectory.json exists)**: {a.non_empty_trials}"
    )
    empty = a.total_trial_dirs - a.non_empty_trials
    empty_rate = (empty / a.total_trial_dirs) if a.total_trial_dirs else float("nan")
    lines.append(f"- **empty trials (no trajectory.json)**: {empty}")
    lines.append(f"- **empty-rate**: {fmt_pct(empty_rate)}")
    lines.append("")
    if a.harbor_exception_stats:
        lines.append("### Harbor exception breakdown")
        lines.append("")
        for k, v in sorted(a.harbor_exception_stats.items(), key=lambda kv: -kv[1]):
            lines.append(f"- {k}: {v}")
        lines.append("")

    # §3
    lines.append("## §3 Serving stats")
    lines.append("")
    all_samples = a.serving_samples
    lines.append(f"- **total serving samples emitted**: {len(all_samples)}")
    lines.append("")
    if all_samples:
        gen_full = [s.gen_tps for s in all_samples]
        prompt_full = [s.prompt_tps for s in all_samples]
        running_full = [float(s.running) for s in all_samples]
        waiting_full = [float(s.waiting) for s in all_samples]
        sat_full = sum(1 for s in all_samples if s.waiting > 0) / len(all_samples)

        gen_warm = [
            s.gen_tps for s in all_samples if s.elapsed_in_cycle_s >= warmup_seconds
        ]
        prompt_warm = [
            s.prompt_tps for s in all_samples if s.elapsed_in_cycle_s >= warmup_seconds
        ]
        running_warm = [
            float(s.running)
            for s in all_samples
            if s.elapsed_in_cycle_s >= warmup_seconds
        ]
        waiting_warm = [
            float(s.waiting)
            for s in all_samples
            if s.elapsed_in_cycle_s >= warmup_seconds
        ]
        sat_warm = sum(
            1
            for s in all_samples
            if s.elapsed_in_cycle_s >= warmup_seconds and s.waiting > 0
        ) / max(len(gen_warm), 1)

        def render(
            label: str,
            gen: list[float],
            prompt: list[float],
            running: list[float],
            waiting: list[float],
            sat: float,
        ) -> None:
            lines.append(f"### {label}")
            lines.append("")
            g = stats_dict(gen)
            p = stats_dict(prompt)
            r = stats_dict(running)
            w = stats_dict(waiting)
            lines.append(f"- samples: {int(g['n'])}")
            lines.append(
                f"- gen_tps: mean={g['mean']:.1f}, median={g['median']:.1f}, "
                f"p10={g['p10']:.1f}, p50={g['p50']:.1f}, p90={g['p90']:.1f}, "
                f"p99={g['p99']:.1f}, peak={g['max']:.1f}, min={g['min']:.1f}"
            )
            lines.append(f"- prompt_tps: mean={p['mean']:.1f}, peak={p['max']:.1f}")
            lines.append(f"- running: mean={r['mean']:.2f}, peak={int(r['max'])}")
            lines.append(f"- waiting: mean={w['mean']:.2f}, peak={int(w['max'])}")
            lines.append(f"- saturation rate (waiting>0): {fmt_pct(sat)}")
            lines.append("")

        render(
            "Full (all samples)",
            gen_full,
            prompt_full,
            running_full,
            waiting_full,
            sat_full,
        )
        render(
            f"Warmup-excluded (elapsed_in_cycle >= {warmup_seconds:.0f}s)",
            gen_warm,
            prompt_warm,
            running_warm,
            waiting_warm,
            sat_warm,
        )

        if gen_full and gen_warm:
            full_mean = statistics.fmean(gen_full)
            warm_mean = statistics.fmean(gen_warm)
            diff_pct = abs(full_mean - warm_mean) / full_mean if full_mean else 0
            if diff_pct < 0.05:
                lines.append(
                    f"_Warmup exclusion changed gen_tps mean by {fmt_pct(diff_pct)} — "
                    f"warmup did not meaningfully bias the all-samples stats._"
                )
            else:
                lines.append(
                    f"_Warmup exclusion changed gen_tps mean by {fmt_pct(diff_pct)} "
                    f"(full={full_mean:.1f}, warm={warm_mean:.1f}) — the first "
                    f"{int(warmup_seconds)}s of each cycle pulls the mean down._"
                )
            lines.append("")

    # bottom-line
    lines.append("## Bottom line")
    lines.append("")
    productive = a.non_empty_trials
    pre = a.preempt_count_from_log
    runtime_h = a.total_runtime_s / 3600.0
    lines.append(
        f"Over **{runtime_h:.1f} hours** of runtime, the job survived **{pre} preempts** "
        f"({n_serving}/{n_cycles} cycles reached the serving phase) and produced "
        f"**{productive} non-empty trial trajectories** out of "
        f"{a.total_trial_dirs} trial dirs "
        f"(empty-rate {fmt_pct(empty_rate)})."
    )
    if a.iris_preemption_count is not None and a.iris_preemption_count != pre:
        lines.append(
            f"Note: iris reports preemptions={a.iris_preemption_count}, log shows "
            f"{pre}. Pick the more trustworthy depending on the discrepancy "
            f"magnitude (log can miss a boundary if the cycle aborted before "
            f"tpu-inference-patch fired)."
        )
    lines.append("")
    return "\n".join(lines)


def analysis_to_json(a: JobAnalysis) -> dict:
    """Serialise JobAnalysis to a JSON-safe dict (datetimes as ISO strings)."""

    def _conv(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return {k: _conv(v) for k, v in asdict(obj).items()}
        if isinstance(obj, list):
            return [_conv(x) for x in obj]
        if isinstance(obj, dict):
            return {k: _conv(v) for k, v in obj.items()}
        return obj

    return {
        "job_id": a.job_id,
        "job_name": a.job_name,
        "submitted_at": a.submitted_at.isoformat(),
        "started_at": a.started_at.isoformat(),
        "current_time": a.current_time.isoformat(),
        "total_runtime_s": a.total_runtime_s,
        "iris_preemption_count": a.iris_preemption_count,
        "preempt_count_from_log": a.preempt_count_from_log,
        "state": a.state,
        "cycles": [
            {
                "idx": c.idx,
                "cycle_start": c.cycle_start.isoformat(),
                "cycle_end": c.cycle_end.isoformat(),
                "duration_s": c.duration_s,
                "did_serve": c.did_serve,
                "time_to_first_serve_s": c.time_to_first_serve_s,
                "serving_samples_in_cycle": c.serving_samples_in_cycle,
                "non_empty_trials_in_cycle": c.non_empty_trials_in_cycle,
            }
            for c in a.cycles
        ],
        "total_trial_dirs": a.total_trial_dirs,
        "non_empty_trials": a.non_empty_trials,
        "harbor_n_completed": a.harbor_n_completed,
        "harbor_n_errored": a.harbor_n_errored,
        "harbor_n_running": a.harbor_n_running,
        "harbor_n_pending": a.harbor_n_pending,
        "harbor_n_total_trials": a.harbor_n_total_trials,
        "harbor_exception_stats": a.harbor_exception_stats,
        "harbor_started_at": a.harbor_started_at,
        "harbor_updated_at": a.harbor_updated_at,
        "serving_samples_count": len(a.serving_samples),
        # Don't dump the full sample stream; keep summary
        "serving_summary": _summarise_samples(a.serving_samples),
        # Completeness contract: whether every enumerated attempt window was
        # covered by the merged LIVE u GCS log, and the gaps if not.
        "logs_complete": a.logs_complete,
        "missing_windows": [asdict(w) for w in a.missing_windows],
    }


def _summarise_samples(samples: list[ServingSample]) -> dict:
    if not samples:
        return {}
    return {
        "gen_tps": stats_dict([s.gen_tps for s in samples]),
        "prompt_tps": stats_dict([s.prompt_tps for s in samples]),
        "running": stats_dict([float(s.running) for s in samples]),
        "waiting": stats_dict([float(s.waiting) for s in samples]),
        "saturation_rate": sum(1 for s in samples if s.waiting > 0) / len(samples),
    }


# ---------- Main ----------


def analyze(
    job_id: str,
    output: Path,
    refresh: bool,
    warmup_seconds: float,
    max_gap_seconds: float,
    allow_incomplete: bool,
    bundle_directory: Path | None = None,
) -> JobAnalysis:
    job_name = job_id.rsplit("/", 1)[-1]
    # Resolve the Harbor datagen/eval job's recorded output prefix ONCE
    # (registry-first, iris-fallback via --cluster). Legacy multi-region jobs
    # resolve to gs://marin-models-{us,eu} and new single-region jobs to
    # gs://marin-<region>; the GCS readers below use this exact bucket instead of
    # a hardcoded scan root.
    job_output_dir = resolve_job_output_dir(job_id, cluster_config=CLUSTER)
    print(f"[{job_name}] output dir: {job_output_dir}", file=sys.stderr)
    meta = get_job_metadata(job_id)
    submitted_at = datetime.fromtimestamp(
        meta["submitted_at_ms"] / 1000, tz=timezone.utc
    )
    started_at = datetime.fromtimestamp(meta["started_at_ms"] / 1000, tz=timezone.utc)
    state = meta["state"]
    now = datetime.now(timezone.utc)
    total_runtime = (now - submitted_at).total_seconds()
    print(
        f"[{job_name}] submitted={submitted_at.isoformat()}, "
        f"runtime={total_runtime / 3600:.1f}h, state={state}",
        file=sys.stderr,
    )

    iris_preempts = get_job_summary_preemptions(job_id)
    print(f"[{job_name}] iris preemptions={iris_preempts}", file=sys.stderr)

    cache_path = Path(f"/tmp/iris_history_{job_name}.filtered.log")
    coverage_cache_path = Path(f"/tmp/iris_history_{job_name}.coverage.json")
    end_ms = int(now.timestamp() * 1000)
    acq = acquire_complete_log(
        job_id,
        cluster=CLUSTER,
        now_ms=end_ms,
        cache_path=cache_path,
        coverage_cache_path=coverage_cache_path,
        refresh=refresh,
        max_gap_seconds=max_gap_seconds,
    )
    if bundle_directory is not None:
        bundle_directory.mkdir(parents=True, exist_ok=True)
        (bundle_directory / "finelog.log").write_text("\n".join(acq.lines) + "\n")
        (bundle_directory / "finelog.coverage.json").write_text(
            json.dumps(
                {
                    "logs_complete": acq.logs_complete,
                    "missing_windows": [
                        asdict(window) for window in acq.missing_windows
                    ],
                    "live_available": acq.live_available,
                    "live_unavailable_reason": acq.live_unavailable_reason,
                    "live_rows": acq.live_rows,
                    "gcs_rows": acq.gcs_rows,
                    "merged_rows": acq.merged_rows,
                },
                indent=2,
            )
            + "\n"
        )
    if not acq.logs_complete and not allow_incomplete:
        details = "\n".join(
            f"    {w.log_key}: {w.gap_seconds / 60:.1f}min uncovered "
            f"[{datetime.fromtimestamp(w.gap_start_ms / 1000, tz=timezone.utc).isoformat()} .. "
            f"{datetime.fromtimestamp(w.gap_end_ms / 1000, tz=timezone.utc).isoformat()}]"
            for w in acq.missing_windows
        )
        live_note = (
            ""
            if acq.live_available
            else "\n  LIVE finelog was unavailable "
            f"({acq.live_unavailable_reason}); run `marin-login login {CLUSTER}` "
            "to cover the recent-L0 window."
        )
        raise RuntimeError(
            f"INCOMPLETE LOG for {job_id}: {len(acq.missing_windows)} attempt window(s) "
            f"are uncovered (no rows for > {max_gap_seconds:.0f}s):\n{details}{live_note}\n"
            "Refusing to write a 'successful' report. Pass --allow-incomplete to override."
        )
    filtered = acq.lines
    parsed, samples = parse_log_lines(filtered, submitted_at)
    print(
        f"[{job_name}] parsed lines={len(parsed)}, samples={len(samples)}",
        file=sys.stderr,
    )

    cycles = build_cycles(job_id, parsed, samples, end_time=now)
    print(f"[{job_name}] cycles detected: {len(cycles)}", file=sys.stderr)

    # GCS trial inspection
    trials = list_trial_trajectories(job_name, job_output_dir)
    non_empty = [t for t in trials if t.has_trajectory]
    print(
        f"[{job_name}] trial dirs={len(trials)}, non_empty={len(non_empty)}",
        file=sys.stderr,
    )

    # Assign non-empty trials to cycles by trajectory mtime
    for c in cycles:
        c.non_empty_trials_in_cycle = sum(
            1
            for t in non_empty
            if t.trajectory_mtime is not None
            and c.cycle_start <= t.trajectory_mtime < c.cycle_end
        )

    # Harbor result.json
    harbor = fetch_harbor_result(job_name, job_output_dir)
    if bundle_directory is not None and harbor is not None:
        harbor_directory = bundle_directory / "harbor"
        harbor_directory.mkdir(parents=True, exist_ok=True)
        (harbor_directory / "result.json").write_text(
            json.dumps(harbor, indent=2) + "\n"
        )
    a = JobAnalysis(
        job_id=job_id,
        job_name=job_name,
        submitted_at=submitted_at,
        started_at=started_at,
        current_time=now,
        total_runtime_s=total_runtime,
        iris_preemption_count=iris_preempts,
        state=state,
        cycles=cycles,
        preempt_count_from_log=max(len(cycles) - 1, 0),
        serving_samples=samples,
        total_trial_dirs=len(trials),
        non_empty_trials=len(non_empty),
        logs_complete=acq.logs_complete,
        missing_windows=acq.missing_windows,
    )
    if harbor:
        stats = harbor.get("stats", {})
        a.harbor_n_completed = stats.get("n_completed_trials", 0)
        a.harbor_n_errored = stats.get("n_errored_trials", 0)
        a.harbor_n_running = stats.get("n_running_trials", 0)
        a.harbor_n_pending = stats.get("n_pending_trials", 0)
        a.harbor_n_total_trials = harbor.get("n_total_trials", 0)
        a.harbor_started_at = harbor.get("started_at")
        a.harbor_updated_at = harbor.get("updated_at")
        evals = stats.get("evals", {})
        for _ev_name, ev_data in evals.items():
            es = ev_data.get("exception_stats", {})
            for k, vs in es.items():
                a.harbor_exception_stats[k] = a.harbor_exception_stats.get(k, 0) + len(
                    vs
                )

    return a


def local_bundle_report(bundle_directory: Path, manifest: dict) -> str:
    """Render a useful report from a previously synchronized Harbor bundle only."""
    result_path = bundle_directory / "harbor" / "result.json"
    result: dict = {}
    if result_path.exists():
        try:
            result = json.loads(result_path.read_text())
        except json.JSONDecodeError:
            result = {}
    stats = result.get("stats", {})
    errors: dict[str, int] = {}
    for evaluation in stats.get("evals", {}).values():
        for name, trial_ids in evaluation.get("exception_stats", {}).items():
            errors[name] = errors.get(name, 0) + len(trial_ids)
    log_path = bundle_directory / "finelog.log"
    log_lines = (
        log_path.read_text(errors="replace").splitlines() if log_path.exists() else []
    )
    lines = [
        f"# Iris Harbor job analysis — {manifest.get('job_id', 'unknown')}",
        "",
        "This report used the local evidence bundle only.",
        "",
        f"- Cluster: `{manifest.get('cluster', 'unknown')}`",
        f"- Job kind: `{manifest.get('job_kind', 'unknown')}`",
        f"- Bundle: `{bundle_directory}`",
        f"- Dataset: `{manifest.get('dataset', 'unknown')}`",
        f"- Completed trials: {stats.get('n_completed_trials', 'unknown')}/{result.get('n_total_trials', 'unknown')}",
        f"- Errored trials: {stats.get('n_errored_trials', 'unknown')}",
        f"- Exception counts: {json.dumps(errors, sort_keys=True) if errors else 'none recorded'}",
        f"- Local Finelog lines: {len(log_lines):,}",
        "",
        "## Finelog tail",
        "",
        "```text",
        "\n".join(log_lines[-30:]) or "No local Finelog was available.",
        "```",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "job_id", help="iris job id, e.g. /benjaminfeuer/qwen122b-q12-v1-..."
    )
    ap.add_argument(
        "--output", type=Path, help="markdown report path (defaults inside the bundle)"
    )
    ap.add_argument("--bundle-root", type=Path, default=DEFAULT_BUNDLE_ROOT)
    ap.add_argument(
        "--local-only",
        action="store_true",
        help="Analyze a synchronized bundle without querying Iris, Finelog, or GCS.",
    )
    ap.add_argument(
        "--resync",
        action="store_true",
        help="Ignore the local Finelog cache while refreshing remote evidence.",
    )
    ap.set_defaults(resync=True)
    ap.add_argument("--warmup-seconds", type=float, default=180.0)
    ap.add_argument(
        "--cluster",
        default="marin",
        help=(
            "iris cluster to target (default: marin/TPU). For CoreWeave GPU "
            "jobs pass 'cw-us-east-02a' (requires KUBECONFIG=~/.kube/"
            "coreweave-iris-gpu in the environment)."
        ),
    )
    ap.add_argument(
        "--iris-bin",
        default=None,
        help=(
            "Path to the iris binary. Default: auto-resolve ($IRIS_BIN env, then "
            "iris on PATH, then the otagent-env iris, then the marin .venv iris). "
            "The marin .venv iris CANNOT drive CoreWeave (broken kubernetes "
            "import), so for cw-* pass the otagent-env iris or leave default."
        ),
    )
    ap.add_argument(
        "--gsutil-sample",
        type=int,
        default=0,
        help="(unused, accepted for compat) cap GCS trial inspection",
    )
    ap.add_argument(
        "--max-coverage-gap-seconds",
        type=float,
        default=DEFAULT_MAX_COVERAGE_GAP_SECONDS,
        help=(
            "Max run of consecutive empty minutes tolerated inside an attempt "
            "window before it is flagged uncovered (completeness check)."
        ),
    )
    ap.add_argument(
        "--allow-incomplete",
        action="store_true",
        help=(
            "Opt out of the strict completeness contract: write the report even "
            "if some attempt window is uncovered (default: fail loudly)."
        ),
    )
    args = ap.parse_args()

    # Wire cluster + binary into the module globals the helpers read.
    global CLUSTER, IRIS_BIN
    CLUSTER = args.cluster
    if args.iris_bin:
        IRIS_BIN = args.iris_bin

    bundle = job_bundle(args.bundle_root, args.cluster, args.job_id)
    output = args.output or bundle.directory / "reports" / "analysis.md"
    output.parent.mkdir(parents=True, exist_ok=True)

    if args.local_only:
        if not bundle.directory.exists():
            print(f"No local bundle exists at {bundle.directory}", file=sys.stderr)
            return 1
        output.write_text(
            local_bundle_report(bundle.directory, load_bundle_manifest(bundle))
        )
        print(f"\nReport written to: {output}", file=sys.stderr)
        return 0

    try:
        a = analyze(
            args.job_id,
            output,
            args.resync,
            args.warmup_seconds,
            max_gap_seconds=args.max_coverage_gap_seconds,
            allow_incomplete=args.allow_incomplete,
            bundle_directory=bundle.directory,
        )
    except LookupError as e:
        # Expected for a non-Harbor job (for example CoreWeave RL with an s3://
        # trials_dir) or a legacy Harbor eval with no recorded output identity.
        # Keep the taxonomy clear instead of dumping a traceback.
        print(f"[analyze_iris_harbor_job] {e}", file=sys.stderr)
        return 1

    md = render_markdown(a, warmup_seconds=args.warmup_seconds)
    output.write_text(md)

    json_path = output.with_suffix(output.suffix + ".json")
    json_path.write_text(json.dumps(analysis_to_json(a), indent=2))
    write_bundle_manifest(
        bundle,
        {
            "kind": "harbor",
            "last_analysis_at": datetime.now(timezone.utc).isoformat(),
            "last_analysis_report": str(output),
        },
    )

    print(f"\nReport written to: {output}", file=sys.stderr)
    print(f"JSON sidecar:     {json_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
