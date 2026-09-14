"""Redis Pub/Sub 管理 + 消息文件持久化 — 改编自 MMA。"""
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional
import redis.asyncio as aioredis

from backend.app.schemas.messages import Message

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class RedisManager:
    def __init__(self):
        self.redis_url = REDIS_URL
        self._client: Optional[aioredis.Redis] = None
        self.messages_dir = Path("backend/logs/messages")
        self.messages_dir.mkdir(parents=True, exist_ok=True)

    async def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                protocol=2,  # 兼容旧版 Redis (不支持 RESP3 HELLO)
            )
        try:
            await self._client.ping()
            logger.info("Redis 连接成功: %s", self.redis_url)
            return self._client
        except Exception as e:
            logger.error("Redis 连接失败: %s", e)
            raise

    async def set(self, key: str, value: str):
        client = await self.get_client()
        await client.set(key, value)
        await client.expire(key, 36000)

    async def _save_message_to_file(self, task_id: str, message: Message):
        try:
            file_path = self.messages_dir / f"{task_id}.json"
            messages = []
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    messages = json.load(f)
            messages.append(message.model_dump())
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("消息文件保存失败: %s", e)

    async def publish_message(self, task_id: str, message: Message):
        client = await self.get_client()
        channel = f"task:{task_id}:messages"
        message_json = message.model_dump_json()
        await client.publish(channel, message_json)
        await self._save_message_to_file(task_id, message)

    async def subscribe_to_task(self, task_id: str):
        client = await self.get_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(f"task:{task_id}:messages")
        return pubsub

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


def save_message_to_file_sync(messages_dir: Path, task_id: str, message: Message):
    """同步文件持久化 — 供 worker 线程（run_in_executor）中的回调使用。

    与 RedisManager._save_message_to_file 逻辑一致，但不依赖 asyncio。
    """
    try:
        file_path = messages_dir / f"{task_id}.json"
        messages = []
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                messages = json.load(f)
        messages.append(message.model_dump())
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("消息文件保存失败 (sync): %s", e)


redis_manager = RedisManager()
