"""Tests for ModelRouter ContextVar-based coding override (concurrency safety).

Verifies that the coding override is isolated per async task using
contextvars.ContextVar, preventing one request's coding model from
leaking into a concurrent request.
"""

from __future__ import annotations

import asyncio
import contextvars

import pytest

from cognithor.config import CognithorConfig
from cognithor.core.model_router import (
    ModelRouter,
    OllamaClient,
    _coding_override_var,
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
def _reset_contextvar():
    """Ensure _coding_override_var is None before and after each test."""
    _coding_override_var.set(None)
    yield
    _coding_override_var.set(None)


class TestContextVarIsolation:
    """Proves that set_coding_override is isolated per async task."""

    async def test_override_isolated_per_task(
        self, router: ModelRouter, config: CognithorConfig
    ) -> None:
        """Two concurrent async tasks: one sets override, the other must NOT see it.

        This is the core concurrency bug scenario. Before the fix, both tasks
        would share the same mutable instance variable on the singleton
        ModelRouter, causing the non-coding task to use the wrong model.
        """
        coding_model = "deepseek-coder-v2:33b"
        barrier = asyncio.Barrier(2)
        results: dict[str, str] = {}

        async def coding_task() -> None:
            """Simulates a request that triggers a coding override."""
            router.set_coding_override(coding_model)
            # Wait until the other task is also running.
            await barrier.wait()
            # Our own context should see the override.
            selected = router.select_model("planning")
            results["coding"] = selected
            router.clear_coding_override()

        async def normal_task() -> None:
            """Simulates a concurrent non-coding request."""
            # Wait until the coding task has set its override.
            await barrier.wait()
            # This task should NOT see the coding override because
            # contextvars gives each task its own copy.
            selected = router.select_model("planning")
            results["normal"] = selected

        # asyncio.create_task copies the current context, so each task
        # gets its own ContextVar state.
        ctx_coding = contextvars.copy_context()
        ctx_normal = contextvars.copy_context()

        loop = asyncio.get_event_loop()

        task1 = loop.create_task(ctx_coding.run(coding_task))
        task2 = loop.create_task(ctx_normal.run(normal_task))

        await asyncio.gather(task1, task2)

        # The coding task should have used the override model.
        assert results["coding"] == coding_model
        # The normal task must use the default planner -- NOT the coding model.
        assert results["normal"] == config.models.planner.name
        assert results["normal"] != coding_model


class TestSetAndClear:
    """Tests that set/clear work correctly within the same context."""

    async def test_set_and_clear(self, router: ModelRouter, config: CognithorConfig) -> None:
        """Setting override changes select_model; clearing restores default."""
        coding_model = "codestral:22b"

        # Before setting: should use default planner.
        default_model = router.select_model("planning")
        assert default_model == config.models.planner.name

        # After setting: should use override.
        router.set_coding_override(coding_model)
        assert router.select_model("planning") == coding_model
        assert router.select_model("general") == coding_model
        # Embeddings are always excluded from coding override.
        assert router.select_model("embedding") == config.models.embedding.name

        # After clearing: should use default again.
        router.clear_coding_override()
        assert router.select_model("planning") == config.models.planner.name

    async def test_clear_when_not_set(self, router: ModelRouter) -> None:
        """Clearing without prior set should not raise."""
        router.clear_coding_override()  # Must not raise.
        assert _coding_override_var.get() is None


class TestDefaultIsNone:
    """Tests that without any override, normal routing is used."""

    async def test_default_is_none(self, router: ModelRouter, config: CognithorConfig) -> None:
        """Without override, select_model uses normal task-type routing."""
        assert _coding_override_var.get() is None

        assert router.select_model("planning") == config.models.planner.name
        assert router.select_model("reflection") == config.models.planner.name
        assert router.select_model("code", "high") == config.models.coder.name
        assert router.select_model("code", "medium") == config.models.coder_fast.name
        assert router.select_model("simple_tool_call") == config.models.executor.name
        assert router.select_model("embedding") == config.models.embedding.name


class TestOverrideAffectsSelectModel:
    """Tests that a set override is actually returned by select_model."""

    async def test_override_affects_select_model(
        self, router: ModelRouter, config: CognithorConfig
    ) -> None:
        """With override set, select_model returns the override for all non-embedding types."""
        override_model = "qwen3-coder:30b"
        router.set_coding_override(override_model)

        for task_type in (
            "planning",
            "reflection",
            "code",
            "simple_tool_call",
            "summarization",
            "general",
        ):
            result = router.select_model(task_type)
            assert result == override_model, (
                f"Expected {override_model} for task_type={task_type}, got {result}"
            )

        # Embedding must still use the embedding model.
        assert router.select_model("embedding") == config.models.embedding.name

    async def test_contextvar_directly_readable(self, router: ModelRouter) -> None:
        """The ContextVar is updated when set_coding_override is called."""
        assert _coding_override_var.get() is None
        router.set_coding_override("test-model:7b")
        assert _coding_override_var.get() == "test-model:7b"
        router.clear_coding_override()
        assert _coding_override_var.get() is None

    async def test_instance_attr_kept_for_backwards_compat(self, router: ModelRouter) -> None:
        """The instance attribute _coding_override is still set for legacy callers."""
        router.set_coding_override("legacy-model:13b")
        assert router._coding_override == "legacy-model:13b"
        router.clear_coding_override()
        assert router._coding_override is None
