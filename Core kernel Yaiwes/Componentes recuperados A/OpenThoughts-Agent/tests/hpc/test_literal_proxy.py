"""Unit tests for the co-located RecordProxy literal-capture wiring.

Covers ``hpc/literal_proxy_utils.py`` (the OT-Agent side of harbor's literal-token
trace machinery):

  * pure helpers (log path, proxy endpoint, default port) — deterministic, no I/O.
  * FLAG-OFF PARITY: ``maybe_serve_literal_proxy(False, ...)`` is a null context
    manager — it yields the upstream endpoint UNCHANGED and NEVER touches
    ``serve_record_proxy`` (no socket, no thread). This is the G0 byte-identical
    proof for the launch-path functions.
  * FLAG-ON gating: ``maybe_serve_literal_proxy(True, ...)`` routes through
    ``serve_record_proxy`` and yields its endpoint (stubbed — no real socket).
  * FLAG-ON surface: harbor's ``RecordProxy.app()`` (what we co-locate) injects the
    literal params and records ``literal.jsonl`` — exercised in-process against a
    STUB vLLM via ``httpx.ASGITransport`` (no GPU, no socket), mirroring the
    sidecar tests' stubbing style.

Run:
    .venv/bin/python -m pytest tests/hpc/test_literal_proxy.py -v
"""

from __future__ import annotations

import contextlib
import fnmatch
import json
import sys
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hpc import literal_proxy_utils as lp  # noqa: E402


# --------------------------------------------------------------------------- #
# 1. Pure helpers
# --------------------------------------------------------------------------- #
def test_literal_proxy_endpoint_default():
    assert lp.literal_proxy_endpoint() == "http://127.0.0.1:8010/v1"
    assert lp.literal_proxy_endpoint("0.0.0.0", 9001) == "http://0.0.0.0:9001/v1"


def test_default_port_avoids_vllm():
    # vLLM / datagen bind 8000; the co-located proxy must not collide.
    assert lp.DEFAULT_LITERAL_PROXY_PORT != 8000


def test_upstream_origin_strips_v1_base():
    # Harbor's RecordProxy re-appends the full request path (/v1/chat/completions),
    # so the base it receives must be origin-only; a .../v1 base would double the
    # segment (/v1/v1/...) and vLLM 404s. upstream_origin strips path/query.
    assert lp.upstream_origin("http://127.0.0.1:8000/v1") == "http://127.0.0.1:8000"
    assert lp.upstream_origin("http://127.0.0.1:8000/v1/") == "http://127.0.0.1:8000"
    assert lp.upstream_origin("http://10.0.0.5:8000") == "http://10.0.0.5:8000"
    # non-absolute URLs must fail loud, not silently forward a bad base.
    with pytest.raises(ValueError):
        lp.upstream_origin("127.0.0.1:8000/v1")


def test_literal_log_path_sanitizes_and_places_under_logs(tmp_path):
    p = lp.literal_log_path(tmp_path, "rl-qwen3_8b/run.1", "20260707-011300")
    assert p.parent == tmp_path / "logs"
    # <slug>__<token>_literal.jsonl — the per-serve token separates attempts and the
    # trailing _literal.jsonl keeps the correlator's discovery glob matching.
    assert p.name == "rl-qwen3_8b-run.1__20260707-011300_literal.jsonl"
    assert fnmatch.fnmatch(p.name, "*_literal.jsonl")
    # empty/None job name -> a stable 'job' slug
    assert lp.literal_log_path(tmp_path, "", "tok").name == "job__tok_literal.jsonl"


# --------------------------------------------------------------------------- #
# 1b. Durability: remote (gs://) experiments_dir -> local staging + upload URI
# --------------------------------------------------------------------------- #
def test_literal_log_remote_uri_for_gcs_experiments_dir():
    # A gs:// experiments_dir yields a DURABLE gs:// upload URI under logs/, NOT a
    # collapsed local ``Path('gs://…')`` (the bug that lost every literal log on iris).
    uri = lp.literal_log_remote_uri(
        "gs://marin-models-us/ot-agent/tgen-x", "rl-q8b/run.1", "tok0"
    )
    assert (
        uri
        == "gs://marin-models-us/ot-agent/tgen-x/logs/rl-q8b-run.1__tok0_literal.jsonl"
    )
    # crucially the scheme survives (no gs:/ collapse)
    assert uri.startswith("gs://")


def test_literal_log_remote_uri_none_for_local_experiments_dir(tmp_path):
    # A plain local experiments_dir needs no upload — the proxy writes it directly.
    assert lp.literal_log_remote_uri(tmp_path, "myjob", "tok") is None
    assert lp.literal_log_remote_uri("/tmp/experiments", "myjob", "tok") is None


