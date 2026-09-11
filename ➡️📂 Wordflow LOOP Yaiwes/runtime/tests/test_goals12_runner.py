from copy import deepcopy
import json
from pathlib import Path

from runtime.src.core.goals12 import (
    ASK_CONSILIO12,
    INPUT_GOALS12,
    OUTPUT_GOALS12,
    REQUIRED_SIMULATIONS,
    evaluate_goals12_run,
)


def _evidence(names):
    return {name: {"passed": True, "evidence_refs": [f"evidence:{name}"]} for name in names}


def _valid_run():
    return {
        "schema": "yaiwes.goals12/v1",
        "node_id": "G-015-test",
        "input_goals": _evidence(INPUT_GOALS12),
        "output_goals": _evidence(OUTPUT_GOALS12),
        "council": [
            {"name": name, "passed": True, "evidence_refs": [f"council:{name}"]}
            for name in ASK_CONSILIO12
        ],
        "simulations": [
            {"name": name, "passed": True, "evidence_refs": [f"simulation:{name}"]}
            for name in REQUIRED_SIMULATIONS
        ],
        "refutations": [
            {"name": f"R{i}", "survived": True, "evidence_refs": [f"refutation:{i}"]}
            for i in range(1, 4)
        ],
        "cross_checks": [
            {"name": "contract-vs-result", "passed": True, "evidence_refs": ["cross:1"]}
        ],
    }


def test_complete_run_is_verified_but_never_authorizes_execution():
    result = evaluate_goals12_run(_valid_run())
    assert result.passed is True
    assert result.status == "VERIFIED_CLOSED"
    assert result.execution_authorized is False
    assert len(result.evidence_sha256) == 64


def test_missing_input_and_output_evidence_fails_closed():
    run = _valid_run()
    del run["input_goals"][INPUT_GOALS12[0]]
    run["output_goals"][OUTPUT_GOALS12[0]]["evidence_refs"] = []
    result = evaluate_goals12_run(run)
    assert result.status == "GAP"
    assert f"INPUT_GOAL_MISSING:{INPUT_GOALS12[0]}" in result.missing
    assert f"OUTPUT_EVIDENCE_MISSING:{OUTPUT_GOALS12[0]}" in result.missing


def test_council_simulation_refutation_and_cross_check_fail_closed():
    run = _valid_run()
    run["council"] = run["council"][:-1]
    run["simulations"][2]["passed"] = False
    run["refutations"] = run["refutations"][:2]
    run["cross_checks"][0]["passed"] = False
    missing = evaluate_goals12_run(run).missing
    assert any(item.startswith("COUNCIL12_MISSING_OR_FAILED") for item in missing)
    assert "SIMULATION_MISSING_OR_FAILED:ADVERSARIAL" in missing
    assert "REFUTATIONS_LT_3" in missing
    assert "CROSS_CHECK_FAILED:1" in missing


def test_canonical_hash_is_stable_and_binds_evidence():
    run = _valid_run()
    first = evaluate_goals12_run(run).evidence_sha256
    assert evaluate_goals12_run(deepcopy(run)).evidence_sha256 == first
    run["cross_checks"][0]["evidence_refs"] = ["cross:changed"]
    assert evaluate_goals12_run(run).evidence_sha256 != first


def test_published_schema_matches_runner_contract():
    schema_path = Path(__file__).parents[1] / "schemas" / "goals12-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["$id"] == "yaiwes.goals12/v1"
    assert set(schema["required"]) == set(_valid_run())
    assert schema["properties"]["council"]["minItems"] == 12
    assert schema["properties"]["simulations"]["minItems"] == 3
    assert schema["properties"]["refutations"]["minItems"] == 3
