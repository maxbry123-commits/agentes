"""Regression test: xla_cache co-locates with the (single-region) output bucket.

``apply_iris_runtime_env`` derives ``OT_AGENT_XLA_CACHE_BASE`` from
``args.gcs_output_dir`` by stripping the ``/ot-agent`` namespace and re-appending
``/ot-agent/xla_cache``. Once the launcher pins outputs to a single-region bucket
(``gs://marin-us-east5/ot-agent``), the compile cache must land co-located at
``gs://marin-us-east5/ot-agent/xla_cache`` — same region, cheaper storage — with
no code change to this derivation. This locks that behavior in.

Run:
    .venv/bin/python -m pytest tests/hpc/test_env_xla_cache.py -v
"""

from __future__ import annotations

import argparse

import pytest

from hpc.iris.accelerator import ResolvedIrisAccelerator
from hpc.iris.env import apply_iris_runtime_env


def _tpu_accelerator() -> ResolvedIrisAccelerator:
    # apply_iris_runtime_env only reads is_tpu / uses_iris_serve, both keyed on kind.
    return ResolvedIrisAccelerator(kind="tpu")


@pytest.mark.parametrize(
    ("gcs_output_dir", "expected_cache_base"),
    [
        ("gs://marin-us-east5/ot-agent", "gs://marin-us-east5/ot-agent/xla_cache"),
        ("gs://marin-eu-west4/ot-agent", "gs://marin-eu-west4/ot-agent/xla_cache"),
        # Legacy multi-region root still derives correctly (no flag day).
        ("gs://marin-models-us/ot-agent", "gs://marin-models-us/ot-agent/xla_cache"),
    ],
)
def test_xla_cache_colocates_with_output_bucket(
    gcs_output_dir: str, expected_cache_base: str
) -> None:
    env_vars: dict[str, str] = {}
    args = argparse.Namespace(gcs_output_dir=gcs_output_dir)
    apply_iris_runtime_env(
        env_vars=env_vars,
        args=args,
        accelerator=_tpu_accelerator(),
        output_mode="gcs",
        remote_output_dir=f"{gcs_output_dir}/some-job",
        extras=["datagen-tpu"],
    )
    assert env_vars["OT_AGENT_XLA_CACHE_BASE"] == expected_cache_base
