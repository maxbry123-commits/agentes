"""Coverage-Tests fuer sandbox.py -- SandboxExecutor, SandboxResult, etc."""

from __future__ import annotations

import sys

import pytest

from cognithor.core.sandbox import (
    BwrapSandbox,
    FirejailSandbox,
    NetworkPolicy,
    SandboxConfig,
    SandboxExecutor,
    SandboxLevel,
    SandboxResult,
    WindowsJobObjectSandbox,
)

# ============================================================================
# SandboxLevel / NetworkPolicy Enums
# ============================================================================


class TestEnums:
    def test_sandbox_levels(self) -> None:
        assert SandboxLevel.BWRAP == "bwrap"
        assert SandboxLevel.FIREJAIL == "firejail"
        assert SandboxLevel.JOBOBJECT == "jobobject"
        assert SandboxLevel.BARE == "bare"

    def test_network_policies(self) -> None:
        assert NetworkPolicy.ALLOW == "allow"
        assert NetworkPolicy.BLOCK == "block"


# ============================================================================
# SandboxConfig
# ============================================================================


class TestSandboxConfig:
    def test_defaults(self) -> None:
        cfg = SandboxConfig()
        assert cfg.max_memory_mb == 512
        assert cfg.default_timeout == 30
        assert cfg.network == NetworkPolicy.ALLOW

    def test_custom_config(self) -> None:
        cfg = SandboxConfig(
            max_memory_mb=1024,
            default_timeout=60,
            network=NetworkPolicy.BLOCK,
        )
        assert cfg.max_memory_mb == 1024
        assert cfg.default_timeout == 60
        assert cfg.network == NetworkPolicy.BLOCK


# ============================================================================
# SandboxResult
# ============================================================================


class TestSandboxResult:
    def test_success_property(self) -> None:
        r = SandboxResult(stdout="hello", exit_code=0)
        assert r.success is True

    def test_failure_exit_code(self) -> None:
        r = SandboxResult(exit_code=1)
        assert r.success is False

    def test_timed_out(self) -> None:
        r = SandboxResult(timed_out=True, exit_code=-1)
        assert r.success is False
        assert "[TIMEOUT]" in r.output

    def test_error(self) -> None:
        r = SandboxResult(error="something broke")
        assert r.success is False
        assert "FEHLER" in r.output

    def test_output_combined(self) -> None:
        r = SandboxResult(stdout="out", stderr="err", exit_code=1)
        output = r.output
        assert "out" in output
        assert "STDERR" in output
        assert "EXIT CODE" in output

    def test_output_empty(self) -> None:
        r = SandboxResult()
        assert r.output == "(Keine Ausgabe)"

    def test_truncated_output(self) -> None:
        r = SandboxResult(stdout="data", truncated=True)
        assert "truncated" in r.output


# ============================================================================
# BwrapSandbox
# ============================================================================


class TestBwrapSandbox:
    def test_is_available(self) -> None:
        # On Windows this should be False
        if sys.platform == "win32":
            assert BwrapSandbox.is_available() is False

    def test_build_command(self, tmp_path) -> None:
        cfg = SandboxConfig(
            workspace_dir=tmp_path,
            network=NetworkPolicy.BLOCK,
            allowed_read_paths=[],
        )
        bw = BwrapSandbox(cfg)
        cmd = bw.build_command("echo hello", str(tmp_path))
        assert "bwrap" in cmd
        assert "echo hello" in cmd[-1]


# ============================================================================
# FirejailSandbox
# ============================================================================


class TestFirejailSandbox:
    def test_is_available(self) -> None:
        if sys.platform == "win32":
            assert FirejailSandbox.is_available() is False

    def test_build_command(self, tmp_path) -> None:
        cfg = SandboxConfig(
            workspace_dir=tmp_path,
            network=NetworkPolicy.BLOCK,
            allowed_read_paths=[],
        )
        fj = FirejailSandbox(cfg)
        cmd = fj.build_command("ls", str(tmp_path))
        assert "firejail" in cmd
        assert "--net=none" in cmd


# ============================================================================
# WindowsJobObjectSandbox
# ============================================================================


class TestWindowsJobObjectSandbox:
    def test_is_available(self) -> None:
        if sys.platform == "win32":
            assert WindowsJobObjectSandbox.is_available() is True
        else:
            assert WindowsJobObjectSandbox.is_available() is False


# ============================================================================
# SandboxExecutor
# ============================================================================


class TestSandboxExecutor:
    def test_detect_sandbox(self, tmp_path) -> None:
        cfg = SandboxConfig(workspace_dir=tmp_path)
        executor = SandboxExecutor(cfg)
        # level should be one of the valid levels
        assert executor.level in (
            SandboxLevel.BWRAP,
            SandboxLevel.FIREJAIL,
            SandboxLevel.JOBOBJECT,
            SandboxLevel.BARE,
        )

    def test_default_config(self) -> None:
        executor = SandboxExecutor()
        assert executor._config is not None

    @pytest.mark.asyncio
    async def test_execute_empty_command(self, tmp_path) -> None:
        cfg = SandboxConfig(workspace_dir=tmp_path)
        executor = SandboxExecutor(cfg)
        result = await executor.execute("")
        assert "no_command" in (result.error or "") or result.error == "Kein Befehl angegeben"

    @pytest.mark.asyncio
    async def test_execute_simple_command(self, tmp_path) -> None:
        cfg = SandboxConfig(workspace_dir=tmp_path)
        executor = SandboxExecutor(cfg)
        if sys.platform == "win32":
            result = await executor.execute("echo hello", working_dir=str(tmp_path))
        else:
            result = await executor.execute("echo hello", working_dir=str(tmp_path))
        assert result.exit_code == 0
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_with_overrides(self, tmp_path) -> None:
        cfg = SandboxConfig(workspace_dir=tmp_path)
        executor = SandboxExecutor(cfg)
        result = await executor.execute(
            "echo test",
            working_dir=str(tmp_path),
            timeout=5,
            network=NetworkPolicy.BLOCK,
            max_memory_mb=256,
            max_processes=32,
        )
        assert isinstance(result, SandboxResult)

    @pytest.mark.asyncio
    async def test_execute_timeout(self, tmp_path) -> None:
        cfg = SandboxConfig(workspace_dir=tmp_path)
        executor = SandboxExecutor(cfg)
        if sys.platform == "win32":
            result = await executor.execute("ping -n 100 127.0.0.1", timeout=1)
        else:
            result = await executor.execute("sleep 100", timeout=1)
        assert result.timed_out is True

    def test_decode_and_truncate_normal(self) -> None:
        stdout, stderr, truncated = SandboxExecutor._decode_and_truncate(b"hello", b"world")
        assert stdout == "hello"
        assert stderr == "world"
        assert truncated is False

    def test_decode_and_truncate_large(self) -> None:
        big = b"x" * 60000
        stdout, stderr, truncated = SandboxExecutor._decode_and_truncate(big, b"")
        assert truncated is True

    def test_decode_and_truncate_empty(self) -> None:
        stdout, stderr, truncated = SandboxExecutor._decode_and_truncate(b"", b"")
        assert stdout == ""
        assert stderr == ""
        assert truncated is False

    def test_decode_latin1_fallback(self) -> None:
        bad_utf8 = bytes([0xFF, 0xFE, 0x41])
        stdout, stderr, truncated = SandboxExecutor._decode_and_truncate(bad_utf8, b"")
        assert len(stdout) > 0
