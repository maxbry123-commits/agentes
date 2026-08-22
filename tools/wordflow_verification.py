from __future__ import annotations

import json
import py_compile
import traceback
from pathlib import Path

OUT = Path("verification-output")
OUT.mkdir(parents=True, exist_ok=True)


def probe(name, fn, results):
    try:
        value = fn()
        results[name] = {"status": "PASS", "value": repr(value)[:2000]}
    except Exception as exc:
        results[name] = {
            "status": "FAIL",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }


def t01():
    roots = (Path("extensions/wordflow"), Path("extensions/wordflow_kernel"))
    files = sorted(p for root in roots for p in root.rglob("*.py"))
    for path in files:
        py_compile.compile(str(path), doraise=True)
    return f"{len(files)} python files compiled"


def t02():
    from extensions.wordflow_kernel.gateway.intelligence import make_request
    from extensions.wordflow_kernel.gateway.router_http import RouterHTTPGateway
    result = RouterHTTPGateway(router_url="", allow_mock_fallback=False).execute(
        make_request("T02", "llm.complete", {"prompt": "probe"}, {}, {"vendor": "DENY"})
    )
    assert result.status == "DENY" and result.provider is None and result.output.get("reason") == "ROUTER_URL_empty", result
    return result


def t03():
    from extensions.wordflow.engine.code_path_runner import consult_path_gateway
    result = consult_path_gateway("probe-mission", "offline gateway probe")
    assert result["invoked"] is True and result["vendor_call"] is False and result["llm_control"] == "DENY", result
    return result


def t04():
    import tempfile
    from extensions.wordflow.standards.gap_registry import Gap, GapRegistry
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "gaps.json"
        first = GapRegistry(str(path))
        first.add(Gap("G-PROBE", "T04", "M", "R", "blocking", "probe"))
        first.transition("G-PROBE", "FIXED", evidence="probe", revision="r1")
        second = GapRegistry(str(path))
        gap = second.to_list()[0]
        assert gap["status"] == "FIXED" and gap["fixed_revision"] == "r1", gap
    return "persistence/reload PASS"


def t05():
    from extensions.wordflow.standards.forensic_core import (
        ForensicProgrammingEnforcer, ForensicEnforcementState, CoreCheckResult,
        CORE_IDS, CONNECTIVITY_CHAIN,
    )
    state = ForensicEnforcementState(
        context_verified=True, handoff_verified=True,
        core_results=[CoreCheckResult(x, True, "probe") for x in CORE_IDS],
        connectivity={x: True for x in CONNECTIVITY_CHAIN},
        evidence_complete=True, final_clean_reaudit_passed=True, quality_dag_ok=True,
    )
    passes = ForensicProgrammingEnforcer().run_four_passes(state)
    assert len(passes) == 4 and all(item.passed for item in passes), passes
    return passes


def t06():
    from extensions.wordflow_kernel.reception.convert import ingest
    result = ingest({"raw_text": "pytest reception wiring deterministic"}, instance_id=None)
    assert result["ok"] is True and result["hops_ok"] is True, result
    assert result["invoked"]["input_compiler"] is True
    assert result["invoked"]["task_classifier"] is True
    assert result["invoked"]["enchufe_plugin"] is True
    assert result["connectivity"]["required_ok"] is True and result["connectivity"]["optional_safe"] is True, result
    assert result["classification"]["gate"]["call_llm"] is False, result
    return result


def t07():
    from extensions.wordflow.engine.evidence_packet import (
        build_evidence_packet, chain_packets, verify_packet_chain, EvidencePacketError,
    )
    first = build_evidence_packet(task_id="T07", claim_status="PARTIAL", timestamp=1.0)
    second = build_evidence_packet(task_id="T07", claim_status="COMPLETED", timestamp=2.0)
    chain = chain_packets([first, second])
    assert chain["ok"] and verify_packet_chain(chain["packets"])["ok"], chain
    tampered = dict(chain["packets"][1])
    tampered["notes"] = "tampered"
    assert verify_packet_chain([chain["packets"][0], tampered])["ok"] is False
    try:
        chain_packets([tampered])
    except EvidencePacketError:
        pass
    else:
        raise AssertionError("tampered source accepted")
    return "chain + tamper detection PASS"


