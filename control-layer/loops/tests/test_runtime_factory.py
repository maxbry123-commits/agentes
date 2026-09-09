from loops.runtime_factory import executor_for_spec, build_adapter_from_project
from loops.contracts.capability import CapabilityRequest
from pathlib import Path


def test_stub_generic():
    fn = executor_for_spec({"id": "coder", "capabilities": ["code_generation"], "meta": {"adapter": {"id": "generic"}}})
    r = fn("code_generation", {"x": 1})
    assert r.ok and r.output.get("agent_id") == "coder"


def test_temporal_missing_bin_is_stub():
    fn = executor_for_spec({
        "id": "temporal-agent",
        "capabilities": ["research"],
        "meta": {"adapter": {"id": "temporal", "entrypoint": "/no/such/bin"}},
    })
    r = fn("research", {})
    assert r.ok and r.output.get("temporal_bin") == "missing"


def test_build_from_fixtures():
    fixtures = Path(__file__).parent / "fixtures"
    if not (fixtures / "nodes").is_dir():
        return
    ad = build_adapter_from_project(fixtures)
    req = CapabilityRequest("1", "R", "code_generation", "t")
    res = ad.dispatch(req, {})
    assert res.ok
