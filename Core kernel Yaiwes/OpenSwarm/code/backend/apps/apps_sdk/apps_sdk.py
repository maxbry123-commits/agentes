"""REST surface for OpenSwarm-built apps (the app-side SDK's host half).

Apps already hold the install token (frontend via ?token=, backends via
OPENSWARM_HOST_TOKEN_FILE), and workflows/agents already expose first-class
routes the SDK helpers call directly. This SubApp adds only what REST could
not do before: a provider-agnostic LLM completion, and an agent spawn that
can land its card at a position on the canvas.
"""

import re
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

from backend.config.Apps import SubApp


@asynccontextmanager
async def apps_sdk_lifespan() -> AsyncIterator[None]:
    yield


apps_sdk = SubApp("apps-sdk", apps_sdk_lifespan)


class LlmRequest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    prompt: str
    system: Optional[str] = None
    # Short model name (sonnet/haiku/gpt-5-mini/...); absent means the cheap tier of whatever provider the user runs.
    model: Optional[str] = None
    max_tokens: int = 1024


class LlmReply(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    text: str
    model: str


@apps_sdk.router.post("/llm")
@typechecked
async def llm(body: LlmRequest) -> LlmReply:
    from backend.apps.agents.providers.registry import resolve_aux_model, resolve_model_id_for_sdk
    from backend.apps.settings.credentials import get_anthropic_client_for_model
    from backend.apps.settings.settings import load_settings

    if not body.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt is empty")
    settings = load_settings()
    if body.model:
        api_model = resolve_model_id_for_sdk(body.model, settings)
    else:
        api_model, _ = await resolve_aux_model(settings)
    client = get_anthropic_client_for_model(settings, api_model)
    kwargs: Dict[str, Any] = {
        "model": api_model,
        "max_tokens": max(1, min(body.max_tokens, 8192)),
        "messages": [{"role": "user", "content": body.prompt}],
    }
    if body.system:
        kwargs["system"] = body.system
    try:
        # STREAM, never .create(): 9router's non-Anthropic lanes answer as real SSE that the non-streaming client parses to empty content.
        async with client.messages.stream(**kwargs) as stream:
            resp = await stream.get_final_message()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
    text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
    return LlmReply(text=text, model=api_model)


class SpawnAgentRequest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    prompt: str
    name: str = "Agent"
    model: Optional[str] = None
    dashboard_id: Optional[str] = None
    # Canvas-space position for the spawned card; both present or the placement broadcast is skipped.
    x: Optional[float] = None
    y: Optional[float] = None


class SpawnAgentReply(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    session_id: str


class ToolsListRequest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    output_id: Optional[str] = None


@typechecked
def resolve_app_from_origin(origin: str) -> Optional[str]:
    """Server-derived app identity: a webview app's fetch carries Origin http://127.0.0.1:<port>,
    and the runtime manager knows which app owns that port. Stronger than a self-reported id."""
    try:
        from urllib.parse import urlparse

        from backend.apps.outputs.runtime import manager

        parsed = urlparse(origin)
        if parsed.hostname not in ("127.0.0.1", "localhost") or not parsed.port:
            return None
        for registry in (manager.runtimes, manager.idle_lru):
            for rt in registry.values():
                if parsed.port in (rt.frontend_port, rt.port):
                    return rt.workspace_id
    except Exception:
        return None
    return None


P_SERVE_REFERER_RE = re.compile(r"/api/outputs/([0-9a-f]{16,64})/serve/")


@typechecked
def resolve_app_from_referer(referer: str) -> Optional[str]:
    """Static serve-mode apps load from /api/outputs/<id>/serve/, so their fetches carry that path
    as Referer; the browser owns that header, making it as trustworthy as the webview boundary."""
    m = P_SERVE_REFERER_RE.search(referer or "")
    return m.group(1) if m else None


class AppToolServerRow(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: str
    name: str
    description: str


@apps_sdk.router.post("/tools/list")
@typechecked
async def tools_list(body: ToolsListRequest) -> Dict[str, Any]:
    """Connected tool servers an app could ask to use: the SAME enabled, vetted set agents see,
    nothing wider. Sub-tools come from POST /api/tools/{id}/discover; calls go through the grant."""
    from backend.apps.tools_lib.tools_lib import load_all_tools

    rows = [
        AppToolServerRow(id=tool.id, name=tool.name, description=tool.description[:200])
        for tool in load_all_tools()
        if tool.mcp_config and tool.enabled and tool.auth_status in ("configured", "connected")
    ]
    return {"servers": [r.model_dump() for r in rows]}


class ToolCallRequest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    # Minted per-app token (OPENSWARM_APP_TOKEN) for app-backend callers; webviews ride Origin instead.
    app_token: Optional[str] = None
    # Legacy self-report, kept ONLY as a label fallback; never trusted for identity.
    output_id: Optional[str] = None
    # "<tool_id>:<ToolName>" from /tools/list.
    tool: str
    args: Dict[str, Any] = {}


@apps_sdk.router.post("/tools/call")
@typechecked
async def tools_call(body: ToolCallRequest, request: Request) -> Dict[str, Any]:
    """The grant gate: denied is refused flat, ungranted blocks on a user approval card, granted
    dispatches through the same transport + credential path agents use. Enforced server-side."""
    import json as p_json

    from backend.apps.apps_sdk.tool_grants import grant_status, request_grant
    from backend.apps.outputs.workspace_io import load_output
    from backend.apps.tools_lib.mcp_call import call_mcp_tool

    from backend.apps.apps_sdk.app_identity import resolve_app_token

    # Identity is server-derived only: the Origin port map (vite webviews), the serve-path Referer
    # (static webviews, whose Origin is the backend itself; a page cannot fake its own Referer), or
    # the minted per-app token (app backends). A bare self-reported output_id is never enough, or
    # any local process could borrow another app's remembered grants.
    output_id = (
        resolve_app_from_origin(request.headers.get("origin", ""))
        or resolve_app_from_referer(request.headers.get("referer", ""))
        or resolve_app_token(body.app_token or "")
    )
    if not output_id:
        raise HTTPException(status_code=403, detail="Could not identify the calling app; tool access is per-app.")
    tool_id, sep, tool_name = body.tool.partition(":")
    if not sep or not tool_id or not tool_name:
        raise HTTPException(status_code=422, detail="tool must be '<tool_id>:<ToolName>' from /tools/list")
    status = grant_status(output_id, body.tool)
    if status == "denied":
        raise HTTPException(status_code=403, detail=f"The user has denied this app access to {tool_name}.")
    if status != "granted":
        try:
            output = load_output(output_id)
            app_name = output.name if output else output_id
        except Exception:
            app_name = output_id
        allowed = await request_grant(output_id, app_name, body.tool, tool_name, p_json.dumps(body.args)[:400])
        if not allowed:
            raise HTTPException(status_code=403, detail=f"The user did not approve this app using {tool_name}.")
    text = await call_mcp_tool(tool_id, tool_name, body.args)
    return {"result": text}


class GrantResolveRequest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    request_id: str
    allow: bool
    remember: bool = False


@apps_sdk.router.delete("/tools/grants/{output_id}")
@typechecked
async def reset_tool_grants(output_id: str) -> Dict[str, bool]:
    from backend.apps.apps_sdk.tool_grants import clear_grants

    clear_grants(output_id)
    return {"ok": True}


@apps_sdk.router.post("/tools/grant")
@typechecked
async def tools_grant(body: GrantResolveRequest) -> Dict[str, bool]:
    from backend.apps.apps_sdk.tool_grants import resolve_grant

    return {"ok": resolve_grant(body.request_id, body.allow, body.remember)}


@apps_sdk.router.post("/agents/spawn")
@typechecked
async def spawn_agent(body: SpawnAgentRequest) -> SpawnAgentReply:
    import asyncio

    from backend.apps.agents.agent_manager import agent_manager
    from backend.apps.agents.core.models import AgentConfig
    from backend.apps.agents.core.ws_manager import ws_manager

    if not body.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt is empty")
    dashboard_id = body.dashboard_id
    if dashboard_id is None:
        # An app webview has no idea which dashboard it lives on; without one the canvas lifecycle
        # never creates a card, so the spawn is real but invisible. Most-recent dashboard wins.
        from backend.apps.dashboards.dashboards import load_all
        boards = sorted(load_all(), key=lambda d: d.updated_at, reverse=True)
        dashboard_id = boards[0].id if boards else None
    config = AgentConfig(
        name=body.name,
        prompt=body.prompt,
        model=body.model or "sonnet",
        dashboard_id=dashboard_id,
    )
    session = await agent_manager.launch_agent(config)
    asyncio.create_task(agent_manager.send_message(session.id, body.prompt))
    if body.x is not None and body.y is not None:
        await ws_manager.broadcast_global("apps_sdk:place_agent_card", {
            "session_id": session.id,
            "dashboard_id": dashboard_id,
            "x": body.x,
            "y": body.y,
        })
    return SpawnAgentReply(session_id=session.id)
