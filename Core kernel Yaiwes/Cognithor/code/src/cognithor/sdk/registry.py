"""SDK Registry — central store for tools, agents, and hooks.

Thread-safe registry that collects decorated definitions and provides
lookup/discovery APIs.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cognithor.sdk.definitions import AgentDefinition, HookDefinition, HookEvent, ToolDefinition


class SDKRegistry:
    """Central registry for SDK-registered tools, agents, and hooks."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._agents: dict[str, AgentDefinition] = {}
        self._hooks: dict[HookEvent, list[HookDefinition]] = {}
        self._lock = threading.Lock()

    # -- Tools --

    def register_tool(self, tool: ToolDefinition) -> None:
        with self._lock:
            self._tools[tool.name] = tool

    def get_tool(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    # -- Agents --

    def register_agent(self, agent: AgentDefinition) -> None:
        with self._lock:
            self._agents[agent.name] = agent

    def get_agent(self, name: str) -> AgentDefinition | None:
        return self._agents.get(name)

    def list_agents(self) -> list[AgentDefinition]:
        return list(self._agents.values())

    # -- Hooks --

    def register_hook(self, hook: HookDefinition) -> None:
        with self._lock:
            if hook.event not in self._hooks:
                self._hooks[hook.event] = []
            self._hooks[hook.event].append(hook)
            self._hooks[hook.event].sort(key=lambda h: h.priority, reverse=True)

    def get_hooks(self, event: HookEvent) -> list[HookDefinition]:
        return list(self._hooks.get(event, []))

    # -- Discovery --

    def find_tools_for_agent(self, agent_name: str) -> list[ToolDefinition]:
        """Find all tools required by an agent."""
        agent = self._agents.get(agent_name)
        if not agent:
            return []
        return [self._tools[t] for t in agent.tools if t in self._tools]

    def find_agents_with_tool(self, tool_name: str) -> list[AgentDefinition]:
        """Find agents that use a specific tool."""
        return [a for a in self._agents.values() if tool_name in a.tools]

    # -- Stats --

    def stats(self) -> dict[str, Any]:
        return {
            "tools": len(self._tools),
            "agents": len(self._agents),
            "hooks": sum(len(hooks) for hooks in self._hooks.values()),
            "hook_events": list(self._hooks.keys()),
        }

    def clear(self) -> None:
        """Clear all registrations (for testing)."""
        with self._lock:
            self._tools.clear()
            self._agents.clear()
            self._hooks.clear()
