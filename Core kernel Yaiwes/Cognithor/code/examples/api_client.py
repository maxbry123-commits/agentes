"""Cognithor REST API Client Example.

Demonstrates how to interact with the Control Center API (port 8741).

Usage:
    python examples/api_client.py
"""

from __future__ import annotations

import json
import urllib.request

BASE_URL = "http://localhost:8741"


def fetch(path: str, method: str = "GET", token: str = "", body: dict | None = None) -> dict:
    """Make an authenticated API request."""
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    # 1. Health check (no auth required)
    health = fetch("/api/v1/health")
    print(f"Health: {health}")

    # 2. Get auth token from bootstrap endpoint
    bootstrap = fetch("/api/v1/bootstrap")
    token = bootstrap.get("token", "")
    print(f"Token: {token[:16]}...")

    # 3. Get system status
    status = fetch("/api/v1/status", token=token)
    print(f"Status: {json.dumps(status, indent=2)}")

    # 4. Get system overview
    overview = fetch("/api/v1/overview", token=token)
    print(f"Overview: {json.dumps(overview, indent=2)}")

    # 5. List registered agents
    agents = fetch("/api/v1/agents", token=token)
    print(f"Agents: {json.dumps(agents, indent=2)}")

    # 6. Get current config (read-only view)
    config = fetch("/api/v1/config", token=token)
    print(f"Config keys: {list(config.keys()) if isinstance(config, dict) else 'N/A'}")


if __name__ == "__main__":
    main()
