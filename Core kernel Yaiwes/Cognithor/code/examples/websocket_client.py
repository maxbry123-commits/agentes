"""Cognithor WebSocket Client Example.

Connects to the Cognithor WebUI WebSocket and sends a message.
Demonstrates the full auth + chat flow.

Usage:
    pip install websockets
    python examples/websocket_client.py "What is the weather in Berlin?"
"""

from __future__ import annotations

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("Install websockets: pip install websockets")
    sys.exit(1)

# Default connection settings (match Vite dev server)
HOST = "localhost"
PORT = 8080
SESSION_ID = "example-session-001"


async def get_auth_token(host: str, port: int) -> str | None:
    """Fetch bootstrap token from the REST API."""
    try:
        import urllib.request

        url = f"http://{host}:{port}/api/v1/bootstrap"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("token")
    except Exception as exc:
        print(f"[WARN] Could not fetch auth token: {exc}")
        return None


async def main(message: str) -> None:
    uri = f"ws://{HOST}:{PORT}/ws/{SESSION_ID}"

    print(f"Connecting to {uri} ...")
    async with websockets.connect(uri) as ws:
        # 1. Authenticate (must be first message)
        token = await get_auth_token(HOST, PORT)
        if token:
            await ws.send(json.dumps({"type": "auth", "token": token}))
            print("[AUTH] Token sent")

        # 2. Send user message
        await ws.send(
            json.dumps(
                {
                    "type": "user_message",
                    "text": message,
                    "session_id": SESSION_ID,
                }
            )
        )
        print(f"[SENT] {message}")

        # 3. Listen for responses
        full_response = ""
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=120)
            except TimeoutError:
                print("[TIMEOUT] No response within 120s")
                break

            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "stream_token":
                token_text = data.get("token", data.get("content", ""))
                print(token_text, end="", flush=True)
                full_response += token_text

            elif msg_type == "stream_end":
                print()  # newline after streaming
                break

            elif msg_type == "assistant_message":
                print(f"[ASSISTANT] {data.get('text', data.get('content', ''))}")
                break

            elif msg_type == "tool_start":
                print(f"  [TOOL] {data.get('tool', data.get('name', '?'))} ...")

            elif msg_type == "tool_result":
                print("  [TOOL] Done")

            elif msg_type == "status_update":
                print(f"  [{data.get('status', data.get('text', ''))}]")

            elif msg_type == "error":
                print(f"[ERROR] {data.get('message', data.get('error', ''))}")
                break

            elif msg_type == "approval_request":
                print(f"  [APPROVAL] {data.get('tool', '?')}: {data.get('reason', '')}")
                # Auto-approve for this example
                await ws.send(
                    json.dumps(
                        {
                            "type": "approval_response",
                            "id": data.get("id", data.get("request_id")),
                            "approved": True,
                            "session_id": SESSION_ID,
                        }
                    )
                )
                print("  [APPROVAL] Auto-approved")

            elif msg_type == "pong":
                pass  # heartbeat

            else:
                print(f"  [???] {msg_type}: {data}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f'Usage: python {sys.argv[0]} "Your message here"')
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
