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
    """WebSocket 端点 — Redis Pub/Sub → 浏览器, 浏览器决策 → Redis。

    工作模式: forward 循环直接 await pubsub.listen() 阻塞在 handler 中
    （与独立测试 8768 端口一致），listen 循环作为 asyncio.Task 后台轮询。
    """
    if not validate_task_id(task_id):
        await websocket.close(code=1008, reason="非法 task_id")
        return

    r = aioredis.Redis.from_url(REDIS_URL, decode_responses=True, protocol=2)
    try:
        exists = await r.exists(f"task_id:{task_id}")
        if not exists:
            await websocket.close(code=1008, reason="任务不存在")
            await r.aclose()
            return
    except Exception:
        await websocket.close(code=1011, reason="Redis 不可用")
        await r.aclose()
        return

    await websocket.accept()
    logger.info("WebSocket 已连接: task=%s", task_id)
    await websocket.send_text(json.dumps({
        "id": "ws-welcome", "msg_type": "system",
        "content": "WebSocket connected", "type": "info",
    }))

    pubsub = r.pubsub()
    await pubsub.subscribe(f"task:{task_id}:messages")
    logger.info("Redis 已订阅: task=%s", task_id)

    # ── 后台任务: 接收浏览器 HIL 决策 ──
    stop_event = asyncio.Event()

    async def _listen_client():
        while not stop_event.is_set():
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                data = json.loads(raw)
                if data.get("type") == "user_decision":
                    checkpoint_id = data.get("checkpoint_id", "")
                    decision = data.get("decision", {})
                    await state_store.set(
                        namespace="checkpoint",
                        key=f"{task_id}:{checkpoint_id}",
                        value=decision, ttl=600,
                    )
                    logger.info("收到用户决策: checkpoint=%s", checkpoint_id)
            except asyncio.TimeoutError:
                continue
            except WebSocketDisconnect:
                break
        stop_event.set()

    listen_task = asyncio.create_task(_listen_client())

    # ── 主循环: Redis Pub/Sub → WebSocket ──
    try:
        async for msg in pubsub.listen():
            if msg and msg.get("type") == "message":
                try:
                    await websocket.send_text(msg["data"])
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    finally:
        stop_event.set()
        listen_task.cancel()
        try:
            await listen_task
        except asyncio.CancelledError:
            pass
        await pubsub.unsubscribe(f"task:{task_id}:messages")
        await r.aclose()
        logger.info("WebSocket 已断开: task=%s", task_id)
