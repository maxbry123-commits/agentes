"""ingress_sidecar.py — an auth-gating reverse-proxy sidecar for the Iris controller.

Stage 1 of the pinggy->controller-ingress plan
(``notes/ot-agent/pinggy_controller_ingress_plan.md``), realizing design-question
Q1 recommendation **(b): the auth gate lives in OUR code, not in marin's
``EndpointProxy``.**

This is ``scripts/inference/serve_public.py`` turned inside-out: instead of a
paid pinggy tunnel wrapping the *unauthenticated* localhost view of the
controller proxy, a thin FastAPI/uvicorn shim sits in front of the controller's
dashboard proxy and:

  * **AuthN** — requires ``Authorization: Bearer <IRIS_INGRESS_API_KEY>`` on
    every ``/proxy/...`` request (constant-time compare). Missing/wrong -> 401.
  * **AuthZ / least-privilege** — forwards ONLY paths matching
    ``^/proxy/<name>/v1(/...)?$`` (the inference surface). Anything else — a
    control route, the RPC port, a non-``/v1`` proxy subpath — -> 403. A sandbox
    key can never reach cluster-control RPCs (plan invariant 3).
  * **Credential swap** — strips the sandbox's inbound ``Authorization`` (and
    ``Cookie``) and attaches the controller's OWN credential
    (``IRIS_CONTROLLER_AUTH``) to the upstream request, so the sandbox never
    holds a cluster credential and the blast radius is inference-only.
  * **Streaming** — passes request/response bodies through unbuffered, so SSE
    (streamed ``/v1/chat/completions``) round-trips.

Security posture is deliberately light per the 2026-07-02 decision: these front
pre-emptible jobs (<12h) and today's ``serve_public.py`` already exposes these
endpoints with NO auth — a single static bearer token is the right amount of
gate. The token and the upstream credential are read from the environment by
name only; nothing is hardcoded or logged.

Env config (all name-only; see plan Q4 / evidence D):
  IRIS_INGRESS_API_KEY   required — the sandbox-facing static bearer token.
  IRIS_CONTROLLER_AUTH   optional — the controller's own upstream credential
                         (opaque bearer string); attached to forwarded requests.
  CONTROLLER_PROXY_BASE  upstream base URL (default http://127.0.0.1:8080) —
                         the controller dashboard proxy on the VM, or the
                         in-cluster svc on CoreWeave.
  SIDECAR_HOST           bind host (default 0.0.0.0).
  SIDECAR_PORT           bind port (default 8443).
  SIDECAR_TLS_CERT /
  SIDECAR_TLS_KEY        optional TLS cert/key paths (Stage 3, GCE-VM arm).

Run:
  IRIS_INGRESS_API_KEY=... CONTROLLER_PROXY_BASE=http://127.0.0.1:8080 \
      python -m hpc.ingress_sidecar
"""

from __future__ import annotations

import hmac
import os
import re
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

# Only the inference surface is forwardable. Two shapes are allowed:
#   * /proxy/<name>/v1(/...)          — the plain endpoint-proxy path (PRIVATE/in-cluster).
#   * /proxy/t/<token>/<name>/v1(/...) — the LINK capability path (scoped token in the URL,
#     the public scheme the native `iris.oa.dev/proxy/t/*` ingress uses). Forwarding it lets
#     the pinggy sidecar front a LINK endpoint (the #7448 bypass) — the token is endpoint-
#     scoped, carries no RPC authority, and the sidecar's own bearer still gates entry.
# `<name>` / `<token>` are single path segments; everything under `/v1` is allowed. Else -> 403.
_ALLOWED_PATH_RE = re.compile(r"^/proxy/(t/[^/]+/)?[^/]+/v1(/.*)?$")

# Hop-by-hop headers (RFC 7230 §6.1) + Authorization/Cookie, mirroring marin's
# EndpointProxy._HOP_BY_HOP. Stripped before forwarding upstream so the sandbox
# credential never leaks and the upstream connection is set up cleanly.
_HOP_BY_HOP = frozenset(
    {
        "host",
        "transfer-encoding",
        "connection",
        "keep-alive",
        "upgrade",
        "te",
        "trailer",
        "proxy-authorization",
        "proxy-authenticate",
        "cookie",
        "set-cookie",
        "authorization",
        "content-length",
    }
)

DEFAULT_CONTROLLER_PROXY_BASE = "http://127.0.0.1:8080"


