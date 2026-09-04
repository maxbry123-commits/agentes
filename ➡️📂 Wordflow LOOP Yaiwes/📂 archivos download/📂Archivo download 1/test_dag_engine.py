"""
tests/core/test_dag_engine.py
Tests unitarios de src/core/dag_engine.py — T-001 (archivo 3/4)
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from src.core.dag_engine import (
    CycleDetectedError,
    DAGEngine,
    ManifestValidationError,
)


def _manifest(edges: Dict[str, List[str]]) -> Dict[str, Any]:
    """Helper: construye un manifest a partir de {node_id: [depends_on]}."""
    return {
        "nodes": {
            node_id: {"payload": {}, "depends_on": deps}
            for node_id, deps in edges.items()
        }
    }


def test_topological_order_linear_chain() -> None:
    engine = DAGEngine()
    manifest = _manifest({"a": [], "b": ["a"], "c": ["b"]})
    assert engine.topological_order(manifest) == ["a", "b", "c"]


def test_topological_order_ties_broken_alphabetically() -> None:
    engine = DAGEngine()
    manifest = _manifest({"c": [], "a": [], "b": []})
    assert engine.topological_order(manifest) == ["a", "b", "c"]


def test_topological_order_diamond_dependency() -> None:
    engine = DAGEngine()
    manifest = _manifest({"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]})
    order = engine.topological_order(manifest)
    assert order[0] == "a"
    assert order[-1] == "d"
    assert set(order[1:3]) == {"b", "c"}


def test_topological_order_is_deterministic_across_runs() -> None:
    engine = DAGEngine()
    manifest = _manifest({"x": [], "y": ["x"], "z": ["x"], "w": ["y", "z"]})
    r1 = engine.topological_order(manifest)
    r2 = engine.topological_order(manifest)
    assert r1 == r2


def test_manifest_missing_nodes_key_raises() -> None:
    engine = DAGEngine()
    with pytest.raises(ManifestValidationError):
        engine.topological_order({})


def test_manifest_empty_nodes_raises() -> None:
    engine = DAGEngine()
    with pytest.raises(ManifestValidationError):
        engine.topological_order({"nodes": {}})


def test_manifest_node_not_dict_raises() -> None:
    engine = DAGEngine()
    with pytest.raises(ManifestValidationError):
        engine.topological_order({"nodes": {"a": "not-a-dict"}})


def test_manifest_unknown_dependency_raises() -> None:
    engine = DAGEngine()
    manifest = _manifest({"a": ["ghost"]})
    with pytest.raises(ManifestValidationError):
        engine.topological_order(manifest)


def test_cycle_detection_direct_cycle() -> None:
    engine = DAGEngine()
    manifest = _manifest({"a": ["b"], "b": ["a"]})
    with pytest.raises(CycleDetectedError):
        engine.topological_order(manifest)


def test_detect_cycle_returns_cycle_list() -> None:
    engine = DAGEngine()
    manifest = _manifest({"a": ["b"], "b": ["a"]})
    cycle = engine.detect_cycle(manifest)
    assert cycle is not None
    assert set(cycle) >= {"a", "b"}


def test_detect_cycle_returns_none_when_acyclic() -> None:
    engine = DAGEngine()
    manifest = _manifest({"a": [], "b": ["a"]})
    assert engine.detect_cycle(manifest) is None


def test_iter_ready_batches_respects_dependencies() -> None:
    import asyncio

    async def scenario() -> None:
        engine = DAGEngine()
        manifest = _manifest({"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]})
        batches: List[List[str]] = []
        async for batch in engine.iter_ready_batches(manifest):
            batches.append(batch)
        assert batches == [["a"], ["b", "c"], ["d"]]

    asyncio.run(scenario())


def test_iter_ready_batches_single_independent_nodes() -> None:
    import asyncio

    async def scenario() -> None:
        engine = DAGEngine()
        manifest = _manifest({"x": [], "y": [], "z": []})
        batches: List[List[str]] = []
        async for batch in engine.iter_ready_batches(manifest):
            batches.append(batch)
        assert batches == [["x", "y", "z"]]

    asyncio.run(scenario())
