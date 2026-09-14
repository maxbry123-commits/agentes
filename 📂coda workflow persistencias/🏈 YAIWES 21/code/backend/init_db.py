"""
初始化数据库
"""
import asyncio
from app.db.database import engine, Base
from app.models.task import Task, Message, Conversation


async def init_database():
    """创建所有表"""
    print("🔨 创建数据库表...")
    
    async with engine.begin() as conn:
        # 删除所有表（仅开发环境）
        await conn.run_sync(Base.metadata.drop_all)
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ 数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(init_database())
