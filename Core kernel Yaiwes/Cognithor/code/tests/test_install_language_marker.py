"""Regression tests for Issue #114: installer language choice must reach config.

The Inno Setup wizard writes %USERPROFILE%\\.cognithor\\install_language.txt with
"en" or "de". ``bootstrap_windows.resolve_install_language`` consumes it on first
run so the user's installer choice beats OS-locale detection.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
BOOTSTRAP_PATH = REPO / "scripts" / "bootstrap_windows.py"


@pytest.fixture(scope="module")
def bootstrap_module():
    spec = importlib.util.spec_from_file_location("bootstrap_windows_mod", BOOTSTRAP_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bootstrap_windows_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestResolveInstallLanguage:
    def test_marker_wins_over_locale(self, bootstrap_module, tmp_path, monkeypatch):
        """Installer-written marker overrides OS locale — the core fix."""
        (tmp_path / "install_language.txt").write_text("en", encoding="utf-8")
        # Force OS locale to German to prove the marker wins.
        import locale as _locale_mod

        monkeypatch.setattr(_locale_mod, "getlocale", lambda *_a, **_kw: ("de_DE", "UTF-8"))
        lang, source = bootstrap_module.resolve_install_language(tmp_path)
        assert lang == "en"
        assert source == "installer"

    def test_marker_is_consumed_after_read(self, bootstrap_module, tmp_path):
        """Marker must be deleted on read so re-runs fall back to locale."""
        marker = tmp_path / "install_language.txt"
        marker.write_text("de", encoding="utf-8")
        bootstrap_module.resolve_install_language(tmp_path)
        assert not marker.exists()

    def test_falls_back_to_locale_when_no_marker(self, bootstrap_module, tmp_path, monkeypatch):
        import locale as _locale_mod

        monkeypatch.setattr(_locale_mod, "getlocale", lambda *_a, **_kw: ("de_DE", "UTF-8"))
        lang, source = bootstrap_module.resolve_install_language(tmp_path)
        assert lang == "de"
        assert source == "locale"

    def test_locale_english(self, bootstrap_module, tmp_path, monkeypatch):
        import locale as _locale_mod

        monkeypatch.setattr(_locale_mod, "getlocale", lambda *_a, **_kw: ("en_US", "UTF-8"))
        lang, source = bootstrap_module.resolve_install_language(tmp_path)
        assert lang == "en"
        assert source == "locale"

    def test_invalid_marker_falls_back(self, bootstrap_module, tmp_path, monkeypatch):
        """A garbage marker file must be ignored, not treated as a valid lang."""
        (tmp_path / "install_language.txt").write_text("xx", encoding="utf-8")
        import locale as _locale_mod

        monkeypatch.setattr(_locale_mod, "getlocale", lambda *_a, **_kw: ("en_US", "UTF-8"))
        lang, source = bootstrap_module.resolve_install_language(tmp_path)
        assert lang == "en"
        assert source == "locale"

    def test_marker_zh(self, bootstrap_module, tmp_path):
        (tmp_path / "install_language.txt").write_text("zh", encoding="utf-8")
        lang, source = bootstrap_module.resolve_install_language(tmp_path)
        assert lang == "zh"
        assert source == "installer"
