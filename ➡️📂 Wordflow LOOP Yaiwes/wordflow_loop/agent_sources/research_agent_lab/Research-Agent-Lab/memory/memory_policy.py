from __future__ import annotations


def memory_scope_for_topic(topic_name: str) -> str:
    normalized = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in topic_name)
    return normalized.strip("_") or "default_topic"
