import asyncio

from runtime.src.parallel.mavis_parallel import MavisPool


def test_concurrent_duplicate_payload_executes_worker_once():
    async def scenario():
        calls = {"count": 0}

        async def worker(payload):
            calls["count"] += 1
            await asyncio.sleep(0.02)
            return {"value": payload["value"] * 2}

        pool = MavisPool(max_workers=4)
        results = await pool.run_batch(
            [
                {"id": "a", "priority": 1, "payload": {"value": 7}},
                {"id": "b", "priority": 1, "payload": {"value": 7}},
            ],
            worker,
        )
        assert calls["count"] == 1
        assert results[0]["output"] == results[1]["output"] == {"value": 14}
        assert {r["dedup_hit"] for r in results} == {False, True}

    asyncio.run(scenario())


def test_cache_prevents_second_execution():
    async def scenario():
        calls = {"count": 0}

        async def worker(payload):
            calls["count"] += 1
            return payload

        pool = MavisPool(max_workers=1)
        first = await pool.execute_task("a", {"x": 1}, worker)
        second = await pool.execute_task("b", {"x": 1}, worker)
        assert calls["count"] == 1
        assert first["cache_hit"] is False
        assert second["cache_hit"] is True

    asyncio.run(scenario())


def test_priority_order_is_deterministic_when_single_worker():
    async def scenario():
        order = []

        async def worker(payload):
            order.append(payload["name"])
            return payload

        pool = MavisPool(max_workers=1)
        await pool.run_batch(
            [
                {"id": "low", "priority": 9, "payload": {"name": "low"}},
                {"id": "high", "priority": 1, "payload": {"name": "high"}},
            ],
            worker,
        )
        assert order == ["high", "low"]

    asyncio.run(scenario())
