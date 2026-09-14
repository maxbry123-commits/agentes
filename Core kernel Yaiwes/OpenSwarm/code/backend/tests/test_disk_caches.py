import json
import os
import time

import pytest

from backend.apps.settings import store
from backend.apps.settings.models import AppSettings
from backend.apps.tools_lib import tools_lib
from backend.apps.tools_lib.models import ToolDefinition


@pytest.fixture
def settings_tmp(tmp_path, monkeypatch):
    f = tmp_path / "settings.json"
    monkeypatch.setattr(store, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(store, "SETTINGS_FILE", str(f))
    monkeypatch.setattr(store, "p_cached_settings", None)
    monkeypatch.setattr(store, "p_cached_sig", None)
    return f


@pytest.fixture
def tools_tmp(tmp_path, monkeypatch):
    d = tmp_path / "tools"
    d.mkdir()
    monkeypatch.setattr(tools_lib, "DATA_DIR", str(d))
    monkeypatch.setattr(tools_lib, "p_tools_cache", None)
    monkeypatch.setattr(tools_lib, "p_tools_cache_sig", None)
    return d


def p_bump_mtime(path):
    # FAT32-style coarse clocks could hide a same-size rewrite; force a distinct mtime.
    st = os.stat(path)
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000))


def test_settings_write_through_is_fresh(settings_tmp):
    s = store.load_settings()
    s.theme = "light"
    store.save_settings(s)
    assert store.load_settings().theme == "light"
    s2 = store.load_settings()
    s2.theme = "dark"
    store.save_settings(s2)
    assert store.load_settings().theme == "dark"


def test_settings_external_edit_detected(settings_tmp):
    store.save_settings(AppSettings(theme="dark"))
    assert store.load_settings().theme == "dark"
    raw = json.loads(settings_tmp.read_text())
    raw["theme"] = "light"
    settings_tmp.write_text(json.dumps(raw))
    p_bump_mtime(settings_tmp)
    assert store.load_settings().theme == "light"


def test_settings_cache_returns_isolated_copies(settings_tmp):
    store.save_settings(AppSettings(theme="dark"))
    a = store.load_settings()
    a.theme = "light"
    assert store.load_settings().theme == "dark"


def test_settings_file_deleted_falls_back_to_defaults(settings_tmp):
    store.save_settings(AppSettings(theme="light"))
    os.remove(settings_tmp)
    assert store.load_settings().theme == AppSettings().theme


def test_tools_write_then_list_is_fresh(tools_tmp):
    assert tools_lib.load_all_tools() == []
    t = ToolDefinition(name="Alpha", description="a")
    tools_lib.save(t)
    p_bump_mtime(tools_tmp / f"{t.id}.json")
    names = [x.name for x in tools_lib.load_all_tools()]
    assert names == ["Alpha"]

    t2 = ToolDefinition(name="Beta", description="b")
    tools_lib.save(t2)
    assert sorted(x.name for x in tools_lib.load_all_tools()) == ["Alpha", "Beta"]


def test_tools_delete_detected(tools_tmp):
    t = ToolDefinition(name="Gone", description="g")
    tools_lib.save(t)
    assert [x.name for x in tools_lib.load_all_tools()] == ["Gone"]
    os.remove(tools_tmp / f"{t.id}.json")
    assert tools_lib.load_all_tools() == []


def test_tools_in_place_rewrite_detected(tools_tmp):
    t = ToolDefinition(name="Old", description="x")
    tools_lib.save(t)
    assert [x.name for x in tools_lib.load_all_tools()] == ["Old"]
    t.name = "New"
    tools_lib.save(t)
    p_bump_mtime(tools_tmp / f"{t.id}.json")
    assert [x.name for x in tools_lib.load_all_tools()] == ["New"]


def test_tools_cached_hit_skips_reparse(tools_tmp, monkeypatch):
    tools_lib.save(ToolDefinition(name="Once", description="o"))
    tools_lib.load_all_tools()
    def boom(*a, **k):
        raise AssertionError("disk re-parse on unchanged dir")
    monkeypatch.setattr(json, "load", boom)
    assert [x.name for x in tools_lib.load_all_tools()] == ["Once"]
