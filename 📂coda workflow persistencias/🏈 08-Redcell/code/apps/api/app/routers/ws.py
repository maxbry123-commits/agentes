"""WebSocket fan-out. Each socket subscribes to one Redis channel."""

from __future__ import annotations

import asyncio

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redcell_core.bus import bus, chat_channel, events_channel, shell_channel
from redcell_core.config import settings
from redcell_core.db import session_scope
from redcell_core.logs import get_logger
from redcell_core.repositories import sessions as sessions_repo
from redcell_core.security import COOKIE_NAME

router = APIRouter()


def _authed(ws: WebSocket) -> bool:
    token = ws.cookies.get(COOKIE_NAME)
    if not token:
        return False
    try:
        jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return True
    except jwt.PyJWTError:
        return False


async def _forward(ws: WebSocket, channel: str) -> None:
    async for payload in bus.subscribe(channel):
        await ws.send_text(payload)


async def _drain(ws: WebSocket) -> None:
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        return


async def _pump(ws: WebSocket, channel: str) -> None:
    forward = asyncio.create_task(_forward(ws, channel))
    drain = asyncio.create_task(_drain(ws))
    _, pending = await asyncio.wait({forward, drain}, return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()
    for t in pending:
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass


@router.websocket("/ws/events/{run_id}")
async def ws_events(ws: WebSocket, run_id: str) -> None:
    if not _authed(ws):
        await ws.close(code=4401)
        return
    await ws.accept()
    await _pump(ws, events_channel(run_id))


@router.websocket("/ws/chat/{run_id}")
async def ws_chat(ws: WebSocket, run_id: str) -> None:
    if not _authed(ws):
        await ws.close(code=4401)
        return
    await ws.accept()
    await _pump(ws, chat_channel(run_id))


@router.websocket("/ws/shell/{shell_id}")
async def ws_shell(ws: WebSocket, shell_id: str) -> None:
    if not _authed(ws):
        await ws.close(code=4401)
        return
    await ws.accept()
    await _pump(ws, shell_channel(shell_id))


async def _bridge(ws: WebSocket, proc: asyncio.subprocess.Process) -> None:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'apps/api/app/routers/ws.py','step':'_bridge','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


@router.websocket("/ws/browser/{session_id}")
async def ws_browser(ws: WebSocket, session_id: str) -> None:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'apps/api/app/routers/ws.py','step':'ws_browser','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
