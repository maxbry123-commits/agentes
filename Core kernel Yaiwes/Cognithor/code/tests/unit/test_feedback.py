"""Tests for the FeedbackStore (thumbs up/down feedback system)."""

import pytest


class TestFeedbackStore:
    @pytest.fixture
    def store(self, tmp_path):
        from cognithor.core.feedback import FeedbackStore

        return FeedbackStore(db_path=tmp_path / "feedback.db")

    def test_submit_thumbs_up(self, store):
        fb_id = store.submit("sess1", "msg1", 1)
        assert fb_id.startswith("fb_")

    def test_submit_thumbs_down(self, store):
        fb_id = store.submit("sess1", "msg1", -1, comment="Too verbose")
        assert fb_id.startswith("fb_")

    def test_add_comment(self, store):
        fb_id = store.submit("sess1", "msg1", -1)
        ok = store.add_comment(fb_id, "Should be shorter")
        assert ok is True

    def test_add_comment_nonexistent(self, store):
        ok = store.add_comment("fb_nonexistent", "test")
        assert ok is False

    def test_stats(self, store):
        store.submit("s1", "m1", 1)
        store.submit("s1", "m2", 1)
        store.submit("s1", "m3", -1)
        stats = store.get_stats()
        assert stats["total"] == 3
        assert stats["positive"] == 2
        assert stats["negative"] == 1
        assert stats["satisfaction_rate"] == 66.7

    def test_stats_empty(self, store):
        stats = store.get_stats()
        assert stats["total"] == 0
        assert stats["satisfaction_rate"] == 0

    def test_stats_by_agent(self, store):
        store.submit("s1", "m1", 1, agent_name="jarvis")
        store.submit("s1", "m2", -1, agent_name="coder")
        stats = store.get_stats(agent_name="jarvis")
        assert stats["total"] == 1
        assert stats["positive"] == 1

    def test_get_negative_feedback(self, store):
        store.submit("s1", "m1", 1)
        store.submit("s1", "m2", -1, comment="Bad")
        store.submit("s1", "m3", -1, comment="Wrong")
        negatives = store.get_negative_feedback()
        assert len(negatives) == 2
        assert all(n["rating"] == -1 for n in negatives)

    def test_get_negative_feedback_by_agent(self, store):
        store.submit("s1", "m1", -1, agent_name="jarvis")
        store.submit("s1", "m2", -1, agent_name="coder")
        negatives = store.get_negative_feedback(agent_name="jarvis")
        assert len(negatives) == 1

    def test_get_recent(self, store):
        for i in range(5):
            store.submit(f"s{i}", f"m{i}", 1 if i % 2 == 0 else -1)
        recent = store.get_recent(limit=3)
        assert len(recent) == 3

    def test_get_recent_empty(self, store):
        recent = store.get_recent()
        assert recent == []

    def test_submit_truncates_long_text(self, store):
        long_text = "x" * 5000
        fb_id = store.submit(
            "s1",
            "m1",
            1,
            user_message=long_text,
            assistant_response=long_text,
            tool_calls=long_text,
        )
        assert fb_id.startswith("fb_")
        # Verify it was stored (no crash)
        recent = store.get_recent(limit=1)
        assert len(recent) == 1
        assert len(recent[0]["user_message"]) == 2000
        assert len(recent[0]["assistant_response"]) == 2000
        assert len(recent[0]["tool_calls"]) == 1000

    def test_stats_with_comments(self, store):
        store.submit("s1", "m1", -1, comment="Bad response")
        store.submit("s1", "m2", -1)
        stats = store.get_stats()
        assert stats["with_comment"] == 1

    def test_unique_ids(self, store):
        ids = set()
        for i in range(20):
            fb_id = store.submit("s1", f"m{i}", 1)
            ids.add(fb_id)
        assert len(ids) == 20
