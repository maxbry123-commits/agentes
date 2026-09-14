"""``@cognithor_tool`` decorator — declarative tool metadata.

Attaches name, description, risk level, and input schema to a function or
coroutine so the Gateway can register it with the MCP client and the
Gatekeeper reads the risk level via the per-tool registry instead of the
hardcoded fallback lists.

Usage::

    from cognithor.tools.decorator import cognithor_tool

    @cognithor_tool(
        name="web_search",
        risk_level="green",
        description="Search the web for information.",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )
    async def web_search(query: str) -> str:
        ...

A ``ToolMetadata`` instance is attached at ``fn.__cognithor_tool__`` so
registration helpers can discover and wire decorated callables:

    from cognithor.tools.decorator import iter_decorated_tools

    for fn, meta in iter_decorated_tools(my_module):
        mcp_client.register_builtin_handler(
            meta.name, fn,
            description=meta.description,
            input_schema=meta.input_schema,
            risk_level=meta.risk_level,
        )

Risk levels:

- ``green``  — read-only, side-effect-free (web_search, read_file, list_*).
- ``yellow`` — low-impact side effects (cron_add_job, memory_write).
- ``orange`` — external side effects that need user confirmation by default
  (send_email, db_execute, pack-unknown).
- ``red``    — destructive / irreversible (file_delete, db_drop). Usually blocked.

Unknown tools fall through to the Gatekeeper's ORANGE default.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

__all__ = [
    "VALID_RISK_LEVELS",
    "ToolMetadata",
    "cognithor_tool",
    "get_tool_metadata",
    "iter_decorated_tools",
]

#: Tuple of the risk levels accepted by the Gatekeeper.
VALID_RISK_LEVELS: tuple[str, ...] = ("green", "yellow", "orange", "red")

_ATTRIBUTE = "__cognithor_tool__"


@dataclass(frozen=True)
class ToolMetadata:
    """Metadata attached to a decorated callable."""

    name: str
    risk_level: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)


def cognithor_tool(
    *,
    name: str,
    risk_level: str,
    description: str = "",
    input_schema: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Mark *fn* as a Cognithor tool.

    Parameters
    ----------
    name:
        Tool name as it appears in plans (e.g. ``"web_search"``). Must be a
        non-empty string. Uniqueness is the caller's responsibility — the
        MCP client raises if two handlers register the same name.
    risk_level:
        One of :data:`VALID_RISK_LEVELS`.
    description:
        Short single-line description shown to the planner.
    input_schema:
        JSON-Schema (draft-07) describing the tool parameters.
    """
    if not name:
        raise ValueError("cognithor_tool: name must be non-empty")
    if risk_level not in VALID_RISK_LEVELS:
        raise ValueError(
            f"cognithor_tool: risk_level={risk_level!r} must be one of {VALID_RISK_LEVELS}"
        )

    meta = ToolMetadata(
        name=name,
        risk_level=risk_level,
        description=description,
        input_schema=dict(input_schema) if input_schema else {},
    )

    def decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
        if not callable(fn):
            raise TypeError(f"cognithor_tool requires a callable, got {type(fn).__name__}")
        setattr(fn, _ATTRIBUTE, meta)
        return fn

    return decorate


def get_tool_metadata(fn: Callable[..., Any]) -> ToolMetadata | None:
    """Return the :class:`ToolMetadata` attached to *fn*, or ``None``."""
    return getattr(fn, _ATTRIBUTE, None)


def iter_decorated_tools(module: Any) -> Iterator[tuple[Callable[..., Any], ToolMetadata]]:
    """Yield ``(fn, metadata)`` for every decorated callable in *module*.

    Walks ``dir(module)`` and filters callables with a
    :class:`ToolMetadata` attached. Useful for bulk registration::

        for fn, meta in iter_decorated_tools(my_tools_module):
            mcp_client.register_builtin_handler(
                meta.name, fn,
                description=meta.description,
                input_schema=meta.input_schema,
                risk_level=meta.risk_level,
            )
    """
    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name, None)
        if obj is None or not callable(obj):
            continue
        # Unwrap common wrappers (functools.partial, etc.) where helpful.
        target = inspect.unwrap(obj) if inspect.isfunction(obj) or inspect.ismethod(obj) else obj
        meta = get_tool_metadata(obj) or get_tool_metadata(target)
        if meta is not None:
            yield obj, meta
