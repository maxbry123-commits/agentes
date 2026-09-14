"""Tests for jarvis.utils.installer — uv/pip detection and command generation."""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from cognithor.utils.installer import (
    InstallerBackend,
    InstallerInfo,
    build_install_command,
    build_sync_command,
    detect_installer,
    detect_pip,
    detect_uv,
    run_install,
)

# ── InstallerBackend ──────────────────────────────────────────────────────


class TestInstallerBackend:
    def test_values(self) -> None:
        assert InstallerBackend.UV == "uv"
        assert InstallerBackend.PIP == "pip"

    def test_str_enum(self) -> None:
        assert str(InstallerBackend.UV) == "uv"


# ── InstallerInfo ─────────────────────────────────────────────────────────


class TestInstallerInfo:
    def test_uv_info(self) -> None:
        info = InstallerInfo(backend=InstallerBackend.UV, path="/usr/bin/uv", version="0.6.3")
        assert info.is_uv is True
        assert info.backend == InstallerBackend.UV

    def test_pip_info(self) -> None:
        info = InstallerInfo(backend=InstallerBackend.PIP, path="python -m pip", version="24.0")
        assert info.is_uv is False

    def test_to_dict(self) -> None:
        info = InstallerInfo(backend=InstallerBackend.UV, path="/usr/bin/uv", version="0.6.3")
        d = info.to_dict()
        assert d["backend"] == "uv"
        assert d["path"] == "/usr/bin/uv"
        assert d["version"] == "0.6.3"

    def test_frozen(self) -> None:
        info = InstallerInfo(backend=InstallerBackend.UV, path="/usr/bin/uv", version="0.6.3")
        with pytest.raises(AttributeError):
            info.version = "1.0"  # type: ignore[misc]


# ── detect_uv ─────────────────────────────────────────────────────────────


