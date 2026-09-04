#!/usr/bin/env python3
"""Copy one or more GCS prefixes into an S3-compatible bucket, one file at a time.

Iris workers have native GCS read auth via workload identity, and we have AWS-style
S3 creds for the LAION / mmlaion bucket at Jülich — so we pull from GCS (gcsfs) and
push to S3 (boto3) in a streaming script, never holding more than one shard on local
disk.

Idempotent: skips files already present at the destination with a matching size.

Usage::

    python -m scripts.iris.mirror_gcs_to_s3 \\
        --gcs-prefix gs://marin-eu-west4/ot-agent/models \\
        --s3-bucket mmlaion \\
        --s3-prefix ot-agent/models \\
        --s3-endpoint https://just-object.fz-juelich.de:9000 \\
        --repo cyankiwi/MiniMax-M2.7-AWQ-4bit \\
        --repo google/gemma-4-31B-it \\
        --repo QuantTrio/Qwen3.5-397B-A17B-AWQ

The S3 endpoint is read from $AWS_ENDPOINT_URL if --s3-endpoint isn't
passed. Credentials use the boto3 default chain (AWS_ACCESS_KEY_ID +
AWS_SECRET_ACCESS_KEY env vars on iris workers — forwarded by the
launcher).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_FILENAME = ".mirror_manifest.json"


def _gcs_fs():
    import gcsfs

    return gcsfs.GCSFileSystem()


def _s3_client(endpoint_url: str | None):
    """Build a boto3 S3 client that talks to either AWS or an S3-compat endpoint.

    The endpoint defaults to ``$AWS_ENDPOINT_URL`` (which the launcher sets
    via secrets-env passthrough); ``None`` falls back to AWS's default
    S3 endpoint.
    """
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        # Path-style addressing — required for most S3-compat endpoints
        # (MinIO, GCS, etc.). Real AWS S3 honors this too even though
        # it prefers virtual-host-style by default.
        config=Config(s3={"addressing_style": "path"}),
    )


def _s3_head(s3, bucket: str, key: str) -> int | None:
    """Return existing object size, or None if absent / error."""
    try:
        resp = s3.head_object(Bucket=bucket, Key=key)
        return int(resp.get("ContentLength", 0))
    except Exception:
        return None


def mirror_repo(
    *,
    repo_id: str,
    gcs_prefix: str,
    s3_bucket: str,
    s3_prefix: str,
    s3_endpoint: str | None,
    verbose: bool = True,
) -> None:
    """Mirror ``<gcs_prefix>/<repo_id>/`` to ``s3://<s3_bucket>/<s3_prefix>/<repo_id>/``.

    Lists the GCS source, streams each file through a temp dir, uploads
    via boto3. Writes a ``.mirror_manifest.json`` at the destination on
    completion (similar to the HF->GCS mirror).
    """
    gcs_fs = _gcs_fs()
    s3 = _s3_client(s3_endpoint)

    src_prefix = f"{gcs_prefix.rstrip('/')}/{repo_id}"
    dst_prefix = f"{s3_prefix.rstrip('/')}/{repo_id}"

    if verbose:
        print(f"[gcs2s3] {src_prefix} -> s3://{s3_bucket}/{dst_prefix}", flush=True)

    # gcsfs.ls returns full paths including bucket; strip back to the
    # relative basename so we can rebuild the S3 key.
    src_list = gcs_fs.ls(src_prefix, detail=True)
    # Filter to files only (exclude pseudo-directories).
    src_files = [f for f in src_list if f.get("type") == "file"]
    if verbose:
        print(f"[gcs2s3] {repo_id}: {len(src_files)} source files", flush=True)

    files_mirrored: list[tuple[str, int]] = []

    for idx, info in enumerate(sorted(src_files, key=lambda f: f["name"]), 1):
        src_path = info["name"]  # e.g. marin-eu-west4/ot-agent/models/<repo>/<file>
        # gcsfs returns paths without the gs:// prefix; add it back for ops.
        if not src_path.startswith("gs://"):
            src_uri = f"gs://{src_path}"
        else:
            src_uri = src_path
        src_size = int(info.get("size", 0))
        rel_name = src_path.rsplit("/", 1)[-1]
        # Skip the previous-mirror manifest; we'll rewrite at the end.
        if rel_name == MANIFEST_FILENAME:
            continue
        dst_key = f"{dst_prefix}/{rel_name}"

        existing = _s3_head(s3, s3_bucket, dst_key)
        if existing is not None and existing == src_size:
            if verbose:
                print(
                    f"[gcs2s3] [{idx}/{len(src_files)}] skip "
                    f"(matched size {existing} bytes): {rel_name}",
                    flush=True,
                )
            files_mirrored.append((rel_name, src_size))
            continue

        with tempfile.TemporaryDirectory(prefix="gcs2s3_") as tmp:
            local_path = Path(tmp) / rel_name
            if verbose:
                print(
                    f"[gcs2s3] [{idx}/{len(src_files)}] download "
                    f"({src_size} bytes): {rel_name}",
                    flush=True,
                )
            gcs_fs.get(src_uri, str(local_path))
            if verbose:
                print(
                    f"[gcs2s3] [{idx}/{len(src_files)}] upload: "
                    f"s3://{s3_bucket}/{dst_key}",
                    flush=True,
                )
            s3.upload_file(str(local_path), s3_bucket, dst_key)
            files_mirrored.append((rel_name, src_size))
            try:
                local_path.unlink()
            except OSError:
                pass

    # Write manifest at destination.
    manifest = {
        "hf_repo": repo_id,
        "mirrored_at": datetime.now(timezone.utc).isoformat(),
        "mirror_script": "scripts/iris/mirror_gcs_to_s3.py",
        "source_gcs": src_prefix,
        "file_count": len(files_mirrored),
        "size_bytes": sum(sz for _, sz in files_mirrored),
        "files": [{"name": n, "size": sz} for n, sz in files_mirrored],
    }
    manifest_key = f"{dst_prefix}/{MANIFEST_FILENAME}"
    s3.put_object(
        Bucket=s3_bucket,
        Key=manifest_key,
        Body=json.dumps(manifest, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    if verbose:
        total = sum(sz for _, sz in files_mirrored)
        print(
            f"[gcs2s3] done: {repo_id} -> s3://{s3_bucket}/{dst_prefix} "
            f"({len(files_mirrored)} files, {total} bytes); manifest at "
            f"s3://{s3_bucket}/{manifest_key}",
            flush=True,
        )


def _legacy_main() -> int:
    p = argparse.ArgumentParser(
        description="Stream files from a GCS prefix into an S3-compatible bucket.",
    )
    p.add_argument(
        "--repo",
        action="append",
        required=True,
        help="HF model repo id (org/name), repeatable.",
    )
    p.add_argument(
        "--gcs-prefix",
        required=True,
        help="Source GCS prefix; src paths are <prefix>/<repo>/...",
    )
    p.add_argument(
        "--s3-bucket",
        required=True,
        help="Destination S3 bucket name (no s3:// scheme).",
    )
    p.add_argument(
        "--s3-prefix",
        required=True,
        help="Destination prefix inside the bucket; dst paths are "
        "s3://<bucket>/<prefix>/<repo>/...",
    )
    p.add_argument(
        "--s3-endpoint",
        default=os.environ.get("AWS_ENDPOINT_URL"),
        help="S3-compatible endpoint URL (e.g. MinIO). "
        "Defaults to $AWS_ENDPOINT_URL; omit / leave unset "
        "for real AWS S3.",
    )
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    if not args.gcs_prefix.startswith("gs://"):
        print(
            f"error: --gcs-prefix must start with gs:// (got {args.gcs_prefix!r})",
            file=sys.stderr,
        )
        return 2

    for repo in args.repo:
        mirror_repo(
            repo_id=repo,
            gcs_prefix=args.gcs_prefix,
            s3_bucket=args.s3_bucket,
            s3_prefix=args.s3_prefix,
            s3_endpoint=args.s3_endpoint,
            verbose=not args.quiet,
        )
    return 0


def main() -> int:
    """Compatibility entrypoint; use ``mirror_models gcs-to-s3`` for new calls."""
    from scripts.iris.mirror_models import main as unified_main

    return unified_main(["gcs-to-s3", *sys.argv[1:]])


if __name__ == "__main__":
    sys.exit(main())
