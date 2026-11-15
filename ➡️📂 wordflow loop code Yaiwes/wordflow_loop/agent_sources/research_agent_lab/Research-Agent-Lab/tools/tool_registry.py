from __future__ import annotations

from dataclasses import dataclass, field

from core.tool_base import Tool, ToolInput, ToolOutput


@dataclass
class ToolRegistry:
    tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def has(self, name: str) -> bool:
        return name in self.tools

    def call(self, name: str, query: str, **options: object) -> ToolOutput:
        if name not in self.tools:
            raise KeyError(f"tool is not registered: {name}")
        return self.tools[name].call(ToolInput(query=query, options=options))


def build_default_tool_registry() -> ToolRegistry:
    return ToolRegistry()
