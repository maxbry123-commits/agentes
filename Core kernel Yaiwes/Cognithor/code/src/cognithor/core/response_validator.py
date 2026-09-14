"""Four Questions anti-hallucination validator for responses.

Validates LLM responses before delivery to the user by checking:
1. Tool result consistency (no contradictions)
2. Requirement coverage (user intent addressed)
3. Assumption detection ("probably", "likely", "should work")
4. Evidence basis (references actual tool outputs)

Inspired by SuperClaude's anti-hallucination validation pattern.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

PASS_THRESHOLD = 0.7


@dataclass
class ValidationResult:
    """Result of the four-question response validation."""

    score: float  # 0.0-1.0 average of 4 checks
    passed: bool  # score >= PASS_THRESHOLD
    consistency_score: float  # 0.0-1.0
    coverage_score: float  # 0.0-1.0
    assumption_score: float  # 0.0-1.0 (high = few assumptions = good)
    evidence_score: float  # 0.0-1.0
    issues: list[str] = field(default_factory=list)


# --- Assumption language patterns ---

ASSUMPTION_WORDS: list[str] = [
    "probably",
    "likely",
    "should work",
    "I think",
    "I believe",
    "might",
    "perhaps",
    "assume",
    "guess",
    "wahrscheinlich",
    "vermutlich",
    "denke ich",
    "glaube ich",
    "moeglicherweise",
    "eventuell",
    "koennte sein",
    "sollte funktionieren",
    "nehme an",
    "schaetze",
]

# Pre-compiled pattern for assumption detection (case insensitive)
_ASSUMPTION_PATTERN = re.compile(
    "|".join(re.escape(w) for w in ASSUMPTION_WORDS),
    re.IGNORECASE,
)

# Contradiction indicators between tool results
_CONTRADICTION_PATTERNS: list[tuple[re.Pattern[str], re.Pattern[str]]] = [
    (re.compile(r"\bnot found\b", re.IGNORECASE), re.compile(r"\bfound\b", re.IGNORECASE)),
    (re.compile(r"\bfailed\b", re.IGNORECASE), re.compile(r"\bsuccess", re.IGNORECASE)),
    (re.compile(r"\berror\b", re.IGNORECASE), re.compile(r"\bcompleted?\b", re.IGNORECASE)),
    (re.compile(r"\bno results\b", re.IGNORECASE), re.compile(r"\d+ results?\b", re.IGNORECASE)),
]

# Stopwords to exclude from coverage matching
_STOPWORDS = frozenset(
    {
        "der",
        "die",
        "das",
        "ein",
        "eine",
        "und",
        "oder",
        "ist",
        "sind",
        "was",
        "wie",
        "wo",
        "wer",
        "wenn",
        "dann",
        "the",
        "a",
        "an",
        "is",
        "are",
        "what",
        "how",
        "where",
        "who",
        "when",
        "then",
        "can",
        "you",
        "me",
        "my",
        "du",
        "mir",
        "mein",
        "bitte",
        "please",
        "ich",
        "kannst",
        "mit",
        "von",
        "fuer",
        "for",
        "with",
        "from",
        "to",
        "in",
        "on",
        "at",
    }
)


class ResponseValidator:
    """Four Questions anti-hallucination validator.

    Validates every LLM response against four criteria before
    it reaches the user. Does not block delivery, only annotates.
    """

    def validate(
        self,
        response: str,
        user_message: str,
        tool_results: list[Any] | None = None,
    ) -> ValidationResult:
        """Run all four validation checks on a response.

        Args:
            response: The LLM-generated response text.
            user_message: The user's original message.
            tool_results: List of ToolResult objects (or dicts with
                         'tool_name', 'content', 'success' keys).

        Returns:
            ValidationResult with per-check scores and issues.
        """
        consistency = self._check_consistency(response, tool_results)
        coverage = self._check_coverage(response, user_message)
        assumptions = self._check_assumptions(response)
        evidence = self._check_evidence(response, tool_results)

        score = (consistency + coverage + assumptions + evidence) / 4.0
        score = round(max(0.0, min(1.0, score)), 3)

        issues: list[str] = []
        if consistency < 0.5:
            issues.append("Response may contradict tool results")
        if coverage < 0.5:
            issues.append("Response does not address key terms from user message")
        if assumptions < 0.5:
            issues.append("Response contains excessive assumption language")
        if evidence < 0.5:
            issues.append("Response lacks references to actual tool outputs")

        result = ValidationResult(
            score=score,
            passed=score >= PASS_THRESHOLD,
            consistency_score=round(consistency, 3),
            coverage_score=round(coverage, 3),
            assumption_score=round(assumptions, 3),
            evidence_score=round(evidence, 3),
            issues=issues,
        )

        log.debug(
            "response_validated",
            score=result.score,
            passed=result.passed,
            consistency=result.consistency_score,
            coverage=result.coverage_score,
            assumptions=result.assumption_score,
            evidence=result.evidence_score,
            issue_count=len(issues),
        )

        return result

    def _check_consistency(
        self,
        response: str,
        tool_results: list[Any] | None,
    ) -> float:
        """Check tool results don't contradict each other or the response.

        Returns 1.0 if no tool results (nothing to contradict).
        Checks for opposing signals (failed vs success, not found vs found).
        """
        if not tool_results:
            return 1.0

        # Extract content from tool results
        contents: list[str] = []
        for tr in tool_results:
            content = getattr(tr, "content", None) or (
                tr.get("content") if isinstance(tr, dict) else None
            )
            if content:
                contents.append(str(content))

        if not contents:
            return 1.0

        combined = " ".join(contents)
        contradiction_count = 0

        for pat_a, pat_b in _CONTRADICTION_PATTERNS:
            a_in_results = pat_a.search(combined)
            b_in_results = pat_b.search(combined)
            # Both opposing signals present in tool results
            if a_in_results and b_in_results:
                contradiction_count += 1

        # Check if response contradicts tool results
        for tr in tool_results:
            success = getattr(tr, "success", None)
            if success is None and isinstance(tr, dict):
                success = tr.get("success")
            content = getattr(tr, "content", None) or (
                tr.get("content", "") if isinstance(tr, dict) else ""
            )

            if success is False and content:
                # Tool failed but response claims success
                tool_name = getattr(tr, "tool_name", None) or (
                    tr.get("tool_name", "") if isinstance(tr, dict) else ""
                )
                if tool_name and re.search(
                    rf"\b(erfolgreich|successfully|done|erledigt)\b.*{re.escape(tool_name)}",
                    response,
                    re.IGNORECASE,
                ):
                    contradiction_count += 1

        if contradiction_count == 0:
            return 1.0
        if contradiction_count == 1:
            return 0.6
        if contradiction_count == 2:
            return 0.3
        return 0.1

    def _check_coverage(self, response: str, user_message: str) -> float:
        """Check response addresses user's key terms.

        Extracts significant words from the user message and checks
        how many appear in the response.
        """
        if not user_message.strip() or not response.strip():
            return 0.5

        # Extract key terms (non-stopword tokens of length >= 3)
        words = re.findall(r"\b\w{3,}\b", user_message.lower())
        key_terms = [w for w in words if w not in _STOPWORDS]

        if not key_terms:
            return 0.8  # No key terms to check = assume OK

        response_lower = response.lower()
        matched = sum(1 for term in key_terms if term in response_lower)
        coverage_ratio = matched / len(key_terms)

        # Be generous: 60% coverage is "full marks"
        if coverage_ratio >= 0.6:
            return 1.0
        if coverage_ratio >= 0.4:
            return 0.8
        if coverage_ratio >= 0.2:
            return 0.6
        if coverage_ratio > 0:
            return 0.4
        return 0.2

    def _check_assumptions(self, response: str) -> float:
        """Detect unverified assumption language.

        Returns high score (good) when few assumptions are present.
        """
        if not response.strip():
            return 1.0

        matches = _ASSUMPTION_PATTERN.findall(response)
        assumption_count = len(matches)

        # Normalize by response length (longer responses may naturally have more)
        word_count = max(1, len(response.split()))
        density = assumption_count / word_count

        if assumption_count == 0:
            return 1.0
        if density < 0.01:
            return 0.9  # Very low density
        if density < 0.02:
            return 0.7
        if density < 0.05:
            return 0.5
        return 0.3

    def _check_evidence(
        self,
        response: str,
        tool_results: list[Any] | None,
    ) -> float:
        """Check response references actual tool outputs.

        Looks for fragments from tool result content appearing in the response.
        Returns 1.0 if no tool results (pure conversation).
        """
        if not tool_results:
            return 1.0

        if not response.strip():
            return 0.0

        # Extract significant fragments from tool results
        fragments: list[str] = []
        for tr in tool_results:
            content = getattr(tr, "content", None) or (
                tr.get("content") if isinstance(tr, dict) else None
            )
            success = getattr(tr, "success", None)
            if success is None and isinstance(tr, dict):
                success = tr.get("success")

            if not content or not success:
                continue

            content_str = str(content)
            # Extract word sequences of 3+ words as evidence fragments
            words = content_str.split()
            for i in range(0, len(words) - 2, 3):
                fragment = " ".join(words[i : i + 3]).lower()
                if len(fragment) >= 10:  # Skip very short fragments
                    fragments.append(fragment)

        if not fragments:
            return 0.8  # No usable fragments = mild pass

        # Check how many fragments appear in the response
        response_lower = response.lower()
        matched = sum(1 for f in fragments[:30] if f in response_lower)  # Cap at 30

        ratio = matched / min(len(fragments), 30)
        if ratio >= 0.3:
            return 1.0
        if ratio >= 0.15:
            return 0.8
        if ratio >= 0.05:
            return 0.6
        if ratio > 0:
            return 0.4
        return 0.2
