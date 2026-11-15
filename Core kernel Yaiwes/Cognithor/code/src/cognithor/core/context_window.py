"""Per-agent isolated context windows with time-weighted trimming.

Each agent owns a ``ContextWindow``. No shared context between agents.
Entries decay over time — newer entries survive longer.

Trimming algorithm:
  effective_weight = importance * exp(-age_minutes / half_life)
  Lowest-weight entries are removed first when over token budget.
  System messages and tool results (importance == 1.0) are never trimmed.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextEntry:
    """A single entry in the context window."""

    content: str
    tokens: int
    timestamp: float = field(default_factory=time.monotonic)
    importance: float = 0.5
    entry_type: str = "message"  # "system", "tool_result", "message", "memory"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_protected(self) -> bool:
        """System messages and tool results are never trimmed."""
        return self.entry_type in ("system", "tool_result") or self.importance >= 1.0


class ContextWindow:
    """Isolated, time-weighted context window for a single agent.

    Args:
        max_tokens: Maximum token budget for this window.
        trim_strategy: Trimming strategy (only ``"time_weighted"`` in v0.36).
        retention_half_life_minutes: Entries older than this decay exponentially.
    """

    def __init__(
        self,
        max_tokens: int = 8192,
        trim_strategy: str = "time_weighted",
        retention_half_life_minutes: int = 30,
    ) -> None:
        self.max_tokens = max_tokens
        self.trim_strategy = trim_strategy
        self.retention_half_life_minutes = retention_half_life_minutes
        self._entries: list[ContextEntry] = []

    @property
    def total_tokens(self) -> int:
        return sum(e.tokens for e in self._entries)

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def add(self, entry: ContextEntry) -> None:
        """Add an entry to the context window, trimming if necessary."""
        self._entries.append(entry)
        if self.total_tokens > self.max_tokens:
            self.trim()

    def trim(self) -> int:
        """Remove lowest-weight entries until under token budget.

        Returns:
            Number of tokens freed.
        """
        if self.total_tokens <= self.max_tokens:
            return 0

        now = time.monotonic()
        half_life_s = self.retention_half_life_minutes * 60.0

        # Calculate effective weight for each entry
        scored: list[tuple[float, int, ContextEntry]] = []
        for i, entry in enumerate(self._entries):
            if entry.is_protected:
                scored.append((float("inf"), i, entry))
            else:
                age_s = max(0.0, now - entry.timestamp)
                decay = math.exp(-age_s / half_life_s) if half_life_s > 0 else 0.0
                weight = entry.importance * decay
                scored.append((weight, i, entry))

        # Sort by weight ascending (lowest first = removed first)
        scored.sort(key=lambda x: (x[0], x[1]))

        freed = 0
        to_remove: set[int] = set()
        for _weight, idx, entry in scored:
            if self.total_tokens - freed <= self.max_tokens:
                break
            if entry.is_protected:
                continue
            to_remove.add(idx)
            freed += entry.tokens

        self._entries = [e for i, e in enumerate(self._entries) if i not in to_remove]
        return freed

    def snapshot(self) -> dict[str, Any]:
        """Serialize the context window for checkpointing."""
        return {
            "max_tokens": self.max_tokens,
            "trim_strategy": self.trim_strategy,
            "retention_half_life_minutes": self.retention_half_life_minutes,
            "entries": [
                {
                    "content": e.content,
                    "tokens": e.tokens,
                    "timestamp": e.timestamp,
                    "importance": e.importance,
                    "entry_type": e.entry_type,
                    "metadata": e.metadata,
                }
                for e in self._entries
            ],
        }

    def restore(self, snapshot: dict[str, Any]) -> None:
        """Restore context window from a checkpoint snapshot."""
        self.max_tokens = snapshot.get("max_tokens", self.max_tokens)
        self.trim_strategy = snapshot.get("trim_strategy", self.trim_strategy)
        self.retention_half_life_minutes = snapshot.get(
            "retention_half_life_minutes", self.retention_half_life_minutes
        )
        self._entries = [
            ContextEntry(
                content=e["content"],
                tokens=e["tokens"],
                timestamp=e["timestamp"],
                importance=e["importance"],
                entry_type=e["entry_type"],
                metadata=e.get("metadata", {}),
            )
            for e in snapshot.get("entries", [])
        ]

    def clear(self) -> None:
        """Remove all entries."""
        self._entries.clear()
