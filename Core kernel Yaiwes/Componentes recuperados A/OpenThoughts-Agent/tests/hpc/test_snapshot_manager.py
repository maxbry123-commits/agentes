"""Unit tests for ``hpc/snapshot_manager.py``.

The tests inject a ``FakeDaytona`` factory into ``ensure_snapshots`` /
``cleanup_unused_snapshots`` / etc. via the ``daytona_factory`` arg, so they
never touch the real Daytona SDK or network. They also patch
``_discover_hash_to_env_dir`` to avoid needing actual on-disk task dirs or
the harbor sibling repo.

Run from the OT-Agent repo root with:
    .venv/bin/python -m pytest tests/hpc/test_snapshot_manager.py -v
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import pytest

from hpc import snapshot_manager as sm
from hpc.snapshot_manager import (
    OrgConfig,
    SnapshotCapExceeded,
    ensure_snapshots,
    cleanup_unused_snapshots,
    load_orgs_from_env,
    _snapshot_name,
)


# -----------------------------------------------------------------------------
# Fakes
# -----------------------------------------------------------------------------


class _FakeSnap:
    def __init__(self, name: str, state: str):
        self.name = name
        self.state = state


class _FakeList:
    def __init__(self, items: List[_FakeSnap]):
        self.items = list(items)
        self.total = len(items)
        self.total_pages = 1


class FakeDaytona:
    """In-memory ``Daytona`` substitute. ``snapshot.{list,get,create,delete}``."""

    def __init__(
        self,
        *,
        initial_state: Optional[Dict[str, List[str]]] = None,
        rate_limit_hits: int = 0,
        not_found_states: Optional[set] = None,
    ):
        # state-machine fake: each `get` pops the next state for that name
        self._states: Dict[str, List[str]] = {
            k: list(v) for k, v in (initial_state or {}).items()
        }
        self._created: List[str] = []
        self._deleted: List[str] = []
        self._not_found = set(not_found_states or [])
        self._rate_limit_hits_left = rate_limit_hits
        self.snapshot = self  # so callers can do client.snapshot.get(...)

    # SDK surface ---------------------------------------------------------

    def _maybe_rate_limit(self):
        if self._rate_limit_hits_left > 0:
            self._rate_limit_hits_left -= 1
            raise _FakeRateLimitError("rate limit")

    def list(self, *, limit=1, page=None):
        self._maybe_rate_limit()
        snaps = [
            _FakeSnap(name, self._states.get(name, ["ACTIVE"])[-1])
            for name in self._states
        ]
        return _FakeList(snaps)

    def get(self, name):
        self._maybe_rate_limit()
        if name in self._not_found and not self._states.get(name):
            raise _FakeNotFoundError(f"snapshot {name} not found")
        states = self._states.get(name)
        if not states:
            raise _FakeNotFoundError(f"snapshot {name} not found")
        state = states.pop(0) if len(states) > 1 else states[0]
        return _FakeSnap(name, state)

    def create(self, params, *, on_logs=None, timeout=None):
        self._maybe_rate_limit()
        name = params.name
        self._created.append(name)
        # newly created snapshots become ACTIVE on next get()
        self._states[name] = ["ACTIVE"]
        return _FakeSnap(name, "ACTIVE")

    def delete(self, snap):
        self._maybe_rate_limit()
        name = getattr(snap, "name", str(snap))
        self._deleted.append(name)
        self._states.pop(name, None)


class _FakeCreateParams:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _FakeImage:
    @classmethod
    def from_dockerfile(cls, path: str):
        return f"image_from:{path}"


class _FakeNotFoundError(Exception):
    pass


class _FakeRateLimitError(Exception):
    pass


# -----------------------------------------------------------------------------
# Test fixtures + helpers
# -----------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_sdk_imports(monkeypatch, tmp_path):
    """Patch SDK imports referenced inside ``_ensure_one`` and helpers.

    The real daytona SDK isn't a test dependency; redirect every import to
    our fakes. Also redirect the registry to ``tmp_path`` so each test gets
    a clean slate.
    """
    fake_daytona_mod = type(sys_mod := __import__("sys").modules["__main__"])  # noqa: F841  # placeholder
    # Inject lightweight modules for the imports inside snapshot_manager.
    import sys
    import types

    daytona_pkg = types.ModuleType("daytona")
    daytona_pkg.CreateSnapshotParams = _FakeCreateParams

    # ``_default_daytona_factory`` imports Daytona/DaytonaConfig from this
    # module; supply lightweight stand-ins so the shim test can also exercise
    # the default factory path.
    class _FakeDaytonaConfig:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class _FakeDaytonaCls:
        def __init__(self, _cfg=None):
            # Return a fresh FakeDaytona that records nothing of interest.
            self._fake = FakeDaytona()

        def __getattr__(self, item):
            return getattr(self._fake, item)

    daytona_pkg.Daytona = _FakeDaytonaCls
    daytona_pkg.DaytonaConfig = _FakeDaytonaConfig
    daytona_common = types.ModuleType("daytona.common")
    daytona_common_image = types.ModuleType("daytona.common.image")
    daytona_common_image.Image = _FakeImage
    daytona_common_errors = types.ModuleType("daytona.common.errors")
    daytona_common_errors.DaytonaNotFoundError = _FakeNotFoundError
    daytona_common_errors.DaytonaRateLimitError = _FakeRateLimitError

    monkeypatch.setitem(sys.modules, "daytona", daytona_pkg)
    monkeypatch.setitem(sys.modules, "daytona.common", daytona_common)
    monkeypatch.setitem(sys.modules, "daytona.common.image", daytona_common_image)
    monkeypatch.setitem(sys.modules, "daytona.common.errors", daytona_common_errors)

    # Patch the registry file location.
    monkeypatch.setenv("OT_AGENT_SNAPSHOT_REGISTRY", str(tmp_path / "registry.jsonl"))

    # Patch out time.sleep so the polling loop doesn't actually sleep.
    monkeypatch.setattr(sm.time, "sleep", lambda *a, **kw: None)

    yield


def _hash_to_env(hashes, tmp_path):
    """Build a {hash: env_dir} dict pointing each hash at a tmp env dir containing a Dockerfile."""
    out = {}
    for h in hashes:
        env_dir = tmp_path / f"env_{h}"
        env_dir.mkdir(parents=True, exist_ok=True)
        (env_dir / "Dockerfile").write_text("FROM scratch\n")
        out[h] = env_dir
    return out


def _patch_discovery(monkeypatch, hash_to_env_dir):
    class _FakeStats:
        total_tasks = sum(1 for _ in hash_to_env_dir)
        unique_hashes = len(hash_to_env_dir)

    monkeypatch.setattr(
        sm,
        "_discover_hash_to_env_dir",
        lambda paths: (hash_to_env_dir, _FakeStats()),
    )


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_single_org_happy_path(monkeypatch, tmp_path):
    """One org, all snapshots missing → all built → all ACTIVE."""
    h2e = _hash_to_env(["aaa111", "bbb222"], tmp_path)
    _patch_discovery(monkeypatch, h2e)

    fake = FakeDaytona()
    result = ensure_snapshots(
        ["/fake/tasks"],
        [OrgConfig(name="org1", api_key="k")],
        daytona_factory=lambda org: fake,
    )
    assert result.built == 2
    assert result.skipped == 0
    assert "harbor__aaa111__snapshot" in fake._created
    assert "harbor__bbb222__snapshot" in fake._created
    assert result.per_org["org1"].active == 2


def test_multi_org(monkeypatch, tmp_path):
    """Two orgs, both get the same snapshots registered."""
    h2e = _hash_to_env(["abc123"], tmp_path)
    _patch_discovery(monkeypatch, h2e)

    fakes = {"org1": FakeDaytona(), "org2": FakeDaytona()}
    ensure_snapshots(
        ["/fake/tasks"],
        [OrgConfig(name="org1", api_key="k1"), OrgConfig(name="org2", api_key="k2")],
        daytona_factory=lambda org: fakes[org.name],
    )
    assert "harbor__abc123__snapshot" in fakes["org1"]._created
    assert "harbor__abc123__snapshot" in fakes["org2"]._created


def test_pending_to_active_transition(monkeypatch, tmp_path):
    """PENDING on first get → ACTIVE on second get → no rebuild."""
    h2e = _hash_to_env(["pen111"], tmp_path)
    _patch_discovery(monkeypatch, h2e)

    fake = FakeDaytona(
        initial_state={"harbor__pen111__snapshot": ["PENDING", "ACTIVE"]}
    )
    result = ensure_snapshots(
        ["/fake/tasks"],
        [OrgConfig(name="org1", api_key="k")],
        daytona_factory=lambda org: fake,
        pending_wait_s=10.0,
    )
    # Snapshot already existed; no create call was issued.
    assert fake._created == []
    assert result.errors == []


def test_pending_then_error_triggers_rebuild(monkeypatch, tmp_path):
    """PENDING → ERROR during wait → delete + recreate path."""
    h2e = _hash_to_env(["err111"], tmp_path)
    _patch_discovery(monkeypatch, h2e)

    fake = FakeDaytona(
        initial_state={
            "harbor__err111__snapshot": ["PENDING", "ERROR"],
        }
    )
    ensure_snapshots(
        ["/fake/tasks"],
        [OrgConfig(name="org1", api_key="k")],
        daytona_factory=lambda org: fake,
        pending_wait_s=10.0,
    )
    assert "harbor__err111__snapshot" in fake._deleted
    assert "harbor__err111__snapshot" in fake._created


def test_cap_overrun_hard_fails(monkeypatch, tmp_path):
    """total_existing + new_needed > max_org_snapshots raises BEFORE any build."""
    h2e = _hash_to_env(["new111"], tmp_path)
    _patch_discovery(monkeypatch, h2e)

    # Org already has 60 snapshots; cap is 60; needed=1 → 61 > 60.
    existing = {f"harbor__existing{i:03d}__snapshot": ["ACTIVE"] for i in range(60)}
    fake = FakeDaytona(initial_state=existing)
    with pytest.raises(SnapshotCapExceeded):
        ensure_snapshots(
            ["/fake/tasks"],
            [OrgConfig(name="full", api_key="k")],
            daytona_factory=lambda org: fake,
            max_org_snapshots=60,
        )
    # No builds attempted.
    assert "harbor__new111__snapshot" not in fake._created


def test_max_new_snapshots_safety(monkeypatch, tmp_path):
    """More unique envs than max_new_snapshots → SnapshotCapExceeded."""
    h2e = _hash_to_env([f"h{i:02d}" for i in range(15)], tmp_path)
    _patch_discovery(monkeypatch, h2e)
    fake = FakeDaytona()
    with pytest.raises(SnapshotCapExceeded):
        ensure_snapshots(
            ["/fake/tasks"],
            [OrgConfig(name="org1", api_key="k")],
            daytona_factory=lambda org: fake,
            max_new_snapshots=10,
        )


def test_rate_limit_backoff_recovers(monkeypatch, tmp_path):
    """Rate-limited on first call → backs off → succeeds."""
    h2e = _hash_to_env(["rate11"], tmp_path)
    _patch_discovery(monkeypatch, h2e)

    fake = FakeDaytona(rate_limit_hits=2)
    ensure_snapshots(
        ["/fake/tasks"],
        [OrgConfig(name="org1", api_key="k")],
        daytona_factory=lambda org: fake,
    )
    assert "harbor__rate11__snapshot" in fake._created


def test_registry_roundtrip_and_dedup(monkeypatch, tmp_path):
    """Run ensure twice; second run reads registry fast-path."""
    h2e = _hash_to_env(["reg111"], tmp_path)
    _patch_discovery(monkeypatch, h2e)

    fake = FakeDaytona()
    ensure_snapshots(
        ["/fake/tasks"],
        [OrgConfig(name="org1", api_key="k")],
        daytona_factory=lambda org: fake,
    )
    # Second run: snapshot is ACTIVE on the fake's side, so we should skip.
    ensure_snapshots(
        ["/fake/tasks"],
        [OrgConfig(name="org1", api_key="k")],
        daytona_factory=lambda org: fake,
    )
    # Only one create across both runs.
    assert fake._created.count("harbor__reg111__snapshot") == 1

    # Registry file should contain at least one record for the (hash, org).
    reg_path = Path(os.environ["OT_AGENT_SNAPSHOT_REGISTRY"])
    assert reg_path.exists()
    records = [
        json.loads(line) for line in reg_path.read_text().splitlines() if line.strip()
    ]
    matching = [r for r in records if r["hash"] == "reg111" and r["org"] == "org1"]
    assert len(matching) >= 1
    assert matching[-1]["state"] == "ACTIVE"


def test_registry_stale_overwritten(monkeypatch, tmp_path):
    """Registry says ACTIVE; SDK 404s; manager rebuilds + overwrites record."""
    h2e = _hash_to_env(["stale1"], tmp_path)
    _patch_discovery(monkeypatch, h2e)

    # Seed the registry with an ACTIVE entry for stale1@org1.
    reg_path = Path(os.environ["OT_AGENT_SNAPSHOT_REGISTRY"])
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(
        json.dumps(
            {
                "hash": "stale1",
                "snapshot_name": "harbor__stale1__snapshot",
                "org": "org1",
                "state": "ACTIVE",
                "env_dir_path": "old",
                "ts": 0.0,
            }
        )
        + "\n"
    )

    # SDK reports the snapshot missing.
    fake = FakeDaytona(not_found_states={"harbor__stale1__snapshot"})
    ensure_snapshots(
        ["/fake/tasks"],
        [OrgConfig(name="org1", api_key="k")],
        daytona_factory=lambda org: fake,
    )
    # Manager called create() to reconcile.
    assert "harbor__stale1__snapshot" in fake._created


def test_concurrent_create_idempotency(monkeypatch, tmp_path):
    """create() raises 'already exists' → swallowed; treated as success."""
    h2e = _hash_to_env(["conc11"], tmp_path)
    _patch_discovery(monkeypatch, h2e)

    fake = FakeDaytona(not_found_states={"harbor__conc11__snapshot"})

    def _create_already_exists(params, on_logs=None, timeout=None):
        # First call raises "already exists"; populate the state so the post-create wait succeeds.
        fake._states[params.name] = ["ACTIVE"]
        raise RuntimeError("snapshot already exists in target region")

    fake.create = _create_already_exists  # type: ignore[assignment]
    result = ensure_snapshots(
        ["/fake/tasks"],
        [OrgConfig(name="org1", api_key="k")],
        daytona_factory=lambda org: fake,
    )
    assert result.errors == []


def test_backward_compat_shim_calls_unified_path(monkeypatch, tmp_path):
    """``prebuild_daytona_snapshots`` delegates to ``ensure_snapshots``."""
    from hpc import rl_launch_utils

    h2e = _hash_to_env(["compat1"], tmp_path)
    _patch_discovery(monkeypatch, h2e)

    monkeypatch.setenv("DAYTONA_API_KEY", "fakekey")
    monkeypatch.setattr(sm, "_default_daytona_factory", lambda org: FakeDaytona())

    # Call the shim; should not raise.
    rl_launch_utils.prebuild_daytona_snapshots(["/fake/tasks"])


def test_load_orgs_from_env(monkeypatch):
    """``load_orgs_from_env`` honors the ``DAYTONA_<NAME>_API_KEY`` convention."""
    monkeypatch.delenv("DAYTONA_API_KEY", raising=False)
    monkeypatch.setenv("DAYTONA_BASE_API_KEY", "kbase")
    monkeypatch.setenv("DAYTONA_DATA_API_KEY", "kdata")
    orgs = load_orgs_from_env(["base", "data"])
    assert {o.name for o in orgs} == {"base", "data"}
    assert {o.api_key for o in orgs} == {"kbase", "kdata"}

    # Empty selection raises.
    with pytest.raises(ValueError):
        load_orgs_from_env(["missing"])


def test_cleanup_only_deletes_unused(monkeypatch, tmp_path):
    """``cleanup_unused_snapshots`` keeps snapshots whose hashes are needed."""
    monkeypatch.setattr(sm, "time", sm.time)  # no-op guard
    fake = FakeDaytona(
        initial_state={
            "harbor__keep01__snapshot": ["ACTIVE"],
            "harbor__drop01__snapshot": ["ACTIVE"],
            "harbor__drop02__snapshot": ["ACTIVE"],
            "other__unrelated": ["ACTIVE"],
        }
    )
    needed = {"keep01"}
    result = cleanup_unused_snapshots(
        needed,
        [OrgConfig(name="org1", api_key="k")],
        daytona_factory=lambda org: fake,
    )
    assert set(fake._deleted) == {
        "harbor__drop01__snapshot",
        "harbor__drop02__snapshot",
    }
    assert "other__unrelated" not in fake._deleted  # untouched
    assert "harbor__keep01__snapshot" not in fake._deleted
    assert result.per_org["org1"] == 2


def test_snapshot_name_function():
    assert _snapshot_name("abc123", "") == "harbor__abc123__snapshot"
    assert _snapshot_name("abc123", "eu") == "harbor__abc123__eu__snapshot"


def test_maybe_prebuild_gates(monkeypatch, tmp_path):
    """The hook in ``launch_utils`` is a no-op for non-daytona env / empty inputs."""
    from hpc.launch_utils import maybe_prebuild_daytona_snapshots

    assert (
        maybe_prebuild_daytona_snapshots(
            ["/fake/tasks"],
            harbor_env="docker",
            orgs=[OrgConfig(name="x", api_key="k")],
        )
        is None
    )
    assert (
        maybe_prebuild_daytona_snapshots(
            [],
            harbor_env="daytona",
            orgs=[OrgConfig(name="x", api_key="k")],
        )
        is None
    )
    assert (
        maybe_prebuild_daytona_snapshots(
            ["/fake/tasks"],
            harbor_env="daytona",
            orgs=[],
        )
        is None
    )
