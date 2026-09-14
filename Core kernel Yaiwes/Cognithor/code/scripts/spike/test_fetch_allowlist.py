"""Spike test 2 — vLLM video_url fetch-allowlist policy.

Sends three video_url completions from inside the spike container's
perspective: a public HTTPS CDN URL, a localhost URL (host.docker.internal
served by a tiny ad-hoc Python file-server), and a 127.0.0.1 URL that
resolves inside the container (should fail). Records what vLLM fetches
and what it blocks. This output tells us whether we need a per-request
allowed_media_domains flag or if vLLM is fully permissive by default.
"""

from __future__ import annotations

import http.server
import os
import socketserver
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "http://127.0.0.1:8765/v1"
PUBLIC_URL = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
MODEL_ID = os.environ.get("SPIKE_MODEL_ID", "QuantTrio/Qwen3.6-35B-A3B-AWQ")
LOCAL_PORT = 8799
LOCAL_HOST_CONTAINER = f"http://host.docker.internal:{LOCAL_PORT}/sample.mp4"
LOCAL_HOST_LOOPBACK_IN_CONTAINER = f"http://127.0.0.1:{LOCAL_PORT}/sample.mp4"


def start_file_server(serve_dir: Path) -> tuple[socketserver.TCPServer, threading.Thread]:
    os.chdir(serve_dir)
    handler = http.server.SimpleHTTPRequestHandler
    server = socketserver.TCPServer(("0.0.0.0", LOCAL_PORT), handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, t


def prepare_sample_file(target: Path) -> None:
    """Copy the public BigBuckBunny sample into a local file for serving."""
    print(f"[prep] downloading {PUBLIC_URL} to {target}")
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        with client.stream("GET", PUBLIC_URL) as r:
            r.raise_for_status()
            with target.open("wb") as f:
                for chunk in r.iter_bytes(65536):
                    f.write(chunk)
    print(f"[prep] wrote {target.stat().st_size} bytes")


def post_chat(video_url: str) -> tuple[int, str]:
    payload: dict[str, Any] = {
        "model": MODEL_ID,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": video_url}},
                    {"type": "text", "text": "Ein Satz zum Video."},
                ],
            }
        ],
        "max_tokens": 32,
        "temperature": 0.0,
    }
    with httpx.Client(timeout=180.0) as client:
        try:
            r = client.post(f"{BASE_URL}/chat/completions", json=payload)
            return r.status_code, r.text[:400]
        except Exception as e:
            return 0, f"EXC: {type(e).__name__}: {e}"


def main() -> int:
    serve_dir = Path(tempfile.mkdtemp(prefix="vllm-spike-"))
    sample = serve_dir / "sample.mp4"
    prepare_sample_file(sample)

    server, _ = start_file_server(serve_dir)
    print(f"[srv] local HTTP server on 0.0.0.0:{LOCAL_PORT}")
    time.sleep(0.5)

    try:
        cases = [
            ("public_https", PUBLIC_URL),
            ("host_docker_internal", LOCAL_HOST_CONTAINER),
            ("loopback_127_in_container", LOCAL_HOST_LOOPBACK_IN_CONTAINER),
        ]
        for name, url in cases:
            print(f"=== {name}: {url}")
            status, body = post_chat(url)
            print(f"    -> status={status}")
            print(f"    -> body={body[:300]}")
            print()
    finally:
        server.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
