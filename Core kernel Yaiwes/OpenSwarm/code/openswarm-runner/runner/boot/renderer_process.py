"""Boot the real Electron shell inside the container so browser tools have a window to drive.

The browser tier is not an HTTP client: the element serialization and every click, type and
scroll live in the frontend and drive a live Electron `<webview>`. There is no way to get
laptop-identical behaviour without the laptop's actual renderer, so this starts one on a
virtual display and points it at the backend that is already running in this container.

The Electron process runs the same `ELECTRON_DEV=1` path a developer uses (`bash run.sh`):
the shell attaches to an existing backend on OPENSWARM_PORT instead of spawning its own, and
loads whatever OPENSWARM_DEV_URL says. Here that URL is the packaged frontend bundle served
off loopback, deep-linked straight at the run's dashboard so the window registers without a
human clicking anything.
"""

import functools
import http.server
import logging
import os
import shutil
import socketserver
import subprocess
import threading
import time
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, ConfigDict, InstanceOf
from typeguard import typechecked

logger = logging.getLogger("runner.renderer")

HOST = "127.0.0.1"
RENDERER_HEALTH_PATH = "/api/health/renderer"
# Same port the packaged app prefers, so the renderer's origin (and therefore its localStorage) is the one the frontend was built expecting.
FRONTEND_PORT = 4173
DISPLAY = ":99"
XVFB_SCREEN = "1920x1080x24"
# Cold Electron under a virtual display: Xvfb, Chromium boot, React mount, then the deferred dashboard socket. Measured in the low tens of seconds, so the budget is generous rather than tight.
RENDERER_TIMEOUT_SECONDS = 180.0
XVFB_READY_TIMEOUT_SECONDS = 20.0
SHUTDOWN_GRACE_SECONDS = 5.0

# Chromium's setuid sandbox needs a root-owned binary and its namespace sandbox needs unprivileged
# user namespaces, neither of which a non-root container under Docker's default seccomp profile has.
# The isolation this run relies on is the Firecracker VM around the whole container, not Chromium's
# own layer. Stated here rather than buried in a launch string, because dropping a sandbox is a
# choice and the reader deserves to see it made.
SANDBOX_FLAGS: List[str] = ["--no-sandbox"]
# /dev/shm defaults to 64MB in a container, which Chromium overruns and then crashes on.
CONTAINER_CHROMIUM_FLAGS: List[str] = ["--disable-dev-shm-usage", "--disable-gpu"]


class RendererUnavailable(RuntimeError):
    """No Electron window ever registered, so browser tools would be dead this run."""


class RendererProcess(BaseModel):
    """The virtual display and the Electron shell drawing into it. Dies with the run."""

    model_config = ConfigDict(validate_assignment=True)

    xvfb: InstanceOf[subprocess.Popen]
    electron: InstanceOf[subprocess.Popen]
    url: str

    @typechecked
    def is_alive(self) -> bool:
        return self.electron.poll() is None and self.xvfb.poll() is None


@typechecked
def dashboard_url(port: int, dashboard_id: str) -> str:
    """The frontend deep-link that mounts a dashboard directly. HashRouter, so the route is a fragment."""
    return f"http://{HOST}:{port}/index.html#/dashboard/{dashboard_id}"


@typechecked
def serve_frontend(frontend_dir: str) -> int:
    """Serve the built bundle off loopback in a daemon thread; returns the port it landed on.

    Falls back to an OS-assigned port if 4173 is held, exactly like the packaged shell does.
    """
    if not os.path.isfile(os.path.join(frontend_dir, "index.html")):
        raise RendererUnavailable(
            f"no frontend bundle at {frontend_dir}; the image must be built with frontend/dist in it"
        )

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=frontend_dir)

    class p_Server(socketserver.ThreadingTCPServer):
        daemon_threads = True
        allow_reuse_address = True

    try:
        server = p_Server((HOST, FRONTEND_PORT), handler)
    except OSError:
        server = p_Server((HOST, 0), handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True, name="frontend-server").start()
    logger.info("frontend bundle served from %s on %s:%d", frontend_dir, HOST, port)
    return port


@typechecked
def p_x_socket_ready(display: str) -> bool:
    return os.path.exists(f"/tmp/.X11-unix/X{display.lstrip(':')}")


