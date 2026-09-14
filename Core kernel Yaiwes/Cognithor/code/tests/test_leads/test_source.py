"""Tests for cognithor.leads.source — LeadSource abstract base."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from cognithor.leads.models import Lead
from cognithor.leads.source import LeadSource


class ConcreteSource(LeadSource):
    source_id = "test"
    display_name = "Test Source"
    icon = "science"
    color = "#FF00FF"
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
                post_id="t1",
                source_id=self.source_id,
                title="test lead",
                url="https://test.example/t1",
                intent_score=99,
            )
        ]


class TestLeadSourceBase:
    def test_cannot_instantiate_abstract_base(self) -> None:
        with pytest.raises(TypeError):
            LeadSource()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_concrete_subclass_works(self) -> None:
        src = ConcreteSource()
        leads = await src.scan(config={}, product="Cognithor", product_description="", min_score=50)
        assert len(leads) == 1
        assert leads[0].source_id == "test"
        assert leads[0].intent_score == 99

    def test_optional_capabilities_raise_not_implemented(self) -> None:
        """draft_reply, refine_reply, post_reply default to NotImplementedError."""
        src = ConcreteSource()
        lead = Lead(post_id="x", source_id="test", title="t", url="u", intent_score=50)
        with pytest.raises(NotImplementedError):
            asyncio.run(src.draft_reply(lead, tone="helpful"))
        with pytest.raises(NotImplementedError):
            asyncio.run(src.refine_reply(lead, "draft"))
        with pytest.raises(NotImplementedError):
            asyncio.run(src.post_reply(lead, "text"))