def test_literal_log_remote_uri_reexpands_path_collapsed_scheme():
    # pathlib.Path collapses "gs://x" -> "gs:/x"; the remote URI must still be
    # detected (regression: a Path-wrapped gs:// dir silently returned None ->
    # the literal log was never uploaded).
    from pathlib import Path

    collapsed = Path(
        "gs://marin-models-us/ot-agent/tgen-x"
    )  # str() == "gs:/marin-models-us/..."
    assert "gs:/" in str(collapsed) and "gs://" not in str(collapsed)
    uri = lp.literal_log_remote_uri(collapsed, "myjob", "tok")
    assert uri == "gs://marin-models-us/ot-agent/tgen-x/logs/myjob__tok_literal.jsonl"
    # bare collapsed string form too
    assert (
        lp.literal_log_remote_uri("gs:/marin-models-us/ot-agent/tgen-x", "myjob", "tok")
        == uri
    )


def test_literal_log_remote_uri_resolved_local_path_stays_local():
    # A fully resolve()'d form ("/app/gs:/…") is genuinely local (scheme lost to
    # the leading "/") and must NOT be treated as remote — callers pass the raw
    # gs:// arg for that case (local_runner_utils fix), not this resolved Path.
    assert (
        lp.literal_log_remote_uri(
            "/app/gs:/marin-models-us/ot-agent/tgen-x", "j", "tok"
        )
        is None
    )


# --------------------------------------------------------------------------- #
# 1c. Per-serve token: distinct, non-clobbering paths across attempts
# --------------------------------------------------------------------------- #
def test_serve_token_folds_in_iris_retry_suffix(monkeypatch):
    # IRIS_TASK_ID gains a ":N" retry suffix on a preempt-retried task; the token
    # folds it in so attempt-0 and its retry derive DISTINCT literal filenames.
    monkeypatch.setenv("IRIS_TASK_ID", "/benjaminfeuer/tracegen/0:2")
    assert lp.serve_token().endswith("-0-2")  # rank 0, retry attempt 2
    monkeypatch.delenv("IRIS_TASK_ID", raising=False)
    assert not lp.serve_token().endswith(
        "-0-2"
    )  # no iris id -> plain serve-start stamp


def test_two_serve_tokens_yield_distinct_glob_matching_paths():
    # The core anti-clobber property: two serve attempts (attempt-0 + a preempt-resume)
    # against the SAME stable job_name derive DISTINCT remote + staging paths, and both
    # still match the correlator's ``*_literal.jsonl`` discovery glob (so the union of
    # attempts is discovered, never one clobbering the other).
    exp = "gs://marin-models-us/ot-agent/tgen-x"
    t0, t1 = "20260707-011300", "20260707-041900-0-2"  # attempt-0, preempt-retry
    r0 = lp.literal_log_remote_uri(exp, "job", t0)
    r1 = lp.literal_log_remote_uri(exp, "job", t1)
    assert r0 != r1 and r0.startswith("gs://") and r1.startswith("gs://")
    assert fnmatch.fnmatch(r0.rsplit("/", 1)[-1], "*_literal.jsonl")
    assert fnmatch.fnmatch(r1.rsplit("/", 1)[-1], "*_literal.jsonl")
    # local staging mirrors the same distinct token (staging + upload stay in sync)
    s0, s1 = lp._local_staging_path("job", t0), lp._local_staging_path("job", t1)
    assert s0 != s1
    assert fnmatch.fnmatch(s0.name, "*_literal.jsonl") and fnmatch.fnmatch(
        s1.name, "*_literal.jsonl"
    )


def test_maybe_serve_remote_stages_locally_and_passes_upload_uri(monkeypatch):
    # On a gs:// experiments_dir the proxy must APPEND to a real local path (object
    # stores have no append) and hand serve_record_proxy the durable upload URI.
    calls: dict = {}

    @contextlib.contextmanager
    def _fake_serve(
        up,
        log_path,
        *,
        host=lp.DEFAULT_LITERAL_PROXY_HOST,
        port=lp.DEFAULT_LITERAL_PROXY_PORT,
        remote_uri=None,
        **kw,
    ):
        calls["log_path"] = Path(log_path)
        calls["remote_uri"] = remote_uri
        yield lp.literal_proxy_endpoint(host, port)

    monkeypatch.setattr(lp, "serve_record_proxy", _fake_serve)
    monkeypatch.setattr(lp, "serve_token", lambda: "tokA")

    with lp.maybe_serve_literal_proxy(
        True,
        "http://10.0.0.1:8000/v1",
        experiments_dir="gs://marin-models-us/ot-agent/tgen-x",
        job_name="myjob",
    ):
        pass

    # local staging path: absolute + local (NOT a gs:/ collapse), carrying the token
    assert calls["log_path"].is_absolute()
    assert "gs:" not in str(calls["log_path"])
    assert calls["log_path"].name == "myjob__tokA_literal.jsonl"
    # durable upload target: the gs:// URI under logs/ with the SAME per-serve token
    assert (
        calls["remote_uri"]
        == "gs://marin-models-us/ot-agent/tgen-x/logs/myjob__tokA_literal.jsonl"
    )


