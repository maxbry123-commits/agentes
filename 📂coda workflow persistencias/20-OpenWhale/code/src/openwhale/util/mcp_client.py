"""MCP 客户端 - 连接竞赛基础设施 MCP 服务器"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from loguru import logger
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import Tool


@asynccontextmanager
async def create_mcp_session(
    server_url: str,
    agent_token: str,
    timeout: float = 30.0,
):
    """创建 MCP 会话的异步上下文管理器（Streamable HTTP 传输）

    Args:
        server_url: MCP 服务器地址，例如 http://<SERVER_HOST>/mcp
        agent_token: 比赛平台 AGENT_TOKEN（用于 Authorization Header）
        timeout: 连接超时秒数
    """
    logger.info(f"正在连接 MCP 服务器: {server_url}")
    headers = {"Authorization": f"Bearer {agent_token}"}
    async with streamablehttp_client(
        server_url,
        headers=headers,
        timeout=timeout,
    ) as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info("MCP 会话初始化成功")
            yield session


async def list_tools(session: ClientSession) -> list[Tool]:
    """获取 MCP 服务器提供的所有工具列表"""
    result = await session.list_tools()
    tools = result.tools
    logger.info(f"获取到 {len(tools)} 个工具: {[t.name for t in tools]}")
    return tools


async def call_tool(
    session: ClientSession, tool_name: str, arguments: dict[str, Any]
) -> Any:
    """调用指定 MCP 工具

    Args:
        session: MCP 会话
        tool_name: 工具名称
        arguments: 工具参数

    Returns:
        工具调用结果
    """
    logger.debug(f"调用工具 [{tool_name}]，参数: {arguments}")
    result = await session.call_tool(tool_name, arguments)
    logger.debug(f"工具 [{tool_name}] 返回: {result}")
    return result


def tools_to_openai_format(tools: list[Tool]) -> list[dict[str, Any]]:
    """将 MCP 工具格式转换为 OpenAI Chat Completions 的工具格式"""
    openai_tools = []
    for tool in tools:
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema if tool.inputSchema else {"type": "object", "properties": {}},
            },
        }
        openai_tools.append(openai_tool)
    return openai_tools
