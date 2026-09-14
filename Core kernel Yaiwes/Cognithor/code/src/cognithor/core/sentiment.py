"""Lightweight keyword/regex-based sentiment detection for German text.

No ML model, no new dependencies. Detects frustration, urgency,
confusion, and positive sentiment from user messages.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import NamedTuple


class Sentiment(StrEnum):
    """Detected sentiment categories."""

    FRUSTRATED = "frustrated"
    URGENT = "urgent"
    POSITIVE = "positive"
    CONFUSED = "confused"
    NEUTRAL = "neutral"


class SentimentResult(NamedTuple):
    """Result of sentiment detection."""

    sentiment: Sentiment
    confidence: float  # 0.0 -- 1.0
    trigger_phrase: str  # The phrase that triggered the detection


# ── Pattern definitions ──────────────────────────────────────────

_FRUSTRATED_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"funktioniert\s+(?:immer\s+)?nicht", re.I), 0.9),
    (re.compile(r"geht\s+(?:immer\s+)?nicht", re.I), 0.85),
    (re.compile(r"schon\s+wieder", re.I), 0.85),
    (re.compile(r"zum\s+(\w+\s+)?mal", re.I), 0.7),
    (re.compile(r"nervt|nervig", re.I), 0.9),
    (re.compile(r"frustriert|frustrier", re.I), 0.95),
    (re.compile(r"ärger|ärgert|ärgerlich", re.I), 0.9),
    (re.compile(r"klappt\s+(?:einfach\s+)?nicht", re.I), 0.85),
    (re.compile(r"warum\s+(?:geht|klappt|funktioniert)\s+das\s+nicht", re.I), 0.9),
    (re.compile(r"immer\s+noch\s+(?:nicht|kaputt|fehler)", re.I), 0.9),
    (re.compile(r"habe\s+(?:es\s+)?schon\s+(?:\d+\s+)?mal\s+(?:versucht|probiert)", re.I), 0.85),
    (re.compile(r"!!+", re.I), 0.6),
    (re.compile(r"mist|verdammt|scheiße|shit|damn", re.I), 0.9),
]

_URGENT_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"dringend|eilig|sofort|asap|schnell", re.I), 0.9),
    (re.compile(r"so\s+schnell\s+wie\s+möglich", re.I), 0.95),
    (re.compile(r"deadline|frist", re.I), 0.8),
    (re.compile(r"muss\s+(?:jetzt|sofort|heute|gleich)", re.I), 0.9),
    (re.compile(r"zeitkritisch|zeitdruck", re.I), 0.9),
    (re.compile(r"brauch(?:e)?\s+(?:das\s+)?(?:jetzt|sofort|schnell|gleich)", re.I), 0.85),
    (re.compile(r"notfall|emergency", re.I), 0.95),
]

_CONFUSED_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"verstehe?\s+(?:\w+\s+)?nicht", re.I), 0.9),
    (re.compile(r"(?:was|wie)\s+meinst\s+du", re.I), 0.8),
    (re.compile(r"bin\s+verwirrt|kapier.?\s+(?:ich\s+)?nicht", re.I), 0.9),
    (re.compile(r"(?:kannst|könntest)\s+du\s+(?:das\s+)?(?:nochmal\s+)?erklär", re.I), 0.8),
    (re.compile(r"hä\??|häh\??|huh\??", re.I), 0.7),
    (re.compile(r"was\s+(?:soll|heißt|bedeutet)\s+das", re.I), 0.8),
    (re.compile(r"wie\s+(?:geht|mach|funktioniert)\s+das", re.I), 0.6),
    (re.compile(r"ich\s+(?:weiß|weiss)\s+nicht\s+(?:wie|was|ob)", re.I), 0.75),
]

_POSITIVE_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"danke|dankeschön|vielen\s+dank", re.I), 0.9),
    (re.compile(r"super|toll|klasse|genial|perfekt|prima|wunderbar|ausgezeichnet", re.I), 0.85),
    (re.compile(r"hat\s+(?:super\s+)?(?:gut\s+)?geklappt|funktioniert", re.I), 0.85),
    (re.compile(r"top|great|awesome|nice|cool", re.I), 0.7),
    (re.compile(r"freut\s+mich|freue\s+mich", re.I), 0.8),
    (re.compile(r"gut\s+gemacht|gute\s+arbeit", re.I), 0.9),
]


def detect_sentiment(text: str) -> SentimentResult:
    """Detects the sentiment of a German text message.

    Checks patterns in priority order: frustrated > urgent > confused > positive > neutral.
    Returns the first match with highest confidence.

    Args:
        text: User message text.

    Returns:
        SentimentResult with sentiment, confidence, and trigger phrase.
    """
    if not text or not text.strip():
        return SentimentResult(Sentiment.NEUTRAL, 0.0, "")

    # Check each category in priority order
    best: SentimentResult | None = None

    for patterns, sentiment in [
        (_FRUSTRATED_PATTERNS, Sentiment.FRUSTRATED),
        (_URGENT_PATTERNS, Sentiment.URGENT),
        (_CONFUSED_PATTERNS, Sentiment.CONFUSED),
        (_POSITIVE_PATTERNS, Sentiment.POSITIVE),
    ]:
        for pattern, confidence in patterns:
            match = pattern.search(text)
            if match:
                candidate = SentimentResult(sentiment, confidence, match.group(0))
                if best is None or candidate.confidence > best.confidence:
                    best = candidate
                break  # Take first match per category, then compare across categories

    if best is not None:
        return best

    return SentimentResult(Sentiment.NEUTRAL, 0.5, "")


# ── Sentiment → System Message ──────────────────────────────────

_SENTIMENT_SYSTEM_MESSAGES: dict[Sentiment, str] = {
    Sentiment.FRUSTRATED: (
        "Der User ist gerade frustriert. Nimm das ernst, "
        "sei geduldig und hilf konkret. Nicht belehren."
    ),
    Sentiment.URGENT: (
        "Der User hat es eilig. Komm direkt zum Punkt, kurze Antwort, schnelle Loesung."
    ),
    Sentiment.CONFUSED: (
        "Der User ist unsicher. Erklaere es einfach und klar, "
        "mit einem konkreten Beispiel. Frag ob es verstaendlich war."
    ),
    Sentiment.POSITIVE: ("Der User ist gut drauf. Teile die Stimmung!"),
}


def get_sentiment_system_message(sentiment: Sentiment) -> str | None:
    """Returns a system message for the given sentiment, or None for NEUTRAL."""
    return _SENTIMENT_SYSTEM_MESSAGES.get(sentiment)