def t08():
    from extensions.wordflow.standards.verdict_authority import VerdictAuthority
    result = VerdictAuthority().decide(evidence=None, require_evidence=True)
    assert result["verdict"] == "FAIL" and result["llm_may_declare_pass"] is False, result
    return result


def t09():
    from extensions.wordflow.standards.quality_dag import QualityDAG, GateStatus, GateResult
    from extensions.wordflow.standards.forensic_core import (
        ForensicProgrammingEnforcer, ForensicEnforcementState, CoreCheckResult,
        CORE_IDS, CONNECTIVITY_CHAIN,
    )
    dag = QualityDAG()
    for node in dag.nodes:
        dag.register(node.name, lambda n=node.name: GateResult(n, GateStatus.PASS, "probe"))
    results = dag.run(fail_closed=True)
    assert dag.passed(results) and len(results) == len(dag.nodes), results
    fail_closed = QualityDAG().run(fail_closed=True)
    assert fail_closed[0].status == GateStatus.FAIL, fail_closed
    state = ForensicEnforcementState(
        context_verified=True, handoff_verified=True,
        core_results=[CoreCheckResult(x, True, "probe") for x in CORE_IDS],
        connectivity={x: True for x in CONNECTIVITY_CHAIN},
        evidence_complete=True, final_clean_reaudit_passed=True, quality_dag_ok=True,
    )
    passes = ForensicProgrammingEnforcer().run_four_passes(state)
    assert all(item.passed for item in passes), passes
    return results


def t10a():
    text = Path("PIPELINE/CLAIM_C100_PROGRESS.md").read_text(encoding="utf-8")
    assert "Claim C100 | **NO**" in text
    return "C100 remains NO"


def t10b():
    import pytest
    args = [
        "-q",
        "extensions/wordflow/tests/test_router_http_gateway.py",
        "extensions/wordflow/tests/test_gap_registry_persistence.py",
        "extensions/wordflow/tests/test_gap_state_machine.py",
        "extensions/wordflow/tests/test_evidence_packet_chain.py",
        "extensions/wordflow/tests/test_audit_history.py",
    ]
    code = pytest.main(args)
    if code != 0:
        raise AssertionError(f"pytest regression exit code={code}")
    return "pytest regression PASS"


PROBES = [("T01", t01), ("T02", t02), ("T03", t03), ("T04", t04), ("T05", t05),
          ("T06", t06), ("T07", t07), ("T08", t08), ("T09", t09), ("T10A", t10a), ("T10B", t10b)]
results = {}
for name, fn in PROBES:
    print(f"=== {name} ===", flush=True)
    probe(name, fn, results)
    print(results[name]["status"], flush=True)

manifest = {"commit": __import__("os").environ.get("GITHUB_SHA", "local"), "results": results}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")

lines = ["# CI LAST RESULT", "", f"Commit: `{manifest['commit']}`", "", "| Probe | Status | Error |", "|---|---|---|"]
for name, _ in PROBES:
    row = results[name]
    error = row.get("error", "")
    lines.append(f"| {name} | **{row['status']}** | {error.replace('|', '/')[:500]} |")
    if row["status"] == "FAIL":
        lines += ["", f"## {name} traceback", "", "```text", row.get("traceback", ""), "```"]
(OUT / "CI_LAST_RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
(OUT / "outcomes.txt").write_text("\n".join(f"{name}={results[name]['status']}" for name, _ in PROBES) + "\n", encoding="utf-8")

failed = [name for name, _ in PROBES if results[name]["status"] != "PASS"]
print("FAILED:", ", ".join(failed) if failed else "NONE", flush=True)
raise SystemExit(1 if failed else 0)
