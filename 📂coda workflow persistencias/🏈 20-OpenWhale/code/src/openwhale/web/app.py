"""极简 Web 前端 - 实时展示智能体运行过程（FastAPI + SSE）"""

from __future__ import annotations

import asyncio
import json
import queue
import threading
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

# 全局消息队列（线程安全）
_message_queues: list[asyncio.Queue] = []
_message_lock = threading.Lock()

# 消息历史（供新连接回放）
_message_history: list[dict] = []

app = FastAPI(title="OpenWhale - 渗透测试智能体", version="0.1.0")

TEMPLATES_DIR = Path(__file__).parent / "templates"


def broadcast_message(role: str, content: str) -> None:
    """向所有 SSE 客户端广播消息（可从任意线程调用）"""
    msg = {"role": role, "content": content}
    _message_history.append(msg)

    with _message_lock:
        for q in _message_queues:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass


@app.get("/", response_class=HTMLResponse)
async def index():
    """返回主页 HTML"""
    html_file = TEMPLATES_DIR / "index.html"
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


@app.get("/events")
async def events():
    """Server-Sent Events 端点 - 实时推送智能体消息"""
    q: asyncio.Queue = asyncio.Queue(maxsize=100)

    with _message_lock:
        _message_queues.append(q)

    # 先发送历史消息（供页面刷新后回放）
    history_snapshot = list(_message_history)

    async def event_generator() -> AsyncGenerator[str, None]:
        # 回放历史
        for msg in history_snapshot:
            yield _format_sse(msg)

        # 推送新消息
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield _format_sse(msg)
                except asyncio.TimeoutError:
                    # 心跳，保持连接
                    yield ": heartbeat\n\n"
        finally:
            with _message_lock:
                if q in _message_queues:
                    _message_queues.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/history")
async def history():
    """返回消息历史（JSON）"""
    return {"messages": _message_history}


def _format_sse(msg: dict) -> str:
    """格式化为 SSE 事件字符串"""
    data = json.dumps(msg, ensure_ascii=False)
    return f"data: {data}\n\n"


def run(host: str = "0.0.0.0", port: int = 8080) -> None:
    """启动 Web 服务器"""
    logger.info(f"启动 Web 界面: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")
