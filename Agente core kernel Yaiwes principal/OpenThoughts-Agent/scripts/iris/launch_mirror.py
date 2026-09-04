#!/usr/bin/env python3
"""Submit model-mirror routes to an Iris worker.

Use one of the explicit transfer routes::

    python -m scripts.iris.launch_mirror hf-to-gcs --repo org/model
    python -m scripts.iris.launch_mirror gcs-to-s3 --repo org/model ...
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from hpc.iris_launch_utils import IrisLauncher
from hpc.iris.outputs import IrisOutputPaths
from hpc.launch_utils import PROJECT_ROOT


class HfMirrorIrisLauncher(IrisLauncher):
    """Iris launcher for the HF-to-GCS mirror route."""

    task_name = "ot-hf-mirror"
    job_name_prefix = "hf-mirror"
    default_tpu = "v6e-4"
    default_gcs_prefixes = (
        "gs://marin-models-us/ot-agent/models",
        "gs://marin-models-eu/ot-agent/models",
    )

    def add_task_specific_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--repo",
            action="append",
            required=True,
            help="HF model repo id (repeatable).",
        )
        parser.add_argument(
            "--gcs-prefix",
            "--gcs_prefix",
            action="append",
            default=None,
            help=(
                "GCS prefix; each repo lands under <prefix>/<repo>/. Repeat for every destination. "
                "Defaults to the Marin US and EU multi-region model buckets."
            ),
        )
        parser.add_argument(
            "--job_name", help="Override the auto-generated Iris job name."
        )
        parser.add_argument(
            "--dry_run",
            action="store_true",
            help="Print the command without submitting.",
        )

    def normalize_paths(self, args: argparse.Namespace) -> None:
        if not args.gcs_prefix:
            args.gcs_prefix = list(self.default_gcs_prefixes)
        invalid = [
            prefix for prefix in args.gcs_prefix if not prefix.startswith("gs://")
        ]
        if invalid:
            raise SystemExit(
                f"--gcs-prefix entries must start with gs:// (got {invalid!r})"
            )

    def build_task_command(
        self, args: argparse.Namespace, output_paths: IrisOutputPaths
    ) -> list[str]:
        command = ["python", "-m", "scripts.iris.mirror_models", "hf-to-gcs"]
        for prefix in args.gcs_prefix:
            command.extend(["--gcs-prefix", prefix])
        for repo in args.repo:
            command.extend(["--repo", repo])
        return command


class GcsToS3Launcher(IrisLauncher):
    """Iris launcher for the GCS-to-S3 mirror route."""

    task_name = "ot-gcs2s3"
    job_name_prefix = "gcs2s3"
    default_tpu = "v6e-4"

    def add_task_specific_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--repo",
            action="append",
            required=True,
            help="HF model repo id (repeatable).",
        )
        parser.add_argument(
            "--gcs-prefix", "--gcs_prefix", required=True, help="Source GCS prefix."
        )
        parser.add_argument("--s3-bucket", "--s3_bucket", required=True)
        parser.add_argument("--s3-prefix", "--s3_prefix", required=True)
        parser.add_argument(
            "--s3-endpoint",
            "--s3_endpoint",
            default=None,
            help="S3-compatible endpoint URL; falls back to AWS_ENDPOINT_URL on the worker.",
        )
        parser.add_argument(
            "--job_name", help="Override the auto-generated Iris job name."
        )
        parser.add_argument("--dry_run", action="store_true")

    def normalize_paths(self, args: argparse.Namespace) -> None:
        if not args.gcs_prefix.startswith("gs://"):
            raise SystemExit("--gcs-prefix must start with gs://")

    def build_task_command(
        self, args: argparse.Namespace, output_paths: IrisOutputPaths
    ) -> list[str]:
        command = [
            "python",
            "-m",
            "scripts.iris.mirror_models",
            "gcs-to-s3",
            "--gcs-prefix",
            args.gcs_prefix,
            "--s3-bucket",
            args.s3_bucket,
            "--s3-prefix",
            args.s3_prefix,
        ]
        if args.s3_endpoint:
            command.extend(["--s3-endpoint", args.s3_endpoint])
        for repo in args.repo:
            command.extend(["--repo", repo])
        return command


LAUNCHERS = {
    "hf-to-gcs": (
        HfMirrorIrisLauncher,
        "Mirror HF model repos to GCS via an Iris worker.",
    ),
    "gcs-to-s3": (
        GcsToS3Launcher,
        "Mirror staged GCS model repos to S3 via an Iris worker.",
    ),
}


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in {"-h", "--help"}:
        print(__doc__)
        print(f"Routes: {', '.join(sorted(LAUNCHERS))}")
        return 0
    route, *remaining = arguments
    if route not in LAUNCHERS:
        raise SystemExit(
            f"Unknown mirror launch route {route!r}; choose one of: {', '.join(sorted(LAUNCHERS))}"
        )
    launcher_type, description = LAUNCHERS[route]
    launcher = launcher_type(PROJECT_ROOT)
    parser = launcher.create_argument_parser(description=description)
    return launcher.run(parser.parse_args(remaining))


if __name__ == "__main__":
    raise SystemExit(main())
