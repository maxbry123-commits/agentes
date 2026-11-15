"""Extended tests for CausalAnalyzer -- missing lines coverage.

Targets:
  - get_model_performance with data and empty
  - close() idempotent
  - record_sequence with model_used
  - suggest_tools fallback path
"""

from __future__ import annotations

from cognithor.learning.causal import CausalAnalyzer


class TestModelPerformance:
    def setup_method(self) -> None:
        self.analyzer = CausalAnalyzer()

    def teardown_method(self) -> None:
        self.analyzer.close()

    def test_empty_returns_empty(self) -> None:
        result = self.analyzer.get_model_performance()
        assert result == {}

    def test_below_min_records_excluded(self) -> None:
        for i in range(3):
            self.analyzer.record_sequence(f"s{i}", ["a", "b"], 0.8, model_used="gpt-4")
        # Default min_records=5, only 3 recorded
        result = self.analyzer.get_model_performance()
        assert result == {}

    def test_with_enough_records(self) -> None:
        for i in range(6):
            self.analyzer.record_sequence(f"s{i}", ["a", "b"], 0.8, model_used="gpt-4")
        result = self.analyzer.get_model_performance(min_records=5)
        assert "gpt-4" in result
        assert result["gpt-4"]["count"] == 6
        assert abs(result["gpt-4"]["avg_score"] - 0.8) < 0.01

    def test_multiple_models(self) -> None:
        for i in range(5):
            self.analyzer.record_sequence(f"g{i}", ["a", "b"], 0.9, model_used="gpt-4")
        for i in range(5):
            self.analyzer.record_sequence(f"c{i}", ["a", "b"], 0.7, model_used="claude")
        result = self.analyzer.get_model_performance(min_records=5)
        assert "gpt-4" in result
        assert "claude" in result
        assert result["gpt-4"]["avg_score"] > result["claude"]["avg_score"]

    def test_empty_model_excluded(self) -> None:
        """Records with model_used='' should not appear in results."""
        for i in range(10):
            self.analyzer.record_sequence(f"s{i}", ["a", "b"], 0.8, model_used="")
        result = self.analyzer.get_model_performance(min_records=5)
        assert result == {}


class TestCloseIdempotent:
    def test_close_twice(self) -> None:
        analyzer = CausalAnalyzer()
        analyzer.record_sequence("s1", ["a", "b"], 0.8)
        analyzer.close()
        analyzer.close()  # Should not crash

    def test_close_none_conn(self) -> None:
        analyzer = CausalAnalyzer()
        analyzer._conn = None
        analyzer.close()  # Should not crash


class TestSuggestToolsFallback:
    def setup_method(self) -> None:
        self.analyzer = CausalAnalyzer()

    def teardown_method(self) -> None:
        self.analyzer.close()

    def test_fallback_last_tool_used(self) -> None:
        """When full sequence doesn't match, should fallback to last tool matching."""
        for i in range(10):
            self.analyzer.record_sequence(f"s{i}", ["search", "analyze", "summarize"], 0.9)
        # Query with sequence that doesn't match as whole but last tool matches
        suggestions = self.analyzer.suggest_tools(["random_tool", "analyze"])
        assert len(suggestions) > 0

    def test_suggest_with_low_score_sequences_excluded(self) -> None:
        """Sequences with score < 0.5 should not be used for suggestions."""
        for i in range(10):
            self.analyzer.record_sequence(
                f"s{i}",
                ["a", "b", "c"],
                0.3,  # Low score
            )
        suggestions = self.analyzer.suggest_tools(["a", "b"])
        assert suggestions == []
