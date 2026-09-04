"""Unit tests for ``hpc/rl_launch_utils.py:resolve_rl_repo_dir`` (+ ``_resolve_skyrl_home``).

The RL training repo dir is historically named ``SkyRL`` but its contents may
be replaced by MarinSkyRL while keeping the name ``SkyRL``, or the dir may be
named ``MarinSkyRL``. ``resolve_rl_repo_dir`` resolves a filesystem path to
whichever exists, while staying byte-identical for existing SkyRL-only
deployments. The Python import name (``skyrl_train``) is unaffected by the dir
name and is NOT exercised here.

Run from the OT-Agent repo root with:
    .venv/bin/python -m pytest tests/hpc/test_resolve_rl_repo_dir.py -v
"""

from __future__ import annotations


import pytest

from hpc.rl_launch_utils import (
    _build_container_pythonpath,
    _resolve_skyrl_home,
    resolve_rl_repo_dir,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Ensure overrides don't leak between cases."""
    monkeypatch.delenv("RL_REPO_DIR", raising=False)
    monkeypatch.delenv("SKYRL_HOME", raising=False)
    monkeypatch.delenv("RL_CONTAINER_PYDEPS", raising=False)
    monkeypatch.delenv("HARBOR_HOME", raising=False)
    monkeypatch.delenv("DCFT", raising=False)
    monkeypatch.delenv("WORKDIR", raising=False)
    monkeypatch.delenv("PYTHONPATH", raising=False)
    yield


# --- resolve_rl_repo_dir: probe precedence ---------------------------------


def test_skyrl_only(tmp_path):
    """SkyRL exists alone -> returns <parent>/SkyRL (byte-identical back-compat)."""
    (tmp_path / "SkyRL").mkdir()
    assert resolve_rl_repo_dir(str(tmp_path)) == str(tmp_path / "SkyRL")


def test_marinskyrl_only(tmp_path):
    """Only MarinSkyRL exists -> returns <parent>/MarinSkyRL."""
    (tmp_path / "MarinSkyRL").mkdir()
    assert resolve_rl_repo_dir(str(tmp_path)) == str(tmp_path / "MarinSkyRL")


def test_both_prefers_skyrl(tmp_path):
    """Both exist -> SkyRL wins (probe order keeps existing deployments stable)."""
    (tmp_path / "SkyRL").mkdir()
    (tmp_path / "MarinSkyRL").mkdir()
    assert resolve_rl_repo_dir(str(tmp_path)) == str(tmp_path / "SkyRL")


def test_neither_falls_back_to_skyrl(tmp_path):
    """Neither exists -> literal <parent>/SkyRL fallback (clone target)."""
    assert resolve_rl_repo_dir(str(tmp_path)) == str(tmp_path / "SkyRL")


def test_env_override_honored_verbatim(tmp_path, monkeypatch):
    """RL_REPO_DIR override is returned verbatim, even when a candidate exists."""
    (tmp_path / "SkyRL").mkdir()
    override = str(tmp_path / "somewhere" / "CustomRLRepo")
    monkeypatch.setenv("RL_REPO_DIR", override)
    assert resolve_rl_repo_dir(str(tmp_path)) == override


def test_env_override_honored_when_neither_exists(tmp_path, monkeypatch):
    """Override wins even when neither candidate dir exists."""
    override = "/nonexistent/MarinSkyRL"
    monkeypatch.setenv("RL_REPO_DIR", override)
    assert resolve_rl_repo_dir(str(tmp_path)) == override


# --- _resolve_skyrl_home: SKYRL_HOME-based resolution ----------------------


def test_skyrl_home_existing_returned_unchanged(tmp_path, monkeypatch):
    """SKYRL_HOME points at an existing dir -> returned unchanged (precedence a)."""
    home = tmp_path / "SkyRL"
    home.mkdir()
    monkeypatch.setenv("SKYRL_HOME", str(home))
    assert _resolve_skyrl_home() == str(home)


def test_skyrl_home_missing_probes_parent_for_alternate(tmp_path, monkeypatch):
    """SKYRL_HOME hardcoded to .../SkyRL but only .../MarinSkyRL exists -> probe wins."""
    (tmp_path / "MarinSkyRL").mkdir()
    monkeypatch.setenv("SKYRL_HOME", str(tmp_path / "SkyRL"))  # does not exist
    assert _resolve_skyrl_home() == str(tmp_path / "MarinSkyRL")


def test_skyrl_home_unset_returns_none(monkeypatch):
    """SKYRL_HOME unset -> None (callers skip adding the path, as before)."""
    assert _resolve_skyrl_home() is None


def test_container_pythonpath_exposes_root_and_trainer_packages(tmp_path, monkeypatch):
    """The live checkout exposes both root ``cloud`` and bundled ``skyrl_train`` packages."""
    skyrl_home = tmp_path / "SkyRL"
    (skyrl_home / "cloud").mkdir(parents=True)
    (skyrl_home / "skyrl-train" / "skyrl_train").mkdir(parents=True)
    monkeypatch.setenv("SKYRL_HOME", str(skyrl_home))

    assert _build_container_pythonpath().split(":") == [
        str(skyrl_home),
        str(skyrl_home / "skyrl-train"),
    ]


def test_container_pythonpath_exposes_skyrl_gym_when_the_checkout_ships_it(
    tmp_path, monkeypatch
):
    """A checkout carrying skyrl-gym must win over the SIF's baked copy.

    skyrl_train.trajectory_runners imports skyrl_gym.verification at module import time.
    Without this entry ``skyrl_gym`` resolves to /opt/SkyRL/skyrl-gym inside the image,
    which is pinned at build time, and any newer host tree fails to import.
    """
    skyrl_home = tmp_path / "SkyRL"
    (skyrl_home / "cloud").mkdir(parents=True)
    (skyrl_home / "skyrl-train" / "skyrl_train").mkdir(parents=True)
    (skyrl_home / "skyrl-gym" / "skyrl_gym").mkdir(parents=True)
    monkeypatch.setenv("SKYRL_HOME", str(skyrl_home))

    assert _build_container_pythonpath().split(":") == [
        str(skyrl_home),
        str(skyrl_home / "skyrl-train"),
        str(skyrl_home / "skyrl-gym"),
    ]
