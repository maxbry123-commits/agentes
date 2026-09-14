"""REST API 路由 — 任务提交 / 状态查询 / 消息历史。"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from backend.app.schemas.request import SolveRequest
from backend.app.schemas.messages import SystemMessage, SolveStepMessage
from backend.app.services.redis_manager import redis_manager
from backend.app.utils.task_id import generate_task_id, validate_task_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/task", tags=["task"])

_MESSAGES_DIR = Path("backend/logs/messages")
_PROJECT_DIR = Path("project")


@router.post("/submit")
async def submit_task(req: SolveRequest, background_tasks: BackgroundTasks):
    """提交解题/渗透测试任务，立即返回 task_id，后台异步执行。"""
    task_id = generate_task_id()

    # 保存输入到文件（兼容现有 CLI 流程）
    _PROJECT_DIR.mkdir(exist_ok=True)
    task_dir = _PROJECT_DIR / task_id
    task_dir.mkdir(exist_ok=True)

    input_file = "scope.txt" if req.mode == "pentest" else "question.txt"
    with open(task_dir / input_file, "w", encoding="utf-8") as f:
        f.write(req.problem)

    # 注册任务到 Redis
    try:
        await redis_manager.set(f"task_id:{task_id}", task_id)
    except Exception as e:
        logger.error("Redis 注册任务失败: %s", e)
        raise HTTPException(status_code=503, detail="Redis 不可用")

    # 后台执行
    background_tasks.add_task(_run_solve_task, task_id, req)

    return JSONResponse({
        "task_id": task_id,
        "status": "processing",
        "mode": req.mode,
    })


@router.get("/{task_id}/messages")
async def get_task_messages(task_id: str):
    """获取任务的消息历史（文件日志回放）。"""
    if not validate_task_id(task_id):
        raise HTTPException(status_code=400, detail="非法 task_id")
    file_path = _MESSAGES_DIR / f"{task_id}.json"
    if not file_path.exists():
        return {"task_id": task_id, "messages": []}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            messages = json.load(f)
        return {"task_id": task_id, "messages": messages}
    except Exception as e:
        logger.error("读取消息文件失败: %s", e)
        return {"task_id": task_id, "messages": []}


@router.get("/{task_id}/status")
async def get_task_status(task_id: str):
    """获取任务运行状态。"""
    if not validate_task_id(task_id):
        raise HTTPException(status_code=400, detail="非法 task_id")
    try:
        client = await redis_manager.get_client()
        exists = await client.exists(f"task_id:{task_id}")
        status = "processing" if exists else "completed"
        return {"task_id": task_id, "status": status}
    except Exception:
        return {"task_id": task_id, "status": "unknown"}


@router.get("/")
async def list_tasks():
    """列出所有任务。"""
    tasks = []
    if _MESSAGES_DIR.exists():
        for f in sorted(_MESSAGES_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
            tid = f.stem
            mtime = datetime.fromtimestamp(os.path.getmtime(f))
            tasks.append({
                "task_id": tid,
                "created_at": mtime.isoformat(),
                "message_count": _count_messages(f),
            })
    return {"tasks": tasks[:50]}


# ── 后台执行 ─────────────────────────────────────────────────────

async def _run_solve_task(task_id: str, req: SolveRequest):
    """在 ThreadPoolExecutor 中运行同步 SolveAgent，消息通过回调推送。"""
    await asyncio.sleep(2)  # 等 WebSocket 连接订阅完成（预留连接时间）

    await redis_manager.publish_message(
        task_id,
        SystemMessage(content=f"任务开始 ({req.mode.upper()})", type="info"),
    )

    loop = asyncio.get_event_loop()

    # 在 executor 中运行同步的 SolveAgent
    result = await loop.run_in_executor(None, _sync_solve, task_id, req)

    await redis_manager.publish_message(
        task_id,
        SystemMessage(content=f"任务完成: {result}", type="success"),
    )

    # 清理 Redis 任务标记
    try:
        client = await redis_manager.get_client()
        await client.delete(f"task_id:{task_id}")
    except Exception:
        pass


def _sync_solve(task_id: str, req: SolveRequest) -> str:
    """在 worker 线程中同步执行 Workflow.solve()。"""
    import sys
    import os as _os
    import redis as sync_redis

    project_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.dirname(_os.path.abspath(__file__))
    )))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from config import Config
    from agent.workflow import Workflow
    from backend.app.adapters.web_ui_interface import WebUIInterface
    from backend.app.schemas.messages import SolveStepMessage
    from backend.app.services.redis_manager import redis_manager, save_message_to_file_sync

    ui = WebUIInterface(task_id=task_id)
    config = Config.load_config()
    _redis = sync_redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True, protocol=2)

    def _on_step_done(snapshot):
        """每步完成后推送 SolveStepMessage 到 Redis + 持久化到文件。"""
        try:
            msg = SolveStepMessage(
                step_num=snapshot.step_num,
                phase=snapshot.phase,
                think=(snapshot.think or "")[:500],
                tool_calls=[
                    {"tool_name": tc.get("tool_name", "?"),
                     "arguments": tc.get("arguments", {})}
                    for tc in (snapshot.tool_calls or [])
                ],
                tool_names=[tc.get("tool_name", "") for tc in (snapshot.tool_calls or [])],
                output=(snapshot.output or "")[:4096],
                analysis=(snapshot.analysis or "")[:1024],
                flag_found=snapshot.flag_found,
                flag_value=snapshot.flag_value,
                stuck_warning=snapshot.stuck_warning,
                vulnerability=snapshot.vulnerability,
                token_stats=snapshot.token_stats or {},
                cache_stats=snapshot.cache_stats or {},
            )
            _redis.publish(f"task:{task_id}:messages", msg.model_dump_json())
            save_message_to_file_sync(redis_manager.messages_dir, task_id, msg)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("SolveStepMessage 发布失败 (step %s): %s",
                           getattr(snapshot, 'step_num', '?'), e)

    workflow = Workflow(config=config, mode=req.mode, ui=ui)
    kwargs = {
        "export_writeup": req.export_writeup,
        "auto_mode": req.auto_mode,
        "on_step_callback": _on_step_done,
    }

    try:
        result = workflow.solve(req.problem, **kwargs)
        return str(result)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("SolveAgent 执行异常")
        return f"执行异常: {e}"


def _count_messages(file_path: Path) -> int:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return len(json.load(f))
    except Exception:
        return 0
