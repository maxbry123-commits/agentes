"""An app whose record vanished but whose work survived must come back.

An app is a record plus a workspace folder. Lose the record and the work sits on disk completely
invisible, with no way for the user to even know it is there. Measured on a real packaged store:
2 apps with genuine work ("Calculator", a 235-line rewrite of the template; "Voxelcraft", a
hand-written game.js) had no record.

The hard part is NOT recovering. It is refusing to recover the other 6, which were template seeds
minted seconds apart by a page that has since been deleted and never touched again. Bringing those
back would hand every user a pile of empty cards, which is a worse product than the bug.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_recover_orphaned_apps.py -v
"""

from __future__ import annotations

import json
import os

import pytest


@pytest.fixture
def p_store(tmp_path, monkeypatch):
    """A data root with a workspace dir, isolated from the real store."""
    root = tmp_path / "data"
    ws = root / "outputs_workspace"
    out = root / "outputs"
    ws.mkdir(parents=True)
    out.mkdir(parents=True)
    import backend.apps.outputs.recover_orphaned_apps as mod
    import backend.apps.outputs.workspace_io as wio
    monkeypatch.setattr(mod, "OUTPUTS_WORKSPACE_DIR", str(ws))
    monkeypatch.setattr(mod, "P_MARKER", str(root / "orphan_app_recovery.done"))
    monkeypatch.setattr(wio, "OUTPUTS_WORKSPACE_DIR", str(ws), raising=False)
    monkeypatch.setattr(wio, "DATA_DIR", str(out), raising=False)
    return {"root": root, "ws": ws, "out": out, "mod": mod, "wio": wio}


def p_workspace(p_store, wid: str, name=None, description="") -> str:
    d = p_store["ws"] / wid
    d.mkdir()
    (d / "index.html").write_text("<html></html>")
    if name is not None:
        (d / "meta.json").write_text(json.dumps({"name": name, "description": description}))
    return wid


def p_names(p_store):
    return sorted(o.name for o in p_store["wio"].load_all())


def test_an_app_with_real_work_comes_back(p_store):
    p_workspace(p_store, "ws-calc", name="Calculator", description="does sums")

    report = p_store["mod"].recover_orphaned_apps()

    assert report.recovered == ["Calculator"]
    assert p_names(p_store) == ["Calculator"]
    restored = p_store["wio"].load_all()[0]
    assert restored.workspace_id == "ws-calc"
    assert restored.description == "does sums", "the app's own meta.json is the source of truth"


def test_an_unused_template_seed_stays_buried(p_store):
    """THE constraint. 6 of 8 real orphans were these; resurrecting them is worse than the bug."""
    p_workspace(p_store, "ws-seed", name="Untitled App")

    report = p_store["mod"].recover_orphaned_apps()

    assert report.recovered == []
    assert report.skipped_unused == 1
    assert p_names(p_store) == []


def test_a_workspace_with_no_meta_stays_buried(p_store):
    p_workspace(p_store, "ws-bare", name=None)
    report = p_store["mod"].recover_orphaned_apps()
    assert report.recovered == []
    assert report.skipped_unused == 1


def test_the_real_mix_recovers_exactly_the_two(p_store):
    """The packaged store as measured: 3 named 'Untitled App', 3 with no meta, 2 real."""
    for i in range(3):
        p_workspace(p_store, f"ws-seed{i}", name="Untitled App")
    for i in range(3):
        p_workspace(p_store, f"ws-bare{i}", name=None)
    p_workspace(p_store, "ws-calc", name="Calculator")
    p_workspace(p_store, "ws-voxel", name="Voxelcraft")

    report = p_store["mod"].recover_orphaned_apps()

    assert sorted(report.recovered) == ["Calculator", "Voxelcraft"]
    assert report.skipped_unused == 6


def test_a_workspace_that_still_has_a_record_is_left_alone(p_store):
    from backend.apps.outputs.models import Output
    p_workspace(p_store, "ws-live", name="Live App")
    p_store["wio"].save(Output(name="Live App", workspace_id="ws-live"))

    report = p_store["mod"].recover_orphaned_apps()

    assert report.recovered == []
    assert p_names(p_store) == ["Live App"], "must not create a duplicate record"


def test_it_runs_only_once(p_store):
    """Deleting an app leaves its workspace behind, so a recovery that ran every boot would make
    deletion impossible: the app would be back the next morning."""
    p_workspace(p_store, "ws-calc", name="Calculator")
    assert p_store["mod"].recover_orphaned_apps().recovered == ["Calculator"]

    for o in p_store["wio"].load_all():
        os.remove(os.path.join(str(p_store["out"]), f"{o.id}.json"))

    assert p_store["mod"].recover_orphaned_apps().recovered == []
    assert p_names(p_store) == [], "the user deleted it; it must stay deleted"


def test_force_overrides_the_marker(p_store):
    p_workspace(p_store, "ws-calc", name="Calculator")
    p_store["mod"].recover_orphaned_apps()
    for o in p_store["wio"].load_all():
        os.remove(os.path.join(str(p_store["out"]), f"{o.id}.json"))

    assert p_store["mod"].recover_orphaned_apps(force=True).recovered == ["Calculator"]


def test_a_blank_name_counts_as_unused(p_store):
    p_workspace(p_store, "ws-blank", name="   ")
    assert p_store["mod"].recover_orphaned_apps().skipped_unused == 1


def test_unparseable_meta_does_not_break_the_sweep(p_store):
    d = p_store["ws"] / "ws-broken"
    d.mkdir()
    (d / "meta.json").write_text("{not json")
    p_workspace(p_store, "ws-calc", name="Calculator")

    report = p_store["mod"].recover_orphaned_apps()

    assert report.recovered == ["Calculator"], "one bad workspace must not strand the rest"
