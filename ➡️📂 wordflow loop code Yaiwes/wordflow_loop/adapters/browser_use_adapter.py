"""Minimal trusted adapter for Browser Use.

This module never launches a browser. It only validates and emits a runtime request
for an authorized sandbox/runtime to execute later.
"""
from __future__ import annotations

from urllib.parse import urlparse

COMPONENT_ID = "yaiwes.browser_use"
COMPONENT_VERSION = "0.13.10"
SOURCE_REPO = "browser-use/browser-use"
SOURCE_COMMIT = "5c892e013a73e6622e6f50336e1eb0aa2c4405f2"
ENTRY_POINT = "browser_use.Agent"


def descriptor() -> dict:
    return {
        "component_id": COMPONENT_ID,
        "version": COMPONENT_VERSION,
        "source_repo": SOURCE_REPO,
        "source_commit": SOURCE_COMMIT,
        "entry_point": ENTRY_POINT,
        "execution_authorized": False,
        "requires_sandbox": True,
        "requires_fables_registration": True,
    }


def build_request(task: str, start_url: str | None = None) -> dict:
    task = task.strip()
    if not task:
        raise ValueError("task is required")
    if len(task) > 4096:
        raise ValueError("task too long")

    if start_url is not None:
        parsed = urlparse(start_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("start_url must be http(s)")

    return {
        "component_id": COMPONENT_ID,
        "entry_point": ENTRY_POINT,
        "kwargs": {"task": task},
        "start_url": start_url,
        "execution_authorized": False,
        "requires_sandbox": True,
        "allowed_actions": ["browser.navigate", "browser.read", "browser.interact"],
    }


def health() -> dict:
    """Static adapter health only; never claims Browser Use runtime health."""
    return {
        "ok": True,
        "scope": "adapter_static_only",
        "browser_runtime_verified": False,
        "execution_authorized": False,
    }
