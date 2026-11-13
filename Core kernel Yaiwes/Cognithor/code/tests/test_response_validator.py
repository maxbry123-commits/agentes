"""Tests for the four-question response validator."""

from __future__ import annotations

from cognithor.core.response_validator import (
    PASS_THRESHOLD,
    ResponseValidator,
    ValidationResult,
)


class FakeToolResult:
    """Minimal tool result for testing."""

    def __init__(
        self,
        tool_name: str = "web_search",
        content: str = "Found 5 results about Python",
        success: bool = True,
    ) -> None:
        self.tool_name = tool_name
        self.content = content
        self.success = success


# --- Basic functionality ---


def test_validate_returns_validation_result():
    validator = ResponseValidator()
    result = validator.validate("Hier ist die Antwort.", "Was ist Python?")
    assert isinstance(result, ValidationResult)
    assert 0.0 <= result.score <= 1.0


def test_empty_response_low_evidence():
    validator = ResponseValidator()
    result = validator.validate(
        "",
        "test",
        tool_results=[FakeToolResult()],
    )
    assert result.evidence_score == 0.0


def test_no_tool_results_high_consistency():
    validator = ResponseValidator()
    result = validator.validate("Some answer", "Some question", tool_results=None)
    assert result.consistency_score == 1.0
    assert result.evidence_score == 1.0


# --- Consistency checks ---


def test_consistency_no_contradictions():
    validator = ResponseValidator()
    results = [
        FakeToolResult(content="Found 3 files matching the pattern"),
        FakeToolResult(content="All files are Python scripts"),
    ]
    result = validator.validate(
        "Ich habe 3 Python-Dateien gefunden.", "Finde Python Dateien", results
    )
    assert result.consistency_score >= 0.8


def test_consistency_with_contradictions():
    validator = ResponseValidator()
    results = [
        FakeToolResult(content="not found any matching files"),
        FakeToolResult(content="found 5 results in the directory"),
    ]
    result = validator.validate("test response", "find files", results)
    assert result.consistency_score < 1.0


def test_consistency_failed_tool_claimed_success():
    validator = ResponseValidator()
    results = [
        FakeToolResult(
            tool_name="write_file",
            content="Permission denied: /etc/hosts",
            success=False,
        ),
    ]
    result = validator.validate(
        "Ich habe die Datei erfolgreich write_file geschrieben.",
        "schreibe die Datei",
        results,
    )
    assert result.consistency_score < 1.0


# --- Coverage checks ---


def test_coverage_all_terms_present():
    validator = ResponseValidator()
    result = validator.validate(
        "Python ist eine Programmiersprache die fuer Webentwicklung geeignet ist.",
        "Was ist Python Programmiersprache?",
    )
    assert result.coverage_score >= 0.8


def test_coverage_no_terms_present():
    validator = ResponseValidator()
    result = validator.validate(
        "Das Wetter ist heute schoen.",
        "Wie installiere ich Docker auf Ubuntu?",
    )
    assert result.coverage_score < 0.6


def test_coverage_empty_message():
    validator = ResponseValidator()
    result = validator.validate("Some response", "")
    assert result.coverage_score == 0.5


def test_coverage_stopwords_excluded():
    validator = ResponseValidator()
    # Message with mostly stopwords
    result = validator.validate(
        "Hier ist die Antwort.",
        "was ist das und wie",
    )
    # "was", "ist", "das", "und", "wie" are all stopwords — should be generous
    assert result.coverage_score >= 0.5


# --- Assumption detection ---


def test_assumptions_clean_response():
    validator = ResponseValidator()
    result = validator.validate(
        "Python 3.12 wurde am 2. Oktober 2023 veroeffentlicht.",
        "Wann wurde Python 3.12 released?",
    )
    assert result.assumption_score >= 0.9


def test_assumptions_heavy_assumptions():
    validator = ResponseValidator()
    result = validator.validate(
        "Wahrscheinlich sollte das funktionieren. Ich denke ich glaube "
        "eventuell moeglicherweise vermutlich koennte sein dass es klappt.",
        "Funktioniert das?",
    )
    assert result.assumption_score < 0.5