def test_maybe_serve_two_attempts_do_not_clobber(monkeypatch):
    # End-to-end anti-clobber: two serve attempts against the SAME job_name + remote
    # dir must hand serve_record_proxy DISTINCT staging + remote paths (attempt-0's
    # populated log is never overwritten by a resume). Two serve tokens simulate the
    # attempt-0 / preempt-resume pair.
    exp = "gs://marin-models-us/ot-agent/tgen-x"
    seen: list = []

    @contextlib.contextmanager
    def _fake_serve(
        up,
        log_path,
        *,
        host=lp.DEFAULT_LITERAL_PROXY_HOST,
        port=lp.DEFAULT_LITERAL_PROXY_PORT,
        remote_uri=None,
        **kw,
    ):
        seen.append((Path(log_path), remote_uri))
        yield lp.literal_proxy_endpoint(host, port)

    monkeypatch.setattr(lp, "serve_record_proxy", _fake_serve)
    tokens = iter(["attempt0", "resume1"])
    monkeypatch.setattr(lp, "serve_token", lambda: next(tokens))

    for _ in range(2):
        with lp.maybe_serve_literal_proxy(
            True, "http://10.0.0.1:8000/v1", experiments_dir=exp, job_name="job"
        ):
            pass

    (log0, remote0), (log1, remote1) = seen
    assert log0 != log1 and remote0 != remote1  # no clobber: distinct per attempt
    assert remote0.endswith("_literal.jsonl") and remote1.endswith("_literal.jsonl")


def test_upload_literal_log_copies_whole_file(tmp_path):
    # _upload_literal_log rewrites the entire object (object stores have no append)
    # and reports True on a real upload so the finalize path can log truthfully.
    local = tmp_path / "stage" / "literal.jsonl"
    local.parent.mkdir(parents=True)
    local.write_text('{"literal": {"completion_token_ids": [1, 2]}}\n')
    remote = tmp_path / "durable" / "myjob_literal.jsonl"  # parent does not exist yet

    assert lp._upload_literal_log(local, str(remote)) is True
    assert remote.read_text() == '{"literal": {"completion_token_ids": [1, 2]}}\n'


def test_upload_literal_log_noop_when_local_missing(tmp_path):
    # Proxy saw no traffic yet -> nothing to upload, must not raise, and must report
    # False so the finalize path does NOT falsely claim "uploaded final literal log".
    remote = tmp_path / "durable" / "x.jsonl"
    assert lp._upload_literal_log(tmp_path / "nope.jsonl", str(remote)) is False
    assert not remote.exists()


def test_upload_literal_log_false_and_no_write_when_local_empty(tmp_path):
    # A resume serve that captured 0 records leaves an EMPTY local file; uploading it
    # would (a) let the finalize path lie "uploaded" and (b) write a 0-byte object
    # that a prior good attempt's discovery might surface. Both are prevented: return
    # False and write nothing.
    local = tmp_path / "stage" / "literal.jsonl"
    local.parent.mkdir(parents=True)
    local.write_bytes(b"")
    remote = tmp_path / "durable" / "empty_literal.jsonl"

    assert lp._upload_literal_log(local, str(remote)) is False
    assert not remote.exists()


# --------------------------------------------------------------------------- #
# 2. FLAG-OFF PARITY — null context manager, byte-identical endpoint
# --------------------------------------------------------------------------- #
def test_maybe_serve_disabled_yields_upstream_unchanged(monkeypatch, tmp_path):
    upstream = "http://10.0.0.1:8000/v1"

    # If the disabled path ever tries to serve, fail loudly.
    def _boom(*a, **k):
        raise AssertionError("serve_record_proxy must NOT be called when disabled")

    monkeypatch.setattr(lp, "serve_record_proxy", _boom)

    with lp.maybe_serve_literal_proxy(
        False, upstream, experiments_dir=tmp_path, job_name="job"
    ) as effective:
        # identity: the exact same object flows through unchanged
        assert effective is upstream


