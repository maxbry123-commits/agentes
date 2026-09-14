"""ATL (Autonomous Thinking Loop) configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["ATLConfig"]


@dataclass
class ATLConfig:
    """Configuration for the Autonomous Thinking Loop (Evolution Phase 6)."""

    enabled: bool = False
    interval_minutes: int = 15
    quiet_hours_start: str = "23:00"
    quiet_hours_end: str = "07:00"
    max_actions_per_cycle: int = 3
    max_tokens_per_cycle: int = 4000
    notification_channel: str = ""
    notification_level: str = "important"
    goal_review_interval: str = "daily"
    risk_ceiling: str = "YELLOW"
    allowed_action_types: list[str] = field(
        default_factory=lambda: [
            "memory_update",
            "research",
            "notification",
            "file_management",
            "goal_management",
        ]
    )
    blocked_action_types: list[str] = field(
        default_factory=lambda: [
            "shell_exec",
            "send_message_unprompted",
        ]
    )

    def __post_init__(self) -> None:
        self.interval_minutes = max(5, min(60, self.interval_minutes))
        if self.risk_ceiling not in ("GREEN", "YELLOW"):
            self.risk_ceiling = "YELLOW"
        if self.notification_level not in ("all", "important", "critical"):
            self.notification_level = "important"
