"""Jarvis MCP module -- Client, Server, Resources, Prompts, Discovery, Bridge."""

from cognithor.mcp.bridge import MCPBridge
from cognithor.mcp.client import JarvisMCPClient, ToolCallResult
from cognithor.mcp.discovery import AgentCard, DiscoveryManager
from cognithor.mcp.prompts import JarvisPromptProvider
from cognithor.mcp.resources import JarvisResourceProvider
from cognithor.mcp.server import (
    JarvisMCPServer,
    MCPPrompt,
    MCPPromptArgument,
    MCPResource,
    MCPResourceTemplate,
    MCPServerConfig,
    MCPServerMode,
    MCPToolDef,
)

__all__ = [
    # Discovery (v15 new)
    "AgentCard",
    "DiscoveryManager",
    # Client (existing)
    "JarvisMCPClient",
    # Server (v15 new)
    "JarvisMCPServer",
    "JarvisPromptProvider",
    # Providers (v15 new)
    "JarvisResourceProvider",
    # Bridge (v15 new)
    "MCPBridge",
    "MCPPrompt",
    "MCPPromptArgument",
    "MCPResource",
    "MCPResourceTemplate",
    "MCPServerConfig",
    "MCPServerMode",
    "MCPToolDef",
    "ToolCallResult",
]
