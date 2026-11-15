"""Tests für die Sentiment-Erkennung.

Testet:
  - Frustration-Patterns (deutsch)
  - Urgency-Patterns
  - Confusion-Patterns
  - Positive-Patterns
  - Neutral fallback
  - Edge cases (leere Strings, gemischte Sentiments)
  - System-Message-Generierung
"""

from __future__ import annotations

import pytest

from cognithor.core.sentiment import (
    Sentiment,
    SentimentResult,
    detect_sentiment,
    get_sentiment_system_message,
)


class TestFrustratedPatterns:
    """Tests für Frustrations-Erkennung."""

    @pytest.mark.parametrize(
        "text",
        [
            "Das funktioniert nicht!",
            "Es geht schon wieder nicht",
            "Das klappt einfach nicht",
            "Warum geht das nicht?",
            "Das nervt mich total",
            "Ich bin frustriert",
            "Immer noch nicht gefixt",
            "Ich habe es schon 5 mal versucht",
            "Verdammt, schon wieder!",
            "Warum funktioniert das nicht???!!!",
        ],
    )
    def test_frustrated_detected(self, text: str) -> None:
        result = detect_sentiment(text)
        assert result.sentiment == Sentiment.FRUSTRATED
        assert result.confidence > 0.5
        assert result.trigger_phrase != ""

    def test_frustrated_exclamation_marks(self) -> None:
        result = detect_sentiment("Das kann doch nicht wahr sein!!!")
        assert result.sentiment == Sentiment.FRUSTRATED


class TestUrgentPatterns:
    """Tests für Dringlichkeits-Erkennung."""

    @pytest.mark.parametrize(
        "text",
        [
            "Das ist dringend",
            "Ich brauche das sofort",
            "So schnell wie möglich bitte",
            "Muss jetzt erledigt werden",
            "Zeitkritisch!",
            "Das ist ein Notfall",
            "Brauche das jetzt schnell",
        ],
    )
    def test_urgent_detected(self, text: str) -> None:
        result = detect_sentiment(text)
        assert result.sentiment == Sentiment.URGENT
        assert result.confidence > 0.5


class TestConfusedPatterns:
    """Tests für Verwirrung-Erkennung."""

    @pytest.mark.parametrize(
        "text",
        [
            "Ich verstehe das nicht",
            "Was meinst du damit?",
            "Ich bin verwirrt",
            "Kannst du das nochmal erklären?",
            "Hä?",
            "Was soll das heißen?",
            "Ich weiß nicht wie das geht",
        ],
    )
    def test_confused_detected(self, text: str) -> None:
        result = detect_sentiment(text)
        assert result.sentiment == Sentiment.CONFUSED
        assert result.confidence > 0.5


class TestPositivePatterns:
    """Tests für Positive-Erkennung."""

    @pytest.mark.parametrize(
        "text",
        [
            "Danke!",
            "Super gemacht!",
            "Das hat geklappt!",
            "Perfekt, genau so!",
            "Cool, danke dir!",
            "Vielen Dank für die Hilfe",
            "Gut gemacht!",
        ],
    )
    def test_positive_detected(self, text: str) -> None:
        result = detect_sentiment(text)
        assert result.sentiment == Sentiment.POSITIVE
        assert result.confidence > 0.5


class TestNeutral:
    """Tests für neutrale Nachrichten."""

    @pytest.mark.parametrize(
        "text",
        [
            "Erstelle eine Datei",
            "Wie ist das Wetter?",
            "Suche nach Python-Tutorials",
            "Was ist eine API?",
            "Öffne die Einstellungen",
        ],
    )
    def test_neutral_detected(self, text: str) -> None:
        result = detect_sentiment(text)
        assert result.sentiment == Sentiment.NEUTRAL


class TestEdgeCases:
    """Tests für Edge-Cases."""

    def test_empty_string(self) -> None:
        result = detect_sentiment("")
        assert result.sentiment == Sentiment.NEUTRAL
        assert result.confidence == 0.0

    def test_whitespace_only(self) -> None:
        result = detect_sentiment("   ")
        assert result.sentiment == Sentiment.NEUTRAL

    def test_result_is_named_tuple(self) -> None:
        result = detect_sentiment("Danke!")
        assert isinstance(result, SentimentResult)
        assert hasattr(result, "sentiment")
        assert hasattr(result, "confidence")
        assert hasattr(result, "trigger_phrase")

    def test_confidence_range(self) -> None:
        for text in ["Das funktioniert nicht", "Dringend!", "Danke", "Hä?"]:
            result = detect_sentiment(text)
            assert 0.0 <= result.confidence <= 1.0


class TestSentimentSystemMessage:
    """Tests für System-Message-Generierung."""

    def test_frustrated_message(self) -> None:
        msg = get_sentiment_system_message(Sentiment.FRUSTRATED)
        assert msg is not None
        assert "geduldig" in msg

    def test_urgent_message(self) -> None:
        msg = get_sentiment_system_message(Sentiment.URGENT)
        assert msg is not None
        assert "prägnant" in msg or "direkt" in msg

    def test_confused_message(self) -> None:
        msg = get_sentiment_system_message(Sentiment.CONFUSED)
        assert msg is not None
        assert "klar" in msg or "schrittweise" in msg

    def test_positive_message(self) -> None:
        msg = get_sentiment_system_message(Sentiment.POSITIVE)
        assert msg is not None

    def test_neutral_no_message(self) -> None:
        msg = get_sentiment_system_message(Sentiment.NEUTRAL)
        assert msg is None
