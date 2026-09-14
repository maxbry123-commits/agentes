"""Pre-execution confidence assessment for the Gatekeeper.

3-stage confidence check before tool execution:
1. Requirement Clarity (50%): Is the message specific enough?
2. Past Mistake Check (30%): Has this tool+context failed before?
3. Context Readiness (20%): Is sufficient context loaded?

Inspired by SuperClaude's confidence gating pattern.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.learning.reflexion import ReflexionMemory

log = get_logger(__name__)

# Threshold constants
PROCEED_THRESHOLD = 0.7
WARN_THRESHOLD = 0.4

# Weight constants
CLARITY_WEIGHT = 0.5
MISTAKE_WEIGHT = 0.3
CONTEXT_WEIGHT = 0.2


@dataclass
class ConfidenceResult:
    """Result of a pre-execution confidence assessment."""

    score: float  # 0.0-1.0 weighted composite
    should_proceed: bool  # score >= PROCEED_THRESHOLD
    should_warn: bool  # WARN_THRESHOLD <= score < PROCEED_THRESHOLD
    should_block: bool  # score < WARN_THRESHOLD
    clarity_score: float  # 0.0-1.0
    mistake_score: float  # 0.0-1.0
    context_score: float  # 0.0-1.0
    blockers: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


# --- Clarity analysis patterns ---

_ACTION_VERBS = re.compile(
    r"\b(erstell|schreib|loesch|such|find|lese|lies|oeffne|starte|stopp|install"
    r"|update|deploy|build|run|execute|create|write|delete|search|read|open"
    r"|start|stop|list|show|zeig|kopier|copy|move|verschieb|download"
    r"|upload|send|fetch|analyze|analysier)\b",
    re.IGNORECASE,
)

_TECHNICAL_SPECIFICITY = re.compile(
    r"(?:"
    r"[a-zA-Z]:\\[^\s]+"  # Windows paths
    r"|/[a-zA-Z0-9_./-]{3,}"  # Unix paths
    r"|https?://\S+"  # URLs
    r"|\b\w+\.\w{1,5}\b"  # file.ext
    r"|\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"  # IP addresses
    r"|`[^`]+`"  # inline code
    r"|\bport\s*\d+"  # port references
    r")",
    re.IGNORECASE,
)

_VAGUE_LANGUAGE = re.compile(
    r"\b(vielleicht|maybe|irgendwie|somehow|irgendwas|something"
    r"|versuche?|try|eventuell|perhaps|mal schauen|see if"
    r"|weiss nicht|don'?t know|keine ahnung|not sure"
    r"|was auch immer|whatever|egal|anything)\b",
    re.IGNORECASE,
)

# Tools that require specific parameters
_TOOLS_NEEDING_PATH = frozenset(
    {
        "read_file",
        "write_file",
        "edit_file",
        "delete_file",
        "list_directory",
    }
)
_TOOLS_NEEDING_QUERY = frozenset(
    {
        "web_search",
        "search_and_read",
        "search_memory",
        "web_news_search",
    }
)
_TOOLS_NEEDING_COMMAND = frozenset(
    {
        "exec_command",
        "shell_exec",
        "shell",
        "run_python",
    }
)


class ConfidenceChecker:
    """Pre-execution confidence assessment.

    Evaluates 3 dimensions before tool execution:
    - Clarity: Is the user request specific enough?
    - Past mistakes: Has this tool+context failed before?
    - Context readiness: Is sufficient context loaded?
    """

    def __init__(self, reflexion_memory: ReflexionMemory | None = None) -> None:
        self._reflexion = reflexion_memory

    def assess(
        self,
        message: str,
        tool_name: str,
        context: dict[str, Any] | None = None,
    ) -> ConfidenceResult:
        """Run the 3-stage confidence check.

        Args:
            message: The user's original message.
            tool_name: The tool about to be executed.
            context: Optional dict with keys like 'memory_results',
                     'user_preferences', 'recent_episodes'.

        Returns:
            ConfidenceResult with composite score and per-dimension scores.
        """
        clarity = self._check_clarity(message, tool_name)
        mistakes = self._check_past_mistakes(tool_name, message)
        readiness = self._check_context_readiness(context)

        score = clarity * CLARITY_WEIGHT + mistakes * MISTAKE_WEIGHT + readiness * CONTEXT_WEIGHT
        # Clamp to [0, 1]
        score = max(0.0, min(1.0, score))

        blockers: list[str] = []
        recommendations: list[str] = []

        if clarity < 0.4:
            blockers.append("Message lacks specificity for this tool")
            recommendations.append("Ask user for more details before proceeding")
        if mistakes < 0.5:
            blockers.append("Similar tool invocation has failed before")
            recommendations.append("Check reflexion memory for prevention rules")
        if readiness < 0.3:
            blockers.append("Insufficient context loaded")
            recommendations.append("Run context pipeline before tool execution")

        should_proceed = score >= PROCEED_THRESHOLD
        should_block = score < WARN_THRESHOLD
        should_warn = not should_proceed and not should_block

        result = ConfidenceResult(
            score=round(score, 3),
            should_proceed=should_proceed,
            should_warn=should_warn,
            should_block=should_block,
            clarity_score=round(clarity, 3),
            mistake_score=round(mistakes, 3),
            context_score=round(readiness, 3),
            blockers=blockers,
            recommendations=recommendations,
        )

        log.debug(
            "confidence_assessed",
            tool=tool_name,
            score=result.score,
            clarity=result.clarity_score,
            mistakes=result.mistake_score,
            context=result.context_score,
            proceed=result.should_proceed,
        )

        return result

    def _check_clarity(self, message: str, tool_name: str) -> float:
        """Check if message is specific enough for this tool.

        Scoring:
        - Baseline: 0.5
        - +0.15 for action verbs
        - +0.2 for technical specificity (paths, URLs, code refs)
        - +0.15 for tool-specific requirements met
        - -0.2 for vague language
        """
        if not message.strip():
            return 0.0

        score = 0.5

        # Bonus for action verbs
        if _ACTION_VERBS.search(message):
            score += 0.15

        # Bonus for technical specificity
        tech_matches = _TECHNICAL_SPECIFICITY.findall(message)
        if tech_matches:
            score += min(0.2, len(tech_matches) * 0.1)

        # Bonus for tool-specific requirements
        tool_lower = tool_name.lower()
        if tool_lower in _TOOLS_NEEDING_PATH:
            # Check for path-like content
            if re.search(r"[/\\]", message) or re.search(r"\.\w{1,5}\b", message):
                score += 0.15
        elif tool_lower in _TOOLS_NEEDING_QUERY:
            # Longer queries are more specific
            word_count = len(message.split())
            if word_count >= 3:
                score += 0.15
            elif word_count >= 2:
                score += 0.08
        elif tool_lower in _TOOLS_NEEDING_COMMAND and re.search(
            r"\b(pip|npm|git|docker|python|node|cargo|make)\b", message, re.IGNORECASE
        ):
            score += 0.15

        # Penalty for vague language
        vague_matches = _VAGUE_LANGUAGE.findall(message)
        if vague_matches:
            score -= min(0.2, len(vague_matches) * 0.1)

        # Message length bonus (very short messages lack context)
        if len(message) < 10:
            score -= 0.1
        elif len(message) > 50:
            score += 0.05

        return max(0.0, min(1.0, score))

    def _check_past_mistakes(self, tool_name: str, message: str) -> float:
        """Check reflexion memory for similar failures.

        Returns:
            1.0 if no reflexion memory or no known failures.
            Decreases with recurrence count of matching patterns.
        """
        if self._reflexion is None:
            return 1.0

        # Check for prevention rules for this tool
        rules = self._reflexion.get_prevention_rules(tool_name)
        if not rules:
            return 1.0

        # Check recurring errors for this tool
        recurring = self._reflexion.get_recurring_errors(min_count=2)
        tool_recurring = [e for e in recurring if e.tool_name == tool_name]

        if not tool_recurring:
            # Has rules but no recurring errors — mild caution
            return 0.8

        # Score decreases with recurrence count
        max_recurrence = max(e.recurrence_count for e in tool_recurring)
        if max_recurrence >= 10:
            return 0.2
        if max_recurrence >= 5:
            return 0.4
        if max_recurrence >= 3:
            return 0.6

        return 0.7

    def _check_context_readiness(self, context: dict[str, Any] | None) -> float:
        """Check if sufficient context is loaded.

        Scoring:
        - No context: 0.3 (baseline)
        - +0.2 for memory results
        - +0.2 for user preferences
        - +0.2 for recent episodes
        - +0.1 for vault snippets
        """
        if not context:
            return 0.3

        score = 0.3

        if context.get("memory_results"):
            score += 0.2
        if context.get("user_preferences"):
            score += 0.2
        if context.get("recent_episodes"):
            score += 0.2
        if context.get("vault_snippets"):
            score += 0.1

        return min(1.0, score)
