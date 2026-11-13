"""Coverage-Tests fuer startup_check.py -- fehlende Zeilen."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from cognithor.config import CognithorConfig, ensure_directory_structure
from cognithor.core.startup_check import (
    StartupChecker,
    StartupReport,
    _can_import,
    _import_name,
)


@pytest.fixture()
def config(tmp_path) -> CognithorConfig:
    cfg = CognithorConfig(cognithor_home=tmp_path)
    ensure_directory_structure(cfg)
    return cfg


# ============================================================================
# StartupReport
# ============================================================================


class TestStartupReport:
    def test_empty_report_ok(self) -> None:
        report = StartupReport()
        assert report.ok is True
        assert report.checks_passed == []
        assert report.fixes_applied == []
        assert report.warnings == []
        assert report.errors == []

    def test_report_with_errors_not_ok(self) -> None:
        report = StartupReport(errors=["something broke"])
        assert report.ok is False

    def test_merge(self) -> None:
        r1 = StartupReport(checks_passed=["a"], fixes_applied=["b"])
        r2 = StartupReport(warnings=["c"], errors=["d"])
        r1.merge(r2)
        assert "a" in r1.checks_passed
        assert "b" in r1.fixes_applied
        assert "c" in r1.warnings
        assert "d" in r1.errors


# ============================================================================
# Helper functions
# ============================================================================


class TestHelpers:
    def test_import_name_known(self) -> None:
        assert _import_name("beautifulsoup4") == "bs4"
        assert _import_name("python-telegram-bot") == "telegram"
        assert _import_name("fpdf2") == "fpdf"

    def test_import_name_unknown(self) -> None:
        assert _import_name("my-package") == "my_package"

    def test_import_name_with_version_specifier(self) -> None:
        assert _import_name("mcp>=1.7") == "mcp"

    def test_can_import_existing(self) -> None:
        assert _can_import("os") is True
        assert _can_import("sys") is True

    def test_can_import_nonexistent(self) -> None:
        assert _can_import("nonexistent_module_xyz_12345") is False


# ============================================================================
# check_and_fix_all
# ============================================================================


class TestCheckAndFixAll:
    def test_basic_run(self, config: CognithorConfig) -> None:
        checker = StartupChecker(config)
        with patch.object(checker, "check_python_packages", return_value=StartupReport()):
            with patch.object(checker, "check_ollama", return_value=StartupReport()):
                with patch.object(checker, "check_models", return_value=StartupReport()):
                    with patch.object(checker, "check_directories", return_value=StartupReport()):
                        with patch.object(checker, "_find_repo_root", return_value=None):
                            report = checker.check_and_fix_all()
        assert isinstance(report, StartupReport)
        assert isinstance(report.fixes_applied, list)
        assert isinstance(report.warnings, list)
        assert isinstance(report.errors, list)

    def test_check_and_fix_all_handles_exceptions(self, config: CognithorConfig) -> None:
        checker = StartupChecker(config)
        with patch.object(checker, "check_python_packages", side_effect=Exception("boom")):
            with patch.object(checker, "check_ollama", return_value=StartupReport()):
                with patch.object(checker, "check_models", return_value=StartupReport()):
                    with patch.object(checker, "check_directories", return_value=StartupReport()):
                        with patch.object(checker, "_find_repo_root", return_value=None):
                            report = checker.check_and_fix_all()
        assert any("Package check failed" in e for e in report.errors)


# ============================================================================
# check_python_packages
# ============================================================================


class TestCheckPythonPackages:
    def test_all_installed(self, config: CognithorConfig) -> None:
        checker = StartupChecker(config)
        with patch("cognithor.core.startup_check._can_import", return_value=True):
            report = checker.check_python_packages()
        assert isinstance(report, StartupReport)
        assert len(report.checks_passed) > 0
        assert len(report.warnings) == 0

    def test_missing_packages_installed(self, config: CognithorConfig) -> None:
        checker = StartupChecker(config, auto_install=True)
        # First call: can't import; after install: can import
        with patch("cognithor.core.startup_check._can_import", return_value=False):
            with patch("cognithor.core.startup_check._pip_install", return_value=(True, "")):
                report = checker.check_python_packages()
        assert len(report.fixes_applied) > 0

    def test_missing_packages_install_fails(self, config: CognithorConfig) -> None:
        checker = StartupChecker(config, auto_install=True)
        with patch("cognithor.core.startup_check._can_import", return_value=False):
            with patch("cognithor.core.startup_check._pip_install", return_value=(False, "error")):
                report = checker.check_python_packages()
        assert len(report.warnings) > 0


# ============================================================================
# check_directories
# ============================================================================


class TestCheckDirectories:
    def test_directories_exist(self, config: CognithorConfig) -> None:
        checker = StartupChecker(config)
        report = checker.check_directories()
        assert isinstance(report, StartupReport)

    def test_directories_no_config(self) -> None:
        checker = StartupChecker(None)
        report = checker.check_directories()
        assert any("No config" in w for w in report.warnings)


# ============================================================================
# check_ollama
# ============================================================================


class TestCheckOllama:
    def test_check_ollama_running(self, config: CognithorConfig) -> None:
        checker = StartupChecker(config)
        with patch.object(checker, "_ollama_is_running", return_value=True):
            report = checker.check_ollama()
        assert "Ollama running" in report.checks_passed

    def test_check_ollama_not_running_warns_without_auto_install(
        self, config: CognithorConfig
    ) -> None:
        checker = StartupChecker(config)
        with patch.object(checker, "_ollama_is_running", return_value=False):
            report = checker.check_ollama()
        assert any("not running" in w.lower() for w in report.warnings)

    def test_check_ollama_not_running_not_found(self, config: CognithorConfig) -> None:
        checker = StartupChecker(config, auto_install=True)
        with patch.object(checker, "_ollama_is_running", return_value=False):
            with patch.object(checker, "_find_ollama", return_value=None):
                report = checker.check_ollama()
        assert any("not found" in w.lower() for w in report.warnings)

    def test_check_ollama_not_running_autostart_ok(self, config: CognithorConfig) -> None:
        checker = StartupChecker(config, auto_install=True)
        with patch.object(checker, "_ollama_is_running", return_value=False):
            with patch.object(checker, "_find_ollama", return_value="/usr/bin/ollama"):
                with patch.object(checker, "_start_ollama", return_value=True):
                    report = checker.check_ollama()
        assert any("auto-started" in f for f in report.fixes_applied)

    def test_check_ollama_not_running_autostart_fail(self, config: CognithorConfig) -> None:
        checker = StartupChecker(config, auto_install=True)
        with patch.object(checker, "_ollama_is_running", return_value=False):
            with patch.object(checker, "_find_ollama", return_value="/usr/bin/ollama"):
                with patch.object(checker, "_start_ollama", return_value=False):
                    report = checker.check_ollama()
        assert any("could not be started" in w for w in report.warnings)

    def test_check_ollama_cloud_backend_skipped(self, config: CognithorConfig) -> None:
        config.llm_backend_type = "openai"
        checker = StartupChecker(config)
        report = checker.check_ollama()
        assert any("skipped" in p.lower() for p in report.checks_passed)


# ============================================================================
# check_models
# ============================================================================


class TestCheckModels:
    def test_check_models_no_config(self) -> None:
        checker = StartupChecker(None)
        report = checker.check_models()
        assert any("No config" in w for w in report.warnings)

    def test_check_models_cloud_backend_skipped(self, config: CognithorConfig) -> None:
        config.llm_backend_type = "openai"
        checker = StartupChecker(config)
        report = checker.check_models()
        assert any("cloud" in p.lower() or "skipped" in p.lower() for p in report.checks_passed)


# TestCheckNodeModules removed — check_node_modules() was deleted
# when the legacy React UI was removed in favor of Flutter (Phase 4).


# ============================================================================
# _find_ollama and _ollama_is_running (static methods)
# ============================================================================


class TestFindOllama:
    def test_find_ollama_in_path(self) -> None:
        with patch("shutil.which", return_value="/usr/bin/ollama"):
            path = StartupChecker._find_ollama()
            assert path == "/usr/bin/ollama"

    def test_find_ollama_not_found(self) -> None:
        with patch("shutil.which", return_value=None):
            with patch("platform.system", return_value="Linux"):
                path = StartupChecker._find_ollama()
                assert path is None

    def test_ollama_is_running_false(self) -> None:
        with patch("urllib.request.urlopen", side_effect=Exception("connection refused")):
            assert StartupChecker._ollama_is_running() is False
