"""Native controller-ingress wiring unit tests — capability-URL api_base + registration.

Proves the controller-ingress wiring lever WITHOUT launching a job: the shared
helpers register under ENDPOINT_ACCESS_LINK, mint a scoped capability token
(worker-side cache), build the ``/proxy/t/<token>/<name>/v1`` api_base, and inject
the inert dummy key. All tokens are in-process fakes; no real secret or live
controller is referenced.

Run:
    .venv/bin/python -m pytest tests/hpc/test_ingress_wiring.py -v
"""

from __future__ import annotations

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

from hpc.harbor_utils import build_endpoint_meta, merge_agent_kwargs  # noqa: E402
from hpc.ingress_utils import (  # noqa: E402
    ADVERTISE_HOST_ENV,
    DEFAULT_VLLM_PORT,
    DUMMY_API_KEY,
    TOKEN_REFRESH_MARGIN_SECONDS,
    CapabilityTokenCache,
    build_capability_api_base,
    build_controller_endpoint_meta,
    capability_api_base,
    controller_endpoint_name,
    controller_registration_plan,
    controller_upstream_address,
    encode_endpoint_name,
    inject_ingress_agent_key,
    register_controller_endpoint,
)
from hpc.literal_proxy_utils import DEFAULT_LITERAL_PROXY_PORT  # noqa: E402


class _FakeMinter:
    """Returns a token per mint and records mint-count for assertions."""

    def __init__(self, expires_at: float = 10_000_000_000.0):
        self.expires_at = expires_at
        self.calls = 0

    def mint(self, endpoint_name, ttl_hours):
        self.calls += 1
        return f"TKN-{self.calls}", self.expires_at


def _fixed_cache(
    token: str = "TKN", expires_at: float = 10_000_000_000.0
) -> CapabilityTokenCache:
    class _Fixed:
        def mint(self, endpoint_name, ttl_hours):
            return token, expires_at

    return CapabilityTokenCache(_Fixed())


def test_controller_endpoint_name_sanitizes():
    # single DOT-FREE segment so encode_endpoint_name is the identity and the
    # registered name == token audience == capability-path name.
    assert controller_endpoint_name("rl-qwen3_8b/run.1") == "otagent-rl-qwen3_8b-run-1"
    assert controller_endpoint_name(None) == "otagent-job"
    assert controller_endpoint_name("") == "otagent-job"
    name = controller_endpoint_name("a/b.c/d")
    assert "/" not in name and "." not in name
    assert encode_endpoint_name(name) == name


def test_encode_endpoint_name_matches_rigging_scheme():
    # Byte-identical to rigging.connect.capability_path/proxy_path encoding:
    # strip leading/trailing '/', then '/' -> '.'.
    assert encode_endpoint_name("/serve/foo") == "serve.foo"
    assert encode_endpoint_name("otagent-job") == "otagent-job"
    assert (
        encode_endpoint_name("/serve/serve-qwen3-0-6b-973241")
        == "serve.serve-qwen3-0-6b-973241"
    )


def test_build_capability_api_base_puts_token_in_path():
    assert (
        build_capability_api_base("ingress.example", "otagent-job1", "JWT.abc.def")
        == "https://ingress.example/proxy/t/JWT.abc.def/otagent-job1/v1"
    )
    # explicit scheme preserved; trailing slash stripped
    assert (
        build_capability_api_base("http://10.0.0.1:8443/", "ep", "TK")
        == "http://10.0.0.1:8443/proxy/t/TK/ep/v1"
    )


def test_capability_api_base_uses_cached_token():
    cache = _fixed_cache(token="ABC")
    url = capability_api_base("ingress.example", "otagent-myjob", cache=cache)
    assert url == "https://ingress.example/proxy/t/ABC/otagent-myjob/v1"


def test_capability_token_cache_reuses_until_margin_then_remints():
    minter = _FakeMinter(expires_at=1000.0)
    cache = CapabilityTokenCache(minter)
    # first call mints
    t1 = cache.token_for("ep", now=0.0)
    assert t1 == "TKN-1" and minter.calls == 1
    # well before the refresh margin -> reuse (no new mint)
    t2 = cache.token_for("ep", now=1000.0 - TOKEN_REFRESH_MARGIN_SECONDS - 1)
    assert t2 == "TKN-1" and minter.calls == 1
    # inside the refresh margin -> re-mint
    t3 = cache.token_for("ep", now=1000.0 - TOKEN_REFRESH_MARGIN_SECONDS + 1)
    assert t3 == "TKN-2" and minter.calls == 2


