"""Tests fuer F-004: Skill-Test-Ausfuehrung muss sandboxed sein.

Prueft dass:
  - _build_safe_env() nur minimale Env-Vars enthaelt
  - Sensitive Env-Vars (API-Keys, Tokens) nicht an den Subprocess vererbt werden
  - pytest mit --import-mode=importlib und -p no:cacheprovider aufgerufen wird
  - Das sanitized Environment tatsaechlich an subprocess.run() uebergeben wird
  - Grundfunktion (Roundtrip) weiterhin funktioniert
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from cognithor.tools.skill_cli import SkillTester


class TestBuildSafeEnv:
    """Prueft dass _build_safe_env() ein minimales Environment liefert."""

    def test_contains_path(self) -> None:
        env = SkillTester._build_safe_env()
        assert "PATH" in env

    def test_no_api_keys(self) -> None:
        """Sensitive Variablen duerfen nicht durchsickern."""
        sensitive_vars = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "AWS_SECRET_ACCESS_KEY",
            "GITHUB_TOKEN",
            "SLACK_TOKEN",
            "TELEGRAM_BOT_TOKEN",
            "DATABASE_URL",
            "COGNITHOR_SECRET",
            "MASTER_SECRET",
        ]
        # Setze temporaer sensitive Vars
        original = {}
        for var in sensitive_vars:
            original[var] = os.environ.get(var)
            os.environ[var] = "leaked-secret"
        try:
            env = SkillTester._build_safe_env()
            for var in sensitive_vars:
                assert var not in env, f"Sensitive Variable {var} darf nicht im safe env sein"
        finally:
            for var in sensitive_vars:
                if original[var] is None:
                    os.environ.pop(var, None)
                else:
                    os.environ[var] = original[var]

    def test_limited_keys_count(self) -> None:
        """Das safe env sollte nur wenige Keys enthalten (nicht das gesamte os.environ)."""
        env = SkillTester._build_safe_env()
        assert len(env) <= 10, f"Safe env hat zu viele Keys ({len(env)}), sollte minimal sein"
        # Muss deutlich weniger als os.environ haben
        assert len(env) < len(os.environ)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-spezifisch")
    def test_windows_has_systemroot(self) -> None:
        env = SkillTester._build_safe_env()
        assert "SYSTEMROOT" in env

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-spezifisch")
    def test_windows_has_temp(self) -> None:
        env = SkillTester._build_safe_env()
        assert "TEMP" in env
        assert "TMP" in env

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-spezifisch")
    def test_unix_has_lang(self) -> None:
        env = SkillTester._build_safe_env()
        assert "LANG" in env
        assert env["HOME"] == "/tmp"


class TestSubprocessInvocation:
    """Prueft dass subprocess.run() mit den richtigen Sicherheits-Argumenten aufgerufen wird."""

    def test_env_passed_to_subprocess(self) -> None:
        """subprocess.run() muss env= erhalten, damit das Eltern-Environment nicht vererbt wird."""
        tester = SkillTester()
        test_code = "def test_dummy():\n    assert True\n"

        mock_result = MagicMock()
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            tester.test_skill("test-skill", test_code)

            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args
            # env= muss gesetzt sein
            assert "env" in call_kwargs.kwargs, "subprocess.run() muss env= erhalten"
            passed_env = call_kwargs.kwargs["env"]
            assert isinstance(passed_env, dict)
            assert len(passed_env) < len(os.environ), (
                "Uebergebenes env muss kleiner als os.environ sein"
            )

    def test_import_mode_importlib(self) -> None:
        """pytest muss mit --import-mode=importlib aufgerufen werden."""
        tester = SkillTester()
        test_code = "def test_dummy():\n    assert True\n"

        mock_result = MagicMock()
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            tester.test_skill("test-skill", test_code)

            cmd = mock_run.call_args.args[0]
            assert "--import-mode=importlib" in cmd, (
                "pytest muss mit --import-mode=importlib aufgerufen werden"
            )

    def test_no_cacheprovider(self) -> None:
        """pytest muss mit -p no:cacheprovider aufgerufen werden."""
        tester = SkillTester()
        test_code = "def test_dummy():\n    assert True\n"

        mock_result = MagicMock()
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            tester.test_skill("test-skill", test_code)

            cmd = mock_run.call_args.args[0]
            assert "-p" in cmd
            p_idx = cmd.index("-p")
            assert cmd[p_idx + 1] == "no:cacheprovider"

    def test_no_header(self) -> None:
        """pytest muss mit --no-header aufgerufen werden."""
        tester = SkillTester()
        test_code = "def test_dummy():\n    assert True\n"

        mock_result = MagicMock()
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            tester.test_skill("test-skill", test_code)

            cmd = mock_run.call_args.args[0]
            assert "--no-header" in cmd

    def test_timeout_still_30s(self) -> None:
        """Timeout muss weiterhin 30 Sekunden sein."""
        tester = SkillTester()
        test_code = "def test_dummy():\n    assert True\n"

        mock_result = MagicMock()
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            tester.test_skill("test-skill", test_code)

            call_kwargs = mock_run.call_args.kwargs
            assert call_kwargs["timeout"] == 30

    def test_cwd_is_tmpdir(self) -> None:
        """cwd muss das tmpdir sein, nicht das Arbeitsverzeichnis des Hauptprozesses."""
        tester = SkillTester()
        test_code = "def test_dummy():\n    assert True\n"

        mock_result = MagicMock()
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            tester.test_skill("test-skill", test_code)

            call_kwargs = mock_run.call_args.kwargs
            cwd = call_kwargs["cwd"]
            assert cwd is not None
            assert "jarvis_skill_test_" in cwd


class TestFunctionalRoundtrip:
    """Prueft dass die Grundfunktion nach dem Sandbox-Fix noch funktioniert."""

    def test_no_tests_still_works(self) -> None:
        tester = SkillTester()
        result = tester.test_skill("empty", "x = 1")
        assert result.total_tests == 0
        assert result.success is False

    def test_empty_code_still_works(self) -> None:
        tester = SkillTester()
        result = tester.test_skill("empty", "")
        assert result.total_tests == 0

    def test_with_test_code_parses_result(self) -> None:
        """Simuliert einen pytest-Lauf und prueft die Ergebnis-Analyse."""
        tester = SkillTester()
        test_code = "def test_a():\n    assert True\ndef test_b():\n    assert False\n"

        mock_result = MagicMock()
        mock_result.stdout = "1 passed, 1 failed"
        mock_result.stderr = ""
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            result = tester.test_skill("mixed", test_code)

        assert result.passed == 1
        assert result.failed == 1
        assert result.total_tests == 2
        assert result.success is False

    def test_timeout_handled(self) -> None:
        """TimeoutExpired muss graceful behandelt werden."""
        import subprocess

        tester = SkillTester()
        test_code = "def test_slow():\n    import time; time.sleep(999)\n"

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 30)):
            result = tester.test_skill("timeout", test_code)

        assert result.failed == 1
        assert result.success is False