@typechecked
def start_xvfb(display: str = DISPLAY) -> subprocess.Popen:
    """Bring up the virtual display and wait for its socket, so Electron never races it."""
    if shutil.which("Xvfb") is None:
        raise RendererUnavailable("Xvfb is not installed in this image, so there is no display to draw on")
    process = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", XVFB_SCREEN, "-nolisten", "tcp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    budget = time.monotonic() + XVFB_READY_TIMEOUT_SECONDS
    while time.monotonic() < budget:
        if process.poll() is not None:
            raise RendererUnavailable(f"Xvfb exited immediately with code {process.returncode}")
        if p_x_socket_ready(display):
            logger.info("virtual display %s up (%s)", display, XVFB_SCREEN)
            return process
        time.sleep(0.1)
    p_stop(process)
    raise RendererUnavailable(f"Xvfb never created a socket for {display}")


@typechecked
def p_electron_env(backend_port: int, url: str, display: str) -> Dict[str, str]:
    environment = dict(os.environ)
    # The dev path: attach to the backend already running here rather than spawning a second one, and load the bundle we are serving instead of a webpack dev server.
    environment["ELECTRON_DEV"] = "1"
    environment["OPENSWARM_DEV_URL"] = url
    environment["OPENSWARM_PORT"] = str(backend_port)
    environment["DISPLAY"] = display
    environment["ELECTRON_DISABLE_SECURITY_WARNINGS"] = "1"
    environment.pop("OPENSWARM_PACKAGED", None)
    return environment


@typechecked
def start_electron(app_root: str, backend_port: int, url: str, display: str = DISPLAY) -> subprocess.Popen:
    binary = os.environ.get("ELECTRON_BIN", "/app/electron-runtime/electron")
    if not os.path.isfile(binary):
        raise RendererUnavailable(f"no Electron binary at {binary}; the image was built without a renderer")
    app_dir = os.path.join(app_root, "electron")
    command = [binary, app_dir, *SANDBOX_FLAGS, *CONTAINER_CHROMIUM_FLAGS]
    logger.info("starting Electron: %s", " ".join(command))
    return subprocess.Popen(command, cwd=app_dir, env=p_electron_env(backend_port, url, display))


@typechecked
def await_registration(
    base_url: str,
    headers: Dict[str, str],
    electron: subprocess.Popen,
    deadline: float,
) -> None:
    """Block until the backend reports a renderer on its dashboard socket, or raise.

    Polls the backend rather than the Electron process because "the window is up" and "the
    window can be driven" are different claims, and only the second one matters.
    """
    budget = min(time.monotonic() + RENDERER_TIMEOUT_SECONDS, deadline)
    with httpx.Client(timeout=5.0) as client:
        while time.monotonic() < budget:
            if electron.poll() is not None:
                raise RendererUnavailable(
                    f"Electron exited with code {electron.returncode} before any window registered"
                )
            try:
                body = client.get(f"{base_url}{RENDERER_HEALTH_PATH}", headers=headers).json()
            except (httpx.HTTPError, ValueError):
                body = {}
            if body.get("attached"):
                logger.info("renderer registered (%s dashboard connection(s))", body.get("connections"))
                return
            time.sleep(0.5)
    raise RendererUnavailable(
        "Electron started but no renderer ever registered on the dashboard WebSocket within "
        f"{RENDERER_TIMEOUT_SECONDS:.0f}s, so browser tools would be dead this run"
    )


@typechecked
def start_renderer(
    app_root: str,
    frontend_dir: str,
    backend_base_url: str,
    backend_headers: Dict[str, str],
    backend_port: int,
    dashboard_id: str,
    deadline: float,
) -> RendererProcess:
    """Display, bundle server, Electron, then block until the window is actually drivable."""
    url = dashboard_url(serve_frontend(frontend_dir), dashboard_id)
    xvfb = start_xvfb()
    try:
        electron = start_electron(app_root, backend_port, url)
    except BaseException:
        p_stop(xvfb)
        raise
    try:
        await_registration(backend_base_url, backend_headers, electron, deadline)
    except BaseException:
        p_stop(electron)
        p_stop(xvfb)
        raise
    return RendererProcess(xvfb=xvfb, electron=electron, url=url)


@typechecked
def p_stop(process: Optional[subprocess.Popen]) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=SHUTDOWN_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=SHUTDOWN_GRACE_SECONDS)


@typechecked
def stop_renderer(renderer: Optional[RendererProcess]) -> None:
    """Electron first, then the display it was drawing on."""
    if renderer is None:
        return
    p_stop(renderer.electron)
    p_stop(renderer.xvfb)
