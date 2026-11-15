"""Coverage-Tests fuer episodic.py -- fehlende Pfade abdecken."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from cognithor.memory.episodic import EpisodicMemory

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def episodes(tmp_path: Path) -> EpisodicMemory:
    return EpisodicMemory(tmp_path / "episodes")


class TestAppendEntry:
    def test_new_file(self, episodes: EpisodicMemory) -> None:
        ts = datetime(2025, 1, 15, 10, 30)
        entry = episodes.append_entry("Test", "Content", timestamp=ts)
        assert "Test" in entry
        assert "10:30" in entry

        file_path = episodes._file_for_date(ts.date())
        content = file_path.read_text(encoding="utf-8")
        assert "2025-01-15" in content
        assert "Test" in content

    def test_append_to_existing(self, episodes: EpisodicMemory) -> None:
        ts = datetime(2025, 1, 15, 10, 0)
        episodes.append_entry("First", "Content1", timestamp=ts)
        ts2 = datetime(2025, 1, 15, 11, 0)
        episodes.append_entry("Second", "Content2", timestamp=ts2)

        content = episodes.get_date(date(2025, 1, 15))
        assert "First" in content
        assert "Second" in content

    def test_default_timestamp(self, episodes: EpisodicMemory) -> None:
        entry = episodes.append_entry("Auto", "AutoContent")
        assert "Auto" in entry


class TestGetToday:
    def test_empty(self, episodes: EpisodicMemory) -> None:
        episodes.ensure_directory()
        result = episodes.get_today()
        assert result == ""


class TestGetDate:
    def test_nonexistent(self, episodes: EpisodicMemory) -> None:
        result = episodes.get_date(date(2020, 1, 1))
        assert result == ""


class TestGetRecent:
    def test_empty(self, episodes: EpisodicMemory) -> None:
        episodes.ensure_directory()
        result = episodes.get_recent(days=3)
        assert result == []

    def test_with_data(self, episodes: EpisodicMemory) -> None:
        today = date.today()
        ts = datetime.combine(today, datetime.min.time().replace(hour=10))
        episodes.append_entry("Today", "TodayContent", timestamp=ts)
        result = episodes.get_recent(days=1)
        assert len(result) == 1
        assert result[0][0] == today


class TestListDates:
    def test_empty(self, episodes: EpisodicMemory) -> None:
        assert episodes.list_dates() == []

    def test_with_dates(self, episodes: EpisodicMemory) -> None:
        episodes.ensure_directory()
        (episodes._dir / "2025-01-15.md").write_text("# 2025-01-15\n", encoding="utf-8")
        (episodes._dir / "2025-01-16.md").write_text("# 2025-01-16\n", encoding="utf-8")
        dates = episodes.list_dates()
        assert len(dates) == 2
        assert dates[0] == date(2025, 1, 16)  # Newest first

    def test_invalid_filenames(self, episodes: EpisodicMemory) -> None:
        episodes.ensure_directory()
        (episodes._dir / "not-a-date.md").write_text("bad", encoding="utf-8")
        (episodes._dir / "2025-01-15.md").write_text("ok", encoding="utf-8")
        dates = episodes.list_dates()
        assert len(dates) == 1


class TestPruneOld:
    def test_zero_retention(self, episodes: EpisodicMemory) -> None:
        assert episodes.prune_old(0) == 0

    def test_negative_retention(self, episodes: EpisodicMemory) -> None:
        assert episodes.prune_old(-1) == 0

    def test_no_directory(self, episodes: EpisodicMemory) -> None:
        assert episodes.prune_old(30) == 0

    def test_prune(self, episodes: EpisodicMemory) -> None:
        episodes.ensure_directory()
        old_date = date.today() - timedelta(days=100)
        (episodes._dir / f"{old_date.isoformat()}.md").write_text("old", encoding="utf-8")
        recent = date.today() - timedelta(days=5)
        (episodes._dir / f"{recent.isoformat()}.md").write_text("new", encoding="utf-8")

        deleted = episodes.prune_old(30)
        assert deleted == 1
        assert not (episodes._dir / f"{old_date.isoformat()}.md").exists()
        assert (episodes._dir / f"{recent.isoformat()}.md").exists()


class TestEnsureDirectory:
    def test_creates_dir(self, episodes: EpisodicMemory) -> None:
        assert not episodes.directory.exists()
        episodes.ensure_directory()
        assert episodes.directory.exists()
