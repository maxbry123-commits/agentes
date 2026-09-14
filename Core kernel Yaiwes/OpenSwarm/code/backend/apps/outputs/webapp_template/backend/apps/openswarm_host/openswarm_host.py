"""Call the OpenSwarm host (the user's models, workflows, agents) from app backend code.

The host hands this runtime a token FILE path via OPENSWARM_HOST_TOKEN_FILE (a path, not the
value, so token rotations are picked up on every call). See SDK.md at the workspace root for
the guide; the frontend twin of this module is frontend/src/openswarmHost.ts.
"""

import os
from typing import Any, Dict, List, Optional

import httpx
from typeguard import typechecked

HOST = os.environ.get("OPENSWARM_HOST_API", "http://127.0.0.1:8324")


@typechecked
def host_token() -> str:
    path = os.environ.get("OPENSWARM_HOST_TOKEN_FILE", "")
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


@typechecked
def p_request(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {host_token()}"}
    with httpx.Client(timeout=120.0) as client:
        resp = client.request(method, f"{HOST}{path}", json=body, headers=headers)
    if resp.status_code >= 400:
        raise RuntimeError(f"OpenSwarm host {path} -> {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    return data if isinstance(data, dict) else {"result": data}


@typechecked
def llm(prompt: str, system: Optional[str] = None, model: Optional[str] = None, max_tokens: int = 1024) -> str:
    """One-shot completion through the user's own configured providers/subscription.
    `model` is a short name (sonnet, haiku, ...); omit for the cheap tier."""
    reply = p_request("POST", "/api/apps-sdk/llm", {
        "prompt": prompt, "system": system, "model": model, "max_tokens": max_tokens,
    })
    return str(reply.get("text", ""))


@typechecked
def list_workflows() -> List[Dict[str, Any]]:
    """The user's saved workflows."""
    data = p_request("GET", "/api/workflows/list")
    flows = data.get("workflows", [])
    return flows if isinstance(flows, list) else []


@typechecked
def run_workflow(workflow_id: str) -> Dict[str, Any]:
    """Fire a workflow now; returns the host's report for the started run."""
    return p_request("POST", f"/api/workflows/{workflow_id}/run", {})


@typechecked
def list_workflow_runs() -> List[Dict[str, Any]]:
    """All workflow runs (newest first), for reading a fired run's status/result."""
    data = p_request("GET", "/api/workflows/runs/all")
    runs = data.get("runs", [])
    return runs if isinstance(runs, list) else []


@typechecked
def spawn_agent(
    prompt: str,
    name: str = "Agent",
    model: Optional[str] = None,
    dashboard_id: Optional[str] = None,
    x: Optional[float] = None,
    y: Optional[float] = None,
) -> str:
    """Spawn a real agent on the canvas with a first prompt; returns its session id.
    Give both x and y to place the card at a canvas position."""
    reply = p_request("POST", "/api/apps-sdk/agents/spawn", {
        "prompt": prompt, "name": name, "model": model,
        "dashboard_id": dashboard_id, "x": x, "y": y,
    })
    return str(reply.get("session_id", ""))


@typechecked
def agent_session(session_id: str) -> Dict[str, Any]:
    """A spawned agent's live state: status plus its transcript so far."""
    return p_request("GET", f"/api/agents/sessions/{session_id}")


@typechecked
def list_tools() -> List[Dict[str, Any]]:
    """The user's connected tool servers (Gmail, Calendar, custom MCP connectors, ...)."""
    reply = p_request("POST", "/api/apps-sdk/tools/list", {})
    servers = reply.get("servers", [])
    return servers if isinstance(servers, list) else []


@typechecked
def discover_tools(server_id: str) -> List[Dict[str, Any]]:
    """The individual tools a server exposes (name + input schema), straight from the live server."""
    reply = p_request("POST", f"/api/tools/{server_id}/discover", {})
    tools = reply.get("tools", [])
    return tools if isinstance(tools, list) else []


@typechecked
def call_tool(tool: str, args: Optional[Dict[str, Any]] = None) -> str:
    """Call one tool as '<server_id>:<ToolName>'. The FIRST call per tool shows the user an
    approval card (Allow once / Always / Never); a deny or an unanswered card raises with a 403.
    Design for that: it is the user saying no, not an error to retry. Backend processes are
    identified by the minted OPENSWARM_APP_TOKEN (injected by the host runtime)."""
    reply = p_request("POST", "/api/apps-sdk/tools/call", {
        "tool": tool,
        "args": args or {},
        "app_token": os.environ.get("OPENSWARM_APP_TOKEN") or None,
    })
    return str(reply.get("result", ""))
