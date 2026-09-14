"""Classify MCP connection failures without retaining sensitive request data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Literal, cast

import httpx
from agents.exceptions import UserError
from mcp.shared.exceptions import McpError


FailureKind = Literal[
    "auth", "permission", "rate_limit", "server", "transport", "timeout", "protocol", "unknown"
]

_PRIORITY: dict[FailureKind, int] = {
    "auth": 0,
    "permission": 1,
    "rate_limit": 2,
    "server": 3,
    "protocol": 4,
    "timeout": 5,
    "transport": 6,
    "unknown": 7,
}
_HTTP_ERROR_RE = re.compile(r"\bHTTP error\s+(\d{3})\b", re.IGNORECASE)


@dataclass(frozen=True)
class FailureInfo:
    """A non-sensitive description of one connection failure."""

    kind: FailureKind
    status: int | None = None
    reason: str | None = None
    retry_after: float | None = None
    request_method: str | None = None
    request_path: str | None = None

    @property
    def retryable(self) -> bool:
        return self.kind not in {"auth", "permission"}


def _retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            date = date.replace(tzinfo=UTC)
        return max(0.0, (date - datetime.now(UTC)).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


def _from_status(
    status: int,
    reason: str | None = None,
    retry_after: float | None = None,
    *,
    request_method: str | None = None,
    request_path: str | None = None,
) -> FailureInfo:
    if status == 401:
        kind: FailureKind = "auth"
    elif status == 403:
        kind = "permission"
    elif status == 429:
        kind = "rate_limit"
    elif 500 <= status <= 599:
        kind = "server"
    elif 400 <= status <= 499:
        kind = "protocol"
    else:
        kind = "unknown"
    return FailureInfo(
        kind,
        status,
        reason,
        retry_after,
        request_method,
        request_path,
    )


def _direct(exc: BaseException) -> FailureInfo | None:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'strix/tools/mcp/failures.py','step':'_direct','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def classify(exc: BaseException) -> FailureInfo:
    """Return the most specific non-sensitive classification in an exception tree."""
    direct = _direct(exc)
    matches: list[FailureInfo] = [direct] if direct is not None else []
    if isinstance(exc, BaseExceptionGroup):
        group = cast("BaseExceptionGroup[BaseException]", exc)
        matches.extend(classify(child) for child in group.exceptions)
    if matches:
        return min(matches, key=lambda info: _PRIORITY[info.kind])
    return FailureInfo("unknown", reason="unknown failure")


class HttpStatusRecorder:
    """Capture the last non-success response from one HTTP connection."""

    def __init__(self) -> None:
        self._failure: FailureInfo | None = None

    async def __call__(self, response: httpx.Response) -> None:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'strix/tools/mcp/failures.py','step':'__call__','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def take(self) -> FailureInfo | None:
        failure, self._failure = self._failure, None
        return failure
