import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "wordflow_loop" / "adapters" / "codebase_memory_mcp_adapter.py"
spec = importlib.util.spec_from_file_location("cbm_adapter", MODULE)
m = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(m)


def test_descriptor_fail_closed():
    d = m.descriptor()
    assert d["component_id"] == "yaiwes.codebase_memory_mcp"
    assert d["source_commit"] == "2058d49a04b785315c9f5bb56b6e2365822b576b"
    assert d["execution_authorized"] is False
    assert d["requires_acquisition_verified"] is True
    assert d["read_only"] is True


def test_read_only_request():
    r = m.build_request("get_architecture", {"path": "."})
    assert r["method"] == "tools/call"
    assert r["params"]["name"] == "get_architecture"
    assert r["execution_authorized"] is False
    assert r["read_only"] is True


def test_mutating_or_unknown_tool_rejected():
    import pytest
    with pytest.raises(ValueError):
        m.build_request("manage_adr", {"action": "create"})
    with pytest.raises(ValueError):
        m.build_request("unknown_tool")


def test_bad_arguments_rejected():
    import pytest
    with pytest.raises(TypeError):
        m.build_request("semantic_query", "not-a-mapping")


def test_health_never_claims_runtime():
    h = m.health()
    assert h["ok"] is True
    assert h["upstream_runtime_verified"] is False
    assert h["acquisition_verified"] is False
    assert h["execution_authorized"] is False
