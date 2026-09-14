"""Complexity-based token budget allocation.

Allocates a token budget per message based on:
- Detected complexity: simple=500, medium=2000, complex=5000, research=10000
- Channel multiplier: telegram=0.3, voice=0.2, webui=1.0, cli=1.0
- Phase ratios: planner=40%, executor=40%, formulate=20%

The budget is advisory — it does not hard-block execution but provides
guidance for response length and tool iteration depth.

Inspired by SuperClaude's token budget management pattern.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


# --- Complexity budgets (base token counts) ---
COMPLEXITY_BUDGETS: dict[str, int] = {
    "simple": 500,
    "medium": 2000,
    "complex": 5000,
    "research": 10000,
}

# --- Channel multipliers ---
CHANNEL_MULTIPLIERS: dict[str, float] = {
    "telegram": 0.3,
    "discord": 0.5,
    "slack": 0.5,
    "whatsapp": 0.3,
    "signal": 0.3,
    "voice": 0.2,
    "webui": 1.0,
    "cli": 1.0,
    "matrix": 0.7,
    "irc": 0.4,
    "teams": 0.6,
    "google_chat": 0.6,
}

# --- Phase allocation ratios ---
PHASE_RATIOS: dict[str, float] = {
    "planner": 0.4,
    "executor": 0.4,
    "formulate": 0.2,
}

# --- Complexity detection patterns ---

_RESEARCH_PATTERNS = re.compile(
    r"\b(research|recherch|analyse|analyz|vergleich|compar|zusammenfass"
    r"|summariz|erklaer|explain|warum|why|how does|wie funktioniert"
    r"|deep.?dive|ausfuehrlich|detailliert|detailed|comprehensive"
    r"|ueberblick|overview|report|bericht)\b",
    re.IGNORECASE,
)

_COMPLEX_PATTERNS = re.compile(
    r"\b(implementier|implement|erstell.*(?:datei|file|script|app|projekt)"
    r"|build|deploy|migrat|refactor|debug|fix.*(?:bug|error|fehler)"
    r"|setup|konfigur|configur|install|automatisier|automat"
    r"|pipeline|workflow|multi.?step)\b",
    re.IGNORECASE,
)

_SIMPLE_PATTERNS = re.compile(
    r"\b(was ist|what is|wer ist|who is|wann|when|wo |where"
    r"|zeig|show|list|hallo|hello|hi |danke|thanks|ja|nein"
    r"|yes|no|ok|gut|good|time|uhrzeit|datum|date|wetter|weather)\b",
    re.IGNORECASE,
)


@dataclass
class BudgetSnapshot:
    """Snapshot of the current budget state."""

    total: int
    allocated: int
    remaining: int
    exceeded: bool
    phase_budgets: dict[str, int]
    complexity: str
    channel: str


class TokenBudgetManager:
    """Manages token budget for a single message lifecycle.

    Created at message receipt, tracks allocation across phases,
    provides guidance for response length.
    """

    def __init__(
        self,
        complexity: str = "medium",
        channel: str = "webui",
    ) -> None:
        if complexity not in COMPLEXITY_BUDGETS:
            complexity = "medium"

        self._complexity = complexity
        self._channel = channel.lower()

        base = COMPLEXITY_BUDGETS[self._complexity]
        multiplier = CHANNEL_MULTIPLIERS.get(self._channel, 0.8)
        self._total = int(base * multiplier)
        self._allocated = 0

        log.debug(
            "token_budget_created",
            complexity=complexity,
            channel=channel,
            base=base,
            multiplier=multiplier,
            total=self._total,
        )

    @property
    def total(self) -> int:
        """Total budget for this message."""
        return self._total

    @property
    def allocated(self) -> int:
        """Tokens allocated so far."""
        return self._allocated

    @property
    def remaining(self) -> int:
        """Tokens remaining in budget."""
        return max(0, self._total - self._allocated)

    @property
    def exceeded(self) -> bool:
        """Whether the budget has been exceeded."""
        return self._allocated > self._total

    @property
    def complexity(self) -> str:
        """The detected/assigned complexity level."""
        return self._complexity

    @property
    def channel(self) -> str:
        """The channel this budget is for."""
        return self._channel

    def get_phase_budget(self, phase: str) -> int:
        """Get the token budget for a specific phase.

        Args:
            phase: One of 'planner', 'executor', 'formulate'.

        Returns:
            Token count allocated to this phase.
        """
        ratio = PHASE_RATIOS.get(phase, 0.0)
        return int(self._total * ratio)

    def allocate(self, tokens: int) -> bool:
        """Record token allocation.

        Args:
            tokens: Number of tokens to allocate.

        Returns:
            True if still within budget after allocation, False if exceeded.
        """
        self._allocated += tokens
        if self.exceeded:
            log.debug(
                "token_budget_exceeded",
                allocated=self._allocated,
                total=self._total,
                overage=self._allocated - self._total,
            )
            return False
        return True

    def snapshot(self) -> BudgetSnapshot:
        """Get a snapshot of the current budget state."""
        return BudgetSnapshot(
            total=self._total,
            allocated=self._allocated,
            remaining=self.remaining,
            exceeded=self.exceeded,
            phase_budgets={phase: self.get_phase_budget(phase) for phase in PHASE_RATIOS},
            complexity=self._complexity,
            channel=self._channel,
        )

    @staticmethod
    def detect_complexity(message: str, tool_count: int = 0) -> str:
        """Auto-detect complexity from message characteristics.

        Uses pattern matching and heuristics:
        - Research keywords -> research
        - Complex/build keywords -> complex
        - Short messages with simple keywords -> simple
        - Multiple tools planned -> complex
        - Default -> medium

        Args:
            message: The user's message.
            tool_count: Number of tools planned (0 if not yet known).

        Returns:
            One of: 'simple', 'medium', 'complex', 'research'.
        """
        if not message.strip():
            return "simple"

        # Tool count is a strong signal
        if tool_count >= 5:
            return "research"
        if tool_count >= 3:
            return "complex"

        # Pattern matching
        if _RESEARCH_PATTERNS.search(message):
            return "research"
        if _COMPLEX_PATTERNS.search(message):
            return "complex"
        if _SIMPLE_PATTERNS.search(message) and len(message.split()) <= 8:
            return "simple"

        # Length heuristic
        word_count = len(message.split())
        if word_count <= 5:
            return "simple"
        if word_count >= 50:
            return "complex"

        return "medium"
