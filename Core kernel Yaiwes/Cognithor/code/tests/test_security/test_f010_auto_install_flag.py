"""Tests fuer F-010: Auto pip install ohne User-Bestaetigung.

Prueft dass:
  - StartupChecker default NICHT auto-installiert
  - --auto-install Flag explizit gesetzt werden muss
  - Ohne --auto-install werden fehlende Pakete nur als Warning gemeldet
  - Mit --auto-install werden fehlende Pakete installiert
  - CLI-Argument --auto-install existiert im ArgumentParser
  - StartupChecker gibt auto_install korrekt an check_python_packages weiter
  - Source-Code das Flag-Pattern enthaelt
"""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

from cognithor.core.startup_check import StartupChecker, StartupReport

# ============================================================================
# Default-Verhalten: kein Auto-Install
# ============================================================================


class TestDefaultNoAutoInstall:
    """Prueft dass ohne --auto-install NICHT installiert wird."""

    def test_auto_install_default_false(self) -> None:
        """StartupChecker hat auto_install=False als Default."""
        checker = StartupChecker()
        assert checker._auto_install is False

    def test_auto_install_explicit_false(self) -> None:
        checker = StartupChecker(auto_install=False)
        assert checker._auto_install is False

    def test_auto_install_explicit_true(self) -> None:
        checker = StartupChecker(auto_install=True)
        assert checker._auto_install is True

    @patch("cognithor.core.startup_check._can_import", return_value=False)
    @patch("cognithor.core.startup_check._pip_install")
    def test_missing_packages_without_flag_warns_only(
        self, mock_pip: MagicMock, mock_import: MagicMock
    ) -> None:
        """Ohne auto_install: fehlende Pakete -> Warning, kein pip install."""
        checker = StartupChecker()  # auto_install=False (default)
        report = checker.check_python_packages()

        mock_pip.assert_not_called()
        assert len(report.warnings) > 0
        assert len(report.fixes_applied) == 0

    @patch("cognithor.core.startup_check._can_import", return_value=False)
    @patch("cognithor.core.startup_check._pip_install")
    def test_warning_contains_hint(self, mock_pip: MagicMock, mock_import: MagicMock) -> None:
        """Warning-Text enthaelt Hinweis auf --auto-install."""
        checker = StartupChecker()
        report = checker.check_python_packages()

        has_hint = any("--auto-install" in w for w in report.warnings)
        assert has_hint, f"No --auto-install hint in warnings: {report.warnings}"

    @patch("cognithor.core.startup_check._can_import", return_value=False)
    @patch("cognithor.core.startup_check._pip_install")
    def test_warning_contains_pip_command(
        self, mock_pip: MagicMock, mock_import: MagicMock
    ) -> None:
        """Warning-Text enthaelt pip install Befehl."""
        checker = StartupChecker()
        report = checker.check_python_packages()

        has_pip = any("pip install" in w for w in report.warnings)
        assert has_pip, f"No pip install hint in warnings: {report.warnings}"


# ============================================================================
# Mit --auto-install: Pakete werden installiert
# ============================================================================


class TestAutoInstallEnabled:
    """Prueft dass mit auto_install=True installiert wird."""

    @patch("cognithor.core.startup_check._can_import", return_value=False)
    @patch("cognithor.core.startup_check._pip_install", return_value=(True, ""))
    def test_auto_install_calls_pip(self, mock_pip: MagicMock, mock_import: MagicMock) -> None:
        """Mit auto_install=True wird _pip_install aufgerufen."""
        checker = StartupChecker(auto_install=True)
        report = checker.check_python_packages()

        assert mock_pip.call_count >= 1
        assert len(report.fixes_applied) > 0

    @patch("cognithor.core.startup_check._can_import", return_value=False)
    @patch("cognithor.core.startup_check._pip_install", return_value=(True, ""))
    def test_auto_install_no_warnings_on_success(
        self, mock_pip: MagicMock, mock_import: MagicMock
    ) -> None:
        """Bei erfolgreichem Install keine Warnings."""
        checker = StartupChecker(auto_install=True)
        report = checker.check_python_packages()

        assert len(report.warnings) == 0

    @patch("cognithor.core.startup_check._can_import", return_value=False)
    @patch("cognithor.core.startup_check._pip_install", return_value=(False, "error"))
    def test_auto_install_failure_creates_warning(
        self, mock_pip: MagicMock, mock_import: MagicMock
    ) -> None:
        """Bei fehlgeschlagenem Install -> Warning."""
        checker = StartupChecker(auto_install=True)
        report = checker.check_python_packages()

        assert len(report.warnings) > 0
        assert any("Failed" in w for w in report.warnings)

    @patch("cognithor.core.startup_check._can_import", return_value=True)
    @patch("cognithor.core.startup_check._pip_install")
    def test_no_install_when_all_present(self, mock_pip: MagicMock, mock_import: MagicMock) -> None:
        """Wenn alle Pakete vorhanden, kein pip install -- auch mit Flag."""
        checker = StartupChecker(auto_install=True)
        report = checker.check_python_packages()

        mock_pip.assert_not_called()
        assert len(report.fixes_applied) == 0
        assert len(report.warnings) == 0