def test_capability_token_cache_rejects_empty_token():
    class _EmptyMinter:
        def mint(self, endpoint_name, ttl_hours):
            return "", 10_000_000_000.0

    cache = CapabilityTokenCache(_EmptyMinter())
    with pytest.raises(RuntimeError):
        cache.token_for("ep", now=0.0)


def test_inject_ingress_agent_key_sets_dummy():
    env: dict = {}
    assert inject_ingress_agent_key(env) is True
    # Bespoke placeholder always set; legacy vars filled when absent.
    assert env["OPENCODE_DUMMY_KEY"] == DUMMY_API_KEY
    assert env["OPENAI_API_KEY"] == DUMMY_API_KEY
    assert env["LLM_API_KEY"] == DUMMY_API_KEY


def test_inject_ingress_agent_key_preserves_real_openai_key():
    # A real host OPENAI_API_KEY (needed by the LLM-judge verifiers) must NOT be
    # clobbered by the agent placeholder.
    env: dict = {"OPENAI_API_KEY": "sk-real-judge-key"}
    assert inject_ingress_agent_key(env) is True
    assert env["OPENAI_API_KEY"] == "sk-real-judge-key"
    assert env["OPENCODE_DUMMY_KEY"] == DUMMY_API_KEY


def test_build_endpoint_meta_api_key_dormant_by_default():
    # legacy path: no api_key arg -> byte-identical dict (no api_key key)
    meta = build_endpoint_meta("http://host:8000/v1")
    assert "api_key" not in meta
    assert meta["api_base"] == "http://host:8000/v1"
    # controller path: dummy api_key carried through
    meta2 = build_endpoint_meta("http://host:8000/v1", api_key=DUMMY_API_KEY)
    assert meta2["api_key"] == DUMMY_API_KEY


def test_build_controller_endpoint_meta_mints_capability_url():
    cache = _fixed_cache(token="XYZ")
    meta = build_controller_endpoint_meta(
        "ingress.example", "otagent-myjob", cache=cache
    )
    assert meta["api_base"] == "https://ingress.example/proxy/t/XYZ/otagent-myjob/v1"
    assert meta["api_key"] == DUMMY_API_KEY
    # metrics endpoint intentionally absent (capability route fronts only /v1)
    assert "metrics_endpoint" not in meta


def test_merge_agent_kwargs_carries_capability_url_in_controller_mode():
    cfg = {"agents": [{"name": "qwen-code", "kwargs": {"model_name": "m"}}]}

    # legacy/pinggy endpoint_meta (no api_key) -> agent_kwargs has NO api_key
    legacy_meta = build_endpoint_meta("http://host:8000/v1")
    merged_legacy, _ = merge_agent_kwargs(
        cfg, agent_name="qwen-code", endpoint_meta=legacy_meta
    )
    assert "api_key" not in merged_legacy
    assert merged_legacy["api_base"] == "http://host:8000/v1"

    # controller endpoint_meta -> api_base is the capability URL + dummy key
    cache = _fixed_cache(token="XYZ")
    ctrl_meta = build_controller_endpoint_meta(
        "ingress.example", "otagent-myjob", cache=cache
    )
    merged_ctrl, _ = merge_agent_kwargs(
        cfg, agent_name="qwen-code", endpoint_meta=ctrl_meta
    )
    assert (
        merged_ctrl["api_base"]
        == "https://ingress.example/proxy/t/XYZ/otagent-myjob/v1"
    )
    assert merged_ctrl["api_key"] == DUMMY_API_KEY


def test_eval_listener_to_env_controller_additive():
    """SbatchParams.to_env(): pinggy default byte-identical; controller adds EVAL_INGRESS_*."""
    from eval.unified_eval_listener import SbatchParams

    default_env = SbatchParams(
        pinggy_url="x.a.pinggy.link", pinggy_token="tok"
    ).to_env()
    assert not any(k.startswith("EVAL_INGRESS_") for k in default_env)
    assert default_env["EVAL_PINGGY_URL"] == "x.a.pinggy.link"

    ctrl_env = SbatchParams(
        ingress_mode="controller", ingress_host="ingress.example"
    ).to_env()
    assert ctrl_env["EVAL_INGRESS_MODE"] == "controller"
    assert ctrl_env["EVAL_INGRESS_HOST"] == "ingress.example"


