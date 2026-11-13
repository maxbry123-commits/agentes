from __future__ import annotations

from cognithor.memory.cag.selectors import CAGSelector


class TestCAGSelector:
    def test_core_memory_selected(self):
        text = " ".join(["word"] * 60)
        result = CAGSelector().select(text)
        assert len(result) == 1
        assert result[0]["cache_id"] == "core_memory"

    def test_empty_skipped(self):
        assert CAGSelector().select("") == []
        assert CAGSelector().select("   ") == []

    def test_short_skipped(self):
        text = " ".join(["word"] * 30)
        assert CAGSelector().select(text) == []

    def test_returns_correct_format(self):
        text = " ".join(["token"] * 100)
        result = CAGSelector().select(text)
        entry = result[0]
        assert entry["cache_id"] == "core_memory"
        assert entry["content"] == text
        assert entry["source_tier"] == "core"
        assert entry["priority"] == 1