# --------------------------------------------------------------------------- #
# 3. FLAG-ON gating — routes through serve_record_proxy (stubbed, no socket)
# --------------------------------------------------------------------------- #
def test_maybe_serve_enabled_routes_through_serve(monkeypatch, tmp_path):
    upstream = "http://10.0.0.1:8000/v1"
    calls: dict = {}

    @contextlib.contextmanager
    def _fake_serve(
        up,
        log_path,
        *,
        host=lp.DEFAULT_LITERAL_PROXY_HOST,
        port=lp.DEFAULT_LITERAL_PROXY_PORT,
        **kw,
    ):
        calls["upstream"] = up
        calls["log_path"] = Path(log_path)
        yield lp.literal_proxy_endpoint(host, port)

    monkeypatch.setattr(lp, "serve_record_proxy", _fake_serve)
    monkeypatch.setattr(lp, "serve_token", lambda: "tokB")

    with lp.maybe_serve_literal_proxy(
        True, upstream, experiments_dir=tmp_path, job_name="myjob"
    ) as effective:
        assert effective == lp.literal_proxy_endpoint()
    # upstream forwarded verbatim; log path derived under <exp>/logs/ with the token
    assert calls["upstream"] == upstream
    assert calls["log_path"] == tmp_path / "logs" / "myjob__tokB_literal.jsonl"


# --------------------------------------------------------------------------- #
# 4. FLAG-ON surface — harbor's RecordProxy.app() injects + records, in-process
# --------------------------------------------------------------------------- #
def _make_stub_vllm() -> FastAPI:
    """A stub OpenAI-compatible server that echoes literal token fields."""
    stub = FastAPI()

    @stub.post("/v1/chat/completions")
    async def _chat(request: Request):
        body = await request.json()
        # Record what the proxy forwarded so the test can assert injection.
        return JSONResponse(
            {
                "id": "resp-1",
                "model": body.get("model", "m"),
                "prompt_token_ids": [10, 11, 12],
                "choices": [
                    {
                        "provider_specific_fields": {"token_ids": [13, 14]},
                        "logprobs": {"content": [{"logprob": -0.1}, {"logprob": -0.2}]},
                        "_echoed_request": body,
                    }
                ],
            }
        )

    return stub


def test_record_proxy_app_injects_and_records(tmp_path, monkeypatch):
    from harbor.literal.proxy import RecordProxy

    log_path = tmp_path / "literal.jsonl"
    proxy = RecordProxy("http://vllm.local", log_path, timeout=10.0)

    # Stub the upstream client with an ASGITransport to the fake vLLM (no socket).
    stub_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_make_stub_vllm()),
        base_url="http://vllm.local",
    )

    async def _fake_get_client():
        return stub_client

    monkeypatch.setattr(proxy, "_get_client", _fake_get_client)

    app = proxy.app()
    with TestClient(app) as client:
        r = client.post(
            "/v1/chat/completions",
            json={"model": "glm-4.6", "messages": []},
        )

    assert r.status_code == 200
    payload = r.json()
    assert payload["id"] == "resp-1"

    # The proxy injected literal params into the forwarded request body.
    echoed = payload["choices"][0]["_echoed_request"]
    assert echoed["return_token_ids"] is True
    assert echoed["logprobs"] is True

    # literal.jsonl recorded the extracted token ids + logprobs.
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["literal"]["prompt_token_ids"] == [10, 11, 12]
    assert entry["literal"]["completion_token_ids"] == [13, 14]
    assert entry["literal"]["logprobs"] == [-0.1, -0.2]


def test_record_proxy_from_v1_base_does_not_double_v1(tmp_path, monkeypatch):
    """Regression: the launcher's .../v1 base must NOT forward to /v1/v1/... (404).

    Production hands ``serve_record_proxy`` the agent-facing vLLM ``.../v1`` base;
    harbor's RecordProxy re-appends the full request path, so we strip to origin
    first (``upstream_origin``). Without that strip the forwarded URL is
    ``/v1/v1/chat/completions`` and the stub (like real vLLM) 404s — the exact
    live-ingress failure this fixes.
    """
    from harbor.literal.proxy import RecordProxy

    # Build RecordProxy the way serve_record_proxy does: strip the /v1 base to origin.
    proxy = RecordProxy(
        lp.upstream_origin("http://vllm.local/v1"), tmp_path / "l.jsonl", timeout=10.0
    )
    stub_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_make_stub_vllm()),
        base_url="http://vllm.local",
    )

    async def _fake_get_client():
        return stub_client

    monkeypatch.setattr(proxy, "_get_client", _fake_get_client)

    with TestClient(proxy.app()) as client:
        r = client.post("/v1/chat/completions", json={"model": "m", "messages": []})

    # 200 proves the forwarded path is /v1/chat/completions (single /v1). If the
    # base had kept its /v1, this would forward to /v1/v1/... and 404.
    assert r.status_code == 200
    assert r.json()["id"] == "resp-1"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
