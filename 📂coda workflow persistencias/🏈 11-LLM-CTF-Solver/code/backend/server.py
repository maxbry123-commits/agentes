"""FastAPI 应用入口 — LLM-CTF-Solver Web UI 后端。"""
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 确保项目根目录可导入
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.app.routers import task_router, ws_router, status_router, kb_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期 — 启动/关闭 Redis。"""
    from backend.app.services.redis_manager import redis_manager
    try:
        await redis_manager.get_client()
        logger.info("Redis 连接已建立")
    except Exception as e:
        logger.warning("Redis 不可用（WebSocket 将无法工作）: %s", e)
    yield
    try:
        await redis_manager.close()
    except Exception:
        pass


app = FastAPI(
    title="LLM-CTF-Solver Web UI",
    description="CTF 自动解题 / 授权渗透测试 Web 界面",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(task_router.router)
app.include_router(ws_router.router)
app.include_router(status_router.router)
app.include_router(kb_router.router)


@app.get("/api/health")
async def health():
    """健康检查。"""
    try:
        from backend.app.services.redis_manager import redis_manager
        client = await redis_manager.get_client()
        await client.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    return {"status": "ok", "redis": redis_ok}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8002, reload=False)