# ============================================================================
# CLI-Integration
# ============================================================================


class TestCLIArgument:
    """Prueft dass --auto-install als CLI-Argument existiert."""

    def test_argparse_has_auto_install(self) -> None:
        """__main__.py definiert --auto-install Argument."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        assert "--auto-install" in source

    def test_auto_install_is_store_true(self) -> None:
        """--auto-install ist ein store_true Flag (kein Wert noetig)."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        # Find the auto-install argument definition
        idx = source.find("--auto-install")
        assert idx > 0
        # Look at the surrounding context (next 200 chars)
        context = source[idx : idx + 200]
        assert "store_true" in context


# ============================================================================
# StartupChecker Konstruktor
# ============================================================================


class TestConstructorParameter:
    """Prueft dass auto_install korrekt durchgereicht wird."""

    def test_keyword_only(self) -> None:
        """auto_install ist keyword-only Parameter."""
        sig = inspect.signature(StartupChecker.__init__)
        param = sig.parameters["auto_install"]
        assert param.kind == inspect.Parameter.KEYWORD_ONLY

    def test_default_value(self) -> None:
        """Default-Wert ist False."""
        sig = inspect.signature(StartupChecker.__init__)
        param = sig.parameters["auto_install"]
        assert param.default is False

    def test_stored_on_instance(self) -> None:
        """auto_install wird als _auto_install gespeichert."""
        checker_on = StartupChecker(auto_install=True)
        checker_off = StartupChecker(auto_install=False)
        assert checker_on._auto_install is True
        assert checker_off._auto_install is False


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf den Fix."""

    def test_auto_install_guard_in_check_python_packages(self) -> None:
        """check_python_packages prueft self._auto_install."""
        source = inspect.getsource(StartupChecker.check_python_packages)
        assert "_auto_install" in source

    def test_no_unconditional_pip_install(self) -> None:
        """_pip_install wird nur unter auto_install-Guard aufgerufen."""
        source = inspect.getsource(StartupChecker.check_python_packages)
        # The _pip_install call should come AFTER the auto_install check
        auto_install_pos = source.find("_auto_install")
        pip_install_pos = source.find("_pip_install")
        assert auto_install_pos > 0
        assert pip_install_pos > 0
        assert auto_install_pos < pip_install_pos, (
            "_auto_install check must come before _pip_install call"
        )

    def test_startup_checker_init_accepts_auto_install(self) -> None:
        source = inspect.getsource(StartupChecker.__init__)
        assert "auto_install" in source

    def test_main_passes_auto_install_to_checker(self) -> None:
        """__main__.py gibt auto_install an StartupChecker weiter."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        assert "auto_install" in source


# ============================================================================
# check_and_fix_all Integration
# ============================================================================


class TestCheckAndFixAllIntegration:
    """Prueft dass check_and_fix_all den auto_install-State respektiert."""

    @patch("cognithor.core.startup_check.StartupChecker._find_repo_root", return_value=None)
    @patch("cognithor.core.startup_check.StartupChecker.check_directories")
    @patch("cognithor.core.startup_check.StartupChecker.check_models")
    @patch("cognithor.core.startup_check.StartupChecker.check_ollama")
    @patch("cognithor.core.startup_check._can_import", return_value=False)
    @patch("cognithor.core.startup_check._pip_install")
    def test_full_check_without_auto_install(
        self,
        mock_pip: MagicMock,
        mock_import: MagicMock,
        mock_ollama: MagicMock,
        mock_models: MagicMock,
        mock_dirs: MagicMock,
        mock_root: MagicMock,
    ) -> None:
        """check_and_fix_all ohne auto_install -> kein pip install."""
        mock_ollama.return_value = StartupReport()
        mock_models.return_value = StartupReport()
        mock_dirs.return_value = StartupReport()

        checker = StartupChecker()
        report = checker.check_and_fix_all()

        mock_pip.assert_not_called()
        assert len(report.warnings) > 0
