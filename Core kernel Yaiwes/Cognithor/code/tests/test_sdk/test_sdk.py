"""Tests for the Cognithor Agent SDK.

Covers decorators (@tool, @agent, @hook), registry, schema inference,
scaffolding, definitions, and integration patterns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cognithor.sdk.decorators import _infer_schema, get_registry
from cognithor.sdk.definitions import (
    AgentDefinition,
    HookDefinition,
    HookEvent,
    ToolDefinition,
)
from cognithor.sdk.registry import SDKRegistry
from cognithor.sdk.scaffold import scaffold_agent, scaffold_tool

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# ToolDefinition
# ============================================================================


class TestToolDefinition:
    def test_defaults(self) -> None:
        t = ToolDefinition(name="test")
        assert t.risk_level == "green"
        assert t.requires_network is False
        assert t.version == "0.1.0"

    def test_to_mcp_schema(self) -> None:
        t = ToolDefinition(
            name="greet",
            description="Greet a user",
            input_schema={"type": "object", "properties": {"name": {"type": "string"}}},
            read_only=True,
        )
        schema = t.to_mcp_schema()
        assert schema["name"] == "greet"
        assert schema["annotations"]["readOnlyHint"] is True
        assert schema["annotations"]["destructiveHint"] is False

    def test_destructive_hint(self) -> None:
        t = ToolDefinition(name="rm", risk_level="red")
        schema = t.to_mcp_schema()
        assert schema["annotations"]["destructiveHint"] is True


# ============================================================================
# HookDefinition
# ============================================================================


class TestHookDefinition:
    def test_hook_events(self) -> None:
        assert len(HookEvent) == 7
        assert HookEvent.ON_MESSAGE == "on_message"
        assert HookEvent.ON_ERROR == "on_error"

    def test_hook_definition(self) -> None:
        h = HookDefinition(event=HookEvent.ON_ERROR, priority=5)
        assert h.event == HookEvent.ON_ERROR
        assert h.priority == 5


# ============================================================================
# AgentDefinition
# ============================================================================


class TestAgentDefinition:
    def test_defaults(self) -> None:
        a = AgentDefinition(name="test")
        assert a.max_iterations == 5
        assert a.timeout_seconds == 300
        assert a.tools == []

    def test_to_yaml_dict(self) -> None:
        a = AgentDefinition(
            name="researcher",
            description="Research agent",
            tools=["web_search"],
            trigger_keywords=["search", "find"],
        )
        d = a.to_yaml_dict()
        assert d["name"] == "researcher"
        assert d["tools"] == ["web_search"]
        assert "trigger_keywords" in d


# ============================================================================
# SDKRegistry
# ============================================================================


class TestSDKRegistry:
    def setup_method(self) -> None:
        self.reg = SDKRegistry()

    def test_register_tool(self) -> None:
        t = ToolDefinition(name="add", description="Add numbers")
        self.reg.register_tool(t)
        assert self.reg.get_tool("add") is not None
        assert self.reg.get_tool("add").description == "Add numbers"

    def test_list_tools(self) -> None:
        self.reg.register_tool(ToolDefinition(name="a"))
        self.reg.register_tool(ToolDefinition(name="b"))
        assert len(self.reg.list_tools()) == 2

    def test_get_unknown_tool(self) -> None:
        assert self.reg.get_tool("unknown") is None

    def test_register_agent(self) -> None:
        a = AgentDefinition(name="bot", tools=["a", "b"])
        self.reg.register_agent(a)
        assert self.reg.get_agent("bot") is not None
        assert self.reg.get_agent("bot").tools == ["a", "b"]

    def test_list_agents(self) -> None:
        self.reg.register_agent(AgentDefinition(name="a"))
        self.reg.register_agent(AgentDefinition(name="b"))
        assert len(self.reg.list_agents()) == 2

    def test_register_hook(self) -> None:
        h = HookDefinition(event=HookEvent.ON_ERROR, priority=1)
        self.reg.register_hook(h)
        hooks = self.reg.get_hooks(HookEvent.ON_ERROR)
        assert len(hooks) == 1

    def test_hooks_sorted_by_priority(self) -> None:
        self.reg.register_hook(HookDefinition(event=HookEvent.ON_ERROR, priority=1))
        self.reg.register_hook(HookDefinition(event=HookEvent.ON_ERROR, priority=5))
        self.reg.register_hook(HookDefinition(event=HookEvent.ON_ERROR, priority=3))
        hooks = self.reg.get_hooks(HookEvent.ON_ERROR)
        assert hooks[0].priority == 5
        assert hooks[2].priority == 1

    def test_find_tools_for_agent(self) -> None:
        self.reg.register_tool(ToolDefinition(name="search"))
        self.reg.register_tool(ToolDefinition(name="write"))
        self.reg.register_agent(AgentDefinition(name="bot", tools=["search", "missing"]))
        tools = self.reg.find_tools_for_agent("bot")
        assert len(tools) == 1
        assert tools[0].name == "search"

    def test_find_agents_with_tool(self) -> None:
        self.reg.register_agent(AgentDefinition(name="a", tools=["search"]))
        self.reg.register_agent(AgentDefinition(name="b", tools=["search", "write"]))
        self.reg.register_agent(AgentDefinition(name="c", tools=["write"]))
        agents = self.reg.find_agents_with_tool("search")
        assert len(agents) == 2
        names = {a.name for a in agents}
        assert names == {"a", "b"}

    def test_stats(self) -> None:
        self.reg.register_tool(ToolDefinition(name="t"))
        self.reg.register_agent(AgentDefinition(name="a"))
        self.reg.register_hook(HookDefinition(event=HookEvent.ON_START))
        s = self.reg.stats()
        assert s["tools"] == 1
        assert s["agents"] == 1
        assert s["hooks"] == 1

    def test_clear(self) -> None:
        self.reg.register_tool(ToolDefinition(name="t"))
        self.reg.register_agent(AgentDefinition(name="a"))
        self.reg.clear()
        assert len(self.reg.list_tools()) == 0
        assert len(self.reg.list_agents()) == 0


# ============================================================================
# Schema Inference
# ============================================================================


class TestSchemaInference:
    def test_simple_function(self) -> None:
        def func(name: str, age: int) -> str:
            return ""

        schema = _infer_schema(func)
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["age"]["type"] == "integer"
        assert "name" in schema["required"]
        assert "age" in schema["required"]

    def test_with_defaults(self) -> None:
        def func(name: str = "World", count: int = 5) -> str:
            return ""

        schema = _infer_schema(func)
        assert "required" not in schema  # No required params
        assert schema["properties"]["name"]["default"] == "World"
        assert schema["properties"]["count"]["default"] == 5

    def test_mixed_required_optional(self) -> None:
        def func(name: str, greeting: str = "Hello") -> str:
            return ""

        schema = _infer_schema(func)
        assert schema["required"] == ["name"]
        assert schema["properties"]["greeting"]["default"] == "Hello"

    def test_bool_and_float(self) -> None:
        def func(flag: bool, score: float) -> None:
            pass

        schema = _infer_schema(func)
        assert schema["properties"]["flag"]["type"] == "boolean"
        assert schema["properties"]["score"]["type"] == "number"

    def test_no_annotations(self) -> None:
        def func(x, y):
            pass

        schema = _infer_schema(func)
        assert schema["properties"]["x"]["type"] == "string"  # Default to string

    def test_self_skipped(self) -> None:
        class Foo:
            def method(self, name: str) -> None:
                pass

        schema = _infer_schema(Foo.method)
        assert "self" not in schema["properties"]


# ============================================================================
# @tool decorator
# ============================================================================


class TestToolDecorator:
    def setup_method(self) -> None:
        get_registry().clear()

    def test_basic_tool(self) -> None:
        from cognithor.sdk import tool

        @tool(name="greet", description="Greet user")
        async def greet(name: str) -> str:
            return f"Hello, {name}!"

        assert hasattr(greet, "_sdk_tool")
        assert greet._sdk_tool.name == "greet"
        assert get_registry().get_tool("greet") is not None

    def test_tool_without_args(self) -> None:
        from cognithor.sdk import tool

        @tool
        async def simple() -> str:
            return "done"

        assert hasattr(simple, "_sdk_tool")
        assert simple._sdk_tool.name == "simple"

    def test_tool_schema_inferred(self) -> None:
        from cognithor.sdk import tool

        @tool(name="calc")
        async def calc(a: int, b: int) -> int:
            return a + b

        defn = get_registry().get_tool("calc")
        assert defn is not None
        assert defn.input_schema["properties"]["a"]["type"] == "integer"


# ============================================================================
# @agent decorator
# ============================================================================


class TestAgentDecorator:
    def setup_method(self) -> None:
        get_registry().clear()

    def test_basic_agent(self) -> None:
        from cognithor.sdk import agent

        @agent(name="bot", description="Test bot", tools=["search"])
        class TestBot:
            async def on_message(self, msg: str) -> str:
                return "ok"

        assert hasattr(TestBot, "_sdk_agent")
        assert TestBot._sdk_agent.name == "bot"
        assert get_registry().get_agent("bot") is not None

    def test_agent_default_name(self) -> None:
        from cognithor.sdk import agent

        @agent(description="Auto-named")
        class MySpecialAgent:
            pass

        assert MySpecialAgent._sdk_agent.name == "myspecialagent"


# ============================================================================
# @hook decorator
# ============================================================================


class TestHookDecorator:
    def setup_method(self) -> None:
        get_registry().clear()

    def test_basic_hook(self) -> None:
        from cognithor.sdk import hook

        @hook("on_error", priority=10)
        async def on_err(error: Exception) -> None:
            pass

        assert hasattr(on_err, "_sdk_hook")
        assert on_err._sdk_hook.event == HookEvent.ON_ERROR
        hooks = get_registry().get_hooks(HookEvent.ON_ERROR)
        assert len(hooks) == 1
        assert hooks[0].priority == 10


# ============================================================================
# Scaffolding
# ============================================================================


class TestScaffold:
    def test_scaffold_agent_content(self) -> None:
        content = scaffold_agent("my_bot", "A helpful bot", keywords=["help"])
        assert "class MyBotAgent:" in content
        assert "@agent(" in content
        assert "@tool(" in content
        assert "my_bot" in content

    def test_scaffold_agent_to_file(self, tmp_path: Path) -> None:
        scaffold_agent("test", output_dir=tmp_path)
        path = tmp_path / "test_agent.py"
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "class TestAgent:" in content

    def test_scaffold_tool_content(self) -> None:
        content = scaffold_tool(
            "summarize",
            "Summarize text",
            params={"text": "str", "max_length": "int"},
            return_type="str",
        )
        assert "@tool(" in content
        assert "summarize" in content
        assert "text: str" in content
        assert "max_length: int" in content

    def test_scaffold_tool_to_file(self, tmp_path: Path) -> None:
        scaffold_tool("mytools", output_dir=tmp_path)
        path = tmp_path / "mytools_tool.py"
        assert path.exists()

    def test_scaffold_tool_risk_levels(self) -> None:
        content = scaffold_tool("dangerous", risk_level="red", read_only=False)
        assert 'risk_level="red"' in content
        assert "read_only=False" in content

    def test_scaffold_tool_return_types(self) -> None:
        for rt in ["str", "int", "float", "bool", "dict", "list"]:
            content = scaffold_tool("test", return_type=rt)
            assert f"-> {rt}:" in content
