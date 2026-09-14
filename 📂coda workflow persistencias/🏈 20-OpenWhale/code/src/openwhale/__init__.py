"""OpenWhale - 渗透测试智能体"""

__version__ = "0.1.0"
__author__ = "OpenWhale Team"

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
	"__version__",
	"__author__",
]
