from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class ToolInput:
    query: str
    options: dict[str, Any] | None = None


@dataclass(slots=True)
class ToolOutput:
    items: list[Any]
    metadata: dict[str, Any]


class Tool(Protocol):
    name: str

    def call(self, tool_input: ToolInput) -> ToolOutput:
        ...
