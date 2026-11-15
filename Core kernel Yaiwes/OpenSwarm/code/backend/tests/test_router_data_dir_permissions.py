"""9Router's state dir must be owner-only.

Its db.json carries live subscription access AND refresh tokens in plaintext, and 9Router writes
that file 0644. On a shared machine every other local account could read them. We tighten the
directory rather than the file because 9Router rewrites db.json on every token refresh, so a chmod
on the file itself would be undone within the hour.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_router_data_dir_permissions.py -v
"""

import os
import stat

import pytest

import backend.apps.nine_router.process as process


@pytest.fixture
def p_data_dir(tmp_path, monkeypatch):
    d = tmp_path / "9router"
    d.mkdir()
    monkeypatch.setenv("DATA_DIR", str(d))
    return d


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_group_and_world_readable_dir_is_tightened(p_data_dir):
    os.chmod(p_data_dir, 0o755)
    process.harden_data_dir_permissions()
    assert stat.S_IMODE(os.stat(p_data_dir).st_mode) == 0o700


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_tokens_are_unreadable_by_others_afterwards(p_data_dir):
    """The property that actually matters, stated as the attacker sees it: no bit outside the owner."""
    os.chmod(p_data_dir, 0o755)
    (p_data_dir / "db.json").write_text('{"providerConnections":[]}')
    process.harden_data_dir_permissions()
    assert stat.S_IMODE(os.stat(p_data_dir).st_mode) & 0o077 == 0


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_already_tight_dir_is_left_alone(p_data_dir):
    os.chmod(p_data_dir, 0o700)
    before = os.stat(p_data_dir).st_mtime_ns
    process.harden_data_dir_permissions()
    assert stat.S_IMODE(os.stat(p_data_dir).st_mode) == 0o700
    assert os.stat(p_data_dir).st_mtime_ns == before


def test_missing_dir_does_not_raise(tmp_path, monkeypatch):
    """Runs before 9Router has ever started, so the dir legitimately may not exist yet."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "nope"))
    process.harden_data_dir_permissions()
