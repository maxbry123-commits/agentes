"""Claude Code SDK 智能体实现。"""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, SystemMessage, TextBlock, ToolResultBlock, ToolUseBlock, query
from loguru import logger

from .base import AgentRunResult, BaseChallengeAgent
from .prompts import MISSION_PROMPT, SYSTEM_PROMPT
from .tooling import build_mcp_servers, default_allowed_tools, parse_csv


class ClaudeCodeChallengeAgent(BaseChallengeAgent):
    """基于 Claude Code Agent SDK 的挑战赛智能体。"""

    def __init__(
        self,
        config: dict[str, str],
        max_iterations: int = 16,
        on_message=None,
    ) -> None:
        model_name = config.get("CLAUDE_MODEL") or config.get("MODEL_ID", "ep-jsc7o0kw")
        super().__init__(model_name=model_name, max_iterations=max_iterations, on_message=on_message)
        self.config = config
        self.model = model_name
        self.cli_path = config.get("CLAUDE_CLI_PATH") or None
        self.challenge_server_name = config.get("CHALLENGE_MCP_SERVER_NAME", "challenge")

    def format_tools(self, tools: list[Any]) -> list[Any]:
        """Claude SDK 自行处理工具，这里保留接口一致性。"""
        return tools

    async def complete_turn(self, messages: list[dict[str, Any]], tools: Any):  # pragma: no cover
        raise NotImplementedError("Claude Code SDK agent does not use manual turn completion")

    async def run_competition(self, mcp_session=None) -> AgentRunResult:
        """通过 Claude Code SDK 直接执行完整任务流。"""
        logger.info("=== 开始 Claude Code SDK 闯关流程 ===")

        tools_preset = self.config.get("CLAUDE_TOOLS_PRESET", "claude_code")
        allowed_tools = parse_csv(self.config.get("CLAUDE_ALLOWED_TOOLS", "")) or default_allowed_tools(
            challenge_server_name=self.challenge_server_name
        )
        disallowed_tools = parse_csv(self.config.get("CLAUDE_DISALLOWED_TOOLS", ""))
        permission_mode = self.config.get("CLAUDE_PERMISSION_MODE", "bypassPermissions")
        mcp_servers = build_mcp_servers(self.config, challenge_server_name=self.challenge_server_name)

        claude_api_key = self.config.get("CLAUDE_API_KEY") or self.config.get("MODEL_API_KEY", "")
        claude_base_url = self.config.get("CLAUDE_BASE_URL") or self.config.get("MODEL_BASE_URL", "")

        model_lower = self.model.lower()

        sdk_env = {
            "ANTHROPIC_API_KEY": claude_api_key,
            "ANTHROPIC_BASE_URL": claude_base_url,
            "ANTHROPIC_MODEL": self.model,
        }

        def _stderr(line: str) -> None:
            line = line.rstrip()
            if line:
                logger.error(f"[claude-sdk-stderr] {line}")

        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            model=self.model,
            max_turns=self.max_iterations,
            permission_mode=permission_mode,
            tools={"type": "preset", "preset": tools_preset},
            allowed_tools=allowed_tools,
            disallowed_tools=disallowed_tools,
            mcp_servers=mcp_servers,
            env={k: v for k, v in sdk_env.items() if v},
            stderr=_stderr,
        )

        if self.cli_path:
            options.cli_path = self.cli_path

        self._emit("system", f"模型已就绪: {self.model_name} ({self.model})")
        self._emit(
            "system",
            f"工具配置 | preset={tools_preset} | permission_mode={permission_mode} | "
            f"allowed={len(allowed_tools)} | disallowed={len(disallowed_tools)} | mcp_servers={list(mcp_servers.keys())} | "
            f"gateway={claude_base_url}",
        )
        self._emit("user", MISSION_PROMPT)

        final_response = ""
        iteration_count = 0

        async for message in query(prompt=MISSION_PROMPT, options=options):
            message_type = type(message).__name__
            logger.debug(f"Claude SDK 消息: {message_type}")

            if isinstance(message, SystemMessage) and getattr(message, "subtype", None) == "init":
                self._emit("system", "Claude Code SDK 已初始化")
                continue

            if isinstance(message, AssistantMessage):
                iteration_count += 1
                text_parts: list[str] = []
                for block in message.content:
                    if isinstance(block, TextBlock) and block.text:
                        text_parts.append(block.text)
                        self._emit("assistant", block.text)
                        final_response = block.text
                    elif isinstance(block, ToolUseBlock):
                        self._emit(
                            "tool_call",
                            f"调用工具: {getattr(block, 'name', '')}，参数: {getattr(block, 'input', {})}",
                        )
                    elif isinstance(block, ToolResultBlock):
                        content = getattr(block, "content", "")
                        self._emit("tool_result", f"工具结果: {str(content)[:500]}")

                if text_parts:
                    final_response = "\n".join(text_parts)

            elif isinstance(message, ResultMessage):
                if getattr(message, "total_cost_usd", None):
                    self._emit("system", f"本次调用成本: ${message.total_cost_usd:.4f}")

        return AgentRunResult(final_message=final_response, iterations=iteration_count)