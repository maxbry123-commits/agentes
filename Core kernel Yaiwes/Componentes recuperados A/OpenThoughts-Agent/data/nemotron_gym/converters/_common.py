"""Common helpers shared by converter modules."""

from __future__ import annotations

from typing import Iterable

from ..adapter import SanitizationError, sanitize_text


PROMPT_MAX_LEN = 64 * 1024


def extract_prompt(row: dict) -> str:
    """Pull the user/system prompt out of a Nemotron-Gym row.

    The collection's rows commonly carry one of:
      - row["input"] : list of {"role": ..., "content": ...}
      - row["responses_create_params"]["input"] : same shape
      - row["prompt"] : flat string
    """
    candidates: list[object] = []
    candidates.append(row.get("input"))
    rcp = row.get("responses_create_params")
    if isinstance(rcp, dict):
        candidates.append(rcp.get("input"))
        candidates.append(rcp.get("messages"))
    elif isinstance(rcp, list):
        candidates.append(rcp)
    candidates.append(row.get("prompt"))
    candidates.append(row.get("question"))

    for c in candidates:
        if isinstance(c, str) and c.strip():
            return sanitize_text(c, field_name="prompt", max_len=PROMPT_MAX_LEN)
        if isinstance(c, list):
            parts: list[str] = []
            for msg in c:
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role", "")
                content = msg.get("content", "")
                if isinstance(content, list):
                    pieces = []
                    for part in content:
                        if isinstance(part, dict):
                            t = part.get("text") or part.get("content")
                            if isinstance(t, str):
                                pieces.append(t)
                        elif isinstance(part, str):
                            pieces.append(part)
                    content = "\n".join(pieces)
                if not isinstance(content, str):
                    continue
                if role and role != "user":
                    parts.append(f"[{role}]\n{content}")
                else:
                    parts.append(content)
            if parts:
                joined = "\n\n".join(parts)
                return sanitize_text(
                    joined, field_name="prompt", max_len=PROMPT_MAX_LEN
                )
    raise SanitizationError("could not extract prompt from row")


def require_str(row: dict, key: str, *, max_len: int = PROMPT_MAX_LEN) -> str:
    val = row.get(key)
    if not isinstance(val, str):
        raise SanitizationError(f"{key}: expected str, got {type(val).__name__}")
    return sanitize_text(val, field_name=key, max_len=max_len)


def sanitize_list_of_str(
    values: Iterable[object], *, field_name: str, max_len: int = PROMPT_MAX_LEN
) -> list[str]:
    out: list[str] = []
    for i, v in enumerate(values):
        if not isinstance(v, str):
            raise SanitizationError(f"{field_name}[{i}]: not a string")
        out.append(sanitize_text(v, field_name=f"{field_name}[{i}]", max_len=max_len))
    return out