# --------------------------------------------------------------------------- #
# Endpoint registration helpers (shared by the controller + literal-combo path)
# --------------------------------------------------------------------------- #
class _FakeRegistrar:
    """Records register(name, address, metadata, access) calls; returns a fixed id."""

    def __init__(self):
        self.calls = []
        self.closed = False

    def register(self, name, address, metadata=None, access=None):
        self.calls.append(
            {"name": name, "address": address, "metadata": metadata, "access": access}
        )
        return "endpoint-id-xyz"

    def close(self):
        self.closed = True


def test_controller_upstream_address_uses_advertise_host():
    env = {ADVERTISE_HOST_ENV: "10.16.4.7"}
    assert controller_upstream_address(8010, env=env) == "http://10.16.4.7:8010"
    assert controller_upstream_address(8000, env={}) == "http://127.0.0.1:8000"


def test_register_controller_endpoint_uses_injected_registrar():
    reg = _FakeRegistrar()
    registration = register_controller_endpoint(
        "otagent-myjob", "http://10.0.0.1:8010", registrar=reg, metadata={"k": "v"}
    )
    assert registration.endpoint_id == "endpoint-id-xyz"
    assert reg.calls[0]["name"] == "otagent-myjob"
    assert reg.calls[0]["address"] == "http://10.0.0.1:8010"
    assert reg.calls[0]["metadata"] == {"k": "v"}
    assert reg.closed is False
    registration.close()
    assert reg.closed is True


def test_register_controller_endpoint_fails_loud_without_registrar(monkeypatch):
    def _boom():
        raise RuntimeError("no in-cluster iris task")

    monkeypatch.setattr("hpc.ingress_utils._default_endpoint_registrar", _boom)
    with pytest.raises(RuntimeError):
        register_controller_endpoint("otagent-j", "http://h:8000")


def test_register_controller_endpoint_fails_loud_on_empty_id():
    class _EmptyRegistrar:
        def register(self, name, address, metadata=None, access=None):
            return ""

    with pytest.raises(RuntimeError):
        register_controller_endpoint(
            "otagent-j", "http://h:8000", registrar=_EmptyRegistrar()
        )


def test_controller_registration_plan_plain_registers_vllm_port():
    """Plain controller: register raw vLLM:8000; api_base built later from the name."""
    name, address = controller_registration_plan(
        "myjob",
        record_literal=False,
        proxy_port=DEFAULT_LITERAL_PROXY_PORT,
        env={ADVERTISE_HOST_ENV: "10.0.0.5"},
    )
    assert name == "otagent-myjob"
    assert address == f"http://10.0.0.5:{DEFAULT_VLLM_PORT}"
    assert address.endswith(":8000")


def test_controller_registration_plan_literal_registers_proxy_port():
    """COMBINED path: the REGISTERED address is the RecordProxy's port, NOT vLLM's.

    The endpoint name is IDENTICAL to the plain path, so the capability URL the
    agent targets is unchanged (only the registered upstream address differs).
    """
    name, address = controller_registration_plan(
        "myjob",
        record_literal=True,
        proxy_port=DEFAULT_LITERAL_PROXY_PORT,
        env={ADVERTISE_HOST_ENV: "10.0.0.5"},
    )
    assert name == "otagent-myjob"
    assert address == f"http://10.0.0.5:{DEFAULT_LITERAL_PROXY_PORT}"
    assert address.endswith(":8010")
    assert ":8000" not in address


