"""Fail-closed adapter for Codebase Memory MCP.

This adapter never starts the upstream server. It emits read-only MCP tool-call
requests for an authorized runtime after canonical acquisition/read-back.
"""
from __future__ import annotations

from typing import Any, Mapping

COMPONENT_ID = "yaiwes.codebase_memory_mcp"
SOURCE_REPO = "https://github.com/DeusData/codebase-memory-mcp"
SOURCE_COMMIT = "2058d49a04b785315c9f5bb56b6e2365822b576b"
TRANSPORT = "mcp_stdio"

READ_ONLY_TOOLS = frozenset({
    "get_architecture",
    "semantic_query",
    "detect_changes",
})


def descriptor() -> dict[str, Any]:
    return {
        "component_id": COMPONENT_ID,
        "source_repo": SOURCE_REPO,
        "source_commit": SOURCE_COMMIT,
        "transport": TRANSPORT,
        "role": "codebase_structural_memory_preanalysis",
        "execution_authorized": False,
        "requires_acquisition_verified": True,
        "requires_fables_registration": True,
        "requires_sandbox": True,
        "read_only": True,
    }


def build_request(tool_name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
    tool = tool_name.strip()
    if tool not in READ_ONLY_TOOLS:
        raise ValueError("tool is not in read-only allowlist")
    if arguments is None:
        args: dict[str, Any] = {}
    elif isinstance(arguments, Mapping):
        args = dict(arguments)
    else:
        raise TypeError("arguments must be a mapping or None")
    return {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool, "arguments": args},
        "component_id": COMPONENT_ID,
        "execution_authorized": False,
        "requires_sandbox": True,
        "read_only": True,
    }


def health() -> dict[str, Any]:
    return {
        "ok": True,
        "scope": "adapter_static_only",
        "upstream_runtime_verified": False,
        "acquisition_verified": False,
        "execution_authorized": False,
    }
