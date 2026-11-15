"""Tests for Concierge-Routing (urgency-based model selection).

Tests:
  - ConciergeProfile dataclass
  - CONCIERGE_PROFILES lookup
  - set_urgency / get_urgency / clear_urgency on ModelRouter
  - Urgency influences select_model() for non-embedding tasks
  - Coding override takes precedence over urgency
  - Embedding tasks ignore urgency
  - Invalid urgency raises ValueError
"""

from __future__ import annotations

import pytest

from cognithor.config import CognithorConfig
from cognithor.core.model_router import (
    CONCIERGE_PROFILES,
    ConciergeProfile,
    ModelRouter,
    OllamaClient,
    _urgency_var,
)


@pytest.fixture()
def config(tmp_path) -> CognithorConfig:
    return CognithorConfig(cognithor_home=tmp_path)


@pytest.fixture()
def client(config: CognithorConfig) -> OllamaClient:
    return OllamaClient(config)


@pytest.fixture()
def router(config: CognithorConfig, client: OllamaClient) -> ModelRouter:
    return ModelRouter(config, client)


@pytest.fixture(autouse=True)
def _reset_urgency():
    """Reset the urgency ContextVar between tests."""
    _urgency_var.set(None)
    yield
    _urgency_var.set(None)


# ============================================================================
# ConciergeProfile
# ============================================================================


class TestConciergeProfile:
    """Tests for the ConciergeProfile dataclass."""

    def test_profile_is_frozen(self) -> None:
        p = ConciergeProfile(name="test", model="m", description="d")
        with pytest.raises(AttributeError):
            p.name = "other"  # type: ignore[misc]

    def test_profile_fields(self) -> None:
        p = ConciergeProfile(name="fast", model="qwen3:1.7b", description="Small")
        assert p.name == "fast"
        assert p.model == "qwen3:1.7b"
        assert p.description == "Small"


# ============================================================================
# CONCIERGE_PROFILES
# ============================================================================


class TestConciergeProfiles:
    """Tests for the default profile registry."""

    def test_all_three_profiles_exist(self) -> None:
        assert "asap" in CONCIERGE_PROFILES
        assert "balanced" in CONCIERGE_PROFILES
        assert "no_hurry" in CONCIERGE_PROFILES

    def test_asap_uses_large_model(self) -> None:
        assert CONCIERGE_PROFILES["asap"].model == "qwen3:32b"

    def test_balanced_uses_medium_model(self) -> None:
        assert CONCIERGE_PROFILES["balanced"].model == "qwen3:8b"

    def test_no_hurry_uses_small_model(self) -> None:
        assert CONCIERGE_PROFILES["no_hurry"].model == "qwen3:1.7b"

    def test_get_concierge_profile_found(self) -> None:
        profile = ModelRouter.get_concierge_profile("asap")
        assert profile is not None
        assert profile.name == "asap"

    def test_get_concierge_profile_not_found(self) -> None:
        assert ModelRouter.get_concierge_profile("nonexistent") is None


# ============================================================================
# Urgency getters / setters
# ============================================================================


class TestUrgencyState:
    """Tests for set_urgency / get_urgency / clear_urgency."""

    def test_default_urgency_is_none(self, router: ModelRouter) -> None:
        assert router.get_urgency() is None

    def test_set_and_get_urgency(self, router: ModelRouter) -> None:
        router.set_urgency("balanced")
        assert router.get_urgency() == "balanced"

    def test_clear_urgency(self, router: ModelRouter) -> None:
        router.set_urgency("asap")
        router.clear_urgency()
        assert router.get_urgency() is None

    def test_invalid_urgency_raises(self, router: ModelRouter) -> None:
        with pytest.raises(ValueError, match="Unknown urgency"):
            router.set_urgency("ultra_fast")

    def test_set_urgency_overwrites_previous(self, router: ModelRouter) -> None:
        router.set_urgency("asap")
        router.set_urgency("no_hurry")
        assert router.get_urgency() == "no_hurry"


# ============================================================================
# Urgency influences select_model()
# ============================================================================


class TestUrgencyModelSelection:
    """Tests that urgency overrides normal model selection."""

    def test_asap_selects_large_model(self, router: ModelRouter) -> None:
        router.set_urgency("asap")
        model = router.select_model("general", "low")
        assert model == "qwen3:32b"

    def test_balanced_selects_medium_model(self, router: ModelRouter) -> None:
        router.set_urgency("balanced")
        model = router.select_model("planning", "high")
        assert model == "qwen3:8b"

    def test_no_hurry_selects_small_model(self, router: ModelRouter) -> None:
        router.set_urgency("no_hurry")
        model = router.select_model("code", "high")
        assert model == "qwen3:1.7b"

    def test_urgency_applies_to_all_task_types(self, router: ModelRouter) -> None:
        router.set_urgency("asap")
        for task in ("planning", "reflection", "code", "simple_tool_call", "general"):
            model = router.select_model(task)
            assert model == "qwen3:32b", f"Failed for task_type={task}"

    def test_embedding_ignores_urgency(self, router: ModelRouter, config: CognithorConfig) -> None:
        router.set_urgency("no_hurry")
        model = router.select_model("embedding")
        assert model == config.models.embedding.name

    def test_no_urgency_uses_normal_routing(
        self, router: ModelRouter, config: CognithorConfig
    ) -> None:
        # No urgency set -- normal behavior
        model = router.select_model("planning")
        assert model == config.models.planner.name

    def test_coding_override_takes_precedence(self, router: ModelRouter) -> None:
        router.set_urgency("no_hurry")
        router.set_coding_override("special-coder:99b")
        model = router.select_model("planning")
        assert model == "special-coder:99b"
        router.clear_coding_override()

    def test_cleared_urgency_reverts_to_normal(
        self, router: ModelRouter, config: CognithorConfig
    ) -> None:
        router.set_urgency("asap")
        router.clear_urgency()
        model = router.select_model("simple_tool_call")
        assert model == config.models.executor.name

    def test_urgency_fallback_when_model_unavailable(
        self, router: ModelRouter, config: CognithorConfig
    ) -> None:
        # Simulate available models that do NOT include the no_hurry model
        router._available_models = {config.models.planner.name, config.models.executor.name}
        router.set_urgency("no_hurry")
        model = router.select_model("general")
        # Should fall back to one of the available models
        assert model in router._available_models
