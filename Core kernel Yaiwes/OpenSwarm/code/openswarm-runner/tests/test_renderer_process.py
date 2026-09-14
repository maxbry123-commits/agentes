"""The renderer half: a run that asked for a browser must never quietly proceed without one.

The Electron boot itself needs a Linux container and a real display, so what is pinned here is
the contract around it: the deep link the window opens on, the bundle check, and the three ways
"no window" is allowed to end (loudly, every time).
"""

import subprocess

import pytest

from runner.boot import renderer_process
from runner.boot.renderer_process import (
    CONTAINER_CHROMIUM_FLAGS,
    RendererUnavailable,
    SANDBOX_FLAGS,
    await_registration,
    dashboard_url,
    serve_frontend,
    start_electron,
)
from runner.run_spec import CLOUD_RUN_DASHBOARD_ID


@pytest.fixture
def dead_electron():
    """A real Popen that has already exited; await_registration is typechecked on Popen."""
    process = subprocess.Popen(["/bin/sh", "-c", "exit 9"])
    process.wait()
    return process


@pytest.fixture
def live_electron():
    """A real Popen that stays up long enough for a poll loop to run against it."""
    process = subprocess.Popen(["/bin/sh", "-c", "sleep 30"])
    yield process
    process.kill()
    process.wait()


def test_the_window_opens_on_the_run_dashboard_not_the_picker() -> None:
    # HashRouter, so the route has to be a fragment or the static server 404s on it.
    assert dashboard_url(4173, CLOUD_RUN_DASHBOARD_ID) == (
        "http://127.0.0.1:4173/index.html#/dashboard/cloud-run"
    )


def test_a_missing_bundle_says_so_instead_of_serving_an_empty_dir(tmp_path) -> None:
    with pytest.raises(RendererUnavailable, match="no frontend bundle"):
        serve_frontend(str(tmp_path))


def test_a_missing_electron_binary_fails_the_run_rather_than_the_workflow(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ELECTRON_BIN", str(tmp_path / "nope"))
    with pytest.raises(RendererUnavailable, match="built without a renderer"):
        start_electron(str(tmp_path), 8324, "http://127.0.0.1:4173/index.html")


def test_chromium_is_launched_unsandboxed_on_purpose_and_out_of_shared_memory() -> None:
    # Dropping Chromium's own sandbox is a real tradeoff (the Firecracker VM is the wall that's
    # left), so it lives in a named constant a reviewer trips over, not inside a launch string.
    assert SANDBOX_FLAGS == ["--no-sandbox"]
    assert "--disable-dev-shm-usage" in CONTAINER_CHROMIUM_FLAGS


def test_a_dead_electron_is_reported_as_dead_not_waited_out(monkeypatch, dead_electron) -> None:
    monkeypatch.setattr(renderer_process, "RENDERER_TIMEOUT_SECONDS", 30.0)
    with pytest.raises(RendererUnavailable, match="exited with code 9"):
        await_registration("http://127.0.0.1:1", {}, dead_electron, deadline=1e9)


def test_a_window_that_never_registers_times_out_loudly(monkeypatch, live_electron) -> None:
    monkeypatch.setattr(renderer_process, "RENDERER_TIMEOUT_SECONDS", 0.5)
    with pytest.raises(RendererUnavailable, match="no renderer ever registered"):
        await_registration("http://127.0.0.1:1", {}, live_electron, deadline=1e9)


def test_registration_is_believed_only_when_the_backend_says_a_socket_is_attached(monkeypatch, live_electron) -> None:
    replies = [{"attached": False, "ever_attached": False, "connections": 0},
               {"attached": True, "ever_attached": True, "connections": 1}]

    class p_Response:
        def json(self):
            return replies.pop(0)

    class p_Client:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def get(self, url, headers=None):
            return p_Response()

    monkeypatch.setattr(renderer_process.httpx, "Client", lambda **kw: p_Client())
    await_registration("http://127.0.0.1:1", {}, live_electron, deadline=1e9)
    assert replies == []
