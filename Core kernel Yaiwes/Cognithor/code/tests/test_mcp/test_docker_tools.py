"""Tests fuer DockerTools -- Container-Management via CLI.

Testet:
  - Tool-Registrierung beim MCP-Client
  - docker_ps (Container auflisten)
  - docker_logs (Logs abrufen)
  - docker_inspect (Container/Image inspizieren)
  - docker_run (Container starten, Security-Checks)
  - docker_stop (Container stoppen)
  - Container-Name-Sanitization
  - Port-Validierung
  - Blocked-Mount-Detection
  - Docker-Fehler-Parsing
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from cognithor.config import CognithorConfig, SecurityConfig, ensure_directory_structure
from cognithor.mcp.docker_tools import (
    DockerTools,
    _is_blocked_mount,
    _parse_docker_error,
    _sanitize_container_name,
    _validate_port,
    register_docker_tools,
)

if TYPE_CHECKING:
    from pathlib import Path

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def config(tmp_path: Path) -> CognithorConfig:
    cfg = CognithorConfig(
        cognithor_home=tmp_path / ".cognithor",
        security=SecurityConfig(
            allowed_paths=[str(tmp_path)],
        ),
    )
    ensure_directory_structure(cfg)
    return cfg


@pytest.fixture()
def docker(config: CognithorConfig) -> DockerTools:
    return DockerTools(config)


@pytest.fixture()
def mock_mcp_client() -> MagicMock:
    client = MagicMock()
    client.register_builtin_handler = MagicMock()
    return client


# =============================================================================
# Helper-Funktion Tests
# =============================================================================


class TestContainerNameSanitization:
    """Tests fuer _sanitize_container_name."""

    def test_valid_name(self) -> None:
        assert _sanitize_container_name("my-container") == "my-container"

    def test_valid_name_with_underscore(self) -> None:
        assert _sanitize_container_name("my_container") == "my_container"

    def test_valid_name_with_dot(self) -> None:
        assert _sanitize_container_name("my.container") == "my.container"

    def test_valid_name_alphanumeric(self) -> None:
        assert _sanitize_container_name("abc123") == "abc123"

    def test_empty_name(self) -> None:
        assert _sanitize_container_name("") is None

    def test_whitespace_only(self) -> None:
        assert _sanitize_container_name("   ") is None

    def test_invalid_name_with_spaces(self) -> None:
        assert _sanitize_container_name("my container") is None

    def test_invalid_name_with_semicolon(self) -> None:
        assert _sanitize_container_name("my;container") is None

    def test_invalid_name_injection(self) -> None:
        assert _sanitize_container_name("test;rm -rf /") is None

    def test_name_with_leading_space_stripped(self) -> None:
        assert _sanitize_container_name("  mycontainer  ") == "mycontainer"


class TestPortValidation:
    """Tests fuer _validate_port."""

    def test_valid_port(self) -> None:
        assert _validate_port("8080:80") is True

    def test_valid_port_high(self) -> None:
        assert _validate_port("65535:443") is True

    def test_invalid_format_no_colon(self) -> None:
        assert _validate_port("8080") is False

    def test_invalid_format_letters(self) -> None:
        assert _validate_port("abc:80") is False

    def test_invalid_port_zero(self) -> None:
        assert _validate_port("0:80") is False

    def test_invalid_port_too_high(self) -> None:
        assert _validate_port("99999:80") is False

    def test_invalid_port_negative(self) -> None:
        assert _validate_port("-1:80") is False

    def test_triple_colon(self) -> None:
        assert _validate_port("80:80:80") is False


class TestBlockedMounts:
    """Tests fuer _is_blocked_mount."""

    def test_blocked_etc(self) -> None:
        assert _is_blocked_mount("/etc") is True

    def test_blocked_etc_subdir(self) -> None:
        assert _is_blocked_mount("/etc/nginx") is True

    def test_blocked_var(self) -> None:
        assert _is_blocked_mount("/var") is True

    def test_blocked_usr(self) -> None:
        assert _is_blocked_mount("/usr") is True

    def test_blocked_windows(self) -> None:
        assert _is_blocked_mount("C:\\Windows") is True

    def test_blocked_windows_system32(self) -> None:
        assert _is_blocked_mount("C:\\Windows\\System32") is True

    def test_allowed_home_dir(self) -> None:
        assert _is_blocked_mount("/home/user/project") is False

    def test_allowed_workspace(self) -> None:
        assert _is_blocked_mount("/workspace/myapp") is False


class TestDockerErrorParsing:
    """Tests fuer _parse_docker_error."""

    def test_no_such_container(self) -> None:
        msg = _parse_docker_error("Error: No such container: abc123")
        assert "nicht gefunden" in msg.lower() or "not found" in msg.lower()

    def test_no_such_image(self) -> None:
        msg = _parse_docker_error("Error: No such image: myimage")
        assert "image" in msg.lower()

    def test_name_in_use(self) -> None:
        msg = _parse_docker_error("name is already in use by container")
        assert "bereits" in msg.lower() or "already" in msg.lower()

    def test_permission_denied(self) -> None:
        msg = _parse_docker_error("permission denied while trying to connect")
        assert "permission" in msg.lower() or "zugriff" in msg.lower()

    def test_connection_refused(self) -> None:
        msg = _parse_docker_error("Cannot connect to the Docker daemon")
        assert "daemon" in msg.lower() or "docker" in msg.lower()

    def test_port_already_allocated(self) -> None:
        msg = _parse_docker_error("port is already allocated")
        assert "port" in msg.lower()

    def test_unknown_error(self) -> None:
        msg = _parse_docker_error("Something unexpected happened")
        assert "Something" in msg


# =============================================================================
# Docker Tool Tests (mit Mock-Subprocess)
# =============================================================================


async def _mock_run_docker(*args: str, timeout: int = 60) -> tuple[int, str, str]:
    """Default-Mock fuer _run_docker."""
    return 0, "", ""


class TestDockerPs:
    """Tests fuer docker_ps."""

    async def test_ps_basic(self, docker: DockerTools) -> None:
        table_output = (
            "CONTAINER ID\tNAMES\tIMAGE\tSTATUS\tPORTS\nabc123\tweb\tnginx\tUp 2 hours\t80/tcp"
        )
        with patch("cognithor.mcp.docker_tools._run_docker", return_value=(0, table_output, "")):
            result = await docker.docker_ps()
            assert "abc123" in result
            assert "nginx" in result

    async def test_ps_all(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "output", "")
        ) as mock:
            await docker.docker_ps(all=True)
            # Verify -a flag was passed
            call_args = mock.call_args[0]
            assert "-a" in call_args

    async def test_ps_with_filter(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "output", "")
        ) as mock:
            await docker.docker_ps(filter="name=web")
            call_args = mock.call_args[0]
            assert "--filter" in call_args
            assert "name=web" in call_args

    async def test_ps_empty(self, docker: DockerTools) -> None:
        with patch("cognithor.mcp.docker_tools._run_docker", return_value=(0, "", "")):
            result = await docker.docker_ps()
            assert "No containers" in result

    async def test_ps_error(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(1, "", "Cannot connect")
        ):
            result = await docker.docker_ps()
            assert "Error" in result


class TestDockerLogs:
    """Tests fuer docker_logs."""

    async def test_logs_basic(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "log line 1\nlog line 2", "")
        ):
            result = await docker.docker_logs(container="web")
            assert "log line 1" in result

    async def test_logs_with_tail(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "output", "")
        ) as mock:
            await docker.docker_logs(container="web", tail=50)
            call_args = mock.call_args[0]
            assert "--tail" in call_args
            assert "50" in call_args

    async def test_logs_with_since(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "output", "")
        ) as mock:
            await docker.docker_logs(container="web", since="1h")
            call_args = mock.call_args[0]
            assert "--since" in call_args
            assert "1h" in call_args

    async def test_logs_invalid_name(self, docker: DockerTools) -> None:
        result = await docker.docker_logs(container="test;rm -rf /")
        assert "Error" in result
        assert "Invalid" in result

    async def test_logs_follow_ignored(self, docker: DockerTools) -> None:
        """follow=True should be silently ignored."""
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "output", "")
        ) as mock:
            await docker.docker_logs(container="web", follow=True)
            call_args = mock.call_args[0]
            assert "--follow" not in call_args
            assert "-f" not in call_args

    async def test_logs_tail_clamped(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "output", "")
        ) as mock:
            await docker.docker_logs(container="web", tail=999999)
            call_args = mock.call_args[0]
            assert "10000" in call_args  # Clamped to max


class TestDockerInspect:
    """Tests fuer docker_inspect."""

    async def test_inspect_basic(self, docker: DockerTools) -> None:
        json_output = '[{"Id": "abc123", "State": {"Status": "running"}}]'
        with patch("cognithor.mcp.docker_tools._run_docker", return_value=(0, json_output, "")):
            result = await docker.docker_inspect(target="web")
            assert "abc123" in result

    async def test_inspect_with_format(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "running", "")
        ) as mock:
            await docker.docker_inspect(target="web", format="{{.State.Status}}")
            call_args = mock.call_args[0]
            assert "--format" in call_args

    async def test_inspect_image_with_slash(self, docker: DockerTools) -> None:
        """Image names like library/nginx should be accepted."""
        with patch("cognithor.mcp.docker_tools._run_docker", return_value=(0, "{}", "")):
            result = await docker.docker_inspect(target="library/nginx:latest")
            assert "Error" not in result

    async def test_inspect_invalid_target(self, docker: DockerTools) -> None:
        result = await docker.docker_inspect(target="test;rm -rf /")
        assert "Error" in result


class TestDockerRun:
    """Tests fuer docker_run -- inkl. Security-Checks."""

    async def test_run_basic(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "abc123def456\n", "")
        ):
            result = await docker.docker_run(image="nginx:latest")
            assert "started successfully" in result.lower() or "abc123" in result

    async def test_run_with_name(self, docker: DockerTools) -> None:
        with patch("cognithor.mcp.docker_tools._run_docker", return_value=(0, "abc123\n", "")):
            result = await docker.docker_run(image="nginx", name="web-server")
            assert "web-server" in result

    async def test_run_with_ports(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "abc123\n", "")
        ) as mock:
            await docker.docker_run(image="nginx", ports=["8080:80"])
            call_args = mock.call_args[0]
            assert "-p" in call_args
            assert "8080:80" in call_args

    async def test_run_invalid_port(self, docker: DockerTools) -> None:
        result = await docker.docker_run(image="nginx", ports=["invalid"])
        assert "Error" in result
        assert "Invalid port" in result

    async def test_run_with_env(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(0, "abc123\n", "")
        ) as mock:
            await docker.docker_run(image="nginx", env={"NODE_ENV": "production"})
            call_args = mock.call_args[0]
            assert "-e" in call_args
            assert "NODE_ENV=production" in call_args

    async def test_run_invalid_env_name(self, docker: DockerTools) -> None:
        result = await docker.docker_run(image="nginx", env={"bad;name": "value"})
        assert "Error" in result
        assert "Invalid environment variable" in result

    async def test_run_empty_image(self, docker: DockerTools) -> None:
        result = await docker.docker_run(image="")
        assert "Error" in result
        assert "required" in result.lower()

    async def test_run_invalid_image(self, docker: DockerTools) -> None:
        result = await docker.docker_run(image="test;rm -rf /")
        assert "Error" in result
        assert "Invalid image" in result

    async def test_run_invalid_container_name(self, docker: DockerTools) -> None:
        result = await docker.docker_run(image="nginx", name="bad;name")
        assert "Error" in result

    # Security tests

    async def test_run_blocks_privileged_in_command(self, docker: DockerTools) -> None:
        result = await docker.docker_run(image="nginx", command="--privileged bash")
        assert "Error" in result
        assert "blocked" in result.lower()

    async def test_run_blocks_network_host_in_command(self, docker: DockerTools) -> None:
        result = await docker.docker_run(image="nginx", command="--network host bash")
        assert "Error" in result
        assert "blocked" in result.lower()

    async def test_run_docker_error(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(1, "", "No such image: foo")
        ):
            result = await docker.docker_run(image="foo")
            assert "Error" in result


class TestDockerStop:
    """Tests fuer docker_stop."""

    async def test_stop_basic(self, docker: DockerTools) -> None:
        with patch("cognithor.mcp.docker_tools._run_docker", return_value=(0, "web\n", "")):
            result = await docker.docker_stop(container="web")
            assert "stopped" in result.lower()

    async def test_stop_with_timeout(self, docker: DockerTools) -> None:
        with patch("cognithor.mcp.docker_tools._run_docker", return_value=(0, "", "")) as mock:
            await docker.docker_stop(container="web", timeout=30)
            call_args = mock.call_args[0]
            assert "-t" in call_args
            assert "30" in call_args

    async def test_stop_invalid_name(self, docker: DockerTools) -> None:
        result = await docker.docker_stop(container="test;rm -rf /")
        assert "Error" in result

    async def test_stop_timeout_clamped(self, docker: DockerTools) -> None:
        with patch("cognithor.mcp.docker_tools._run_docker", return_value=(0, "", "")) as mock:
            await docker.docker_stop(container="web", timeout=99999)
            call_args = mock.call_args[0]
            assert "300" in call_args  # Clamped to max

    async def test_stop_error(self, docker: DockerTools) -> None:
        with patch(
            "cognithor.mcp.docker_tools._run_docker", return_value=(1, "", "No such container")
        ):
            result = await docker.docker_stop(container="nonexistent")
            assert "Error" in result


# =============================================================================
# Registration Tests
# =============================================================================


class TestRegistration:
    """Tests fuer register_docker_tools."""

    def test_registration_when_docker_available(
        self, mock_mcp_client: MagicMock, config: CognithorConfig
    ) -> None:
        with patch("cognithor.mcp.docker_tools._docker_available", return_value=True):
            result = register_docker_tools(mock_mcp_client, config)
            assert result is not None
            assert isinstance(result, DockerTools)
            # 5 tools registered
            assert mock_mcp_client.register_builtin_handler.call_count == 5
            # Verify tool names
            registered_names = [
                call[0][0] for call in mock_mcp_client.register_builtin_handler.call_args_list
            ]
            assert "docker_ps" in registered_names
            assert "docker_logs" in registered_names
            assert "docker_inspect" in registered_names
            assert "docker_run" in registered_names
            assert "docker_stop" in registered_names

    def test_registration_skipped_when_docker_unavailable(
        self,
        mock_mcp_client: MagicMock,
        config: CognithorConfig,
    ) -> None:
        with patch("cognithor.mcp.docker_tools._docker_available", return_value=False):
            result = register_docker_tools(mock_mcp_client, config)
            assert result is None
            assert mock_mcp_client.register_builtin_handler.call_count == 0


# =============================================================================
# Output Truncation Test
# =============================================================================


class TestOutputTruncation:
    """Tests fuer Output-Truncation."""

    async def test_long_output_truncated(self, docker: DockerTools) -> None:
        long_output = "x" * 60_000
        with patch("cognithor.mcp.docker_tools._run_docker", return_value=(0, long_output, "")):
            result = await docker.docker_ps()
            assert len(result) <= 50_100  # 50000 + truncation message
            assert "truncated" in result.lower() or "gekürzt" in result.lower()