def test_combined_path_registers_link_and_builds_capability_url():
    """End-to-end (in-process) proof of the record_literal x controller wiring.

    Mirrors what the launcher does with BOTH flags set: compute the plan,
    register via the (fake) registrar, mint via the (fake) cache, build agent
    kwargs. Asserts: registered address is the PROXY's (not vLLM's), api_base is
    the capability URL, api_key is the inert dummy.
    """
    reg = _FakeRegistrar()
    name, address = controller_registration_plan(
        "myjob",
        record_literal=True,
        proxy_port=DEFAULT_LITERAL_PROXY_PORT,
        env={ADVERTISE_HOST_ENV: "10.0.0.5"},
    )
    register_controller_endpoint(name, address, registrar=reg)

    assert reg.calls[0]["address"].endswith(f":{DEFAULT_LITERAL_PROXY_PORT}")
    assert not reg.calls[0]["address"].endswith(":8000")

    cache = _fixed_cache(token="XYZ")
    meta = build_controller_endpoint_meta("ingress.example", name, cache=cache)
    merged, _ = merge_agent_kwargs(
        {"agents": [{"name": "qwen-code", "kwargs": {"model_name": "m"}}]},
        agent_name="qwen-code",
        endpoint_meta=meta,
    )
    assert merged["api_base"] == "https://ingress.example/proxy/t/XYZ/otagent-myjob/v1"
    assert merged["api_key"] == DUMMY_API_KEY


def test_record_proxy_accepts_unauthenticated_calls():
    """The registered upstream (RecordProxy) must accept NO-bearer in-cluster calls.

    EndpointProxy strips Authorization before forwarding upstream, so the
    RecordProxy — like raw vLLM today — must serve requests with no bearer.
    """
    from harbor.literal.proxy import RecordProxy

    stub = FastAPI()

    @stub.post("/v1/chat/completions")
    async def _chat(request: Request):  # noqa: ANN001
        return JSONResponse({"id": "r1", "model": "m", "choices": [{}]})

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        proxy = RecordProxy(
            "http://vllm.local", Path(td) / "literal.jsonl", timeout=10.0
        )
        stub_client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=stub), base_url="http://vllm.local"
        )

        async def _fake_get_client():
            return stub_client

        proxy._get_client = _fake_get_client  # type: ignore[assignment]
        with TestClient(proxy.app()) as client:
            r = client.post("/v1/chat/completions", json={"model": "m", "messages": []})
        assert r.status_code == 200
        assert "authorization" not in {k.lower() for k in r.request.headers}


# --------------------------------------------------------------------------- #
# opencode model routing (openai provider + OPENAI_BASE_URL)
# --------------------------------------------------------------------------- #
def test_opencode_model_routing_uses_vllm_provider_and_api_base():
    from hpc.local_runner_utils import opencode_model_routing

    meta = {"api_base": "https://ingress.example/proxy/t/TK/otagent-myjob/v1"}
    route = opencode_model_routing(
        agent_name="opencode", served_model_id="1783107198924068", serving_meta=meta
    )
    assert route == (
        "vllm/1783107198924068",
        "https://ingress.example/proxy/t/TK/otagent-myjob/v1",
    )


def test_opencode_model_routing_inert_for_other_agents():
    from hpc.local_runner_utils import opencode_model_routing

    meta = {"api_base": "http://host:8000/v1"}
    assert opencode_model_routing("terminus-2", "abc123", meta) is None
    assert opencode_model_routing("opencode", None, meta) is None


def test_opencode_model_routing_requires_api_base():
    from hpc.local_runner_utils import opencode_model_routing

    with pytest.raises(ValueError):
        opencode_model_routing("opencode", "abc123", None)
    with pytest.raises(ValueError):
        opencode_model_routing("opencode", "abc123", {"api_base": ""})


def test_notimplementederror_guard_removed_from_launchers():
    """The record_literal x controller NotImplementedError guard is gone from both launchers."""
    guard = "record_literal + ingress_mode=controller is not supported"
    for fname in ("rl_launch_utils.py", "datagen_launch_utils.py"):
        src = (_REPO_ROOT / "hpc" / fname).read_text()
        assert guard not in src, f"stale NotImplementedError guard still in hpc/{fname}"


# --------------------------------------------------------------------------- #
# Federated parent-minting (Exp2 cross-cluster ingress fix #1)
# --------------------------------------------------------------------------- #

from hpc.ingress_utils import (  # noqa: E402
    DEFAULT_PARENT_INGRESS_HOST,
    FederatedCapabilityTokenCache,
    federated_capability_api_base,
    wait_for_endpoint_mirror,
)


