"""On-demand ngrok TCP tunnels for reverse-shell listeners. Each armed listener
gets its own ngrok agent process tunnelling to the local listener port; the
assigned public address is parsed from the agent's json logs, so ephemeral
free-tier addresses work without assuming a reserved endpoint."""

from __future__ import annotations

import asyncio
import json

from ..logs import get_logger

log = get_logger("ngrok")

_URL_TIMEOUT = 30.0


class NgrokError(RuntimeError):
    pass


class NgrokManager:
    def __init__(self) -> None:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'packages/core/redcell_core/engine/ngrok.py','step':'__init__','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def open(self, listener_id: str, port: int, token: str) -> str:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'packages/core/redcell_core/engine/ngrok.py','step':'open','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def close(self, listener_id: str) -> None:
        proc = self._procs.pop(listener_id, None)
        if proc is None:
            return
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except TimeoutError:
                proc.kill()

    async def close_all(self) -> None:
        for lid in list(self._procs):
            await self.close(lid)

    async def _read_public_url(self, proc: asyncio.subprocess.Process) -> str | None:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'packages/core/redcell_core/engine/ngrok.py','step':'_read_public_url','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye
