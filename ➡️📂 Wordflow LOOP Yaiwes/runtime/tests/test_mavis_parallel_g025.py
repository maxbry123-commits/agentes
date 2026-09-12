import asyncio
from pathlib import Path

from runtime.src.parallel.mavis_parallel import (
    MavisPool,
    evaluate_benchmark_gate,
    load_pattern_matrix,
)


MATRIX_PATH = (
    Path(__file__).parents[2]
    / "wordflow_loop"
    / "contracts"
    / "mavis-parallel-g025-matrix.json"
)


def test_g025_matrix_covers_every_director_pattern_with_evidence():
    required = {
        "persistent_pool", "priority_queue", "cache", "batching", "backpressure",
        "async_pipeline", "dedup", "job_abi", "registry", "factory", "dependency_injection",
        "event_bus", "middleware", "fsm", "checkpoints", "audit", "tests", "versioning",
        "sandbox", "capability_routing", "fan_out_fan_in", "dlq", "outbox", "multi_pool",
        "durable_recovery",
    }
    matrix = load_pattern_matrix(MATRIX_PATH)
    assert set(matrix) == required
    assert all(row["decision"] in {"ADOPT", "ADAPT", "REJECT"} for row in matrix.values())


def test_g025_matrix_evidence_paths_and_symbols_exist():
    root = Path(__file__).parents[2]
    matrix = load_pattern_matrix(MATRIX_PATH)
    for row in matrix.values():
        for reference in row["evidence_refs"]:
            relative_path, separator, symbol = reference.partition(":")
            source = root / relative_path
            assert source.is_file(), reference
            if separator:
                symbol_name = symbol.rsplit(".", 1)[-1]
                assert symbol_name in source.read_text(encoding="utf-8"), reference


def test_benchmark_is_not_invented_without_performance_claim():
    result = evaluate_benchmark_gate([], [])
    assert result["status"] == "NOT_REQUIRED_NO_PERFORMANCE_CLAIM"
    assert result["benchmark_required"] is False
    assert result["claim_authorized"] is False


def test_performance_claim_fails_closed_without_benchmark_evidence():
    result = evaluate_benchmark_gate(["20x faster"], [])
    assert result["status"] == "BLOCKED_BENCHMARK_EVIDENCE_REQUIRED"
    assert result["benchmark_required"] is True
    assert result["claim_authorized"] is False


def test_benchmark_evidence_never_self_authorizes_claim():
    result = evaluate_benchmark_gate(["lower latency"], ["benchmark://run/1"])
    assert result["status"] == "EVIDENCE_PRESENT_REVIEW_REQUIRED"
    assert result["claim_authorized"] is False


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
