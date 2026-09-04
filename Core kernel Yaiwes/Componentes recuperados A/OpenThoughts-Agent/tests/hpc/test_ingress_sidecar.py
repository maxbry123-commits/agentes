"""Unit tests for the auth-gating ingress sidecar (Stage 1 / gate G1).

Spins the sidecar app against a STUB upstream (an in-process ASGI app wired via
httpx.ASGITransport — no real socket), and asserts:

  (a) valid key + GET /proxy/<ep>/v1/models          -> 200 with the stub body
  (b) missing / wrong key                             -> 401
  (c) valid key + a control-route / non-/v1 path      -> 403
  (d) the UPSTREAM request carries IRIS_CONTROLLER_AUTH and NOT the sandbox key
  (e) a streamed (SSE) completion round-trips intact

All tokens here are in-process dummies; no real secret is referenced.

Run:
    .venv/bin/python -m pytest tests/hpc/test_ingress_sidecar.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.testclient import TestClient

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hpc.ingress_sidecar import create_app  # noqa: E402

# In-process dummy tokens (NEVER a real secret).
DUMMY_INGRESS_KEY = "dummy-sandbox-key-abc123"
DUMMY_CONTROLLER_AUTH = "dummy-controller-cred-xyz789"

# Captures the headers/path the stub upstream last received, so tests can assert
# credential-swap behavior.
_LAST_UPSTREAM: dict = {}


def _make_stub_upstream() -> FastAPI:
    stub = FastAPI()

    @stub.api_route("/{full_path:path}", methods=["GET", "POST"])
    async def _catch_all(request: Request, full_path: str):
        _LAST_UPSTREAM.clear()
        _LAST_UPSTREAM["path"] = request.url.path
        _LAST_UPSTREAM["headers"] = dict(request.headers)
        if request.url.path.endswith("/v1/models"):
            return JSONResponse({"object": "list", "data": [{"id": "stub-model"}]})
        if request.url.path.endswith("/v1/chat/completions"):

            async def _sse():
                for i in range(3):
                    yield f"data: chunk{i}\n\n".encode()
                yield b"data: [DONE]\n\n"

            return StreamingResponse(_sse(), media_type="text/event-stream")
        return JSONResponse({"echo": request.url.path})

    return stub


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("IRIS_INGRESS_API_KEY", DUMMY_INGRESS_KEY)
    monkeypatch.setenv("IRIS_CONTROLLER_AUTH", DUMMY_CONTROLLER_AUTH)
    upstream = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_make_stub_upstream()),
        base_url="http://upstream.local",
    )
    app = create_app(upstream_client=upstream)
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
def test_valid_key_models_returns_200(client):
    r = client.get(
        "/proxy/otagent.job1/v1/models",
        headers={"Authorization": f"Bearer {DUMMY_INGRESS_KEY}"},
    )
    assert r.status_code == 200
    assert r.json()["data"][0]["id"] == "stub-model"


def test_missing_key_returns_401(client):
    r = client.get("/proxy/otagent.job1/v1/models")
    assert r.status_code == 401


def test_wrong_key_returns_401(client):
    r = client.get(
        "/proxy/otagent.job1/v1/models",
        headers={"Authorization": "Bearer not-the-key"},
    )
    assert r.status_code == 401


def test_non_bearer_scheme_returns_401(client):
    r = client.get(
        "/proxy/otagent.job1/v1/models",
        headers={"Authorization": f"Basic {DUMMY_INGRESS_KEY}"},
    )
    assert r.status_code == 401


@pytest.mark.parametrize(
    "path",
    [
        "/proxy/otagent.job1/admin",  # non-/v1 proxy subpath
        "/proxy/otagent.job1",  # bare endpoint, no /v1
        "/rpc/submit_job",  # control/RPC route
        "/api/cluster/status",  # dashboard control route
        "/proxy/otagent.job1/v2/models",  # not /v1
        "/v1/models",  # /v1 but not under /proxy/<name>/
    ],
)
def test_valid_key_but_forbidden_path_returns_403(client, path):
    r = client.get(path, headers={"Authorization": f"Bearer {DUMMY_INGRESS_KEY}"})
    assert r.status_code == 403, f"expected 403 for {path}, got {r.status_code}"


def test_upstream_gets_controller_cred_not_sandbox_key(client):
    r = client.get(
        "/proxy/otagent.job1/v1/models",
        headers={"Authorization": f"Bearer {DUMMY_INGRESS_KEY}"},
    )
    assert r.status_code == 200
    up_auth = _LAST_UPSTREAM["headers"].get("authorization")
    assert up_auth == f"Bearer {DUMMY_CONTROLLER_AUTH}", up_auth
    # The sandbox key must never appear anywhere in the upstream headers.
    joined = " ".join(_LAST_UPSTREAM["headers"].values())
    assert DUMMY_INGRESS_KEY not in joined
    # Path is preserved verbatim upstream.
    assert _LAST_UPSTREAM["path"] == "/proxy/otagent.job1/v1/models"


def test_streamed_completion_round_trips(client):
    r = client.post(
        "/proxy/otagent.job1/v1/chat/completions",
        headers={"Authorization": f"Bearer {DUMMY_INGRESS_KEY}"},
        json={"model": "stub-model", "stream": True, "messages": []},
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers.get("content-type", "")
    body = r.text
    for i in range(3):
        assert f"data: chunk{i}" in body
    assert "data: [DONE]" in body


def test_healthz_unauthenticated(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_no_ingress_key_env_returns_401(client, monkeypatch):
    # If the server has no key configured, even a "valid-looking" request is denied.
    monkeypatch.delenv("IRIS_INGRESS_API_KEY", raising=False)
    r = client.get(
        "/proxy/otagent.job1/v1/models",
        headers={"Authorization": f"Bearer {DUMMY_INGRESS_KEY}"},
    )
    assert r.status_code == 401
