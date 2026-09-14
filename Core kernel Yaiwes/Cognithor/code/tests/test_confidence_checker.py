"""Tests for the pre-execution confidence checker."""

from __future__ import annotations

from cognithor.core.confidence import (
    PROCEED_THRESHOLD,
    ConfidenceChecker,
    ConfidenceResult,
)


class FakeReflexionEntry:
    """Minimal reflexion entry for testing."""

    def __init__(self, tool_name: str, recurrence_count: int = 1) -> None:
        self.tool_name = tool_name
        self.recurrence_count = recurrence_count
        self.prevention_rule = "Check parameters before calling"
        self.status = "pending"


class FakeReflexionMemory:
    """Fake reflexion memory for testing confidence checker."""

    def __init__(
        self,
        rules: list[str] | None = None,
        recurring: list[FakeReflexionEntry] | None = None,
    ) -> None:
        self._rules = rules or []
        self._recurring = recurring or []

    def get_prevention_rules(self, tool_name: str | None = None) -> list[str]:
        return self._rules

    def get_recurring_errors(self, min_count: int = 3) -> list[FakeReflexionEntry]:
        return [e for e in self._recurring if e.recurrence_count >= min_count]


# --- Basic functionality ---


def test_assess_returns_confidence_result():
    checker = ConfidenceChecker()
    result = checker.assess("erstelle eine Datei test.txt", "write_file")
    assert isinstance(result, ConfidenceResult)
    assert 0.0 <= result.score <= 1.0
    assert 0.0 <= result.clarity_score <= 1.0
    assert 0.0 <= result.mistake_score <= 1.0
    assert 0.0 <= result.context_score <= 1.0


def test_empty_message_low_clarity():
    checker = ConfidenceChecker()
    result = checker.assess("", "write_file")
    assert result.clarity_score == 0.0


def test_specific_message_high_clarity():
    checker = ConfidenceChecker()
    result = checker.assess(
        "erstelle die Datei C:\\Users\\test\\projekt\\main.py mit Hello World",
        "write_file",
    )
    assert result.clarity_score >= 0.7


def test_vague_message_lower_clarity():
    checker = ConfidenceChecker()
    result = checker.assess(
        "vielleicht irgendwas irgendwie machen",
        "exec_command",
    )
    assert result.clarity_score < 0.5


# --- Threshold classification ---


def test_high_score_should_proceed():
    checker = ConfidenceChecker()
    result = checker.assess(
        "lies die Datei /home/user/config.yaml und zeige den Inhalt",
        "read_file",
        context={"memory_results": True, "user_preferences": True, "recent_episodes": True},
    )
    assert result.should_proceed is True
    assert result.should_block is False
    assert result.should_warn is False


def test_low_score_should_block():
    checker = ConfidenceChecker()
    # Empty message + no context = very low score
    result = checker.assess("", "write_file")
    assert result.should_block is True
    assert result.should_proceed is False


def test_medium_score_should_warn():
    checker = ConfidenceChecker()
    # Somewhat vague but not empty
    result = checker.assess("mach was", "exec_command")
    # With no context, score should be in warn range
    assert result.score < PROCEED_THRESHOLD


# --- Reflexion memory integration ---


def test_no_reflexion_memory_full_mistake_score():
    checker = ConfidenceChecker(reflexion_memory=None)
    result = checker.assess("test message", "read_file")
    assert result.mistake_score == 1.0


def test_reflexion_with_rules_but_no_recurring():
    memory = FakeReflexionMemory(rules=["Always check path exists"])
    checker = ConfidenceChecker(reflexion_memory=memory)
    result = checker.assess("read file", "read_file")
    assert result.mistake_score == 0.8


def test_reflexion_with_high_recurrence():
    entry = FakeReflexionEntry("exec_command", recurrence_count=10)
    memory = FakeReflexionMemory(
        rules=["Check command syntax"],
        recurring=[entry],
    )
    checker = ConfidenceChecker(reflexion_memory=memory)
    result = checker.assess("run something", "exec_command")
    assert result.mistake_score <= 0.2


def test_reflexion_with_moderate_recurrence():
    entry = FakeReflexionEntry("web_search", recurrence_count=4)
    memory = FakeReflexionMemory(
        rules=["Rate limit searches"],
        recurring=[entry],
    )
    checker = ConfidenceChecker(reflexion_memory=memory)
    result = checker.assess("search for news", "web_search")
    assert 0.3 <= result.mistake_score <= 0.7


# --- Context readiness ---


def test_no_context_low_readiness():
    checker = ConfidenceChecker()
    result = checker.assess("test", "read_file", context=None)
    assert result.context_score == 0.3


def test_full_context_high_readiness():
    checker = ConfidenceChecker()
    result = checker.assess(
        "test",
        "read_file",
        context={
            "memory_results": ["some memory"],
            "user_preferences": {"lang": "de"},
            "recent_episodes": ["episode1"],
            "vault_snippets": ["secret"],
        },
    )
    assert result.context_score == 1.0


def test_partial_context_medium_readiness():
    checker = ConfidenceChecker()
    result = checker.assess(
        "test",
        "read_file",
        context={"memory_results": ["some memory"]},
    )
    assert 0.4 <= result.context_score <= 0.6


# --- Blockers and recommendations ---


def test_blockers_populated_on_low_scores():
    checker = ConfidenceChecker()
    result = checker.assess("", "write_file")
    assert len(result.blockers) > 0
    assert any("specificity" in b.lower() or "context" in b.lower() for b in result.blockers)


def test_recommendations_populated_on_low_scores():
    checker = ConfidenceChecker()
    result = checker.assess("", "write_file")
    assert len(result.recommendations) > 0


# --- Tool-specific clarity ---


def test_path_tool_bonus_for_paths():
    checker = ConfidenceChecker()
    result_with = checker.assess("read /etc/hosts", "read_file")
    result_without = checker.assess("read something", "read_file")
    assert result_with.clarity_score > result_without.clarity_score


def test_search_tool_bonus_for_longer_query():
    checker = ConfidenceChecker()
    result_long = checker.assess("search for python asyncio patterns", "web_search")
    result_short = checker.assess("search", "web_search")
    assert result_long.clarity_score > result_short.clarity_score


def test_command_tool_bonus_for_tech_terms():
    checker = ConfidenceChecker()
    result_tech = checker.assess("run pip install requests", "exec_command")
    result_vague = checker.assess("run something", "exec_command")
    assert result_tech.clarity_score > result_vague.clarity_score


# --- Score composition ---


def test_score_is_weighted_composite():
    """Verify that score = clarity*0.5 + mistakes*0.3 + context*0.2."""
    checker = ConfidenceChecker()
    result = checker.assess(
        "erstelle die Datei test.py",
        "write_file",
        context={"memory_results": True},
    )
    expected = result.clarity_score * 0.5 + result.mistake_score * 0.3 + result.context_score * 0.2
    assert abs(result.score - round(expected, 3)) < 0.01
