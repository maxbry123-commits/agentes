#!/usr/bin/env python3
"""Stdio MCP server letting an agent read and write the user's memory facts.

Two tools, MemoryRead and MemoryWrite, backed by /api/memory. Always on while the
memory feature is enabled (register_builtin_mcp_servers keys the module on the
Settings toggle, so "off" removes the tools AND the prompt block together). Writes
go through one atomic batch endpoint: every op lands or none do, and the cap is
checked on the final state, so consolidate-then-add is a single call. The store,
the cap, and the dedupe all live server-side; this thin client can't weaken them."""

import json
import os
import sys
import urllib.error
import urllib.request

BACKEND_PORT = os.environ.get("OPENSWARM_PORT", "8324")
BACKEND_AUTH = os.environ.get("OPENSWARM_AUTH_TOKEN", "")
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}/api/memory"


TOOLS = [
    {
        "name": "MemoryRead",
        "description": (
            "List the user's saved memory facts with their ids and the capacity meter. "
            "Call this before MemoryWrite when replacing or removing, so you target the "
            "right fact id. The user sees and edits this exact list in Settings > Memory."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "MemoryWrite",
        "description": (
            "Save, update, or prune the user's memory facts; they persist across ALL future "
            "chats. Pass `ops` as a list applied atomically: "
            "{action:'add', text:'...'} | {action:'replace', id:'...', text:'...'} | "
            "{action:'remove', id:'...'}. Save short, standalone, durable facts (preferences, "
            "recurring context), never session trivia, never secrets. Near-duplicate adds "
            "update the existing fact. If memory is full, the error returns every current "
            "fact: consolidate with replace/remove AND retry the add in ONE batch. A success "
            "is final; do not repeat or double-check it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "ops": {
                    "type": "array",
                    "description": "Operations applied in order, atomically (all or none).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["add", "replace", "remove"]},
                            "text": {"type": "string", "description": "The fact text (add/replace)."},
                            "id": {"type": "string", "description": "Fact id from MemoryRead (replace/remove)."},
                        },
                        "required": ["action"],
                        "additionalProperties": False,
                    },
                    "minItems": 1,
                },
            },
            "required": ["ops"],
            "additionalProperties": False,
        },
    },
]


def send_response(id_, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def call_backend(method: str, path: str, payload=None) -> dict:
    headers = {"Content-Type": "application/json"}
    if BACKEND_AUTH:
        headers["Authorization"] = f"Bearer {BACKEND_AUTH}"
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{BACKEND_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode() if e.fp else str(e)
        return {"error": f"HTTP {e.code}: {detail}"}
    except Exception as e:
        return {"error": str(e)}


def p_render_facts(facts: list) -> str:
    if not facts:
        return "(no facts saved yet)"
    return "\n".join(f"- [{f.get('id')}] {f.get('text')} (source: {f.get('source')})" for f in facts)


def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    if tool_name == "MemoryRead":
        result = call_backend("GET", "")
        if "error" in result:
            return {"content": [{"type": "text", "text": f"Error: {result['error']}"}], "isError": True}
        facts = result.get("facts", [])
        chars = sum(len(f.get("text", "")) for f in facts)
        return {"content": [{"type": "text", "text": f"Memory [{len(facts)}/60 facts, {chars} chars]:\n{p_render_facts(facts)}"}]}

    if tool_name == "MemoryWrite":
        ops = arguments.get("ops")
        if not isinstance(ops, list) or not ops:
            return {"content": [{"type": "text", "text": "Error: `ops` must be a non-empty list."}], "isError": True}
        result = call_backend("POST", "/ops", {"ops": ops})
        if "error" in result:
            return {"content": [{"type": "text", "text": f"Error: {result['error']}"}], "isError": True}
        lines = list(result.get("outcomes", []))
        if result.get("note"):
            lines.append(result["note"])
        lines.append(f"Usage: {result.get('usage', '')}")
        if not result.get("ok") and result.get("facts") is not None:
            lines.append("Current facts:\n" + p_render_facts(result["facts"]))
        return {"content": [{"type": "text", "text": "\n".join(lines)}], "isError": not result.get("ok", False)}

    return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = msg.get("method")
        id_ = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            send_response(id_, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "openswarm-memory-meta", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            send_response(id_, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            try:
                send_response(id_, handle_tool_call(tool_name, arguments))
            except Exception as e:
                send_response(id_, error={"code": -32000, "message": str(e)})
        elif method == "resources/list":
            send_response(id_, {"resources": []})
        elif method == "prompts/list":
            send_response(id_, {"prompts": []})
        elif id_ is not None:
            send_response(id_, error={"code": -32601, "message": f"Method not found: {method}"})


if __name__ == "__main__":
    main()
