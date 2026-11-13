"""兼容导出：保留旧的 openwhale.agent 导入路径。"""

from .agents import (
    AgentRunResult,
    AgentToolCall,
    BaseChallengeAgent,
    ClaudeCodeChallengeAgent,
    DeepAgentsChallengeAgent,
    OpenAIChallengeAgent,
    create_agent,
)

__all__ = [
    "AgentRunResult",
    "AgentToolCall",
    "BaseChallengeAgent",
    "ClaudeCodeChallengeAgent",
    "DeepAgentsChallengeAgent",
    "OpenAIChallengeAgent",
    "create_agent",
]
