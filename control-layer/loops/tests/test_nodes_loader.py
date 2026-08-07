from pathlib import Path
from loops.nodes_loader import NodesLoader, parse_node_doc
from loops.contracts.capability import CapabilityRequest
from loops.phase_handlers import make_default_handlers
from loops.phases import PhaseRunner

FIXTURES = Path(__file__).parent / "fixtures" / "nodes"


def test_parse_and_load():
    loader = NodesLoader()
    ad = loader.load_dir(FIXTURES)
    assert len(loader.loaded) >= 2
    ids = {x["id"] for x in loader.loaded}
    assert "coder" in ids and "researcher" in ids
    req = CapabilityRequest("1", "R", "code_generation", "t")
    res = ad.dispatch(req, {"x": 1})
    assert res.ok and res.output.get("agent_id") == "coder"


def test_ejecutar_via_loaded_nodes():
    loader = NodesLoader()
    ad = loader.load_dir(FIXTURES)
    runner = PhaseRunner(handlers=make_default_handlers(ad))
    results, verdict = runner.run({"run_id": "R", "capability": "research"})
    assert verdict.ok
    ejec = next(r for r in results if r.phase == "ejecutar")
    assert ejec.ok and ejec.output.get("resolved_by") == "researcher"
