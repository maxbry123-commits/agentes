#!/usr/bin/env python3
"""
Gemma 4 VPS API — OpenAI-compatible wrapper para Ollama.
Sirve en :8002. Compatible con /v1/chat/completions y /v1/models.
"""
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import URLError

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_NAME = "gemma3:1b"
PUBLIC_NAME = "gemma-4-vps"  # nombre que ve OpenClaw
API_PORT = 8002

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silenciar

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            return self._send_json(200, {"status": "ok", "model": PUBLIC_NAME, "real": MODEL_NAME})
        if self.path == "/v1/models" or self.path == "/v1/models/":
            return self._send_json(200, {
                "object": "list",
                "data": [{
                    "id": PUBLIC_NAME,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "local",
                    "real_model": MODEL_NAME
                }]
            })
        return self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            return self._send_json(404, {"error": "only /v1/chat/completions supported"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            return self._send_json(400, {"error": f"bad json: {e}"})

        messages = payload.get("messages", [])
        if not messages:
            return self._send_json(400, {"error": "no messages"})

        # Prompt plano
        prompt_parts = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(f"User: {content}")
        prompt_parts.append("Assistant:")
        prompt = "\n".join(prompt_parts)

        # Llamar a Ollama
        try:
            req = Request(
                f"{OLLAMA_URL}/api/generate",
                data=json.dumps({"model": MODEL_NAME, "prompt": prompt, "stream": False}).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urlopen(req, timeout=60) as r:
                ollama_resp = json.loads(r.read())
        except URLError as e:
            return self._send_json(502, {"error": f"ollama error: {e}"})

        text = ollama_resp.get("response", "")
        return self._send_json(200, {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": PUBLIC_NAME,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": ollama_resp.get("prompt_eval_count", 0),
                "completion_tokens": ollama_resp.get("eval_count", 0),
                "total_tokens": ollama_resp.get("prompt_eval_count", 0) + ollama_resp.get("eval_count", 0)
            }
        })


if __name__ == "__main__":
    print(f"Gemma 4 VPS API on :{API_PORT} (model={PUBLIC_NAME} -> {MODEL_NAME})")
    ThreadingHTTPServer(("0.0.0.0", API_PORT), Handler).serve_forever()
