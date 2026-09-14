"""Tests for ATL Journal."""

from __future__ import annotations

import datetime

import pytest

from cognithor.evolution.atl_journal import ATLJournal


@pytest.fixture
def journal(tmp_path):
    return ATLJournal(journal_dir=tmp_path / "journal")


@pytest.mark.asyncio
async def test_log_cycle(journal):
    await journal.log_cycle(
        cycle=1,
        summary="Evaluated BU goals",
        goal_updates=[{"goal_id": "g_001", "delta": 0.05, "note": "OK"}],
        actions=["memory_update: saved BU tariff"],
    )
    content = journal.today()
    assert content is not None
    assert "Zyklus #1" in content
    assert "BU goals" in content


@pytest.mark.asyncio
async def test_multiple_cycles(journal):
    await journal.log_cycle(cycle=1, summary="First", goal_updates=[], actions=[])
    await journal.log_cycle(cycle=2, summary="Second", goal_updates=[], actions=[])
    content = journal.today()
    assert "Zyklus #1" in content
    assert "Zyklus #2" in content


@pytest.mark.asyncio
async def test_no_journal_returns_none(journal):
    assert journal.today() is None


def test_recent_includes_older_files(tmp_path):
    jdir = tmp_path / "journal"
    jdir.mkdir(parents=True, exist_ok=True)
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    (jdir / f"{yesterday}.md").write_text("# Yesterday\nSome thoughts", encoding="utf-8")
    journal = ATLJournal(journal_dir=jdir)
    entries = journal.recent(days=3)
    assert len(entries) >= 1
    assert "Yesterday" in entries[0]


@pytest.mark.asyncio
async def test_journal_dir_created(tmp_path):
    jdir = tmp_path / "deep" / "nested" / "journal"
    journal = ATLJournal(journal_dir=jdir)
    await journal.log_cycle(cycle=1, summary="Test", goal_updates=[], actions=[])
    assert jdir.exists()
    assert journal.today() is not None
