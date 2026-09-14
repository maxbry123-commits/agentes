"""Tests for ModelsConfig.observer slot."""

from __future__ import annotations

from cognithor.config import CognithorConfig, ModelsConfig
from cognithor.models import ModelConfig


class TestModelsConfigObserver:
    def test_observer_default_is_qwen3_32b(self):
        cfg = ModelsConfig()
        assert isinstance(cfg.observer, ModelConfig)
        assert cfg.observer.name == "qwen3:32b"

    def test_observer_overrideable(self):
        cfg = ModelsConfig(observer=ModelConfig(name="qwen3:8b"))
        assert cfg.observer.name == "qwen3:8b"

    def test_observer_in_default_ollama_names_mapping(self):
        from cognithor.config import _OLLAMA_DEFAULT_MODEL_NAMES

        assert "observer" in _OLLAMA_DEFAULT_MODEL_NAMES
        assert _OLLAMA_DEFAULT_MODEL_NAMES["observer"] == "qwen3:32b"

    def test_available_via_jarvis_config(self):
        cfg = CognithorConfig()
        assert cfg.models.observer.name == "qwen3:32b"

    def test_all_providers_have_observer_entry(self):
        """Provider-switching must include observer so it tracks the planner across backends."""
        from cognithor.config import _PROVIDER_MODEL_DEFAULTS

        for provider in ("openai", "anthropic", "gemini"):
            assert "observer" in _PROVIDER_MODEL_DEFAULTS[provider], (
                f"Provider {provider!r} missing observer entry — "
                "observer will not switch with planner"
            )

    def test_observer_in_provider_switch_loop(self):
        """The auto-switch role iteration must include observer."""
        import inspect

        from cognithor import config as _cfg_module

        src = inspect.getsource(_cfg_module)
        # Find the tuple that iterates roles for provider-switching.
        # (Kept intentionally loose — any tuple naming planner/observer/executor is fine.)
        assert '"observer"' in src or "'observer'" in src, (
            "observer role name missing from config module"
        )
        # Stronger: the specific iteration must include observer
        # Look for a pattern like `for role in ("planner", "observer", ...):` in the module.
        import re

        pattern = re.compile(r'for\s+role\s+in\s+\([^)]*["\']observer["\'][^)]*\)')
        assert pattern.search(src), "Provider-switching for-loop does not iterate 'observer'"

    def test_observer_factory_mirrors_planner_fields(self):
        """observer default: non-zero vram_gb + non-empty strengths (mirroring planner)."""
        cfg = ModelsConfig()
        assert cfg.observer.vram_gb > 0, (
            "Observer factory understates VRAM — zero-cost models mislead schedulers"
        )
        assert cfg.observer.strengths, "Observer factory has empty strengths — mirror the planner"
        assert cfg.observer.context_window > 0, "Observer factory has zero context_window"
