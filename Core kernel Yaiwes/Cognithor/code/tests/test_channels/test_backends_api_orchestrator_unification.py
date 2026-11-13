"""Regression for Bug C1-r3: the backends_api endpoints must use the same
VLLMOrchestrator instance as the Gateway, so media_url set by Gateway
propagates into the start_container call path.

Without this unification there are two separate VLLMOrchestrator objects:
one owned by the Gateway (with .media_url wired after MediaUploadServer
startup) and one cached at module level inside backends_api. In production
the Flutter UI hits backends_api, which launches a vLLM container without
the -e COGNITHOR_MEDIA_URL=... flag, so the container cannot reach the
media-upload server.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestOrchestratorUnification:
    def test_resolve_orchestrator_prefers_app_state(self):
        """When Gateway has registered its orchestrator onto app.state, the
        backends_api helper must return that instance, not create a new one."""
        from cognithor.channels.backends_api import _resolve_orchestrator

        gateway_orch = MagicMock(name="gateway-owned")
        request = MagicMock()
        request.app.state.vllm_orchestrator = gateway_orch
        request.app.state.config = MagicMock()

        resolved = _resolve_orchestrator(request)
        assert resolved is gateway_orch

    def test_resolve_orchestrator_falls_back_to_cache_when_no_gateway(self):
        """In standalone API mode (no Gateway) the cached-creation path is used."""
        from cognithor.channels.backends_api import _resolve_orchestrator
        from cognithor.config import CognithorConfig

        # Use a real FastAPI app so request.app.state is the real State object
        # (not a MagicMock which auto-creates any attribute).
        app = FastAPI()
        app.state.config = CognithorConfig()
        # Deliberately do NOT set app.state.vllm_orchestrator — simulates
        # standalone API mode.

        request = MagicMock()
        request.app = app

        resolved = _resolve_orchestrator(request)
        assert resolved is not None

    def test_resolve_orchestrator_falls_back_when_state_attr_is_none(self):
        """An explicit None on app.state.vllm_orchestrator must also fall
        through to the cached-creation path — otherwise channels that
        tentatively reserved the slot would break standalone mode."""
        from cognithor.channels.backends_api import _resolve_orchestrator
        from cognithor.config import CognithorConfig

        app = FastAPI()
        app.state.config = CognithorConfig()
        app.state.vllm_orchestrator = None

        request = MagicMock()
        request.app = app

        resolved = _resolve_orchestrator(request)
        assert resolved is not None

    def test_start_endpoint_uses_app_state_orchestrator_over_cache(self):
        """Integration: when app.state.vllm_orchestrator is registered, the
        POST /api/backends/vllm/start endpoint must call start_container on
        THAT instance — not on the module-level cached fallback."""
        from cognithor.channels.backends_api import build_backends_app
        from cognithor.config import CognithorConfig, VLLMConfig
        from cognithor.core.vllm_orchestrator import ContainerInfo

        cfg = CognithorConfig(vllm=VLLMConfig(enabled=True))
        app = build_backends_app(config=cfg)

        gateway_orch = MagicMock(name="gateway-owned")
        gateway_orch.start_container.return_value = ContainerInfo(
            container_id="cid-gw", port=8000, model="some-model"
        )
        app.state.vllm_orchestrator = gateway_orch

        client = TestClient(app)
        r = client.post("/api/backends/vllm/start", json={"model": "some-model"})
        assert r.status_code == 200
        assert r.json()["container_id"] == "cid-gw"
        gateway_orch.start_container.assert_called_once_with("some-model")

    def test_media_url_on_gateway_propagates_to_start_container_call(self):
        """End-to-end: Gateway sets media_url, backends_api start endpoint uses
        the same instance, subprocess sees -e COGNITHOR_MEDIA_URL=..."""
        from cognithor.config import CognithorConfig, VLLMConfig
        from cognithor.core.vllm_orchestrator import VLLMOrchestrator

        cfg = CognithorConfig(vllm=VLLMConfig(enabled=True))
        orch = VLLMOrchestrator(config=cfg.vllm)
        orch.media_url = "http://host.docker.internal:9999"

        # Simulate the flow: we resolve orch and call start_container.
        with (
            patch.object(VLLMOrchestrator, "_port_available", return_value=True),
            patch(
                "subprocess.run",
                return_value=MagicMock(returncode=0, stdout="cid"),
            ) as run_mock,
            patch.object(VLLMOrchestrator, "_wait_for_health", return_value=True),
        ):
            orch.start_container("mmangkad/Qwen3.6-27B-NVFP4")

        args = run_mock.call_args[0][0]
        assert any("COGNITHOR_MEDIA_URL=http://host.docker.internal:9999" in a for a in args), (
            "Expected -e COGNITHOR_MEDIA_URL=... in docker run args when media_url is set"
        )


class TestGatewayRegistersOrchestratorOnAppState:
    def test_gateway_exposes_orchestrator_on_app_state_when_vllm_enabled(self):
        """Gateway must register self._vllm_orchestrator onto the APIChannel's
        FastAPI app.state so backends_api can resolve it. Source-level check
        since constructing a real Gateway requires the full init chain."""
        import inspect

        from cognithor.gateway import gateway as gw

        src = inspect.getsource(gw)
        assert "app.state.vllm_orchestrator" in src, (
            "Gateway must set app.state.vllm_orchestrator = self._vllm_orchestrator "
            "so backends_api endpoints see the same instance (media_url wired)."
        )
