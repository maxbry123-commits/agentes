"""
Mavis Parallel Engine Module - PECP-MAXBRY-100x (Nodo T-013)
Motor de paralelización masiva con colas de prioridad y caché determinista de resultados.
"""

import asyncio
import hashlib
import json
from typing import Dict, Any, List, Optional, Callable, Awaitable


class SmartCache:
    """Caché determinista de resultados basada en hashes de entrada."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    @staticmethod
    def _hash_key(key_data: Dict[str, Any]) -> str:
        serialized = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, payload: Dict[str, Any]) -> Optional[Any]:
        key = self._hash_key(payload)
        return self._store.get(key)

    def set(self, payload: Dict[str, Any], result: Any) -> None:
        key = self._hash_key(payload)
        self._store[key] = result


class PriorityTaskQueue:
    """Cola de tareas con prioridades numéricas (menor valor = mayor prioridad)."""

    def __init__(self) -> None:
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

    async def put(self, priority: int, task_id: str, payload: Dict[str, Any]) -> None:
        await self._queue.put((priority, task_id, payload))

    async def get(self) -> tuple[int, str, Dict[str, Any]]:
        return await self._queue.get()

    def empty(self) -> bool:
        return self._queue.empty()


class MavisPool:
    """Pool de ejecución paralela asíncrona optimizado con MavisPool y Deduplicación."""

    def __init__(self, max_workers: int = 10) -> None:
        self.max_workers = max_workers
        self.queue = PriorityTaskQueue()
        self.cache = SmartCache()
        self._active_hashes: set = set()

    async def execute_task(
        self,
        task_id: str,
        payload: Dict[str, Any],
        worker_fn: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Ejecuta una tarea consultando caché o previniendo tareas duplicadas."""
        cached_result = self.cache.get(payload)
        if cached_result:
            return {"task_id": task_id, "status": "COMPLETED", "cache_hit": True, "output": cached_result}

        # Deduplicación básica
        payload_hash = SmartCache._hash_key(payload)
        if payload_hash in self._active_hashes:
            await asyncio.sleep(0.05)  # Breve pausa para resolver colisiones

        self._active_hashes.add(payload_hash)
        try:
            result = await worker_fn(payload)
            self.cache.set(payload, result)
            return {"task_id": task_id, "status": "COMPLETED", "cache_hit": False, "output": result}
        finally:
            self._active_hashes.remove(payload_hash)

    async def run_batch(
        self,
        tasks: List[Dict[str, Any]],
        worker_fn: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Ejecuta un lote de tareas en paralelo respetando los límites del pool."""
        semaphore = asyncio.Semaphore(self.max_workers)

        async def _bounded_exec(t: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.execute_task(t["id"], t["payload"], worker_fn)

        futures = [_bounded_exec(task) for task in tasks]
        return await asyncio.gather(*futures)


async def _dummy_worker(payload: Dict[str, Any]) -> Dict[str, Any]:
    await asyncio.sleep(0.01)
    return {"processed": True, "data": payload.get("value", 0) * 2}


if __name__ == "__main__":
    print("=== TEST NODO T-013: MAVIS PARALLEL ENGINE ===")
    
    async def main() -> None:
        pool = MavisPool(max_workers=5)
        batch = [
            {"id": f"task_{i}", "payload": {"value": i}} for i in range(5)
        ]
        # Tarea duplicada para probar SmartCache
        batch.append({"id": "task_dup", "payload": {"value": 0}})

        results = await pool.run_batch(batch, _dummy_worker)
        print(json.dumps(results, indent=2))

    asyncio.run(main())