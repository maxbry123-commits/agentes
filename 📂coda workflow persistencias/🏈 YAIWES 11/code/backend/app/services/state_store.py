"""Redis 状态持久化 — 改编自 MMA，用于 HIL checkpoint 等待。"""
import asyncio
import json
import logging
from typing import Any

from backend.app.services.redis_manager import redis_manager

logger = logging.getLogger(__name__)


class StateStore:
    def _make_key(self, namespace: str, key: str) -> str:
        return f"state:{namespace}:{key}"

    async def set(self, namespace: str, key: str, value: Any, ttl: int | None = None):
        client = await redis_manager.get_client()
        redis_key = self._make_key(namespace, key)
        serialized = json.dumps(value, ensure_ascii=False)
        await client.set(redis_key, serialized)
        if ttl is not None:
            await client.expire(redis_key, ttl)

    async def get(self, namespace: str, key: str) -> Any | None:
        client = await redis_manager.get_client()
        redis_key = self._make_key(namespace, key)
        raw = await client.get(redis_key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def delete(self, namespace: str, key: str):
        client = await redis_manager.get_client()
        redis_key = self._make_key(namespace, key)
        await client.delete(redis_key)

    async def wait_for_update(self, namespace: str, key: str, timeout: float = 300) -> Any | None:
        """轮询 Redis 等待值出现（HIL checkpoint 专用）。"""
        redis_key = self._make_key(namespace, key)
        client = await redis_manager.get_client()
        poll_interval = 1.0
        elapsed = 0.0

        raw = await client.get(redis_key)
        if raw is not None:
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return raw

        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            raw = await client.get(redis_key)
            if raw is not None:
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return raw

        logger.warning("StateStore wait_for_update 超时 (%s, %ss)", redis_key, timeout)
        return None


state_store = StateStore()
