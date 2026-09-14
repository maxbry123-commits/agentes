"""
异步数据库引擎 - SQLAlchemy 2.0 + asyncio
"""
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.models.task import Base

# 确保数据库目录存在
db_path = settings.DATABASE_URL.replace('sqlite+aiosqlite:///', '')
db_dir = Path(db_path).parent
db_dir.mkdir(parents=True, exist_ok=True)


# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,  # SQLite不支持连接池
    future=True
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        # 强制创建所有表（如果不存在）
        await conn.run_sync(Base.metadata.create_all)
        print("✅ 数据库初始化完成")
        
        # 验证表是否创建成功
        await conn.run_sync(lambda sync_conn: print(f"📊 已创建表: {list(Base.metadata.tables.keys())}"))


async def get_db() -> AsyncSession:
    """获取数据库会话（依赖注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
