"""
FastAPI Main - 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.db.database import init_db
from app.api import tasks, websocket_api, messages, conversations, context, config

# 🔥🔥🔥 禁用HTTP请求日志
logging.getLogger("uvicorn.access").disabled = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动
    print("="*80)
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    print("="*80)
    
    # 初始化数据库
    await init_db()
    
    yield
    
    # 关闭
    print("\n" + "="*80)
    print(f"👋 {settings.APP_NAME} 关闭")
    print("="*80)


# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="渗透测试可视化平台 - 全异步重构版",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(websocket_api.router, prefix="/api/v1/ws", tags=["WebSocket"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(messages.router, prefix="/api/v1", tags=["Messages"])
app.include_router(conversations.router, prefix="/api/v1", tags=["Conversations"])
app.include_router(context.router, prefix="/api/v1", tags=["Context"])
app.include_router(config.router, prefix="/api/v1", tags=["Config"])  # 🔥 新增Config路由


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
