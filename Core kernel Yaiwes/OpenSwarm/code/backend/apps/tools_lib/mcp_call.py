"""Call ONE tool on a connected MCP server, over whichever transport its config names.

The dispatch half of the apps-SDK tool grant gate: the grant decides IF a call may happen,
this module is HOW it happens. Reuses the exact credential guards and config derivation the
discovery path uses, so an app can never reach a server an agent could not."""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException
from typeguard import typechecked


@typechecked
def render_tool_result(content: List[Any]) -> str:
    """Flatten MCP content blocks to the text an app can actually use."""
    parts: List[str] = []
    for block in content:
        kind = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
        if kind == "text":
            parts.append(getattr(block, "text", None) or (block.get("text", "") if isinstance(block, dict) else ""))
        else:
            try:
                parts.append(json.dumps(block if isinstance(block, dict) else block.__dict__))
            except Exception:
                parts.append(str(block))
    return "\n".join(p for p in parts if p)


@typechecked
async def call_mcp_tool_stdio(command: str, args: Optional[List[str]], env: Optional[Dict[str, str]], tool_name: str, arguments: Dict[str, Any]) -> str:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=command, args=args or [], env={**os.environ, **(env or {})})
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            text = render_tool_result(list(result.content))
            if getattr(result, "isError", False):
                raise HTTPException(status_code=502, detail=text or f"{tool_name} returned an error")
            return text


@typechecked
async def call_mcp_tool_http(url: str, headers: Optional[Dict[str, str]], tool_name: str, arguments: Dict[str, Any]) -> str:
    from backend.apps.tools_lib.mcp_discovery import parse_sse_json

    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **(headers or {})}
    async with httpx.AsyncClient(timeout=90.0) as client:
        init_resp = await client.post(url, headers=h, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "self-swarm", "version": "0.1.0"}},
        })
        if init_resp.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"MCP initialize failed: {init_resp.status_code}")
        session_id = init_resp.headers.get("mcp-session-id", "")
        if session_id:
            h["mcp-session-id"] = session_id
        await client.post(url, headers=h, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
        call_resp = await client.post(url, headers=h, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        })
        if call_resp.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"MCP tools/call failed: {call_resp.status_code}")
        data = parse_sse_json(call_resp.text) if "text/event-stream" in call_resp.headers.get("content-type", "") else call_resp.json()
        if not data:
            raise HTTPException(status_code=502, detail="Empty response from MCP server")
        if data.get("error"):
            raise HTTPException(status_code=502, detail=str(data["error"].get("message", data["error"])))
        result = data.get("result", {})
        text = render_tool_result(result.get("content", []))
        if result.get("isError"):
            raise HTTPException(status_code=502, detail=text or f"{tool_name} returned an error")
        return text


@typechecked
async def call_mcp_tool_sse(url: str, headers: Optional[Dict[str, str]], tool_name: str, arguments: Dict[str, Any]) -> str:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    from mcp.types import Implementation

    try:
        async with sse_client(url=url, headers=headers, timeout=30, sse_read_timeout=90) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream, client_info=Implementation(name="self-swarm", version="0.1.0")) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                text = render_tool_result(list(result.content))
                if getattr(result, "isError", False):
                    raise HTTPException(status_code=502, detail=text or f"{tool_name} returned an error")
                return text
    except BaseExceptionGroup as eg:
        first = eg.exceptions[0] if eg.exceptions else eg
        raise HTTPException(status_code=502, detail=f"SSE tool call failed: {first}") from first


@typechecked
async def call_mcp_tool(tool_id: str, tool_name: str, arguments: Dict[str, Any]) -> str:
    """Resolve the tool's transport + credentials exactly like discovery does, then call it."""
    from backend.apps.tools_lib.mcp_config import derive_mcp_config
    from backend.apps.tools_lib.oauth_tokens import refresh_airtable_token, refresh_google_token, refresh_hubspot_token
    from backend.apps.tools_lib.tools_lib import load

    tool = load(tool_id)
    if not tool.enabled:
        raise HTTPException(status_code=403, detail=f"{tool.name} is disabled in Settings.")
    if tool.auth_type == "env_vars" and not tool.credentials:
        raise HTTPException(status_code=409, detail=f"{tool.name} isn't connected yet.")
    # Same refresh dance as discover_tools: a stale OAuth token fails the child, not the user.
    if tool.auth_type == "oauth2" and tool.auth_status == "connected" and tool.oauth_tokens.get("refresh_token"):
        if tool.name.lower() == "airtable":
            refreshed = await refresh_airtable_token(tool)
        elif tool.name.lower() == "hubspot":
            refreshed = await refresh_hubspot_token(tool)
        else:
            refreshed = await refresh_google_token(tool)
        if not refreshed and tool.oauth_tokens.get("access_token") and time.time() >= tool.oauth_tokens.get("token_expiry", 0) - 60:
            raise HTTPException(status_code=502, detail=f"OAuth token expired and refresh failed. Reconnect {tool.name}.")

    config = derive_mcp_config(tool)
    if not config:
        raise HTTPException(status_code=400, detail="Cannot derive MCP config for tool")
    transport = config.get("type", "")
    call = None
    if transport == "stdio":
        if not config.get("command"):
            raise HTTPException(status_code=400, detail="stdio transport requires a 'command'")
        call = call_mcp_tool_stdio(config["command"], config.get("args"), config.get("env"), tool_name, arguments)
    elif transport in ("http", "sse") or config.get("url"):
        url = config.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="HTTP/SSE transport requires a 'url'")
        if transport == "sse":
            call = call_mcp_tool_sse(url, config.get("headers"), tool_name, arguments)
        else:
            call = call_mcp_tool_http(url, config.get("headers"), tool_name, arguments)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported MCP transport type: '{transport}'.")
    try:
        return await asyncio.wait_for(call, timeout=120.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail=f"{tool_name} timed out after 120s")
