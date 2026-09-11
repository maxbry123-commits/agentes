"""Mavis Parallel Engine - deterministic cache, priority and in-flight dedup."""
from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any, Awaitable, Callable, Dict, List, Optional


class SmartCache:
    """Deterministic result cache keyed by canonical JSON hash."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    @staticmethod
    def _hash_key(key_data: Dict[str, Any]) -> str:
        serialized = json.dumps(key_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, payload: Dict[str, Any]) -> Optional[Any]:
        return self._store.get(self._hash_key(payload))

    def set(self, payload: Dict[str, Any], result: Any) -> None:
        self._store[self._hash_key(payload)] = result


class PriorityTaskQueue:
    """Priority queue: lower number means higher priority."""

    def __init__(self) -> None:
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

    async def put(self, priority: int, task_id: str, payload: Dict[str, Any]) -> None:
        await self._queue.put((priority, task_id, payload))

    async def get(self) -> tuple[int, str, Dict[str, Any]]:
        return await self._queue.get()

    def empty(self) -> bool:
        return self._queue.empty()


class MavisPool:
    """Bounded asynchronous worker pool with cache and exact in-flight dedup."""

    def __init__(self, max_workers: int = 10) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self.max_workers = max_workers
        self.queue = PriorityTaskQueue()
        self.cache = SmartCache()
        self._inflight: Dict[str, asyncio.Future] = {}

    async def execute_task(
        self,
        task_id: str,
        payload: Dict[str, Any],
        worker_fn: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        cached_result = self.cache.get(payload)
        if cached_result is not None:
            return {
                "task_id": task_id,
                "status": "COMPLETED",
                "cache_hit": True,
                "dedup_hit": False,
                "output": cached_result,
            }

        payload_hash = SmartCache._hash_key(payload)
        existing = self._inflight.get(payload_hash)
        if existing is not None:
            result = await asyncio.shield(existing)
            return {
                "task_id": task_id,
                "status": "COMPLETED",
                "cache_hit": False,
                "dedup_hit": True,
                "output": result,
            }

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._inflight[payload_hash] = future
        try:
            result = await worker_fn(payload)
            self.cache.set(payload, result)
            if not future.done():
                future.set_result(result)
            return {
                "task_id": task_id,
                "status": "COMPLETED",
                "cache_hit": False,
                "dedup_hit": False,
                "output": result,
            }
        except Exception as exc:
            if not future.done():
                future.set_exception(exc)
                future.add_done_callback(lambda done: done.exception())
            raise
        finally:
            self._inflight.pop(payload_hash, None)

    async def run_batch(
        self,
        tasks: List[Dict[str, Any]],
        worker_fn: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Run independent tasks with deterministic priority ordering and backpressure."""
        semaphore = asyncio.Semaphore(self.max_workers)
        ordered = sorted(tasks, key=lambda task: (int(task.get("priority", 0)), str(task["id"])))

        async def _bounded_exec(task: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.execute_task(task["id"], task["payload"], worker_fn)

        return await asyncio.gather(*(_bounded_exec(task) for task in ordered))