class _FakeResolver:
    """Reports the endpoint mirrored after ``ready_after`` polls."""

    def __init__(self, ready_after: int = 0, raise_first: int = 0):
        self.ready_after = ready_after
        self.raise_first = raise_first
        self.calls = 0

    def is_mirrored(self, endpoint_name):
        self.calls += 1
        if self.calls <= self.raise_first:
            raise RuntimeError("transient resolve error")
        return self.calls > self.ready_after


def test_wait_for_endpoint_mirror_returns_when_ready():
    resolver = _FakeResolver(ready_after=2)
    slept = []
    # fake clock never advances past the deadline until resolver is ready
    wait_for_endpoint_mirror(
        "otagent-x",
        resolver,
        timeout_s=100,
        interval_s=1,
        sleep=slept.append,
        now=lambda: 0.0,
    )
    assert resolver.calls == 3  # two "not yet" + one ready
    assert slept == [1, 1]  # slept between the three polls


def test_wait_for_endpoint_mirror_tolerates_transient_errors():
    resolver = _FakeResolver(ready_after=0, raise_first=2)
    wait_for_endpoint_mirror(
        "otagent-x",
        resolver,
        timeout_s=100,
        interval_s=1,
        sleep=lambda _s: None,
        now=lambda: 0.0,
    )
    assert resolver.calls == 3  # 2 raised + 1 True


def test_wait_for_endpoint_mirror_times_out():
    resolver = _FakeResolver(ready_after=999)  # never ready
    clock = {"t": 0.0}

    def now():
        return clock["t"]

    def sleep(s):
        clock["t"] += s

    with pytest.raises(TimeoutError, match="was not mirrored"):
        wait_for_endpoint_mirror(
            "otagent-x",
            resolver,
            timeout_s=5,
            interval_s=2,
            sleep=sleep,
            now=now,
        )


def test_federated_cache_waits_for_mirror_then_mints_at_parent():
    minter = _FakeMinter(expires_at=10_000_000_000.0)
    resolver = _FakeResolver(ready_after=1)
    cache = FederatedCapabilityTokenCache(
        minter,
        resolver,
        mirror_interval_s=0,
        mirror_timeout_s=100,
    )
    # first token: waits for mirror (2 polls) then mints once
    t1 = cache.token_for("otagent-fed", now=0.0)
    assert t1 == "TKN-1" and minter.calls == 1 and resolver.calls == 2
    # cached reuse — mirror wait is NOT repeated
    t2 = cache.token_for("otagent-fed", now=1.0)
    assert t2 == "TKN-1" and minter.calls == 1 and resolver.calls == 2


def test_federated_cache_remint_does_not_repoll_mirror():
    minter = _FakeMinter(expires_at=1000.0)
    resolver = _FakeResolver(ready_after=0)
    cache = FederatedCapabilityTokenCache(
        minter,
        resolver,
        mirror_interval_s=0,
        mirror_timeout_s=100,
    )
    cache.token_for("ep", now=0.0)
    assert minter.calls == 1 and resolver.calls == 1
    # inside refresh margin -> re-mint, but mirror already confirmed (no re-poll)
    cache.token_for("ep", now=1000.0 - TOKEN_REFRESH_MARGIN_SECONDS + 1)
    assert minter.calls == 2 and resolver.calls == 1


def test_federated_cache_propagates_mirror_timeout():
    minter = _FakeMinter()
    resolver = _FakeResolver(ready_after=999)
    cache = FederatedCapabilityTokenCache(
        minter,
        resolver,
        mirror_interval_s=0,
        mirror_timeout_s=0,
    )
    with pytest.raises(TimeoutError):
        cache.token_for("ep", now=0.0)
    assert minter.calls == 0  # never minted an unreachable token


def test_federated_capability_api_base_builds_parent_url():
    minter = _FakeMinter()
    resolver = _FakeResolver(ready_after=0)
    cache = FederatedCapabilityTokenCache(minter, resolver, mirror_interval_s=0)
    url = federated_capability_api_base(
        "otagent-fedjob",
        ingress_host="iris.oa.dev",
        cache=cache,
        now=0.0,
    )
    assert url == "https://iris.oa.dev/proxy/t/TKN-1/otagent-fedjob/v1"


def test_default_parent_ingress_host_is_marin():
    assert DEFAULT_PARENT_INGRESS_HOST == "iris.oa.dev"
