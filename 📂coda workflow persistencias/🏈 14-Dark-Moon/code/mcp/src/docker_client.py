import os
import re
import time
import socket
import docker
import sys
from typing import Optional, List, Dict, Any
from docker.models.containers import Container
from docker.errors import DockerException, NotFound

from src.models.common import ExecutionResult, ExecutionStatus
from src.execution_guard import adapt_command, classify, effective_timeout, remediation

STREAM_BASE = "/tmp/darkmoon_mcp_stream"

# Long-running scanners that routinely outlive the `timeout` wrapper: coreutils
# signals its direct child (bash), and a grandchild started through a pipe can be
# reparented and keep hammering the target long after the campaign moved on. Two
# of these were still running 72 minutes after their campaign had frozen.
_REAPABLE = (
    "hydra", "medusa", "ncrack", "patator", "sqlmap", "ffuf", "dirb",
    "gobuster", "feroxbuster", "wfuzz", "naabu", "masscan", "nuclei",
)


class DarkmoonDockerClient:
    """
    Docker client to interact with the Darkmoon security toolbox container.
    Handles command execution, health checks, and resource management.

    + Live stream broadcast to UNIX socket for monitoring console.
    """

    def __init__(
        self,
        container_name: str = "darkmoon",
        timeout: int = 300,
    ):
        self.container_name = container_name
        self.default_timeout = timeout
        try:
            self.client = docker.from_env()
        except DockerException as e:
            raise RuntimeError(f"Failed to connect to Docker: {e}")

        # Ensure stream socket exists (server created by darkmoon-cli)
        # Client will just connect if available.
        self._stream_enabled = True
        self._gpu_cache = None

    def _broadcast(self, b: bytes, session_id: str | None = None):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'mcp/src/docker_client.py','step':'_broadcast','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def get_container(self) -> Optional[Container]:
        """Get the Darkmoon container if it exists and is running."""
        try:
            container = self.client.containers.get(self.container_name)
            container.reload()
            return container if container.status == "running" else None
        except NotFound:
            return None
        except DockerException as e:
            raise RuntimeError(f"Error accessing container: {e}")

    def execute_command(
        self,
        command: str | List[str],
        timeout: Optional[int] = None,
        workdir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,   # NEW
    ) -> ExecutionResult:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'mcp/src/docker_client.py','step':'execute_command','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def _gpu_state(self, container) -> Dict[str, str]:
        """Read the GPU profile the toolbox entrypoint wrote at container start.

        The file lives INSIDE the toolbox, not next to the MCP: reading it from the
        local filesystem silently returned "no GPU" on every host and hashcat was
        never pinned to the card. Cached for the process lifetime, since hardware
        does not change under a running container.
        """
        if getattr(self, "_gpu_cache", None) is not None:
            return self._gpu_cache

        state = {"DM_GPU": "0", "DM_GPU_VENDOR": "unknown", "DM_HASHCAT_OPTS": ""}
        try:
            exec_id = self.client.api.exec_create(
                container=container.id,
                cmd=["bash", "-c", "cat /run/darkmoon-gpu.env 2>/dev/null || true"],
            )["Id"]
            raw = self.client.api.exec_start(exec_id).decode("utf-8", errors="ignore")
            for line in raw.splitlines():
                if "=" in line:
                    k, _, v = line.strip().partition("=")
                    state[k.strip()] = v.strip()
        except Exception:
            pass  # absent or unreadable: fall back to CPU assumptions, never crash

        self._gpu_cache = state
        return state

    def _reap_survivors(self, container, cmd_str: str) -> None:
        """Kill scanner grandchildren that outlived the `timeout` wrapper.

        `timeout` signals the bash it started; a tool launched inside a pipeline
        can survive that and keep running against the target indefinitely. Only
        binaries from a fixed allow-list are reaped, and only when the command
        that just expired actually mentions them, so this can never kill an
        unrelated process.
        """
        targets = [t for t in _REAPABLE if re.search(rf"\b{t}\b", cmd_str or "")]
        if not targets:
            return
        try:
            for tool in targets:
                self.client.api.exec_start(
                    self.client.api.exec_create(
                        container=container.id,
                        cmd=["bash", "-c", f"pkill -9 -x {tool} 2>/dev/null || true"],
                    )["Id"]
                )
        except Exception:
            pass  # best effort: never let cleanup mask the timeout itself

    def check_tool_available(self, tool_name: str) -> bool:
        result = self.execute_command(f"which {tool_name}", timeout=5)
        return result.success

    def check_tools_bulk(self, tools: List[str]) -> Dict[str, bool]:
        """Probe many tools in ONE container round-trip.

        The old health check ran one `docker exec which <tool>` per tool. At a
        dozen tools that is a dozen round-trips of container-exec overhead on
        every campaign start; over the full toolbox it would be a hundred. A
        single `command -v` loop inside one exec returns the whole map at once,
        so reporting the complete toolbox costs no more than probing four tools
        did before. A tool name is validated to a safe charset so the joined
        loop can never inject.
        """
        safe = [t for t in tools if re.fullmatch(r"[A-Za-z0-9_.+-]+", t or "")]
        if not safe:
            return {}
        names = " ".join(safe)
        script = (
            'for t in ' + names + '; do '
            'if command -v "$t" >/dev/null 2>&1; then echo "$t=1"; '
            'else echo "$t=0"; fi; done'
        )
        result = self.execute_command(["bash", "-c", script], timeout=30)
        status = {t: False for t in safe}
        for line in (result.stdout or "").splitlines():
            line = line.strip()
            if "=" in line:
                name, _, val = line.partition("=")
                if name in status:
                    status[name] = val.strip() == "1"
        return status

    def get_disk_usage(self) -> Optional[Dict[str, Any]]:
        """Get disk usage information from the container."""
        result = self.execute_command("df -h /opt/darkmoon/out", timeout=5)
        if result.success:
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                return {
                    "filesystem": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "use_percent": parts[4],
                    "mounted_on": parts[5] if len(parts) > 5 else "-",
                }
        return None

    def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check."""
        container = self.get_container()
        if not container:
            return {
                "healthy": False,
                "container_running": False,
                "message": f"Container '{self.container_name}' not found or not running",
            }

        tools_to_check = ["naabu", "nuclei", "httpx", "subfinder"]
        tools_status = {}
        for tool in tools_to_check:
            tools_status[tool] = self.check_tool_available(tool)

        disk_usage = self.get_disk_usage()
        all_tools_available = all(tools_status.values())

        return {
            "healthy": all_tools_available,
            "container_running": True,
            "tools_available": tools_status,
            "disk_usage": disk_usage,
            "message": "All systems operational"
            if all_tools_available
            else "Some tools are not available",
        }

    def cleanup(self):
        """Clean up Docker client resources."""
        if hasattr(self, "client"):
            self.client.close()