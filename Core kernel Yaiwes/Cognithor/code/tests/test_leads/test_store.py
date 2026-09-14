"""Tests for cognithor.leads.store — generic SQLCipher-backed lead store."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from cognithor.leads.models import Lead, LeadStatus
from cognithor.leads.store import LeadStore


@pytest.fixture
def store(tmp_path: Path) -> LeadStore:
    return LeadStore(str(tmp_path / "leads.db"))


class TestLeadStoreBasics:
    def test_save_and_retrieve_reddit_lead(self, store: LeadStore) -> None:
        lead = Lead(
            post_id="abc",
            source_id="reddit",
            subreddit="LocalLLaMA",
            title="t",
            url="u",
            intent_score=90,
        )
        store.save_lead(lead)
        fetched = store.get_leads(limit=10)
        assert len(fetched) == 1
        assert fetched[0].post_id == "abc"
        assert fetched[0].source_id == "reddit"

    def test_save_and_retrieve_hn_lead(self, store: LeadStore) -> None:
        lead = Lead(
            post_id="hn-xyz",
            source_id="hn",
            title="Ask HN",
            url="https://news.ycombinator.com/item?id=xyz",
            intent_score=70,
        )
        store.save_lead(lead)
        fetched = store.get_leads(source_id="hn")
        assert len(fetched) == 1
        assert fetched[0].source_id == "hn"

    def test_already_seen(self, store: LeadStore) -> None:
        lead = Lead(
            post_id="dup",
            source_id="reddit",
            subreddit="X",
            title="t",
            url="u",
            intent_score=50,
        )
        store.save_lead(lead)
        assert store.already_seen("dup") is True
        assert store.already_seen("fresh") is False

    def test_filter_by_source_id(self, store: LeadStore) -> None:
        store.save_lead(Lead(post_id="a", source_id="reddit", title="a", url="u1", intent_score=80))
        store.save_lead(Lead(post_id="b", source_id="hn", title="b", url="u2", intent_score=80))
        store.save_lead(Lead(post_id="c", source_id="rss", title="c", url="u3", intent_score=80))
        assert len(store.get_leads(source_id="reddit")) == 1
        assert len(store.get_leads(source_id="hn")) == 1
        assert len(store.get_leads()) == 3  # no filter

    def test_filter_by_status(self, store: LeadStore) -> None:
        store.save_lead(
            Lead(
                post_id="a",
                source_id="reddit",
                title="a",
                url="u",
                intent_score=80,
                status=LeadStatus.NEW,
            )
        )
        store.save_lead(
            Lead(
                post_id="b",
                source_id="reddit",
                title="b",
                url="u",
                intent_score=80,
                status=LeadStatus.ARCHIVED,
            )
        )
        assert len(store.get_leads(status=LeadStatus.NEW)) == 1
        assert len(store.get_leads(status=LeadStatus.ARCHIVED)) == 1
