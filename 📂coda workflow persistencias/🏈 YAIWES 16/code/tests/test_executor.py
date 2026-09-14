"""Tests for the tool executor safety features."""

import pytest
from src.tools.executor import ToolExecutor


class TestToolExecutorSafety:
    """Test safety guardrails on command execution."""

    def setup_method(self):
        self.executor = ToolExecutor(dry_run=True)

    def test_blocks_rm_rf_root(self):
        result = self.executor.execute("rm -rf /")
        assert result.exit_code == -1
        assert "BLOCKED" in result.output

    def test_blocks_fork_bomb(self):
        result = self.executor.execute(":(){ :|:& };:")
        assert result.exit_code == -1
        assert "BLOCKED" in result.output

    def test_blocks_dd_overwrite(self):
        result = self.executor.execute("dd if=/dev/zero of=/dev/sda")
        assert result.exit_code == -1
        assert "BLOCKED" in result.output

    def test_allows_nmap(self):
        result = self.executor.execute("nmap -sV 10.10.10.56")
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_allows_gobuster(self):
        result = self.executor.execute("gobuster dir -u http://10.10.10.56 -w /usr/share/wordlists/common.txt")
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_allows_curl(self):
        result = self.executor.execute("curl -v http://10.10.10.56")
        assert result.exit_code == 0


class TestToolExecutorDryRun:
    """Test dry run mode doesn't execute anything."""

    def test_dry_run_returns_zero(self):
        executor = ToolExecutor(dry_run=True)
        result = executor.execute("whoami")
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_dry_run_logs_command(self):
        executor = ToolExecutor(dry_run=True)
        executor.execute("nmap -sV 10.10.10.56")
        assert len(executor.execution_log) == 1
        assert executor.execution_log[0].command == "nmap -sV 10.10.10.56"