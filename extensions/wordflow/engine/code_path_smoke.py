# -*- coding: utf-8 -*-
"""C-31 code_path_smoke — offline integration of code-path modules. 0% LLM."""
from __future__ import annotations

from typing import Any

from extensions.github_deploy.deployer import FakeGitDataPort, GitHubDeployer
from extensions.wordflow.engine.acquire_12 import acquire_12
from extensions.wordflow.engine.analyze_12 import analyze_document
from extensions.wordflow.engine.claim_validator import validate_claim
from extensions.wordflow.engine.code_path_runner import run_code_path
from extensions.wordflow.engine.dual_compiler import compile_output, promote_12
from extensions.wordflow.engine.evidence_packet import build_evidence_packet, verify_evidence_packet
from extensions.wordflow.engine.policy_engine import check_action, load_policy
from extensions.wordflow.engine.reuse_12 import reuse_12
from extensions.wordflow.engine.resource_catalog import ResourceCatalog, make_entry
from extensions.wordflow.engine.skill_native_compiler import compile_skill_to_code
from extensions.wordflow.engine.github_publisher import MapCredentialStore
from extensions.wordflow.standards.forensic_core import CORE_IDS, CONNECTIVITY_CHAIN, FC_IDS


def run_smoke() -> dict[str, Any]:
    steps: dict[str, Any] = {}

    text = (
        "Objetivo: validar path de code determinista C-31 "
        "con analyze compile promote y claim evidence."
    )
    # GR-01: fail-closed — context + measures explícitas (no asumir PASS sin gates)
    steps["code_path"] = run_code_path(
        text,
        mission_id="C31",
        context_verified=True,
        handoff_verified=True,
        core_measures={cid: True for cid in CORE_IDS},
        connectivity={k: True for k in CONNECTIVITY_CHAIN},
        evidence_complete=True,
        final_clean_reaudit_passed=True,
        quality_dag_ok=True,
        fc_results={fid: True for fid in FC_IDS},
        auto_measure_core=True,
    )

    analyzed = analyze_document("# C31\n\nUse engine/smoke.py\n", doc_id="c31")
    steps["analyze"] = analyzed
    steps["arch_compile"] = compile_output("architecture_output", analyzed["architecture_seed"])

    skill = compile_skill_to_code({"package_id": "sk.c31", "inputs": ["x"], "outputs": ["y"]})
    steps["skill"] = skill
    steps["code_compile"] = compile_output("code", skill["code_output"])

    pin = "c" * 40
    steps["promote"] = promote_12(package_id="sk.c31", track="code", version_pin=pin)

    cat = ResourceCatalog()
    cat.add(make_entry(name="sk.c31", kind="skill", source="local", tags=["c31"]))
    steps["reuse"] = reuse_12(cat, "sk.c31", kind="skill")
    steps["acquire"] = acquire_12(["local:///tmp/c31"])

    pol = load_policy()
    steps["policy_license"] = check_action(pol, "use_license", license="MIT")

    port = FakeGitDataPort(head_sha="0" * 40)
    deployer = GitHubDeployer(
        credentials=MapCredentialStore({"github_token": "test"}),
        port=port,
        dry_run=False,
    )
    steps["deploy"] = deployer.deploy({
        "token_ref": "github_token",
        "repository": "maxbry123-commits/agentes",
        "branch": "main",
        "files": [{"source": "build/a.py", "destination": "extensions/demo/a.py"}],
        "commit_message": "C-31 smoke",
        "expected_head": "0" * 40,
        "content_map": {"build/a.py": "x=1\n"},
    })

    evidence = build_evidence_packet(
        task_id="C-31",
        claim_status="COMPLETED",
        paths=[{
            "path": "extensions/wordflow/engine/code_path_smoke.py",
            "blob_sha": "pending_ci",
        }],
        tests={"smoke": True},
        doc_anchors=["C-31", "Lista2"],
        notes="code_path_smoke",
    )
    steps["evidence"] = evidence
    steps["evidence_ok"] = verify_evidence_packet(evidence)["ok"]
    steps["claim"] = validate_claim({
        "task_id": "C-31",
        "claim_status": "COMPLETED",
        "paths": evidence["paths"],
        "tests": evidence["tests"],
        "doc_anchors": evidence["doc_anchors"],
    })

    ok = all([
        steps["code_path"].get("ok"),
        steps["arch_compile"].get("ok"),
        steps["code_compile"].get("ok"),
        steps["promote"].get("ok"),
        steps["reuse"].get("action") == "REUSE",
        steps["deploy"].get("ok"),
        steps["evidence_ok"],
        steps["claim"].get("ok"),
    ])
    return {"ok": ok, "steps": steps, "llm_control": "DENY", "path": "UNIFIED_RUNNER_V1"}
