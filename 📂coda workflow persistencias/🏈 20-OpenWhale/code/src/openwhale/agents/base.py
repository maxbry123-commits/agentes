"""智能体基类与通用执行框架。"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

from loguru import logger
from mcp import ClientSession

from ..util.mcp_client import call_tool, list_tools
from .prompts import MISSION_PROMPT, SYSTEM_PROMPT


@dataclass(slots=True)
class AgentToolCall:
    """统一工具调用描述。"""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class AgentRunResult:
    """智能体执行结果。"""

    final_message: str
    iterations: int

    def __str__(self) -> str:
        return self.final_message


class BaseChallengeAgent(ABC):
    """渗透挑战赛智能体基类。"""

    def __init__(
        self,
        model_name: str,
        max_iterations: int = 16,
        on_message: Callable[[str, str], None] | None = None,
    ) -> None:
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.on_message = on_message
        self._submit_failures: dict[str, int] = {}

    def _emit(self, role: str, content: str) -> None:
        logger.info(f"[{role.upper()}] {content[:200]}{'...' if len(content) > 200 else ''}")
        if self.on_message:
            self.on_message(role, content)

    def build_initial_messages(self) -> list[dict[str, Any]]:
        """构建首轮消息。子类可覆盖以适配不同基座的消息格式。"""
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": MISSION_PROMPT},
        ]

    @abstractmethod
    def format_tools(self, tools: list[Any]) -> Any:
        """将 MCP 工具映射到当前基座所需的工具格式。"""

    @abstractmethod
    async def complete_turn(self, messages: list[dict[str, Any]], tools: Any) -> tuple[str, list[AgentToolCall]]:
        """执行一轮模型推理，返回文本与工具调用。"""

    async def run_competition(self, mcp_session: ClientSession) -> AgentRunResult:
        """执行闯关流程并返回最终结果。"""
        logger.info("=== 开始闯关流程 ===")

        tools = await list_tools(mcp_session)
        model_tools = self.format_tools(tools)

        messages = self.build_initial_messages()
        self._emit("system", f"模型已就绪: {self.model_name}")
        self._emit("user", MISSION_PROMPT)

        final_response = ""
        iteration_count = 0
        for iteration in range(self.max_iterations):
            iteration_count = iteration + 1
            logger.debug(f"迭代轮次: {iteration_count}/{self.max_iterations}")

            assistant_text, tool_calls = await self.complete_turn(messages, model_tools)
            assistant_message: dict[str, Any] = {"role": "assistant", "content": assistant_text or None}
            if tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(tool_call.arguments, ensure_ascii=False),
                        },
                    }
                    for tool_call in tool_calls
                ]
            messages.append(assistant_message)

            if assistant_text:
                self._emit("assistant", assistant_text)
                final_response = assistant_text

            if not tool_calls:
                logger.info("智能体无更多工具调用，流程结束")
                break

            for tool_call in tool_calls:
                self._emit("tool_call", f"调用工具: {tool_call.name}，参数: {json.dumps(tool_call.arguments, ensure_ascii=False)}")

                try:
                    result = await call_tool(mcp_session, tool_call.name, tool_call.arguments)
                    result_text = _extract_tool_result(result)
                    self._emit("tool_result", f"[{tool_call.name}] 结果: {result_text[:500]}")

                    self._record_submit_feedback(tool_call.name, tool_call.arguments, result_text, messages)
                except Exception as exc:  # noqa: BLE001
                    result_text = f"工具调用失败: {exc}"
                    logger.error(f"工具 {tool_call.name} 调用失败: {exc}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text,
                    }
                )
        else:
            logger.warning(f"达到最大迭代次数 {self.max_iterations}，强制停止")

        return AgentRunResult(final_message=final_response, iterations=iteration_count)

    def _record_submit_feedback(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result_text: str,
        messages: list[dict[str, Any]],
    ) -> None:
        """当 flag 提交失败时，向模型注入更明确的纠错反馈，避免无效猜测循环。"""
        if tool_name != "submit_flag":
            return

        code = str(arguments.get("code", ""))
        if not code:
            return

        if '"correct": false' in result_text or "答案错误" in result_text:
            failures = self._submit_failures.get(code, 0) + 1
            self._submit_failures[code] = failures

            if failures >= 2:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"赛题 {code} 的 flag 已连续提交失败 {failures} 次。"
                            "停止继续盲猜，必须回到信息收集、页面分析、参数探测或提示信息复核。"
                        ),
                    }
                )


def _extract_tool_result(result: Any) -> str:
    """从 MCP 工具调用结果中提取文本内容。"""
    if result is None:
        return "无返回结果"

    if hasattr(result, "content"):
        contents = result.content
        if isinstance(contents, list):
            parts = []
            for item in contents:
                if hasattr(item, "text"):
                    parts.append(item.text)
                elif hasattr(item, "data"):
                    parts.append(str(item.data))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(contents)

    return str(result)