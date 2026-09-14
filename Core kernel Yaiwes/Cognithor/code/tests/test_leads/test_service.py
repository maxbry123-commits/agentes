"""Tests for cognithor.leads.service — source-agnostic orchestrator."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from cognithor.leads.models import Lead
from cognithor.leads.service import LeadService
from cognithor.leads.source import LeadSource
from cognithor.leads.store import LeadStore


class FakeRedditSource(LeadSource):
    source_id = "reddit"
    display_name = "Reddit"
    icon = "forum"
    color = "#FF4500"
    capabilities = frozenset({"scan"})

    def __init__(self) -> None:
        self.scan_calls = 0

    async def scan(
        self,
        *,
        config: dict[str, Any],
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]:
        self.scan_calls += 1
        return [
            Lead(
                post_id=f"r-{self.scan_calls}-1",
                source_id="reddit",
                title="pain point",
                url="https://reddit.com/r/x/1",
                intent_score=85,
            ),
            Lead(
                post_id=f"r-{self.scan_calls}-2",
                source_id="reddit",
                title="meh",
                url="https://reddit.com/r/x/2",
                intent_score=20,  # below min_score
            ),
        ]


class FakeHnSource(LeadSource):
    source_id = "hn"
    display_name = "Hacker News"
    icon = "article"
    color = "#FF6600"
    capabilities = frozenset({"scan"})

    async def scan(
        self,
        *,
        config: dict[str, Any],
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]:
        return [
            Lead(
                post_id="hn-1",
                source_id="hn",
                title="Show HN",
                url="https://news.ycombinator.com/item?id=1",
                intent_score=75,
            )
        ]


@pytest.fixture
def service(tmp_path: Path) -> LeadService:
    store = LeadStore(str(tmp_path / "leads.db"))
    svc = LeadService(store=store)
    svc.register_source(FakeRedditSource())
    svc.register_source(FakeHnSource())
    return svc


class TestLeadService:
    @pytest.mark.asyncio
    async def test_scan_single_source(self, service: LeadService) -> None:
        result = await service.scan(source_id="reddit", min_score=60)
        assert result.leads_found == 1  # only one lead >= 60
        assert result.posts_checked == 2

    @pytest.mark.asyncio
    async def test_scan_unknown_source_raises(self, service: LeadService) -> None:
        with pytest.raises(ValueError, match="unknown source"):
            await service.scan(source_id="twitter", min_score=60)

    @pytest.mark.asyncio
    async def test_scan_all_sources(self, service: LeadService) -> None:
        result = await service.scan(min_score=60)
        # reddit yields 1 lead (score 85), hn yields 1 lead (score 75).
        assert result.leads_found == 2

    @pytest.mark.asyncio
    async def test_scan_persists_leads(self, service: LeadService) -> None:
        from cognithor.leads.models import LeadStatus

        await service.scan(source_id="reddit", min_score=60)
        new_leads = service.get_leads(source_id="reddit", status=LeadStatus.NEW)
        assert len(new_leads) == 1
        assert new_leads[0].source_id == "reddit"
        # The low-score lead is persisted with status=ARCHIVED so a future
        # scan's already_seen() check can skip it without re-scoring.
        archived_leads = service.get_leads(source_id="reddit", status=LeadStatus.ARCHIVED)
        assert len(archived_leads) == 1

    @pytest.mark.asyncio
    async def test_scan_dedups_across_runs(self, service: LeadService) -> None:
        from cognithor.leads.models import LeadStatus

        await service.scan(source_id="reddit", min_score=60)
        await service.scan(source_id="reddit", min_score=60)
        # FakeRedditSource generates fresh post_ids on each call (r-1-1, r-2-1, ...)
        # so the store accumulates distinct records. Each run produces one NEW and
        # one ARCHIVED lead, so after two runs there are 2 NEW + 2 ARCHIVED = 4.
        new_leads = service.get_leads(source_id="reddit", status=LeadStatus.NEW)
        assert len(new_leads) == 2

    def test_list_sources(self, service: LeadService) -> None:
        ids = {s.source_id for s in service.list_sources()}
        assert ids == {"reddit", "hn"}

    def test_register_unregister(self, service: LeadService) -> None:
        assert len(service.list_sources()) == 2
        service.unregister_source("reddit")
        assert len(service.list_sources()) == 1
        assert {s.source_id for s in service.list_sources()} == {"hn"}
