"""Regression tests for the RL Hydra override list built by ``build_skyrl_hydra_args``.

Both cases here cost a real campaign a launch. Neither is visible in the config file, in a
schema check, or in a diff between two arms of the same campaign: the fault is in what the
launcher emits, and it is identical across every arm.

Run from the OT-Agent repo root with:
    .venv/bin/python -m pytest tests/hpc/test_rl_hydra_overrides.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hpc.rl_config_utils import ParsedRLConfig, build_skyrl_hydra_args
from hpc.rl_paths import RLPathManager, hydra_override_values

JOB_NAME = "override-regression"


@pytest.fixture
def hpc():
    return type("HPC", (), {"gpus_per_node": 4})()


def _build(tmp_path: Path, hpc, **parsed_fields) -> list[str]:
    root = tmp_path / JOB_NAME
    run_paths = RLPathManager(JOB_NAME, root, root).resolve()
    parsed = ParsedRLConfig(
        config_path=tmp_path / "config.yaml",
        raw={},
        entrypoint="skyrl_train.entrypoints.terminal_bench",
        **parsed_fields,
    )
    return build_skyrl_hydra_args(
        parsed, {"job_name": JOB_NAME}, hpc, run_paths=run_paths
    )


def test_terminal_bench_overrides_use_the_add_or_override_prefix(tmp_path, hpc):
    """Terminal-bench keys must survive a config group that already defines them.

    A single ``+`` means "add, and fail if present". The terminal_bench config group has
    grown its own defaults over time, so ``+`` now aborts config composition at startup:

        ConfigCompositionException: An item is already at
        'terminal_bench_config.trace_upload.enabled'.
    """
    arguments = _build(
        tmp_path,
        hpc,
        terminal_bench={
            "trace_upload": {"enabled": False},
            "harbor": {"name": "terminus-2"},
        },
    )

    emitted = [arg for arg in arguments if "terminal_bench_config." in arg]
    assert emitted, "no terminal_bench overrides were emitted"
    assert all(arg.startswith("++") for arg in emitted), emitted


def test_offline_wandb_selects_the_console_backend(tmp_path, hpc, monkeypatch, capsys):
    """An offline wandb backend hangs wandb.init(); console is the safe equivalent.

    SkyRL's Tracking() passes an explicit ``settings=`` to ``wandb.init()``, which overrides
    WANDB_MODE, so the wandb backend reaches for api.wandb.ai even when the launcher has
    pinned offline mode. On a compute node with no egress that call never returns.
    """
    monkeypatch.setenv("WANDB_MODE", "offline")

    arguments = _build(tmp_path, hpc, trainer={"logger": "wandb"})

    assert hydra_override_values(arguments)["trainer.logger"] == "console"
    assert "wandb -> console" in capsys.readouterr().out


def test_online_wandb_keeps_the_wandb_backend(tmp_path, hpc, monkeypatch):
    """A cluster with egress opts back in by exporting WANDB_MODE=online."""
    monkeypatch.setenv("WANDB_MODE", "online")

    arguments = _build(tmp_path, hpc, trainer={"logger": "wandb"})

    assert hydra_override_values(arguments)["trainer.logger"] == "wandb"


def test_a_non_wandb_backend_is_left_alone(tmp_path, hpc, monkeypatch):
    """The guard only ever downgrades wandb; it must not rewrite an explicit choice."""
    monkeypatch.setenv("WANDB_MODE", "offline")

    arguments = _build(tmp_path, hpc, trainer={"logger": "tensorboard"})

    assert hydra_override_values(arguments)["trainer.logger"] == "tensorboard"
