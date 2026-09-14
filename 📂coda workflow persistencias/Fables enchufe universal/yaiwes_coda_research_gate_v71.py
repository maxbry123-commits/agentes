from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any, Iterable

import yaiwes_coda_bus_v7 as bus

SCHEMA = "yaiwes.coda.research-gate/v7.1"
MCP_PROTOCOL_VERSION = "2026-07-28"


def _validated_endpoint(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.username or parsed.password:
        raise ValueError("credentials must not be embedded in endpoint URLs")
    if parsed.scheme == "https" and parsed.hostname:
        return url
    if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        return url
    raise ValueError("research endpoint must use HTTPS, except localhost")


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> Any:
    endpoint = _validated_endpoint(url)
    data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    request_headers = {
        "Content-Type": "application/json",
        "User-Agent": "YAIWES-CODA/7.1 research-gate",
    }
    request_headers.update(headers or {})
    req = urllib.request.Request(endpoint, data=data, headers=request_headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


class ApiResearchAdapter:
    def __init__(self, url: str, token_env: str = "YAIWES_RESEARCH_API_TOKEN"):
        self.url = _validated_endpoint(url)
        self.token_env = token_env

    def __call__(self, payload: dict[str, Any]) -> Any:
        headers: dict[str, str] = {}
        token = os.environ.get(self.token_env)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return _post_json(self.url, payload, headers)


class McpResearchAdapter:
    def __init__(
        self,
        url: str,
        tool_name: str = "search",
        token_env: str = "YAIWES_RESEARCH_MCP_TOKEN",
    ):
        self.url = _validated_endpoint(url)
        self.tool_name = tool_name.strip() or "search"
        self.token_env = token_env

    def __call__(self, payload: dict[str, Any]) -> Any:
        request_id = "yaiwes-" + bus._digest(payload)[:16]
        body = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": self.tool_name,
                "arguments": {
                    "query": payload.get("query"),
                    "component": payload.get("component"),
                    "task": payload.get("task"),
                    "previous_output": payload.get("previous_output"),
                    "learned_context": payload.get("learned_context"),
                },
                "_meta": {
                    "io.modelcontextprotocol/clientInfo": {
                        "name": "yaiwes-coda",
                        "version": "7.1",
                    }
                },
            },
        }
        headers = {
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
            "Mcp-Method": "tools/call",
            "Mcp-Name": self.tool_name,
        }
        token = os.environ.get(self.token_env)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = _post_json(self.url, body, headers)
        if isinstance(response, dict) and response.get("error"):
            raise RuntimeError(f"MCP research error: {response['error']}")
        return response.get("result") if isinstance(response, dict) and "result" in response else response


def build_research_broker() -> bus.ToolBroker:
    """Build the canonical production broker.

    Discovery remains metadata-only. Real research executes only through an
    explicitly configured API or MCP endpoint.
    """
    broker = bus.ToolBroker(bus.McpRegistryDiscovery())
    mcp_url = os.environ.get("YAIWES_RESEARCH_MCP_URL", "").strip()
    api_url = os.environ.get("YAIWES_RESEARCH_API_URL", "").strip()

    if mcp_url:
        tool_name = os.environ.get("YAIWES_RESEARCH_MCP_TOOL", "search").strip() or "search"
        broker.register(
            bus.ToolDescriptor(
                capability="web.research",
                name=f"configured-mcp:{tool_name}",
                source="configured-mcp",
                description="approved benign web research through configured MCP",
                risk="benign",
                executable=True,
            ),
            McpResearchAdapter(mcp_url, tool_name=tool_name),
        )
        return broker

    if api_url:
        broker.register(
            bus.ToolDescriptor(
                capability="web.research",
                name="configured-research-api",
                source="configured-api",
                description="approved benign web research through configured JSON API",
                risk="benign",
                executable=True,
            ),
            ApiResearchAdapter(api_url),
        )
        return broker

    raise RuntimeError(
        "web.research is required: configure YAIWES_RESEARCH_MCP_URL or YAIWES_RESEARCH_API_URL"
    )


def run_coda_chain(state_root, task_id: str, task: dict[str, Any] | None = None) -> dict[str, Any]:
    broker = build_research_broker()
    report = bus.run_coda_chain(state_root, task_id, task, broker=broker)
    if report.get("research_cycles") != 24:
        raise RuntimeError("all 24 CODA research cycles are required")
    if any(item.get("research_status") != "EXECUTED" for item in report.get("evidence", [])):
        raise RuntimeError("a CODA research cycle did not execute")
    return {**report, "research_gate_schema": SCHEMA, "research_fail_closed": True}


def run_parallel_tasks(
    state_root,
    tasks: Iterable[dict[str, Any]],
    *,
    max_workers: int = 4,
) -> dict[str, Any]:
    broker = build_research_broker()
    report = bus.run_parallel_tasks(state_root, tasks, broker=broker, max_workers=max_workers)
    if report.get("status") != "COMPLETED":
        raise RuntimeError("parallel CODA research execution did not complete")
    return {**report, "research_gate_schema": SCHEMA, "research_fail_closed": True}
