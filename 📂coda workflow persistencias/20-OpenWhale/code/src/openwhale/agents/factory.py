"""智能体工厂。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .claude_code_agent import ClaudeCodeChallengeAgent
from .openai_agent import OpenAIChallengeAgent
from .deepagents_agent import DeepAgentsChallengeAgent


def create_agent(config: dict[str, str], on_message: Callable[[str, str], None] | None = None):
    """根据配置创建智能体实例。"""
    backend = config.get("AGENT_BACKEND", "openai_compat").lower()

    if backend in {"openai", "openai_compat", "minimax", "chat_completions"}:
        return OpenAIChallengeAgent(
            api_key=config["MODEL_API_KEY"],
            base_url=config["MODEL_BASE_URL"],
            model=config["MODEL_ID"],
            model_name=config["MODEL_NAME"],
            on_message=on_message,
        )

    if backend in {"claude", "claude_code", "claude_sdk", "claude-agent-sdk"}:
        return ClaudeCodeChallengeAgent(
            config=config,
            on_message=on_message,
        )

    if backend == "deepagents":
        return DeepAgentsChallengeAgent(
            config=config,
            on_message=on_message,
        )

    raise NotImplementedError(
        "暂不支持的智能体基座: "
        f"{backend}. 目前可用: openai_compat/minimax/openai/chat_completions/claude_code/deepagents"
    )