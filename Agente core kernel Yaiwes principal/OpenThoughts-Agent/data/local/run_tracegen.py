#!/usr/bin/env python3
"""
Local trace generation runner.

Starts a single-node Ray cluster + vLLM controller and then launches a Harbor job
to generate traces from tasks. Designed for non-SLURM Linux hosts where we have
exclusive access to the box.

Usage:
    python run_tracegen.py \
        --harbor_config harbor_configs/default.yaml \
        --tasks_input_path /path/to/tasks \
        --datagen_config datagen_configs/my_config.yaml \
        --upload_hf_repo my-org/my-traces
"""

from __future__ import annotations

import argparse
from typing import Optional, Tuple

from hpc.launch_utils import PROJECT_ROOT
from hpc.local_runner_utils import LocalHarborRunner
from hpc.arg_groups import (
    add_harbor_env_arg,
    add_hf_upload_args,
    add_ingress_literal_args,
    add_tasks_input_arg,
)


class TracegenRunner(LocalHarborRunner):
    """Local Harbor runner for trace generation."""

    JOB_PREFIX = "tracegen"
    DEFAULT_EXPERIMENTS_SUBDIR = "trace_runs"
    DEFAULT_N_CONCURRENT = 64
    DATAGEN_CONFIG_REQUIRED = True

    @classmethod
    def create_parser(cls) -> argparse.ArgumentParser:
        """Create argument parser with tracegen-specific arguments."""
        parser = argparse.ArgumentParser(
            description="Run local trace generation with Ray/vLLM server.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=__doc__,
        )

        # Add common arguments from base class
        cls.add_common_arguments(parser)

        # Tracegen-specific arguments (with underscore primary, kebab alias)
        add_tasks_input_arg(parser, required=True)

        parser.add_argument(
            "--datagen_config",
            required=True,
            help="Path to datagen YAML with vLLM settings.",
        )
        parser.add_argument(
            "--datagen-config", dest="datagen_config", help=argparse.SUPPRESS
        )

        # Harbor environment backend (unified --harbor_env, with legacy aliases)
        # Default=None to allow inference from harbor config's environment.type field
        add_harbor_env_arg(
            parser, default=None, legacy_names=["--trace-env", "--trace_env"]
        )

        parser.add_argument(
            "--experiments_dir",
            default=str(PROJECT_ROOT / cls.DEFAULT_EXPERIMENTS_SUBDIR),
            help="Directory for logs + endpoint JSON.",
        )
        parser.add_argument(
            "--experiments-dir", dest="experiments_dir", help=argparse.SUPPRESS
        )

        # HuggingFace upload options (shared from arg_groups)
        add_hf_upload_args(parser)

        # Literal-token capture + controller-ingress (opencode / SUPPORTS_LITERAL_TRACES).
        add_ingress_literal_args(parser)

        return parser

    def get_env_type(self) -> str:
        """Get the environment type from --harbor-env or infer from Harbor config."""
        if self.args.harbor_env:
            return self.args.harbor_env
        # Infer from harbor config if not explicitly specified
        from hpc.harbor_utils import get_harbor_env_from_config

        return get_harbor_env_from_config(self.args.harbor_config)

    def get_dataset_label(self) -> str:
        """Get the dataset label for job naming."""
        return self.args.tasks_input_path

    def get_dataset_for_harbor(self) -> Tuple[Optional[str], Optional[str]]:
        """Return (dataset_slug, dataset_path) for harbor command."""
        return (None, self.args.tasks_input_path)

    def validate_args(self) -> None:
        """Validate tracegen-specific arguments.

        ``--tasks_input_path`` accepts two shapes:

        * Local FS path with raw task subdirs (each containing
          ``instruction.md``, ``task.toml``, etc.) — used directly.
        * HuggingFace dataset id (``org/name``) — downloaded via
          ``snapshot_download``; if the snapshot is parquet-format
          (with a ``task_binary`` column), tasks are extracted from
          the parquet into a local directory tree via
          ``convert_parquet_to_tasks``.

        Mirrors the convert_parquet_to_tasks convention shared across
        the datagen/tracegen launch paths so eval and tracegen share the
        same "task extraction" convention.
        """
        from hpc.hf_utils import resolve_dataset_path, is_raw_tasks_directory
        from hpc.launch_utils import convert_parquet_to_tasks

        original = self.args.tasks_input_path
        resolved = resolve_dataset_path(original, verbose=True)
        if not is_raw_tasks_directory(resolved):
            resolved = convert_parquet_to_tasks(resolved, original)
        self.args.tasks_input_path = str(resolved)

    def print_banner(self) -> None:
        """Print startup banner for tracegen."""
        args = self.args
        needs_local_vllm = getattr(args, "_needs_local_vllm", True)
        engine_type = getattr(args, "_engine_type", "vllm_local")

        print("=== Local Trace Generation ===")
        print(f"  Model: {args.model}")
        print(f"  Tasks: {args.tasks_input_path}")
        if needs_local_vllm:
            print(
                f"  TP/PP/DP: {args.tensor_parallel_size}/{args.pipeline_parallel_size}/{args.data_parallel_size}"
            )
            print(f"  GPUs: {args.gpus}")
        else:
            print(f"  Engine: {engine_type} (API)")
        print("==============================")

    def post_harbor_hook(self) -> None:
        """HF upload is now handled by harbor's own export.

        When ``--upload_hf_repo`` is set, ``build_harbor_command`` passes
        ``--export-push --export-repo <repo>`` to ``harbor jobs start``, so
        harbor exports AND pushes from the (gs://-aware) job dir in one pass.
        This hook used to do a second upload via ``upload_traces_to_hf``, but
        it resolved the jobs dir from the YAML's relative ``jobs_dir`` (→ a
        nonexistent local ``/app/trace_jobs/<job>``) and silently skipped on a
        gs:// job dir — so it never actually uploaded. Delegating to harbor's
        push removes that dead, misleading path.
        """
        if self.args.upload_hf_repo:
            print(
                "[upload] HF push delegated to harbor --export-push "
                f"(repo {self.args.upload_hf_repo})."
            )


def main() -> None:
    parser = TracegenRunner.create_parser()
    args = parser.parse_args()

    runner = TracegenRunner(args, PROJECT_ROOT)
    runner.setup()
    runner.run()


if __name__ == "__main__":
    main()
