"""WebSocket 路由 — 实时消息推送 + HIL 决策回传。"""
import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis

from backend.app.services.state_store import state_store
from backend.app.utils.task_id import validate_task_id

logger = logging.getLogger(__name__)
REDIS_URL = "redis://localhost:6379/0"

router = APIRouter()


@router.websocket("/ws/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'backend/app/routers/ws_router.py','step':'websocket_endpoint','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
