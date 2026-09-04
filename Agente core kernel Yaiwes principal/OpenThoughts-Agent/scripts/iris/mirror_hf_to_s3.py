#!/usr/bin/env python3
"""Mirror a HuggingFace model repo to a CW (S3-compatible) object store, one file at a time.

This is the S3 analog of ``scripts/iris/mirror_hf_to_gcs.py``, purpose-built to SEED
the CoreWeave object store (``s3://marin-us-east-02a``) so the RL controller's warm
path (``start_rl_iris_controller.py::_warm_sync_model_from_s3``) can pull the model
IN-REGION on every node instead of cold-pulling from HF Hub.

Must run IN-CLUSTER on cw-us-east-02a (not the Mac): the CW pod natively carries
BOTH HF egress AND the CW-object-store creds + ``AWS_ENDPOINT_URL`` (the iris-task-env
Secret projected into every task pod); the Mac has neither the CW-S3 creds nor the
bandwidth to push 160 GB. Each safetensors shard is downloaded from HF, uploaded to
S3, then DELETED before the next — so the worker's ephemeral disk never holds more than
one shard. Idempotent + resumable: a file already present at the destination with a
matching size is skipped, so a re-run resumes an interrupted mirror.

Destination convention (MUST match the controller warm-path reader
``_warm_sync_model_from_s3`` + the launcher's auto-derive in ``launch_rl_iris.py``)::

    s3://<bucket>/<prefix>/<org>--<name>/<repo-relative-path>

e.g. ``s3://marin-us-east-02a/models/Qwen--Qwen3-Next-80B-A3B-Thinking/config.json``.

Usage (inside a CW pod, creds + AWS_ENDPOINT_URL injected)::

    python scripts/iris/mirror_hf_to_s3.py \\
        --repo Qwen/Qwen3-Next-80B-A3B-Thinking \\
        --s3-prefix s3://marin-us-east-02a/models
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from scripts.iris.hf_model_files import select_model_files, selection_policy

MANIFEST_FILENAME = ".mirror_manifest.json"


def sanitize_repo(repo_id: str) -> str:
    """``org/name`` -> ``org--name`` (the shared CW-S3 model-dir convention)."""
    return repo_id.replace("/", "--")


def _s3_client(endpoint_url: str | None):
    """boto3 S3 client for the CW object store. Virtual-hosted addressing (CW/R2
    rejects path-style with PathStyleRequestNotAllowed); endpoint + creds from env."""
    import boto3
    from botocore.config import Config

    style = os.environ.get("OT_AGENT_S3_ADDRESSING_STYLE", "virtual")
    return boto3.client(
        "s3", endpoint_url=endpoint_url, config=Config(s3={"addressing_style": style})
    )


def _s3_head_size(s3, bucket: str, key: str) -> int | None:
    """Existing object size, or None if absent / error (treated as 'needs upload')."""
    try:
        resp = s3.head_object(Bucket=bucket, Key=key)
        return int(resp.get("ContentLength", 0))
    except Exception:
        return None


def mirror(
    *,
    repo_id: str,
    bucket: str,
    prefix: str,
    s3_endpoint: str | None,
    verbose: bool = True,
) -> None:
    """Mirror ``repo_id`` to ``s3://<bucket>/<prefix>/<org>--<name>/``, one file at a time."""
    from huggingface_hub import HfApi, hf_hub_download

    s3 = _s3_client(s3_endpoint)
    dst_prefix = f"{prefix.rstrip('/')}/{sanitize_repo(repo_id)}"

    api = HfApi()
    files = sorted(api.list_repo_files(repo_id, repo_type="model"))
    # Selection and metadata-first ordering both live in hf_model_files, shared with the
    # GCS route so the two mirrors cannot drift.
    keep = select_model_files(files)

    if verbose:
        print(f"[hf2s3] {repo_id} -> s3://{bucket}/{dst_prefix}", flush=True)
        print(f"[hf2s3] repo has {len(files)} files; mirroring {len(keep)}", flush=True)
        skipped = sorted(set(files) - set(keep))
        if skipped:
            print(f"[hf2s3] skipping {len(skipped)}: {', '.join(skipped)}", flush=True)

    files_mirrored: list[tuple[str, int]] = []
    for idx, fname in enumerate(keep, 1):
        dst_key = f"{dst_prefix}/{fname}"
        existing = _s3_head_size(s3, bucket, dst_key)
        # We don't know the HF size without downloading; if an object already exists with
        # a non-zero size we treat it as done (resume). A truncated prior upload would have
        # to be deleted manually — acceptable for a one-shot seed.
        if existing is not None and existing > 0:
            if verbose:
                print(
                    f"[hf2s3] [{idx}/{len(keep)}] skip (in S3, {existing} bytes): {fname}",
                    flush=True,
                )
            files_mirrored.append((fname, existing))
            continue

        with tempfile.TemporaryDirectory(prefix="hf2s3_") as tmp:
            if verbose:
                print(f"[hf2s3] [{idx}/{len(keep)}] download: {fname}", flush=True)
            local_file = Path(
                hf_hub_download(
                    repo_id=repo_id,
                    filename=fname,
                    local_dir=tmp,
                    local_dir_use_symlinks=False,
                )
            )
            size = local_file.stat().st_size
            if verbose:
                print(
                    f"[hf2s3] [{idx}/{len(keep)}] upload ({size} bytes): "
                    f"s3://{bucket}/{dst_key}",
                    flush=True,
                )
            s3.upload_file(str(local_file), bucket, dst_key)
            files_mirrored.append((fname, size))
            try:
                local_file.unlink(missing_ok=True)
            except OSError:
                pass

    # Manifest last so a partial mirror is detectable (manifest missing -> incomplete).
    manifest = {
        "hf_repo": repo_id,
        "mirrored_at": datetime.now(timezone.utc).isoformat(),
        "mirror_script": "scripts/iris/mirror_hf_to_s3.py",
        "dest": f"s3://{bucket}/{dst_prefix}",
        "file_count": len(files_mirrored),
        "size_bytes": sum(sz for _, sz in files_mirrored),
        "files": [{"name": n, "size": sz} for n, sz in files_mirrored],
        # The POLICY, not just the resulting file list: a manifest that records only
        # what was copied cannot answer "why is this file missing?" later.
        "selection_policy": selection_policy(),
        "iris_job_id": os.environ.get("IRIS_JOB_ID"),
    }
    s3.put_object(
        Bucket=bucket,
        Key=f"{dst_prefix}/{MANIFEST_FILENAME}",
        Body=json.dumps(manifest, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    if verbose:
        total = sum(sz for _, sz in files_mirrored)
        print(
            f"[hf2s3] DONE: {repo_id} -> s3://{bucket}/{dst_prefix} "
            f"({len(files_mirrored)} files, {total} bytes); manifest at "
            f"s3://{bucket}/{dst_prefix}/{MANIFEST_FILENAME}",
            flush=True,
        )


def _parse_s3_prefix(uri: str) -> tuple[str, str]:
    if not uri.startswith("s3://"):
        raise SystemExit(f"--s3-prefix must start with s3:// (got {uri!r})")
    bucket, _, prefix = uri[len("s3://") :].partition("/")
    if not bucket:
        raise SystemExit(f"--s3-prefix missing bucket (got {uri!r})")
    return bucket, prefix.rstrip("/")


def _legacy_main() -> int:
    p = argparse.ArgumentParser(
        description="Stream one or more HF model repos into a CW S3-compatible bucket.",
    )
    p.add_argument(
        "--repo",
        action="append",
        required=True,
        help="HF model repo id (org/name); repeatable.",
    )
    p.add_argument(
        "--s3-prefix",
        "--s3_prefix",
        default="s3://marin-us-east-02a/models",
        help="Destination s3://bucket/prefix; each repo lands under "
        "<prefix>/<org>--<name>/. Default s3://marin-us-east-02a/models.",
    )
    p.add_argument(
        "--s3-endpoint",
        default=os.environ.get("AWS_ENDPOINT_URL"),
        help="S3-compatible endpoint URL. Defaults to $AWS_ENDPOINT_URL "
        "(injected into CW pods).",
    )
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    bucket, prefix = _parse_s3_prefix(args.s3_prefix)
    for repo in args.repo:
        mirror(
            repo_id=repo,
            bucket=bucket,
            prefix=prefix,
            s3_endpoint=args.s3_endpoint,
            verbose=not args.quiet,
        )
    return 0


def main() -> int:
    """Compatibility entrypoint; use ``mirror_models hf-to-s3`` for new calls."""
    from scripts.iris.mirror_models import main as unified_main

    return unified_main(["hf-to-s3", *sys.argv[1:]])


if __name__ == "__main__":
    sys.exit(main())
