"""Task source adapters — detect and build tasks from various Cognithor subsystems."""

from __future__ import annotations

import re
from typing import Any


class ChatTaskDetector:
    """Detect task creation intent in chat messages / planner output."""

    _PATTERNS = [
        re.compile(r"\[KANBAN:(.+?)\]", re.IGNORECASE),
        re.compile(r"(?:erstelle|create)\s+(?:(?:einen?|a)\s+)?task:\s*(.+)", re.IGNORECASE),
        re.compile(r"(?:neuer|new)\s+task:\s*(.+)", re.IGNORECASE),
        re.compile(r"add\s+to\s+board:\s*(.+)", re.IGNORECASE),
    ]

    @classmethod
    def detect(cls, text: str) -> dict[str, str] | None:
        for pattern in cls._PATTERNS:
            m = pattern.search(text)
            if m:
                title = m.group(1).strip().rstrip(".")
                return {"title": title}
        return None


class CronTaskAdapter:
    """Build task data from cron job execution results."""

    @staticmethod
    def build_task_data(
        job_name: str,
        result: str,
        follow_up: bool = False,
    ) -> dict[str, Any]:
        return {
            "title": f"Cron: {job_name}",
            "description": result,
            "source": "cron",
            "source_ref": job_name,
            "status": "todo" if follow_up else "done",
            "priority": "medium" if follow_up else "low",
            "created_by": "system",
        }


class EvolutionTaskAdapter:
    """Build task data from evolution engine observations."""

    @staticmethod
    def from_skill_failure(skill_name: str, failure_rate: float) -> dict[str, Any]:
        return {
            "title": f"Optimize skill: {skill_name} ({failure_rate:.0%} failure rate)",
            "description": f"Skill '{skill_name}' has a {failure_rate:.0%} failure rate. "
            f"Investigate root cause and improve.",
            "source": "evolution",
            "source_ref": f"skill:{skill_name}",
            "priority": "high" if failure_rate > 0.5 else "medium",
            "labels": ["optimization", "skill"],
            "created_by": "system",
        }

    @staticmethod
    def from_knowledge_gap(topic: str) -> dict[str, Any]:
        return {
            "title": f"Research: {topic}",
            "description": f"Knowledge gap detected for topic '{topic}'. Schedule deep research.",
            "source": "evolution",
            "source_ref": f"gap:{topic}",
            "priority": "medium",
            "labels": ["research", "knowledge-gap"],
            "created_by": "system",
        }


class SystemTaskAdapter:
    """Build task data from system events (recovery failures, errors)."""

    @staticmethod
    def from_recovery_failure(
        tool_name: str,
        attempts: int,
        error: str,
    ) -> dict[str, Any]:
        return {
            "title": f"Investigate: {tool_name} failures ({attempts}x)",
            "description": f"Tool '{tool_name}' failed {attempts} times. "
            f"Last error: {error}. Recovery exhausted.",
            "source": "system",
            "source_ref": f"recovery:{tool_name}",
            "priority": "urgent",
            "labels": ["bug", "investigation"],
            "created_by": "system",
        }