def test_assumptions_single_assumption():
    validator = ResponseValidator()
    result = validator.validate(
        "Die Datei existiert und das Ergebnis sieht gut aus, "
        "basierend auf den Daten die ich gefunden habe. "
        "Der Server laeuft korrekt und die Konfiguration ist in Ordnung. "
        "Alles funktioniert einwandfrei, das System ist stabil und einsatzbereit. "
        "Ich vermute dass es keine Probleme geben wird.",
        "Funktioniert der Server?",
    )
    # Single assumption ("vermute") in longer text should be mild
    assert result.assumption_score >= 0.7


def test_assumptions_empty_response():
    validator = ResponseValidator()
    result = validator.validate("", "test")
    assert result.assumption_score == 1.0


# --- Evidence checks ---


def test_evidence_references_tool_output():
    validator = ResponseValidator()
    results = [
        FakeToolResult(
            content="Python 3.12 was released on October 2 2023 with many improvements",
        ),
    ]
    result = validator.validate(
        "Python 3.12 was released on October 2 2023 with many improvements to the language.",
        "When was Python 3.12 released?",
        results,
    )
    assert result.evidence_score >= 0.6


def test_evidence_no_references():
    validator = ResponseValidator()
    results = [
        FakeToolResult(
            content="The database contains 500 records with customer data from 2024",
        ),
    ]
    result = validator.validate(
        "Alles ist in Ordnung, keine Probleme gefunden.",
        "Pruefe die Datenbank",
        results,
    )
    assert result.evidence_score < 0.8


def test_evidence_failed_tools_excluded():
    validator = ResponseValidator()
    results = [
        FakeToolResult(content="Error: connection refused", success=False),
    ]
    result = validator.validate("Some response", "test", results)
    # Failed tool results should not count as expected evidence
    assert result.evidence_score >= 0.5


# --- Pass/fail ---


def test_high_quality_response_passes():
    validator = ResponseValidator()
    results = [
        FakeToolResult(
            content=(
                "Python 3.12 final release date was October 2 2023"
                " according to the official schedule"
            ),
        ),
    ]
    result = validator.validate(
        "Python 3.12 final release date was October 2 2023. "
        "Das offizielle Release-Datum war der 2. Oktober 2023.",
        "Wann wurde Python 3.12 released?",
        results,
    )
    assert result.passed is True
    assert result.score >= PASS_THRESHOLD


def test_low_quality_response_fails():
    validator = ResponseValidator()
    results = [
        FakeToolResult(
            content="The server returned status 200 with 15 records",
        ),
    ]
    result = validator.validate(
        "Wahrscheinlich vermutlich eventuell irgendwas.",
        "Wie viele Datensaetze hat die Datenbank?",
        results,
    )
    assert result.passed is False


# --- Issues reporting ---


def test_issues_populated_for_low_scores():
    validator = ResponseValidator()
    results = [
        FakeToolResult(content="Error occurred: file not found", success=False),
    ]
    result = validator.validate(
        "Wahrscheinlich vermutlich koennte sein funktioniert eventuell.",
        "Pruefe den Server und die Datenbank und die API",
        results,
    )
    assert len(result.issues) > 0


def test_no_issues_for_high_quality():
    validator = ResponseValidator()
    result = validator.validate(
        "Die Antwort auf deine Frage ist klar und eindeutig.",
        "Was ist die Antwort auf meine Frage?",
    )
    # No tool results → consistency and evidence are 1.0
    # Coverage should be high, assumptions zero
    assert result.score >= 0.7


# --- Dict-based tool results ---


def test_dict_tool_results_work():
    validator = ResponseValidator()
    results = [
        {"tool_name": "web_search", "content": "Python is a programming language", "success": True},
    ]
    result = validator.validate(
        "Python is a programming language used worldwide.",
        "What is Python?",
        results,
    )
    assert isinstance(result, ValidationResult)
    assert result.consistency_score >= 0.5
