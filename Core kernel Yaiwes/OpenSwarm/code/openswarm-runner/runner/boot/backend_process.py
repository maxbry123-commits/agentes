"""Boot the OpenSwarm backend inside the container and wait until it answers.

Spawned the same way the desktop shell spawns it (`python -m uvicorn backend.main:app`
on loopback) so the cloud path and the laptop path are the same code on the same
socket. Loopback, not 0.0.0.0: every caller of this API lives in this container, and
the agent running inside it has Bash, so there is no reason to publish the port onto
the machine's private network.
"""

import os
import subprocess
import time
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, ConfigDict, InstanceOf
from typeguard import typechecked

HOST = "127.0.0.1"
HEALTH_PATH = "/api/health/check"
# 9Router is a Next.js standalone server: it binds `process.env.HOSTNAME || '0.0.0.0'`, and Docker sets HOSTNAME to the container id, so left alone it listens on the container's eth0 address and every probe of 127.0.0.1:20128 gets ECONNREFUSED. Set on the backend's env because the backend is what spawns node.
ROUTER_BIND_HOSTNAME = "127.0.0.1"
AUTH_TOKEN_FILENAME = "auth.token"
# The backend imports the whole app graph before it binds; on a cold Fly machine that has been measured in tens of seconds, so the budget is generous rather than tight.
BOOT_TIMEOUT_SECONDS = 120.0
SHUTDOWN_GRACE_SECONDS = 10.0


class BackendUnavailable(RuntimeError):
    """The backend never came up, or died while we were using it."""


class BackendProcess(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    process: InstanceOf[subprocess.Popen]
    base_url: str
    token: str

    @typechecked
    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    @typechecked
    def is_alive(self) -> bool:
        return self.process.poll() is None


@typechecked
def p_command(port: int) -> List[str]:
    return ["python3", "-m", "uvicorn", "backend.main:app", "--host", HOST, "--port", str(port)]


@typechecked
def p_read_auth_token(data_root: str) -> str:
    """The backend mints this before it binds, so by the time health passes the file exists."""
    path = os.path.join(data_root, AUTH_TOKEN_FILENAME)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    except OSError as exc:
        raise BackendUnavailable(f"backend is up but its auth token is unreadable at {path}: {exc}") from exc


@typechecked
def start_backend(app_root: str, data_root: str, port: int, deadline: float) -> BackendProcess:
    """Spawn the backend and block until it answers health, or raise BackendUnavailable."""
    environment = dict(os.environ)
    environment["OPENSWARM_DATA_ROOT"] = data_root
    environment["OPENSWARM_HEADLESS"] = "1"
    environment["OPENSWARM_PORT"] = str(port)
    environment["OPENSWARM_HOST"] = HOST
    environment["HOSTNAME"] = ROUTER_BIND_HOSTNAME
    environment["PYTHONPATH"] = app_root

    process = subprocess.Popen(p_command(port), cwd=app_root, env=environment)
    base_url = f"http://{HOST}:{port}"
    budget = min(time.monotonic() + BOOT_TIMEOUT_SECONDS, deadline)

    with httpx.Client(timeout=2.0) as client:
        while time.monotonic() < budget:
            if process.poll() is not None:
                raise BackendUnavailable(f"backend exited during startup with code {process.returncode}")
            try:
                healthy = client.get(f"{base_url}{HEALTH_PATH}").status_code == 200
            except httpx.HTTPError:
                healthy = False
            if healthy:
                try:
                    token = p_read_auth_token(data_root)
                except BackendUnavailable:
                    stop_backend(process)
                    raise
                return BackendProcess(process=process, base_url=base_url, token=token)
            time.sleep(0.25)

    stop_backend(process)
    raise BackendUnavailable(f"backend did not answer {HEALTH_PATH} within its startup budget")


@typechecked
def stop_backend(process: Optional[subprocess.Popen]) -> None:
    """SIGTERM then SIGKILL. The machine is about to die anyway; this just stops the logs mid-sentence."""
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=SHUTDOWN_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=SHUTDOWN_GRACE_SECONDS)
