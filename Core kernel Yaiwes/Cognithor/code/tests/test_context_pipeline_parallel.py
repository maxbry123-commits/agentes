"""Tests for parallel wave execution in ContextPipeline.

Tests:
  - Wave 1 parallel execution (memory, vault, episodes)
  - Wave 2 parallel execution (skill injection, user preferences)
  - One wave task fails, others continue
  - Timing fields populated
  - Deduplication at checkpoint
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.config import ContextPipelineConfig
from cognithor.core.context_pipeline import ContextPipeline, ContextResult
from cognithor.models import Chunk, MemorySearchResult, WorkingMemory

# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def pipeline_config() -> ContextPipelineConfig:
    return ContextPipelineConfig()


@pytest.fixture
def pipeline(pipeline_config: ContextPipelineConfig) -> ContextPipeline:
    return ContextPipeline(pipeline_config)


@pytest.fixture
def wm() -> WorkingMemory:
    return WorkingMemory()


def _make_search_result(text: str, score: float = 0.5) -> MemorySearchResult:
    return MemorySearchResult(
        chunk=Chunk(text=text, source_path="test.md"),
        score=score,
        bm25_score=score,
    )


def _make_memory_manager(
    search_results: list[MemorySearchResult] | None = None,
    episodes: list[tuple[date, str]] | None = None,
) -> MagicMock:
    mm = MagicMock()
    mm.search_memory = AsyncMock(return_value=search_results or [])
    mm.search_memory_sync.return_value = search_results or []
    episodic = MagicMock()
    episodic.get_recent.return_value = episodes or []
    mm.episodic = episodic
    return mm


def _make_vault_tools(search_result: str = "") -> AsyncMock:
    vt = AsyncMock()
    vt.vault_search = AsyncMock(return_value=search_result)
    return vt


# ── Wave 1: Parallel Execution ──────────────────────────────────


class TestWave1Parallel:
    """Wave 1 runs memory, vault, and episodes in parallel."""

    @pytest.mark.asyncio
    async def test_all_wave1_sources_gathered(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        results = [_make_search_result("fact 1", 0.8)]
        mm = _make_memory_manager(
            search_results=results,
            episodes=[(date(2026, 3, 1), "episode text")],
        )
        pipeline.set_memory_manager(mm)
        vt = _make_vault_tools("vault hit")
        pipeline.set_vault_tools(vt)

        ctx = await pipeline.enrich("What is the status of project Alpha?", wm)

        assert ctx.skipped is False
        assert len(ctx.memory_results) == 1
        assert len(ctx.vault_snippets) == 1
        assert len(ctx.episode_snippets) == 1

    @pytest.mark.asyncio
    async def test_memory_failure_does_not_block_vault(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        mm = MagicMock()
        mm.search_memory = AsyncMock(side_effect=RuntimeError("BM25 crash"))
        mm.search_memory_sync.side_effect = RuntimeError("BM25 crash")
        mm.episodic = MagicMock()
        mm.episodic.get_recent.return_value = []
        pipeline.set_memory_manager(mm)

        vt = _make_vault_tools("vault result despite memory failure")
        pipeline.set_vault_tools(vt)

        ctx = await pipeline.enrich("Tell me about the project", wm)

        assert ctx.skipped is False
        assert len(ctx.memory_results) == 0
        assert len(ctx.vault_snippets) == 1

    @pytest.mark.asyncio
    async def test_vault_failure_does_not_block_memory(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        results = [_make_search_result("memory works", 0.9)]
        mm = _make_memory_manager(search_results=results)
        pipeline.set_memory_manager(mm)

        vt = AsyncMock()
        vt.vault_search = AsyncMock(side_effect=RuntimeError("Vault down"))
        pipeline.set_vault_tools(vt)

        ctx = await pipeline.enrich("Search for information", wm)

        assert len(ctx.memory_results) == 1
        assert len(ctx.vault_snippets) == 0

    @pytest.mark.asyncio
    async def test_episode_failure_does_not_block_others(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        results = [_make_search_result("memory ok", 0.7)]
        mm = MagicMock()
        mm.search_memory = AsyncMock(return_value=results)
        mm.search_memory_sync.return_value = results
        mm.episodic = MagicMock()
        mm.episodic.get_recent.side_effect = RuntimeError("Episodes corrupt")
        pipeline.set_memory_manager(mm)

        ctx = await pipeline.enrich("What happened recently?", wm)

        assert len(ctx.memory_results) == 1
        assert len(ctx.episode_snippets) == 0


# ── Wave 2: Parallel Execution ──────────────────────────────────


class TestWave2Parallel:
    """Wave 2 runs skill injection and user preference lookup in parallel."""

    @pytest.mark.asyncio
    async def test_skill_context_populated(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        skill_reg = MagicMock()
        skill_match = MagicMock()
        skill_match.skill.name = "web-research"
        skill_match.skill.description = "Web research skill"
        skill_match.skill.trigger_keywords = ["web", "search"]
        skill_reg.match.return_value = [skill_match]
        pipeline.set_skill_registry(skill_reg)

        ctx = await pipeline.enrich("Search the web for news", wm)

        assert "web-research" in ctx.skill_context

    @pytest.mark.asyncio
    async def test_user_pref_populated(self, pipeline: ContextPipeline, wm: WorkingMemory) -> None:
        pref_store = MagicMock()
        pref_obj = MagicMock()
        pref_obj.verbosity_hint = "Keep it verbose"
        pref_store.get_preference.return_value = pref_obj
        pipeline.set_user_pref_store(pref_store)

        ctx = await pipeline.enrich("Tell me everything", wm, user_id="user123")

        assert ctx.user_pref_hint == "Keep it verbose"

    @pytest.mark.asyncio
    async def test_skill_failure_does_not_block_prefs(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        skill_reg = MagicMock()
        skill_reg.match.side_effect = RuntimeError("Registry down")
        pipeline.set_skill_registry(skill_reg)

        pref_store = MagicMock()
        pref_obj = MagicMock()
        pref_obj.verbosity_hint = "Be terse"
        pref_store.get_preference.return_value = pref_obj
        pipeline.set_user_pref_store(pref_store)

        ctx = await pipeline.enrich("Do something", wm, user_id="user1")

        assert ctx.skill_context == ""
        assert ctx.user_pref_hint == "Be terse"

    @pytest.mark.asyncio
    async def test_pref_failure_does_not_block_skills(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        skill_reg = MagicMock()
        skill_match = MagicMock()
        skill_match.skill.name = "code-review"
        skill_match.skill.description = "Code review skill"
        skill_match.skill.trigger_keywords = ["code", "review"]
        skill_reg.match.return_value = [skill_match]
        pipeline.set_skill_registry(skill_reg)

        pref_store = MagicMock()
        pref_store.get_preference.side_effect = RuntimeError("DB locked")
        pipeline.set_user_pref_store(pref_store)

        ctx = await pipeline.enrich("Review my code", wm, user_id="user2")

        assert "code-review" in ctx.skill_context
        assert ctx.user_pref_hint == ""


# ── Timing ───────────────────────────────────────────────────────


class TestTimingFields:
    """Timing fields are populated with non-negative values."""

    @pytest.mark.asyncio
    async def test_timing_fields_populated(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        mm = _make_memory_manager()
        pipeline.set_memory_manager(mm)

        ctx = await pipeline.enrich("What is the project status?", wm)

        assert ctx.wave1_ms >= 0.0
        assert ctx.wave2_ms >= 0.0
        assert ctx.duration_ms >= 0.0
        assert ctx.duration_ms >= ctx.wave1_ms

    @pytest.mark.asyncio
    async def test_smalltalk_has_no_wave_timing(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        ctx = await pipeline.enrich("Hi", wm)
        assert ctx.skipped is True
        # Smalltalk skips waves entirely
        assert ctx.wave1_ms == 0.0
        assert ctx.wave2_ms == 0.0


# ── Deduplication ────────────────────────────────────────────────


class TestDeduplication:
    """Checkpoint deduplicates overlapping results."""

    @pytest.mark.asyncio
    async def test_vault_deduped_against_memory(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        """Vault snippet matching memory text is removed."""
        memory_text = "Project Alpha deadline March 15"
        results = [_make_search_result(memory_text, 0.9)]
        mm = _make_memory_manager(search_results=results)
        pipeline.set_memory_manager(mm)

        # Vault returns same text (should be deduped)
        vt = _make_vault_tools(memory_text)
        pipeline.set_vault_tools(vt)

        ctx = await pipeline.enrich("What about Project Alpha?", wm)

        assert len(ctx.memory_results) == 1
        # Vault snippet matching memory content is deduped
        assert len(ctx.vault_snippets) == 0

    @pytest.mark.asyncio
    async def test_different_vault_not_deduped(
        self, pipeline: ContextPipeline, wm: WorkingMemory
    ) -> None:
        """Vault snippet with different text is kept."""
        results = [_make_search_result("Memory fact A", 0.9)]
        mm = _make_memory_manager(search_results=results)
        pipeline.set_memory_manager(mm)

        vt = _make_vault_tools("Completely different vault info")
        pipeline.set_vault_tools(vt)

        ctx = await pipeline.enrich("Give me all info", wm)

        assert len(ctx.memory_results) == 1
        assert len(ctx.vault_snippets) == 1


# ── ContextResult defaults ───────────────────────────────────────


class TestContextResultDefaults:
    """New ContextResult fields have correct defaults."""

    def test_new_fields_default(self) -> None:
        cr = ContextResult()
        assert cr.skill_context == ""
        assert cr.user_pref_hint == ""
        assert cr.wave1_ms == 0.0
        assert cr.wave2_ms == 0.0
