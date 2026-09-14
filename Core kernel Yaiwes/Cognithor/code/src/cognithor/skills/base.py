"""Base class for all Cognithor skills.

Every skill inherits from ``BaseSkill`` and implements ``execute()``.
The SkillScaffolder (``jarvis.tools.skill_cli``) automatically generates
code that imports ``BaseSkill`` and uses it as parent class.

Example:
    class WeatherSkill(BaseSkill):
        NAME = "weather_query"
        DESCRIPTION = "Fetch current weather data"
        VERSION = "0.1.0"
        REQUIRES_NETWORK = True

        async def execute(self, params: dict) -> dict:
            city = params.get("city", "Berlin")
            ...
            return {"status": "ok", "result": data}

Architecture reference: §6.2 (Procedural Skills), §4.6 (Working Memory Injection)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SkillError(Exception):
    """Error during skill execution."""


class BaseSkill(ABC):
    """Abstract base class for all Cognithor skills.

    Class attributes:
        NAME:              Unique skill identifier (slug).
        DESCRIPTION:       Short description of the skill.
        VERSION:           Semantic version (e.g. ``0.1.0``).
        REQUIRES_NETWORK:  ``True`` if the skill requires network access.
        API_BASE:          Base URL for API skills (optional).
        CRON:              Cron expression for automated skills (optional).
    """

    NAME: str = ""
    DESCRIPTION: str = ""
    VERSION: str = "0.1.0"
    REQUIRES_NETWORK: bool = False
    API_BASE: str = ""
    CRON: str = ""

    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the skill.

        Args:
            params: Parameter dictionary from the Planner/Executor.

        Returns:
            Result dictionary with at least ``status`` (``ok`` or ``error``).

        Raises:
            SkillError: On execution errors.
        """

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def description(self) -> str:
        return self.DESCRIPTION

    @property
    def version(self) -> str:
        return self.VERSION

    @property
    def is_automated(self) -> bool:
        """True if the skill has a cron schedule."""
        return bool(self.CRON)

    @property
    def is_network_skill(self) -> bool:
        """True if the skill requires network access."""
        return self.REQUIRES_NETWORK

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """Validate parameters. Override for specific checks.

        Returns:
            List of error messages (empty = OK).
        """
        return []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.NAME!r} v{self.VERSION}>"
