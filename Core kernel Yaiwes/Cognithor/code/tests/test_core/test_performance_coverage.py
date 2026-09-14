"""Coverage-Tests fuer performance.py -- VectorStore, LoadBalancer, etc."""

from __future__ import annotations

from cognithor.core.performance import (
    Backend,
    BalancingStrategy,
    CloudFallback,
    LatencyTracker,
    LoadBalancer,
    PerformanceManager,
    QueryDecomposer,
    ResourceOptimizer,
    VectorStore,
)

# ============================================================================
# VectorStore
# ============================================================================


class TestVectorStore:
    def test_add_entry(self) -> None:
        vs = VectorStore(dimension=3)
        entry = vs.add("hello", [1.0, 0.0, 0.0])
        assert entry.entry_id.startswith("VEC-")
        assert entry.text == "hello"

    def test_search_returns_sorted(self) -> None:
        vs = VectorStore(dimension=3)
        vs.add("a", [1.0, 0.0, 0.0])
        vs.add("b", [0.0, 1.0, 0.0])
        vs.add("c", [0.9, 0.1, 0.0])

        results = vs.search([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2
        # First result should be most similar
        assert results[0].score >= results[1].score

    def test_search_empty_store(self) -> None:
        vs = VectorStore(dimension=3)
        results = vs.search([1.0, 0.0, 0.0])
        assert results == []

    def test_delete(self) -> None:
        vs = VectorStore(dimension=3)
        entry = vs.add("test", [1.0, 0.0, 0.0])
        assert vs.delete(entry.entry_id) is True
        assert vs.delete("nonexistent") is False

    def test_clear(self) -> None:
        vs = VectorStore(dimension=3)
        vs.add("a", [1.0, 0.0, 0.0])
        vs.add("b", [0.0, 1.0, 0.0])
        count = vs.clear()
        assert count == 2
        assert vs.entry_count == 0

    def test_entry_count(self) -> None:
        vs = VectorStore(dimension=3)
        assert vs.entry_count == 0
        vs.add("x", [1.0, 0.0, 0.0])
        assert vs.entry_count == 1

    def test_stats(self) -> None:
        vs = VectorStore(dimension=4)
        stats = vs.stats()
        assert stats["backend"] == "in_memory"
        assert stats["dimension"] == 4

    def test_cosine_similarity_identical(self) -> None:
        score = VectorStore._cosine_similarity([1.0, 0.0], [1.0, 0.0])
        assert abs(score - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self) -> None:
        score = VectorStore._cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert abs(score) < 0.001

    def test_cosine_similarity_empty(self) -> None:
        score = VectorStore._cosine_similarity([], [])
        assert score == 0.0

    def test_cosine_similarity_different_length(self) -> None:
        score = VectorStore._cosine_similarity([1.0], [1.0, 0.0])
        assert score == 0.0

    def test_cosine_similarity_zero_vector(self) -> None:
        score = VectorStore._cosine_similarity([0.0, 0.0], [1.0, 0.0])
        assert score == 0.0

    def test_add_with_metadata(self) -> None:
        vs = VectorStore(dimension=2)
        entry = vs.add("meta", [1.0, 0.0], metadata={"source": "test"})
        assert entry.metadata["source"] == "test"

    def test_add_truncates_embedding(self) -> None:
        vs = VectorStore(dimension=2)
        entry = vs.add("long", [1.0, 2.0, 3.0, 4.0])
        assert len(entry.embedding) == 2


# ============================================================================
# QueryDecomposer
# ============================================================================


class TestQueryDecomposer:
    def test_simple_query_not_split(self) -> None:
        qd = QueryDecomposer()
        subs = qd.decompose("Was ist Python?")
        assert len(subs) == 1
        assert subs[0].text == "Was ist Python?"

    def test_compound_query_split(self) -> None:
        qd = QueryDecomposer()
        subs = qd.decompose("Was ist Python und was ist JavaScript?")
        assert len(subs) >= 2

    def test_classification_factual(self) -> None:
        qd = QueryDecomposer()
        assert qd._classify("Wer ist der CEO?") == "factual"

    def test_classification_comparison(self) -> None:
        qd = QueryDecomposer()
        assert qd._classify("Vergleich von Python vs Java") == "comparison"

    def test_classification_analytical(self) -> None:
        qd = QueryDecomposer()
        assert qd._classify("Warum ist Python so beliebt?") == "analytical"

    def test_stats(self) -> None:
        qd = QueryDecomposer()
        assert "split_markers" in qd.stats()

    def test_short_parts_filtered(self) -> None:
        qd = QueryDecomposer()
        subs = qd.decompose("A und B")
        # Both parts are too short (<10 chars), so original query is used
        assert len(subs) >= 1


# ============================================================================
# LoadBalancer
# ============================================================================


class TestLoadBalancer:
    def _make_backend(self, bid: str, latency: float = 10.0, healthy: bool = True) -> Backend:
        return Backend(
            backend_id=bid,
            name=bid,
            url=f"http://{bid}:11434",
            avg_latency_ms=latency,
            healthy=healthy,
        )

    def test_add_and_select(self) -> None:
        lb = LoadBalancer(strategy=BalancingStrategy.LATENCY_BASED)
        lb.add_backend(self._make_backend("a", latency=10))
        lb.add_backend(self._make_backend("b", latency=20))
        selected = lb.select_backend()
        assert selected is not None
        assert selected.backend_id == "a"  # Lower latency

    def test_round_robin(self) -> None:
        lb = LoadBalancer(strategy=BalancingStrategy.ROUND_ROBIN)
        lb.add_backend(self._make_backend("a"))
        lb.add_backend(self._make_backend("b"))
        first = lb.select_backend()
        second = lb.select_backend()
        assert first.backend_id != second.backend_id

    def test_least_connections(self) -> None:
        lb = LoadBalancer(strategy=BalancingStrategy.LEAST_CONNECTIONS)
        b1 = self._make_backend("a")
        b1.current_load = 3
        b2 = self._make_backend("b")
        b2.current_load = 1
        lb.add_backend(b1)
        lb.add_backend(b2)
        selected = lb.select_backend()
        assert selected.backend_id == "b"

    def test_weighted(self) -> None:
        lb = LoadBalancer(strategy=BalancingStrategy.WEIGHTED)
        lb.add_backend(self._make_backend("a"))
        selected = lb.select_backend()
        assert selected is not None

    def test_no_healthy_backends(self) -> None:
        lb = LoadBalancer()
        lb.add_backend(self._make_backend("a", healthy=False))
        assert lb.select_backend() is None

    def test_remove_backend(self) -> None:
        lb = LoadBalancer()
        lb.add_backend(self._make_backend("a"))
        assert lb.remove_backend("a") is True
        assert lb.remove_backend("nonexistent") is False

    def test_record_request(self) -> None:
        lb = LoadBalancer()
        lb.add_backend(self._make_backend("a"))
        lb.record_request("a", 50.0)
        lb.record_request("a", 100.0, error=True)

    def test_backend_properties(self) -> None:
        b = self._make_backend("a")
        b.current_load = 2
        b.max_concurrent = 4
        assert b.load_percent == 50.0
        b.total_requests = 10
        b.total_errors = 2
        assert b.error_rate == 20.0

    def test_backend_zero_concurrent(self) -> None:
        b = self._make_backend("a")
        b.max_concurrent = 0
        assert b.load_percent == 100.0

    def test_backend_to_dict(self) -> None:
        b = self._make_backend("a")
        d = b.to_dict()
        assert d["id"] == "a"
        assert "healthy" in d


# ============================================================================
# LatencyTracker (if available)
# ============================================================================


class TestLatencyTracker:
    def test_record_and_stats(self) -> None:
        lt = LatencyTracker()
        lt.record(100.0, "planner")
        lt.record(200.0, "planner")
        lt.record(50.0, "executor")
        stats = lt.stats()
        assert stats["total_samples"] == 3
        assert "planner" in stats["operations"]

    def test_percentile(self) -> None:
        lt = LatencyTracker()
        for i in range(100):
            lt.record(float(i))
        p50 = lt.percentile(50)
        assert 40 <= p50 <= 60

    def test_percentile_empty(self) -> None:
        lt = LatencyTracker()
        assert lt.percentile(50) == 0.0

    def test_avg_property(self) -> None:
        lt = LatencyTracker()
        lt.record(100.0)
        lt.record(200.0)
        assert lt.avg == 150.0

    def test_avg_empty(self) -> None:
        lt = LatencyTracker()
        assert lt.avg == 0.0

    def test_p50_p95_p99(self) -> None:
        lt = LatencyTracker()
        for i in range(100):
            lt.record(float(i))
        assert lt.p50 >= 0
        assert lt.p95 >= lt.p50
        assert lt.p99 >= lt.p95

    def test_by_operation(self) -> None:
        lt = LatencyTracker()
        lt.record(100.0, "planner")
        lt.record(200.0, "planner")
        result = lt.by_operation("planner")
        assert result["avg"] == 150.0

    def test_by_operation_empty(self) -> None:
        lt = LatencyTracker()
        result = lt.by_operation("unknown")
        assert result["avg"] == 0


# ============================================================================
# ResourceOptimizer (if available)
# ============================================================================


class TestResourceOptimizer:
    def test_snapshot(self) -> None:
        ro = ResourceOptimizer()
        snap = ro.snapshot(cpu=50.0, ram_used=8.0, ram_total=16.0)
        assert snap.cpu_percent == 50.0
        assert snap.ram_used_gb == 8.0

    def test_alerts_empty(self) -> None:
        ro = ResourceOptimizer()
        assert ro.alerts() == []

    def test_alerts_high_cpu(self) -> None:
        ro = ResourceOptimizer()
        ro.snapshot(cpu=95.0, ram_used=4.0, ram_total=16.0)
        alerts = ro.alerts()
        assert len(alerts) >= 1

    def test_recommendations(self) -> None:
        ro = ResourceOptimizer()
        ro.snapshot(cpu=50.0, ram_used=8.0, ram_total=16.0)
        recs = ro.recommendations()
        assert isinstance(recs, list)


# ============================================================================
# CloudFallback (if available)
# ============================================================================


class TestCloudFallback:
    def test_should_fallback_false_by_default(self) -> None:
        cf = CloudFallback()
        # Disabled by default
        assert cf.should_fallback(local_latency_ms=10.0, local_load_percent=10.0) is False

    def test_should_fallback_true_on_high_load(self) -> None:
        from cognithor.core.performance import FallbackConfig

        cfg = FallbackConfig(enabled=True, trigger_load_percent=80)
        cf = CloudFallback(config=cfg)
        assert cf.should_fallback(local_latency_ms=10.0, local_load_percent=95.0) is True

    def test_should_fallback_high_latency(self) -> None:
        from cognithor.core.performance import FallbackConfig

        cfg = FallbackConfig(enabled=True, trigger_latency_ms=1000)
        cf = CloudFallback(config=cfg)
        assert cf.should_fallback(local_latency_ms=5000.0, local_load_percent=10.0) is True

    def test_record_fallback(self) -> None:
        cf = CloudFallback()
        cf.record_fallback(cost_eur=0.05)
        assert cf._daily_requests == 1
        assert cf._daily_cost == 0.05

    def test_config_property(self) -> None:
        cf = CloudFallback()
        assert cf.config is not None


# ============================================================================
# PerformanceManager
# ============================================================================


class TestPerformanceManager:
    def test_init(self) -> None:
        pm = PerformanceManager()
        assert pm.vector_store is not None
        assert pm.balancer is not None
        assert pm.decomposer is not None
        assert pm.fallback is not None
        assert pm.optimizer is not None
        assert pm.latency is not None

    def test_stats(self) -> None:
        pm = PerformanceManager()
        stats = pm.stats()
        assert isinstance(stats, dict)

    def test_process_query(self) -> None:
        pm = PerformanceManager()
        result = pm.process_query("Was ist Python?")
        assert isinstance(result, dict)

    def test_process_query_with_embedding(self) -> None:
        pm = PerformanceManager()
        pm.vector_store.add("Python ist toll", [1.0] * 384)
        result = pm.process_query("Was ist Python?", query_embedding=[1.0] * 384)
        assert isinstance(result, dict)