def _extract_bearer(request: Request) -> Optional[str]:
    """Return the bearer token from the Authorization header, or None."""
    auth = request.headers.get("authorization")
    if not auth:
        return None
    parts = auth.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def _filtered_upstream_headers(
    request: Request, controller_auth: Optional[str]
) -> dict:
    """Copy request headers minus hop-by-hop/auth, then attach the controller cred."""
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP}
    if controller_auth:
        headers["authorization"] = f"Bearer {controller_auth}"
    return headers


def create_app(upstream_client: Optional[httpx.AsyncClient] = None) -> FastAPI:
    """Build the sidecar FastAPI app.

    Args:
        upstream_client: optional pre-built httpx AsyncClient whose ``base_url``
            points at the controller dashboard proxy. If None, one is built from
            ``CONTROLLER_PROXY_BASE`` on startup. Tests inject a client backed by
            an ASGITransport stub so no real socket is needed.
    """
    _injected = upstream_client is not None

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        if app.state.upstream_client is None:
            base = os.environ.get(
                "CONTROLLER_PROXY_BASE", DEFAULT_CONTROLLER_PROXY_BASE
            )
            # Generous read timeout: generation can be long-running.
            timeout = httpx.Timeout(connect=10.0, read=None, write=60.0, pool=10.0)
            app.state.upstream_client = httpx.AsyncClient(
                base_url=base, timeout=timeout
            )
        try:
            yield
        finally:
            # Only close a client we created; leave an injected (test-owned) one alone.
            if not _injected and app.state.upstream_client is not None:
                await app.state.upstream_client.aclose()

    app = FastAPI(
        title="iris-ingress-sidecar",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=_lifespan,
    )
    app.state.upstream_client = upstream_client

    @app.get("/healthz")
    async def _healthz() -> JSONResponse:
        # Unauthenticated liveness probe for the ingress LB. NOT under /proxy.
        return JSONResponse({"status": "ok"})

    @app.api_route(
        "/{full_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
        response_model=None,
    )
    async def _proxy(request: Request, full_path: str):
        # 1. AuthN — constant-time bearer compare against IRIS_INGRESS_API_KEY.
        expected = os.environ.get("IRIS_INGRESS_API_KEY")
        presented = _extract_bearer(request)
        if (
            not expected
            or not presented
            or not hmac.compare_digest(presented, expected)
        ):
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        # 2. AuthZ — only the inference path is forwardable.
        path = request.url.path
        if not _ALLOWED_PATH_RE.match(path):
            return JSONResponse({"error": "forbidden"}, status_code=403)

        # 3. Forward upstream with the controller's own credential (never the
        #    sandbox key), streaming request + response bodies.
        controller_auth = os.environ.get("IRIS_CONTROLLER_AUTH")
        headers = _filtered_upstream_headers(request, controller_auth)
        body = await request.body()

        client: httpx.AsyncClient = request.app.state.upstream_client
        upstream_url = httpx.URL(path=path, query=request.url.query.encode("utf-8"))
        upstream_req = client.build_request(
            request.method, upstream_url, headers=headers, content=body
        )
        upstream_resp = await client.send(upstream_req, stream=True)

        async def _body_iter():
            try:
                async for chunk in upstream_resp.aiter_raw():
                    yield chunk
            finally:
                await upstream_resp.aclose()

        # Drop hop-by-hop from the response too; preserve content-type (SSE).
        resp_headers = {
            k: v
            for k, v in upstream_resp.headers.items()
            if k.lower() not in _HOP_BY_HOP
        }
        return StreamingResponse(
            _body_iter(),
            status_code=upstream_resp.status_code,
            headers=resp_headers,
            media_type=upstream_resp.headers.get("content-type"),
        )

    return app


def main() -> int:
    import uvicorn

    if not os.environ.get("IRIS_INGRESS_API_KEY"):
        raise SystemExit(
            "IRIS_INGRESS_API_KEY must be set (name-only secret; see secrets.env)."
        )
    host = os.environ.get("SIDECAR_HOST", "0.0.0.0")
    port = int(os.environ.get("SIDECAR_PORT", "8443"))
    cert = os.environ.get("SIDECAR_TLS_CERT")
    key = os.environ.get("SIDECAR_TLS_KEY")
    kwargs = {}
    if cert and key:
        kwargs["ssl_certfile"] = cert
        kwargs["ssl_keyfile"] = key
    uvicorn.run(create_app(), host=host, port=port, **kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
