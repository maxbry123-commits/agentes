"""Output path handling for Iris launchers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


# Default GCS prefix for workload outputs. EU-region matches where most
# of our v6e-preemptible TPU slices land; us-region jobs incur small
# cross-region writes (eval outputs are ~MB-scale, so this is fine).
# Override with $OT_AGENT_GCS_OUTPUT_ROOT or the --gcs-output-dir flag.
DEFAULT_GCS_OUTPUT_ROOT = "gs://marin-eu-west4/ot-agent"

# Pod-local runtime scratch root used by the GPU S3 path for endpoint files and
# transient process logs. It is never a durable artifact destination.
DEFAULT_LOCAL_OUTPUT_ROOT = "/tmp/ot-agent-runs"

# No universal default S3 prefix — the CoreWeave object-store bucket
# (s3://marin-us-east-02a/...) is cluster-specific, so require it explicitly (flag
# or OT_AGENT_S3_OUTPUT_ROOT). NOTE: the default store moved R2 (s3://marin-na) ->
# CW (s3://marin-us-east-02a) on 2026-07-05 (marin c7caecc95a); s3://marin-na (R2)
# is no longer reachable from pods.
DEFAULT_S3_OUTPUT_ROOT = None


@dataclass(frozen=True)
class IrisOutputPaths:
    """Resolved runtime and durable output locations for one Iris job."""

    remote_output_dir: str
    work_output_dir: str
    harbor_jobs_dir: str


def _join_output_path(root: str, job_name: str) -> str:
    """Append one job-name component to an output root."""
    if not job_name or "/" in job_name:
        raise ValueError(
            f"job_name must be one non-empty path component, got {job_name!r}"
        )
    return f"{root.rstrip('/')}/{job_name.strip('/')}"


def s3_harbor_jobs_dir(s3_output_root: str, job_name: str) -> str:
    """Return the canonical durable Harbor jobs root for an S3-backed Iris job."""
    if not s3_output_root.startswith("s3://"):
        raise ValueError("--s3-output-dir must start with s3://")
    return f"{_join_output_path(s3_output_root, job_name)}/trace_jobs"


def resolve_output_mode(
    args: argparse.Namespace,
    *,
    accelerator_kind: str,
) -> str:
    """Resolve ``--output-mode auto`` after the accelerator is known.

    TPU keeps the established GCS path. GPU defaults to S3 so Harbor trial
    artifacts survive a pod loss. The S3 path still uses pod-local scratch for
    endpoint files and transient logs, but ``trace_jobs`` are durable from the
    start. A launch without an S3 root therefore fails closed.
    """
    output_mode = getattr(args, "output_mode", "auto")
    if output_mode != "auto":
        return output_mode
    if accelerator_kind == "gpu":
        return "s3"
    return "gcs"


def validate_output_args(
    args: argparse.Namespace,
    output_mode: str,
    *,
    accelerator_kind: str,
) -> None:
    if accelerator_kind == "gpu" and output_mode == "gcs":
        raise SystemExit(
            "CoreWeave GPU Iris runs must not write to GCS. Use "
            "--output-mode s3 (the default) with --s3-output-dir s3://..."
        )
    if accelerator_kind == "gpu" and output_mode == "local":
        raise SystemExit(
            "CoreWeave GPU Iris runs must write durable artifacts to S3; "
            "use --output-mode s3 with --s3-output-dir s3://..."
        )
    if accelerator_kind == "tpu" and output_mode in ("s3", "local"):
        raise SystemExit(
            "TPU Iris runs use --output-mode gcs. --output-mode s3/local is only "
            "supported for the CoreWeave GPU eval path."
        )
    if output_mode == "gcs" and not args.gcs_output_dir:
        raise SystemExit(
            "--gcs-output-dir is required (set OT_AGENT_GCS_OUTPUT_ROOT or pass the flag)."
        )
    if output_mode in ("s3", "local"):
        if getattr(args, "resume_from", None):
            raise SystemExit("--resume-from is only supported with --output-mode gcs.")
        local_output_root = str(args.local_output_dir).rstrip("/")
        if not local_output_root.startswith("/"):
            raise SystemExit(
                "--local-output-dir must be an absolute path inside the task container."
            )
        args.local_output_dir = local_output_root
    if output_mode == "s3":
        if not getattr(args, "s3_output_dir", None):
            raise SystemExit(
                "--s3-output-dir is required for --output-mode s3 "
                "(set OT_AGENT_S3_OUTPUT_ROOT or pass the flag)."
            )
        s3_output_root = str(args.s3_output_dir).rstrip("/")
        if not s3_output_root.startswith("s3://"):
            raise SystemExit("--s3-output-dir must start with s3://.")
        args.s3_output_dir = s3_output_root


def _resolve_remote_output_dir(
    args: argparse.Namespace,
    *,
    job_name: str,
    output_mode: str,
    resume_target: str | None,
) -> str:
    """Return the durable/output path advertised for the Iris task."""
    if resume_target:
        # Resume: point at the OLD job's full GCS path so harbor finds
        # its existing config.json / trial dirs. Do NOT re-join job_name.
        return args._resume_gcs_output_dir.rstrip("/")
    if output_mode == "s3":
        return _join_output_path(args.s3_output_dir, job_name)
    if output_mode == "local":
        return _join_output_path(args.local_output_dir, job_name)
    return _join_output_path(args.gcs_output_dir, job_name)


def _resolve_work_output_dir(
    args: argparse.Namespace,
    *,
    job_name: str,
    output_mode: str,
    remote_output_dir: str,
) -> str:
    """Return the pod-local runtime scratch path used by ``run_eval.py``.

    For ``s3`` mode the durable Harbor ``--jobs-dir`` is the s3:// URI but
    ``run_eval``'s ``--experiments_dir`` (endpoint.json, logs) must be a real
    local path, so it lives under ``--local-output-dir``. For ``local`` mode
    the work dir IS the output dir. For ``gcs`` the workload writes straight
    to GCS via Harbor's UPath patch.
    """
    if output_mode == "s3":
        return _join_output_path(args.local_output_dir, job_name)
    return remote_output_dir


def resolve_output_paths(
    args: argparse.Namespace,
    *,
    job_name: str,
    output_mode: str,
    resume_target: str | None,
) -> IrisOutputPaths:
    """Resolve all output paths consumed by Iris eval and datagen launchers."""
    remote_output_dir = _resolve_remote_output_dir(
        args,
        job_name=job_name,
        output_mode=output_mode,
        resume_target=resume_target,
    )
    work_output_dir = _resolve_work_output_dir(
        args,
        job_name=job_name,
        output_mode=output_mode,
        remote_output_dir=remote_output_dir,
    )
    if output_mode == "s3":
        harbor_jobs_dir = s3_harbor_jobs_dir(args.s3_output_dir, job_name)
    elif output_mode == "local":
        harbor_jobs_dir = f"{args.local_output_dir.rstrip('/')}/harbor_jobs"
    else:
        harbor_jobs_dir = remote_output_dir
    return IrisOutputPaths(
        remote_output_dir=remote_output_dir,
        work_output_dir=work_output_dir,
        harbor_jobs_dir=harbor_jobs_dir,
    )
