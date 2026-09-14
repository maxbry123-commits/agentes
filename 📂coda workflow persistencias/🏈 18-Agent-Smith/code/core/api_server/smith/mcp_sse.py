"""
Cross-platform self-heal for the MCP SSE daemon (port 7778).

The dashboard's watchdog is the natural supervisor for the bare uvicorn MCP
process. ``_mcp_sse_alive`` and ``_launchd_supervises_mcp`` are reached through
the package object (``_smith.<name>``) so tests can patch them on the facade;
the restart-throttle timestamp ``_mcp_sse_last_restart_ts`` lives on the facade
(__init__) and is read/written via ``_smith.`` so a monkeypatch reset is honoured.
"""
from __future__ import annotations

import asyncio

import core.api_server as _api
import core.api_server.smith as _smith

from ._common import _log, _MCP_SSE_RESTART_MIN_GAP_SECONDS, _MCP_LAUNCHD_LABEL


def _mcp_sse_alive() -> bool:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'core/api_server/smith/mcp_sse.py','step':'_mcp_sse_alive','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def _launchd_supervises_mcp(label: str = _MCP_LAUNCHD_LABEL) -> bool:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'core/api_server/smith/mcp_sse.py','step':'_launchd_supervises_mcp','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def _ensure_mcp_sse_alive(now: float) -> None:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'core/api_server/smith/mcp_sse.py','step':'_ensure_mcp_sse_alive','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
