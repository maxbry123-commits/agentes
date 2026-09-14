"""Regression for Bug-3 (round 4): call sites that construct VLLMOrchestrator
must thread the live config.vllm through, not fall back to VLLMConfig() defaults."""

from __future__ import annotations

from cognithor.config import CognithorConfig, VLLMConfig


class TestConfigPropagation:
    def test_gateway_threads_live_vllm_config(self) -> None:
        """Gateway.__init__ must pass config=self._config.vllm to orchestrator.

        Verified via source inspection: constructing a full Gateway in a unit
        test is heavyweight, but the bug is about a literal missing kwarg at a
        specific call site — source-level assertion is both faster and more
        direct.
        """
        import inspect

        from cognithor.gateway import gateway as gw

        src = inspect.getsource(gw)
        idx = src.find("self._vllm_orchestrator = VLLMOrchestrator(")
        assert idx != -1, "Could not locate VLLMOrchestrator construction in gateway.py"
        snippet = src[idx : idx + 400]
        assert "config=self._config.vllm" in snippet, (
            f"Gateway must pass config=self._config.vllm to orchestrator. Got:\n{snippet}"
        )

    def test_backends_api_get_orchestrator_threads_config(self) -> None:
        """backends_api._get_orchestrator must pass config=config.vllm too."""
        from cognithor.channels import backends_api

        # Ensure clean cache
        backends_api._orchestrator_cache.clear()
        cfg = CognithorConfig(
            vllm=VLLMConfig(
                enabled=True,
                max_model_len=32768,
                cpu_offload_gb=8,
            )
        )
        orch = backends_api._get_orchestrator(cfg)
        assert orch._config.max_model_len == 32768
        assert orch._config.cpu_offload_gb == 8

    def test_orchestrator_defaults_used_when_config_omitted(self) -> None:
        """Baseline: without config=, defaults apply (documented behaviour)."""
        from cognithor.core.vllm_orchestrator import VLLMOrchestrator

        orch = VLLMOrchestrator(port=8000)
        # Spike default
        assert orch._config.max_model_len == 16384
