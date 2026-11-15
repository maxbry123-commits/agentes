"""Resolve an iris job's recorded GCS output directory.

Every GCS-mode submission records its output URI in two places: the local
registry (``~/.ot-agent/state/iris_jobs.db``) and the iris controller's baked
worker command (``job_config.entrypoint_json``). Readers (analysis scripts,
rescue skills) must learn a job's output bucket from that RECORDED URI, never
from a hardcoded scan bucket — old jobs recorded a multi-region bucket
(``gs://marin-models-{us,eu}``) and new jobs record a co-located single-region
bucket (``gs://marin-us-east5``, ...). Resolving from the recorded URI returns
the correct bucket for BOTH, which is what makes the single-region output
migration flag-day-free.

Resolution order:

1. Local registry — authoritative for anything launched from this host (the
   operational path: the cron launches from one operator laptop).
2. Iris fallback — for cross-host jobs, parse the OUTER output dir out of the
   job's baked worker command. Requires a ``cluster_config``.

If neither yields a URI we FAIL FAST rather than guess a bucket.

CLI::

    python -m hpc.iris.job_output_resolver <job_ref> [--cluster <cfg>]
"""

from __future__ import annotations

import argparse
import re
import sys

from hpc.iris.regions import _iris_query
from hpc.iris_job_registry import get, get_latest_by_job_name


# The datagen/eval worker command bakes the OUTER `.../ot-agent/<job>/` output
# prefix as harbor's ``--jobs-dir`` (and run_eval's ``--experiments_dir``); the
# launcher-level ``--gcs-output-dir`` carries the same value. Match any of them
# so the resolver works across job types. ``gs://[^\s"']+`` stops at the JSON
# string / shell boundary so a trailing quote or space is not captured.
_OUTPUT_ARG_RE = re.compile(
    r"--(?:jobs[-_]dir|gcs[-_]output[-_]dir|experiments[-_]dir)[= ]+(gs://[^\s\"']+)"
)


def _bare_job_name(job_ref: str) -> str:
    """Strip any leading ``/<user>/`` prefix from an iris job reference.

    The local registry keys on the bare job name (``tracegen-iris-...``); the
    iris controller keys on the fully-qualified id (``/benjaminfeuer/tracegen-iris-...``).
    Accept either form on input.
    """
    return job_ref.rsplit("/", 1)[-1]


def _resolve_from_iris(job_ref: str, cluster_config: str) -> str:
    """Parse the recorded output dir out of the job's baked iris worker command.

    Reads ``job_config.entrypoint_json`` for the most recent job whose name
    matches ``job_ref`` and extracts the ``--jobs-dir`` / ``--gcs-output-dir`` /
    ``--experiments_dir`` argument. Raises ``LookupError`` if no such job exists
    on the controller or its command carries no recognizable output arg.
    """
    bare = _bare_job_name(job_ref)
    sql = (
        "SELECT jc.entrypoint_json AS entrypoint_json "
        "FROM job_config jc JOIN jobs j ON jc.job_id = j.job_id "
        f"WHERE j.name = '{bare}' OR j.name LIKE '%/{bare}' "
        "ORDER BY j.submitted_at_ms DESC LIMIT 1"
    )
    rows = _iris_query(cluster_config, sql)
    if not rows:
        raise LookupError(
            f"Job {job_ref!r} not found on the iris controller "
            f"(cluster_config={cluster_config!r}); cannot resolve its output dir."
        )
    entrypoint = rows[0].get("entrypoint_json") or ""
    match = _OUTPUT_ARG_RE.search(entrypoint)
    if match is None:
        # CoreWeave RL jobs write trials/checkpoints to an s3:// prefix (CW LOTA /
        # R2), NOT a gs:// output dir — this resolver (and analyze_iris_harbor_job's
        # trace-progress section) only understands the gs:// TPU convention, so
        # give a directional error instead of a bare "no gs:// arg".
        s3_hit = re.search(r"(s3://[^\s\"']+)", entrypoint)
        if s3_hit is not None:
            raise LookupError(
                f"Job {job_ref!r} is a CoreWeave/S3 job — its trials/output live under "
                f"{s3_hit.group(1)!r} (s3://), not a gs:// prefix. analyze_iris_harbor_job's "
                "output-dir / trace-progress resolution only supports gs:// (TPU) jobs. "
                "For CoreWeave RL trial-banking + rollout inspection use "
                "`MarinSkyRL/scripts/iris/analyze_coreweave_rl_job_live.sh <job>` "
                "(the authoritative banking signal); "
                "analyze_iris_harbor_job's finelog/throughput sections still work on their own."
            )
        raise LookupError(
            f"Job {job_ref!r} baked command carries no --jobs-dir/--gcs-output-dir/"
            "--experiments_dir gs:// argument (and no s3:// path either); cannot "
            "resolve its output dir."
        )
    return match.group(1).rstrip("/")


def resolve_job_output_dir(job_ref: str, *, cluster_config: str | None = None) -> str:
    """Return the recorded OUTER ``.../ot-agent/<job>/`` output URI for a job.

    Registry-first (jobs launched from this host), then iris-fallback (cross-host
    jobs, requires ``cluster_config``). Returns the recorded URI verbatim, so a
    legacy multi-region job resolves to ``gs://marin-models-{us,eu}/...`` and a
    new single-region job resolves to ``gs://marin-us-east5/...``.

    Args:
        job_ref: Bare job name (``tracegen-iris-...``) or fully-qualified iris id
            (``/<user>/tracegen-iris-...``).
        cluster_config: Path to the iris cluster config, used only for the
            cross-host fallback when the job is absent from the local registry.

    Raises:
        LookupError: The job is neither in the local registry nor resolvable from
            iris (no ``cluster_config`` given, or the controller has no matching
            job / no output arg). We never guess a bucket.
    """
    bare = _bare_job_name(job_ref)
    record = get_latest_by_job_name(bare) or get(job_ref)
    if record is not None:
        return record.gcs_output_dir.rstrip("/")
    if cluster_config is None:
        raise LookupError(
            f"Job {job_ref!r} not in the local registry and no cluster_config given "
            "for the iris fallback. Pass --cluster <cfg> to resolve a cross-host job, "
            "or --output-dir to override explicitly."
        )
    return _resolve_from_iris(job_ref, cluster_config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve an iris job's recorded GCS output directory."
    )
    parser.add_argument("job_ref", help="Bare job name or /<user>/<job-name> iris id.")
    parser.add_argument(
        "--cluster",
        "--cluster-config",
        dest="cluster_config",
        default=None,
        help="Iris cluster config path (only needed for the cross-host fallback).",
    )
    args = parser.parse_args(argv)
    print(resolve_job_output_dir(args.job_ref, cluster_config=args.cluster_config))
    return 0


if __name__ == "__main__":
    sys.exit(main())