class TestDetectUv:
    @patch("cognithor.utils.installer.shutil.which", return_value=None)
    def test_not_found(self, _mock: MagicMock) -> None:
        assert detect_uv() is None

    @patch("cognithor.utils.installer.subprocess.run")
    @patch("cognithor.utils.installer.shutil.which", return_value="/usr/bin/uv")
    def test_found(self, _which: MagicMock, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="uv 0.6.3\n")
        result = detect_uv()
        assert result is not None
        assert result.is_uv is True
        assert result.version == "0.6.3"
        assert result.path == "/usr/bin/uv"

    @patch("cognithor.utils.installer.subprocess.run")
    @patch("cognithor.utils.installer.shutil.which", return_value="/usr/bin/uv")
    def test_version_parse_no_prefix(self, _which: MagicMock, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="0.7.0")
        result = detect_uv()
        assert result is not None
        assert result.version == "0.7.0"

    @patch("cognithor.utils.installer.subprocess.run", side_effect=FileNotFoundError)
    @patch("cognithor.utils.installer.shutil.which", return_value="/usr/bin/uv")
    def test_run_error(self, _which: MagicMock, _run: MagicMock) -> None:
        assert detect_uv() is None

    @patch("cognithor.utils.installer.subprocess.run")
    @patch("cognithor.utils.installer.shutil.which", return_value="/usr/bin/uv")
    def test_non_zero_exit(self, _which: MagicMock, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert detect_uv() is None


# ── detect_pip ────────────────────────────────────────────────────────────


class TestDetectPip:
    @patch("cognithor.utils.installer.subprocess.run")
    def test_found(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="pip 24.0 from /usr/lib/python3.12/site-packages (python 3.12)\n"
        )
        result = detect_pip()
        assert result is not None
        assert result.is_uv is False
        assert result.version == "24.0"

    @patch("cognithor.utils.installer.subprocess.run")
    def test_not_found(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert detect_pip() is None

    @patch("cognithor.utils.installer.subprocess.run", side_effect=Exception("boom"))
    def test_exception(self, _run: MagicMock) -> None:
        assert detect_pip() is None


# ── detect_installer ──────────────────────────────────────────────────────


class TestDetectInstaller:
    @patch("cognithor.utils.installer.detect_pip")
    @patch("cognithor.utils.installer.detect_uv")
    def test_prefers_uv(self, mock_uv: MagicMock, mock_pip: MagicMock) -> None:
        uv_info = InstallerInfo(InstallerBackend.UV, "/usr/bin/uv", "0.6.3")
        pip_info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        mock_uv.return_value = uv_info
        mock_pip.return_value = pip_info
        result = detect_installer(prefer_uv=True)
        assert result is not None
        assert result.is_uv is True

    @patch("cognithor.utils.installer.detect_pip")
    @patch("cognithor.utils.installer.detect_uv")
    def test_fallback_to_pip(self, mock_uv: MagicMock, mock_pip: MagicMock) -> None:
        pip_info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        mock_uv.return_value = None
        mock_pip.return_value = pip_info
        result = detect_installer(prefer_uv=True)
        assert result is not None
        assert result.is_uv is False

    @patch("cognithor.utils.installer.detect_pip")
    @patch("cognithor.utils.installer.detect_uv")
    def test_skip_uv(self, mock_uv: MagicMock, mock_pip: MagicMock) -> None:
        uv_info = InstallerInfo(InstallerBackend.UV, "/usr/bin/uv", "0.6.3")
        pip_info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        mock_uv.return_value = uv_info
        mock_pip.return_value = pip_info
        result = detect_installer(prefer_uv=False)
        assert result is not None
        assert result.is_uv is False
        mock_uv.assert_not_called()

    @patch("cognithor.utils.installer.detect_pip", return_value=None)
    @patch("cognithor.utils.installer.detect_uv", return_value=None)
    def test_nothing_found(self, _uv: MagicMock, _pip: MagicMock) -> None:
        assert detect_installer() is None


# ── build_install_command ─────────────────────────────────────────────────


class TestBuildInstallCommand:
    def test_uv_editable(self) -> None:
        info = InstallerInfo(InstallerBackend.UV, "/usr/bin/uv", "0.6.3")
        cmd = build_install_command(info, "/project", "all")
        assert cmd[0] == "/usr/bin/uv"
        assert "pip" in cmd
        assert "install" in cmd
        assert "-e" in cmd
        assert ".[all]" in cmd
        assert "--quiet" in cmd
        assert "--python" in cmd

    def test_uv_non_editable(self) -> None:
        info = InstallerInfo(InstallerBackend.UV, "/usr/bin/uv", "0.6.3")
        cmd = build_install_command(info, "/project", "all", editable=False)
        assert "-e" not in cmd
        assert ".[all]" in cmd

    def test_pip_editable(self) -> None:
        info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        cmd = build_install_command(info, "/project", "web,voice")
        assert cmd[0] == sys.executable
        assert "-m" in cmd
        assert "pip" in cmd
        assert "-e" in cmd
        assert ".[web,voice]" in cmd
        assert "--disable-pip-version-check" in cmd

    def test_pip_no_extras(self) -> None:
        info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        cmd = build_install_command(info, "/project", "")
        assert "." in cmd
        assert ".[" not in " ".join(cmd)

    def test_pip_not_quiet(self) -> None:
        info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        cmd = build_install_command(info, "/project", "all", quiet=False)
        assert "--quiet" not in cmd
        assert "--disable-pip-version-check" not in cmd


# ── build_sync_command ────────────────────────────────────────────────────


class TestBuildSyncCommand:
    def test_uv_sync(self) -> None:
        info = InstallerInfo(InstallerBackend.UV, "/usr/bin/uv", "0.6.3")
        cmd = build_sync_command(info, "/project", "all")
        assert cmd is not None
        assert cmd[0] == "/usr/bin/uv"
        assert "sync" in cmd
        assert "--extra" in cmd
        assert "all" in cmd

    def test_uv_sync_multiple_extras(self) -> None:
        info = InstallerInfo(InstallerBackend.UV, "/usr/bin/uv", "0.6.3")
        cmd = build_sync_command(info, "/project", "web,voice,dev")
        assert cmd is not None
        extras = [cmd[i + 1] for i, v in enumerate(cmd) if v == "--extra"]
        assert extras == ["web", "voice", "dev"]

    def test_pip_returns_none(self) -> None:
        info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        assert build_sync_command(info, "/project", "all") is None

    def test_uv_sync_no_extras(self) -> None:
        info = InstallerInfo(InstallerBackend.UV, "/usr/bin/uv", "0.6.3")
        cmd = build_sync_command(info, "/project", "")
        assert cmd is not None
        assert "--extra" not in cmd


# ── run_install ───────────────────────────────────────────────────────────


class TestRunInstall:
    @patch("cognithor.utils.installer.detect_installer", return_value=None)
    def test_no_installer(self, _det: MagicMock) -> None:
        ok, info, msg = run_install("/project")
        assert ok is False
        assert info is None
        assert "Neither" in msg

    @patch("cognithor.utils.installer.subprocess.run")
    @patch("cognithor.utils.installer.detect_installer")
    def test_success_uv(self, mock_det: MagicMock, mock_run: MagicMock) -> None:
        uv_info = InstallerInfo(InstallerBackend.UV, "/usr/bin/uv", "0.6.3")
        mock_det.return_value = uv_info
        mock_run.return_value = MagicMock(returncode=0, stdout="ok\n", stderr="")
        ok, info, msg = run_install("/project", "all", prefer_uv=True)
        assert ok is True
        assert info is not None
        assert info.is_uv is True

    @patch("cognithor.utils.installer.subprocess.run")
    @patch("cognithor.utils.installer.detect_installer")
    def test_failure(self, mock_det: MagicMock, mock_run: MagicMock) -> None:
        pip_info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        mock_det.return_value = pip_info
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error: boom")
        ok, info, msg = run_install("/project")
        assert ok is False
        assert "boom" in msg

    @patch(
        "cognithor.utils.installer.subprocess.run",
        side_effect=subprocess.TimeoutExpired("cmd", 600),
    )
    @patch("cognithor.utils.installer.detect_installer")
    def test_timeout(self, mock_det: MagicMock, _run: MagicMock) -> None:
        pip_info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        mock_det.return_value = pip_info
        ok, info, msg = run_install("/project", timeout=600)
        assert ok is False
        assert "timed out" in msg

    @patch("cognithor.utils.installer.subprocess.run", side_effect=OSError("disk full"))
    @patch("cognithor.utils.installer.detect_installer")
    def test_os_error(self, mock_det: MagicMock, _run: MagicMock) -> None:
        pip_info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        mock_det.return_value = pip_info
        ok, info, msg = run_install("/project")
        assert ok is False
        assert "disk full" in msg


# ── Integration: Command structure ────────────────────────────────────────


class TestCommandStructure:
    """Verify generated commands have correct structure."""

    def test_uv_command_is_list_of_strings(self) -> None:
        info = InstallerInfo(InstallerBackend.UV, "/usr/bin/uv", "0.6.3")
        cmd = build_install_command(info, "/project", "all")
        assert all(isinstance(c, str) for c in cmd)

    def test_pip_command_is_list_of_strings(self) -> None:
        info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        cmd = build_install_command(info, "/project", "all")
        assert all(isinstance(c, str) for c in cmd)

    def test_uv_targets_current_python(self) -> None:
        info = InstallerInfo(InstallerBackend.UV, "/usr/bin/uv", "0.6.3")
        cmd = build_install_command(info, "/project", "all")
        idx = cmd.index("--python")
        assert cmd[idx + 1] == sys.executable

    def test_pip_uses_current_python(self) -> None:
        info = InstallerInfo(InstallerBackend.PIP, "pip", "24.0")
        cmd = build_install_command(info, "/project", "all")
        assert cmd[0] == sys.executable
