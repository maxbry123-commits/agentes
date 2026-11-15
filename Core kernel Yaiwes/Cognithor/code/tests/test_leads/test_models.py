"""Tests for cognithor.leads.models — generic lead data structures."""

from __future__ import annotations

import pytest

from cognithor.leads.models import Lead, LeadStats, LeadStatus, ScanResult  # noqa: F401


class TestLead:
    def test_defaults(self) -> None:
        lead = Lead(
            post_id="abc",
            source_id="reddit",
            title="Looking for local LLM",
            url="https://reddit.com/r/LocalLLaMA/abc",
            intent_score=85,
        )
        assert lead.post_id == "abc"
        assert lead.source_id == "reddit"
        assert lead.status == LeadStatus.NEW
        assert lead.subreddit == ""  # back-compat default

    def test_source_id_required(self) -> None:
        with pytest.raises(TypeError):
            Lead(post_id="a", title="t", url="u", intent_score=10)  # type: ignore[call-arg]

    def test_to_dict_round_trip(self) -> None:
        lead = Lead(
            post_id="xyz",
            source_id="hn",
            title="Ask HN: LLM?",
            url="https://news.ycombinator.com/item?id=xyz",
            intent_score=72,
        )
        d = lead.to_dict()
        assert d["post_id"] == "xyz"
        assert d["source_id"] == "hn"
        assert d["status"] == "new"

    def test_subreddit_legacy_field_still_works(self) -> None:
        """Back-compat: old Reddit records set subreddit, new generic code reads source_id."""
        lead = Lead(
            post_id="r1",
            source_id="reddit",
            subreddit="LocalLLaMA",
            title="t",
            url="u",
            intent_score=50,
        )
        assert lead.subreddit == "LocalLLaMA"
        assert lead.source_id == "reddit"


class TestLeadStatus:
    def test_enum_values(self) -> None:
        assert LeadStatus.NEW.value == "new"
        assert LeadStatus.REVIEWED.value == "reviewed"
        assert LeadStatus.REPLIED.value == "replied"
        assert LeadStatus.ARCHIVED.value == "archived"


class TestScanResult:
    def test_summary_format(self) -> None:
        result = ScanResult(
            subreddits_scanned=["LocalLLaMA"],
            posts_checked=30,
            leads_found=4,
            posts_skipped_duplicate=2,
            posts_skipped_low_score=24,
            trigger="cli",
        )
        summary = result.summary()
        assert "30" in summary
        assert "4" in summary
