"""OpenAI 兼容智能体实现。"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger
from openai import OpenAI

from ..util.mcp_client import tools_to_openai_format
from .base import AgentToolCall, BaseChallengeAgent


class OpenAIChallengeAgent(BaseChallengeAgent):
    """基于 OpenAI Chat Completions 的智能体实现。"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        model_name: str,
        max_iterations: int = 16,
        on_message=None,
    ) -> None:
        super().__init__(model_name=model_name, max_iterations=max_iterations, on_message=on_message)
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def format_tools(self, tools: list[Any]) -> list[dict[str, Any]]:
        return tools_to_openai_format(tools)

    async def complete_turn(self, messages: list[dict[str, Any]], tools: Any) -> tuple[str, list[AgentToolCall]]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=4096,
        )

        msg = response.choices[0].message
        assistant_text = msg.content or ""

        tool_calls: list[AgentToolCall] = []
        for tool_call in msg.tool_calls or []:
            raw_args = tool_call.function.arguments or "{}"
            try:
                arguments = json.loads(raw_args)
            except json.JSONDecodeError:
                logger.warning(f"工具参数解析失败，已回退为空对象: {raw_args}")
                arguments = {}

            tool_calls.append(
                AgentToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=arguments,
                )
            )

        return assistant_text, tool_calls