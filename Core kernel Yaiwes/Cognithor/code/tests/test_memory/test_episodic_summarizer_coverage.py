"""Coverage-Tests fuer episodic_summarizer.py -- fehlende Pfade abdecken."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.memory.episodic_summarizer import EpisodicSummarizer


@pytest.fixture
def store() -> MagicMock:
    return MagicMock()


@pytest.fixture
def summarizer(store: MagicMock) -> EpisodicSummarizer:
    return EpisodicSummarizer(store)


class TestSummarizeDay:
    @pytest.mark.asyncio
    async def test_no_episodes(self, summarizer: EpisodicSummarizer, store: MagicMock) -> None:
        store.list_episodes.return_value = []
        result = await summarizer.summarize_day(date(2025, 1, 15))
        assert "Keine Episoden" in result
        assert "2025-01-15" in result

    @pytest.mark.asyncio
    async def test_search_exception(self, summarizer: EpisodicSummarizer, store: MagicMock) -> None:
        store.list_episodes.side_effect = RuntimeError("db error")
        result = await summarizer.summarize_day(date(2025, 1, 15))
        assert "Keine Episoden" in result

    @pytest.mark.asyncio
    async def test_with_episodes(self, summarizer: EpisodicSummarizer, store: MagicMock) -> None:
        ep = MagicMock()
        ep.success_score = 0.8
        ep.topic = "Task A"
        ep.outcome = "Success"
        ep.content = "Did something"
        store.list_episodes.return_value = [ep]

        result = await summarizer.summarize_day(date(2025, 1, 15))
        assert "Task A" in result
        assert "Success" in result
        store.store_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_llm(self, store: MagicMock) -> None:
        llm = AsyncMock()
        llm.chat = AsyncMock(return_value={"message": {"content": "LLM Summary"}})
        summarizer = EpisodicSummarizer(store, llm=llm)

        ep = MagicMock()
        ep.success_score = 1.0
        ep.topic = "Work"
        ep.outcome = "Done"
        ep.content = "Worked on stuff"
        store.list_episodes.return_value = [ep]

        result = await summarizer.summarize_day(date(2025, 3, 1))
        assert result == "LLM Summary"

    @pytest.mark.asyncio
    async def test_llm_error_fallback(self, store: MagicMock) -> None:
        llm = AsyncMock()
        llm.chat = AsyncMock(side_effect=RuntimeError("llm fail"))
        summarizer = EpisodicSummarizer(store, llm=llm)

        ep = MagicMock()
        ep.success_score = 0.5
        ep.topic = "Task"
        ep.outcome = None
        ep.content = "Content text here for the summary"
        store.list_episodes.return_value = [ep]

        result = await summarizer.summarize_day(date(2025, 3, 1))
        # Should fall back to non-LLM summary
        assert "Task" in result

    @pytest.mark.asyncio
    async def test_episode_without_outcome(
        self, summarizer: EpisodicSummarizer, store: MagicMock
    ) -> None:
        ep = MagicMock()
        ep.success_score = 0.0
        ep.topic = "Failed Task"
        ep.outcome = None
        ep.content = "This is the content text that is quite long"
        store.list_episodes.return_value = [ep]

        result = await summarizer.summarize_day(date(2025, 1, 15))
        assert "Failed Task" in result


class TestSummarizeWeek:
    @pytest.mark.asyncio
    async def test_no_summaries(self, summarizer: EpisodicSummarizer, store: MagicMock) -> None:
        store.get_summaries.return_value = []
        result = await summarizer.summarize_week(date(2025, 1, 13))
        assert "Keine Zusammenfassungen" in result

    @pytest.mark.asyncio
    async def test_with_summaries(self, summarizer: EpisodicSummarizer, store: MagicMock) -> None:
        store.get_summaries.return_value = [
            {"start_date": "2025-01-13", "summary": "Monday summary"},
            {"start_date": "2025-01-14", "summary": "Tuesday summary"},
        ]
        result = await summarizer.summarize_week(date(2025, 1, 13))
        assert "Monday summary" in result
        assert "Tuesday summary" in result
        store.store_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_filters_to_week(self, summarizer: EpisodicSummarizer, store: MagicMock) -> None:
        store.get_summaries.return_value = [
            {"start_date": "2025-01-13", "summary": "In week"},
            {"start_date": "2025-01-25", "summary": "Outside week"},
        ]
        result = await summarizer.summarize_week(date(2025, 1, 13))
        assert "In week" in result
        assert "Outside week" not in result
