#!/usr/bin/env python3
"""Canonical CLI for Iris model mirrors."""

from __future__ import annotations

import argparse
import os
from typing import Sequence

from scripts.iris import mirror_gcs_to_s3, mirror_hf_to_gcs, mirror_hf_to_s3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    routes = parser.add_subparsers(dest="route", required=True)
    hf_gcs = routes.add_parser("hf-to-gcs", help="Mirror Hub model repos to GCS.")
    hf_gcs.add_argument("--repo", action="append", required=True)
    hf_gcs.add_argument("--gcs-prefix", "--gcs_prefix", action="append", required=True)
    hf_gcs.add_argument("--quiet", action="store_true")
    hf_gcs.add_argument("--iris-job-id", default=os.environ.get("IRIS_JOB_ID"))
    gcs_s3 = routes.add_parser("gcs-to-s3", help="Mirror staged GCS model repos to S3.")
    gcs_s3.add_argument("--repo", action="append", required=True)
    gcs_s3.add_argument("--gcs-prefix", required=True)
    gcs_s3.add_argument("--s3-bucket", required=True)
    gcs_s3.add_argument("--s3-prefix", required=True)
    gcs_s3.add_argument("--s3-endpoint", default=os.environ.get("AWS_ENDPOINT_URL"))
    gcs_s3.add_argument("--quiet", action="store_true")
    hf_s3 = routes.add_parser(
        "hf-to-s3", help="Mirror Hub model repos to CoreWeave S3."
    )
    hf_s3.add_argument("--repo", action="append", required=True)
    hf_s3.add_argument(
        "--s3-prefix", "--s3_prefix", default="s3://marin-us-east-02a/models"
    )
    hf_s3.add_argument("--s3-endpoint", default=os.environ.get("AWS_ENDPOINT_URL"))
    hf_s3.add_argument("--quiet", action="store_true")
    return parser


def run(args: argparse.Namespace) -> int:
    if args.route == "hf-to-gcs":
        invalid = [
            prefix for prefix in args.gcs_prefix if not prefix.startswith("gs://")
        ]
        if invalid:
            raise SystemExit(
                f"--gcs-prefix entries must start with gs:// (got {invalid!r})"
            )
        for repo in args.repo:
            mirror_hf_to_gcs.mirror(
                repo,
                args.gcs_prefix,
                verbose=not args.quiet,
                iris_job_id=args.iris_job_id,
            )
        return 0
    if args.route == "gcs-to-s3":
        if not args.gcs_prefix.startswith("gs://"):
            raise SystemExit("--gcs-prefix must start with gs://")
        for repo in args.repo:
            mirror_gcs_to_s3.mirror_repo(
                repo_id=repo,
                gcs_prefix=args.gcs_prefix,
                s3_bucket=args.s3_bucket,
                s3_prefix=args.s3_prefix,
                s3_endpoint=args.s3_endpoint,
                verbose=not args.quiet,
            )
        return 0
    if args.route == "hf-to-s3":
        bucket, prefix = mirror_hf_to_s3._parse_s3_prefix(args.s3_prefix)
        for repo in args.repo:
            mirror_hf_to_s3.mirror(
                repo_id=repo,
                bucket=bucket,
                prefix=prefix,
                s3_endpoint=args.s3_endpoint,
                verbose=not args.quiet,
            )
        return 0
    raise AssertionError(f"Unhandled mirror route {args.route!r}")


def main(argv: Sequence[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
