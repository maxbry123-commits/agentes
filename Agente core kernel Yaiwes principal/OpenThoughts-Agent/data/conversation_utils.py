"""Shared conversation-field helpers for standard data generation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Optional


def extract_user_prompt(conversations: Sequence[Mapping[str, Any]]) -> str:
    """Return the first user/human message, preserving legacy fallback behavior."""
    for message in conversations:
        role = message.get("from") or message.get("role", "")
        content = message.get("value") or message.get("content", "")
        if role in ("human", "user"):
            return content
    if conversations:
        message = conversations[-1]
        return message.get("value") or message.get("content", "")
    return ""


def extract_system_prompt(conversations: Sequence[Mapping[str, Any]]) -> Optional[str]:
    """Return the first system message, if present."""
    for message in conversations:
        role = message.get("from") or message.get("role", "")
        content = message.get("value") or message.get("content", "")
        if role == "system":
            return content
    return None
