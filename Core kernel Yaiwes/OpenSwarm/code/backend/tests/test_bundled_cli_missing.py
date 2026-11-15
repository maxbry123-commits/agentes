"""Pins the boot-time AV-quarantine detector: binary present = quiet, binary
deleted out of an intact _bundled dir = flagged with the expected path, no
_bundled dir at all (source installs) = quiet, so it can never cry wolf on dev."""
import platform
import sys
import types

from backend.apps.agents.core.bundled_cli_missing import bundled_cli_missing

P_CLI_NAME = "claude.exe" if platform.system() == "Windows" else "claude"


def p_fake_sdk(monkeypatch, tmp_path, with_dir=True, with_binary=True):
    pkg = tmp_path / "claude_agent_sdk"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    if with_dir:
        (pkg / "_bundled").mkdir()
        if with_binary:
            (pkg / "_bundled" / P_CLI_NAME).write_text("stub")
    mod = types.ModuleType("claude_agent_sdk")
    mod.__file__ = str(pkg / "__init__.py")
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", mod)


def test_present_binary_is_quiet(monkeypatch, tmp_path):
    p_fake_sdk(monkeypatch, tmp_path)
    assert bundled_cli_missing() is None


def test_deleted_binary_is_flagged_with_path(monkeypatch, tmp_path):
    p_fake_sdk(monkeypatch, tmp_path, with_binary=False)
    result = bundled_cli_missing()
    assert result is not None
    assert result.endswith(P_CLI_NAME)


def test_no_bundled_dir_is_quiet(monkeypatch, tmp_path):
    p_fake_sdk(monkeypatch, tmp_path, with_dir=False)
    assert bundled_cli_missing() is None
