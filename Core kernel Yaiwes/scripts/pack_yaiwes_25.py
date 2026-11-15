#!/usr/bin/env python3
"""Pack repo into 25 segment ZIPs + micro ZIPs. Copy only. No invent. No move source."""
from __future__ import annotations

import csv
import hashlib
import os
import zipfile
from pathlib import Path

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
DIST = ROOT / "dist" / "YAIWES-WORDFLOW-25"
SKIP_DIRS = {".git", "dist", "node_modules", "__pycache__"}

SEGMENTS = [
    "01_INTERFACE",
    "02_INPUT_CORE",
    "03_MISSION_CONTRACT",
    "04_GOVERNANCE_CONTRACTS",
    "05_GOVERNANCE_ENFORCEMENT",
    "06_FORENSIC_GOVERNANCE",
    "07_LLM_CONTROL",
    "08_REASONING_KERNEL",
    "09_EXTENSION_KERNEL",
    "10_CONTROL_LAYER",
    "11_DEFINITION_REGISTRY",
    "12_WORKFLOW_COMPILER",
    "13_MULTI_WORKFLOW_ENGINE",
    "14_EXECUTION_ORCHESTRATOR",
    "15_PLANNING_SCHEDULING",
    "16_AGENT_FLEET",
    "17_CODE_ENGINE_POOL",
    "18_CODE_ENGINES",
    "19_CODE_PROGRAMMING_ENGINE",
    "20_WORDFLOW_CODE_HOT_PATH",
    "21_DURABLE_EXECUTION",
    "22_MEMORY_KNOWLEDGE",
    "23_TOOL_MODEL_RUNTIME",
    "24_GUARDRAILS_OBSERVABILITY",
    "25_PUBLISH_DEPLOY",
    "00_UNASSIGNED",
]

RULES = [
    ("20_WORDFLOW_CODE_HOT_PATH", (
        "extensions/wordflow/engine/code_path_runner.py",
        "extensions/wordflow/engine/code_path_smoke.py",
        "extensions/wordflow/tests/test_code_path_runner.py",
        "extensions/wordflow/tests/test_code_path_smoke.py",
        "agente-yaiwes/code-programming-engine/code-path-execution/",
    )),
    ("01_INTERFACE", (
        "agente-yaiwes/input-layer/cli-entry/",
        "agente-yaiwes/input-layer/route-entry/",
        "agente-yaiwes/control-plane-ui/",
        "wordflow/abi.py",
        "wordflow/ABI_v1.md",
        "extensions/wordflow/engine/entrypoint.py",
        "extensions/wordflow/engine/entrypoint_v1.py",
    )),
    ("02_INPUT_CORE", (
        "extensions/wordflow/engine/input_compiler.py",
        "extensions/wordflow/engine/input_normalizer.py",
        "extensions/wordflow/engine/input_quality_bar.py",
        "extensions/wordflow/reception/",
        "extensions/wordflow/engine/enchufe_gate.py",
        "extensions/wordflow/engine/cursor_hooks.py",
        "agente-yaiwes/input-layer/",
        "Desplegar/",
    )),
    ("03_MISSION_CONTRACT", (
        "extensions/wordflow/engine/structured_questions.py",
        "extensions/wordflow/engine/mission.py",
        "extensions/wordflow/contracts/",
        "extensions/wordflow/schemas/input_block.schema.json",
        "extensions/wordflow/schemas/input_contract.schema.json",
        "extensions/wordflow/schemas/structured_questions.schema.json",
        "extensions/wordflow/planner/",
    )),
    ("07_LLM_CONTROL", (
        "extensions/wordflow_kernel/fail_closed.py",
        "extensions/wordflow_kernel/llm_control.py",
        "agente-yaiwes/control-governance/llm-control-deny/",
        "agente-yaiwes/control-governance/fail_closed.py",
        "agente-yaiwes/control-governance/llm_control.py",
    )),
    ("06_FORENSIC_GOVERNANCE", (
        "extensions/wordflow/standards/forensic_core.py",
        "extensions/wordflow/standards/forensic_contract.py",
        "extensions/wordflow/standards/verdict_authority.py",
        "extensions/wordflow/standards/quality_dag.py",
        "extensions/wordflow/standards/quality_handlers.py",
        "extensions/wordflow/standards/closure_engine.py",
        "extensions/wordflow/standards/core_auto_measure.py",
        "extensions/wordflow/standards/fc_auto_measure.py",
        "agente-yaiwes/control-governance/forensic-core/",
        "agente-yaiwes/control-governance/verdict-authority/",
        "agente-yaiwes/control-governance/quality-dag/",
        "agente-yaiwes/control-governance/closure-engine/",
    )),
    ("05_GOVERNANCE_ENFORCEMENT", (
        "extensions/wordflow/standards/sheriff.py",
        "extensions/wordflow/standards/checklist_sheriff.py",
        "extensions/wordflow/engine/sheriff_adapter.py",
        "extensions/wordflow/engine/control_sheriff_bridge.py",
        "extensions/wordflow/engine/sentinel.py",
        "extensions/wordflow/engine/council.py",
        "extensions/wordflow/engine/policy_engine.py",
        "extensions/wordflow/policies/",
        "agente-yaiwes/control-governance/sheriff-bridge/",
        "agente-yaiwes/control-governance/sentinel/",
        "agente-yaiwes/control-governance/council/",
        "agente-yaiwes/control-governance/policy-engine/",
    )),
    ("04_GOVERNANCE_CONTRACTS", (
        "extensions/wordflow/standards/",
        "agente-yaiwes/control-governance/",
        "wordflow/85_CONTRACTS_INDEX.md",
        "wordflow/ENCHUFE_UNIVERSAL_v2_SCHEMA.json",
        "wordflow/validator_v2.py",
        "wordflow/sentinela_stub.py",
    )),
    ("08_REASONING_KERNEL", (
        "agente-yaiwes/kernel-principal/reasoning-kernel/",
        "extensions/wordflow/engine/cognitive_loop.py",
        "extensions/wordflow/engine/cognitive_registers.py",
        "extensions/wordflow/engine/expert_panel.py",
        "extensions/wordflow/engine/expert_decision.py",
        "extensions/wordflow/engine/expert_router.py",
        "extensions/wordflow/engine/reasoning_ledger.py",
        "extensions/wordflow/engine/role_analyzer.py",
    )),
    ("09_EXTENSION_KERNEL", (
        "agente-yaiwes/kernel-principal/extension-kernel/",
        "extensions/wordflow/engine/bootstrap.py",
        "extensions/wordflow/engine/microkernel_install.py",
        "extensions/wordflow/engine/engine_abi.py",
        "extensions/wordflow/engine/engine_attach.py",
        "extensions/wordflow/engine/extension_registry.py",
        "extensions/wordflow/engine/capability_brain.py",
        "extensions/wordflow/engine/capability_intent.py",
        "extensions/wordflow/engine/capability_passport.py",
        "extensions/wordflow_kernel/ficha_loader.py",
        "extensions/wordflow_kernel/engine_registry.py",
        "extensions/wordflow_kernel/bootstrap_fake.py",
        "extensions/wordflow_kernel/bootstrap_multi.py",
        "extensions/wordflow_kernel/bootstrap_v1.py",
        "extensions/wordflow/ficha.v2.json",
        "extensions/wordflow/manifest.yaml",
    )),
    ("10_CONTROL_LAYER", (
        "control-layer/",
        "agente-yaiwes/kernel-principal/control-layer/",
        "agente-yaiwes/kernel-principal/workflow.py",
        "agente-yaiwes/kernel-principal/runtime.py",
        "agente-yaiwes/kernel-principal/stages/",
        "extensions/wordflow_kernel/workflow.py",
        "extensions/wordflow_kernel/runtime.py",
        "extensions/wordflow_kernel/stages/",
        "extensions/wordflow_kernel/preflight.py",
    )),
    ("11_DEFINITION_REGISTRY", (
        "agente-yaiwes/definition-registry/",
        "extensions/wordflow/schemas/",
        "extensions/wordflow/store/",
        "extensions/wordflow/component_catalog.json",
        "extensions/wordflow/connect_catalog.json",
    )),
    ("13_MULTI_WORKFLOW_ENGINE", (
        "agente-yaiwes/multi-workflow-engine/",
        "extensions/wordflow_kernel/instance.py",
        "extensions/wordflow_kernel/instance_store.py",
        "extensions/wordflow/engine/loop_bridge.py",
        "extensions/maxbry_loop/",
    )),
    ("12_WORKFLOW_COMPILER", (
        "extensions/wordflow/engine/dual_compiler.py",
        "extensions/wordflow/engine/skill_native_compiler.py",
        "extensions/wordflow/engine/goals_compiler.py",
        "extensions/wordflow/engine/build_plan_only.py",
        "extensions/wordflow/codegen/",
    )),
    ("15_PLANNING_SCHEDULING", (
        "extensions/wordflow/engine/goal_lock.py",
        "extensions/wordflow/engine/scheduler.py",
        "extensions/wordflow/engine/task_classifier.py",
        "extensions/wordflow/engine/task_queue.py",
        "extensions/wordflow/engine/planning_proposal.py",
        "extensions/wordflow/engine/fetch_planner.py",
        "extensions/wordflow/engine/goals_extractor.py",
        "extensions/wordflow/engine/objective_echo.py",
        "agente-yaiwes/execution-orchestration/goal-lock/",
        "agente-yaiwes/execution-orchestration/mission-planning/",
        "agente-yaiwes/execution-orchestration/task-classifier-scheduler/",
    )),
    ("14_EXECUTION_ORCHESTRATOR", (
        "agente-yaiwes/execution-orchestration/",
        "extensions/wordflow/engine/orchestrator.py",
        "extensions/wordflow/engine/orchestrator_v1.py",
        "extensions/wordflow/engine/execution_facade.py",
        "extensions/wordflow/engine/execution_manifest.py",
        "extensions/wordflow/engine/main_loop.py",
        "extensions/wordflow/engine/supervisor.py",
    )),
    ("16_AGENT_FLEET", (
        "agente-yaiwes/agent-fleet-parallelism/",
        "extensions/wordflow/engine/parallel_facade.py",
        "extensions/wordflow/engine/parallel_runtime.py",
        "extensions/wordflow/engine/parallel_runtime_guarded.py",
        "extensions/wordflow/engine/wave4_runtime.py",
        "extensions/wordflow/engine/wave5_runtime.py",
        "extensions/wordflow/engine/handoff.py",
        "extensions/wordflow_kernel/spawn.py",
    )),
    ("17_CODE_ENGINE_POOL", (
        "agente-yaiwes/execution-engine-pool/",
        "extensions/wordflow/cables/",
        "extensions/wordflow/engine/ports/",
        "extensions/adapters/",
        "extensions/wordflow_kernel/gateway/",
    )),
    ("18_CODE_ENGINES", (
        "extensions/wordflow_kernel/engines/",
        "extensions/wordflow/engine/engines/",
        "extensions/wordflow/motors/",
        "extensions/wordflow/engine/kimi_policy.py",
    )),
    ("19_CODE_PROGRAMMING_ENGINE", (
        "code-programming-engine/",
        "agente-yaiwes/code-programming-engine/",
        "extensions/wordflow/engine/programming_pipeline.py",
        "extensions/wordflow/engine/programming_kwargs.py",
    )),
    ("21_DURABLE_EXECUTION", (
        "extensions/wordflow/engine/checkpoint_store.py",
        "extensions/wordflow/engine/state_store.py",
        "extensions/wordflow/engine/state_authority.py",
        "extensions/wordflow/engine/lease_manager.py",
        "extensions/wordflow/engine/retry_policy.py",
        "extensions/wordflow/engine/circuit_breaker.py",
        "extensions/wordflow/engine/recovery.py",
        "extensions/wordflow/state/",
        "agente-yaiwes/state-events-durability/",
        "extensions/wordflow_kernel/checkpoint.py",
        "extensions/wordflow_kernel/ledger.py",
    )),
    ("22_MEMORY_KNOWLEDGE", (
        "memory/",
        "extensions/knowledge/",
        "agente-yaiwes/tools-models-memory-knowledge/",
        "extensions/wordflow/engine/hf_index.py",
        "extensions/wordflow/engine/hf_resolver.py",
        "extensions/wordflow_kernel/memory.py",
        "extensions/wordflow_kernel/memory_slot/",
        "extensions/wordflow_kernel/knowledge_index.py",
    )),
    ("23_TOOL_MODEL_RUNTIME", (
        "tools/",
        "extensions/wordflow/engine/resource_broker.py",
        "extensions/wordflow/engine/resource_catalog.py",
        "extensions/wordflow/engine/resource_gate.py",
        "extensions/wordflow/engine/resource_runtime.py",
        "extensions/wordflow/engine/resource_trace.py",
        "extensions/wordflow/engine/sandbox_manager.py",
        "extensions/wordflow/engine/docker_transport.py",
        "extensions/wordflow_kernel/resources/",
        "agente-yaiwes/kernel-principal/resource-governance/",
    )),
    ("24_GUARDRAILS_OBSERVABILITY", (
        "extensions/wordflow/engine/evidence_packet.py",
        "extensions/wordflow/engine/evidence_bridge.py",
        "extensions/wordflow/engine/evidence_graph.py",
        "extensions/wordflow/engine/claim_validator.py",
        "extensions/wordflow/engine/write_evidence.py",
        "extensions/wordflow/engine/bitacora.py",
        "extensions/wordflow_kernel/trace.py",
        "agente-yaiwes/observability/",
        "agente-yaiwes/security-auth/",
        "extensions/audit_forensic/",
    )),
    ("25_PUBLISH_DEPLOY", (
        "despliegue/",
        "agente-yaiwes/deploy-publish/",
        "extensions/github_deploy/",
        "extensions/github_publisher/",
        "extensions/wordflow/engine/github_api.py",
        "extensions/wordflow/engine/github_publisher.py",
        "extensions/wordflow/engine/publish_path.py",
        "extensions/wordflow/engine/push_ping.py",
        "extensions/wordflow/engine/push_ping_hooks.py",
        "extensions/wordflow/engine/project_mirror.py",
        "extensions/wordflow/accounts/",
        "extensions/wordflow/connectors/",
        ".github/workflows/",
        "GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md",
        "METODO_ZIP_COPY_DETERMINISTA.md",
        "GUIA_CUENTAS_REMOTE.md",
        "GUIA_CUENTA_B_REMOTE.md",
    )),
]

MICROS = [
    ("G5_SHERIFF_STACK", "05_GOVERNANCE_ENFORCEMENT", (
        "extensions/wordflow/engine/sheriff_adapter.py",
        "extensions/wordflow/engine/sentinel.py",
        "extensions/wordflow/engine/council.py",
    )),
    ("K2_DECISION_CONSENSUS", "08_REASONING_KERNEL", (
        "extensions/wordflow/engine/expert_decision.py",
        "extensions/wordflow/engine/expert_panel.py",
    )),
    ("K3_ABI_REGISTRY", "09_EXTENSION_KERNEL", (
        "extensions/wordflow/engine/engine_abi.py",
        "extensions/wordflow/engine/extension_registry.py",
    )),
    ("C1_ADAPTER_LAYER", "17_CODE_ENGINE_POOL", (
        "extensions/wordflow_kernel/gateway/",
        "extensions/wordflow/engine/ports/",
    )),
    ("C5_ENGINE_INTEGRATIONS", "18_CODE_ENGINES", (
        "extensions/wordflow_kernel/engines/",
        "extensions/wordflow/motors/",
    )),
    ("P5_CODE_PATH", "20_WORDFLOW_CODE_HOT_PATH", (
        "extensions/wordflow/engine/code_path_runner.py",
        "extensions/wordflow/engine/code_path_smoke.py",
    )),
]


def lang_of(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {".py": "py", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".md": "md", ".txt": "txt"}.get(ext, ext.lstrip(".") or "none")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            out.append(Path(dirpath) / name)
    return sorted(out)


def matches(rel: str, rule: str) -> bool:
    rel_n = rel.replace("\\", "/")
    rule_n = rule.replace("\\", "/")
    if rule_n.endswith("/"):
        return rel_n.startswith(rule_n)
    return rel_n == rule_n


def assign(rel: str) -> str:
    for seg, prefixes in RULES:
        if any(matches(rel, p) for p in prefixes):
            return seg
    return "00_UNASSIGNED"


def copy_into(seg_dir: Path, src: Path, rel: str) -> None:
    dest = seg_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())


def zip_dir(folder: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(folder.parent).as_posix())


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    source_sha = os.environ.get("GITHUB_SHA") or "LOCAL"
    files = iter_files()
    assigned = {s: [] for s in SEGMENTS}
    for src in files:
        rel = src.relative_to(ROOT).as_posix()
        if rel.startswith("dist/"):
            continue
        seg = assign(rel)
        rec = {
            "path": rel,
            "tipo": lang_of(rel),
            "size": src.stat().st_size,
            "sha256": sha256_file(src),
            "segment": seg,
            "placeholder": "1" if src.name in {"PLACEHOLDER.md", "SOURCE.md", "PENDIENTE_CODE"} else "0",
        }
        assigned[seg].append(rec)
        copy_into(DIST / seg, src, rel)
    inv = DIST / "INVENTARIO-MAESTRO.csv"
    with inv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "tipo", "size", "sha256", "segment", "placeholder"])
        w.writeheader()
        for seg in SEGMENTS:
            for rec in assigned[seg]:
                w.writerow(rec)
    total = sum(len(v) for v in assigned.values())
    lines = [
        "# SOURCE-LOCK",
        f"- source_sha: `{source_sha}`",
        f"- files_scanned: {total}",
        "- rule: copy-only; no move; no invent; Guia-plan not rewritten; hot path not rewritten",
        "",
        "| segment | files | py | json | yaml | md |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for seg in SEGMENTS:
        rows = assigned[seg]
        lines.append(
            f"| {seg} | {len(rows)} | {sum(1 for r in rows if r['tipo']=='py')} | {sum(1 for r in rows if r['tipo']=='json')} | {sum(1 for r in rows if r['tipo']=='yaml')} | {sum(1 for r in rows if r['tipo']=='md')} |"
        )
    (DIST / "SOURCE-LOCK.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for seg in SEGMENTS:
        folder = DIST / seg
        folder.mkdir(exist_ok=True)
        rows = assigned[seg]
        (folder / "MANIFEST-SHA256.txt").write_text(
            "\n".join(f"{r['sha256']}  {r['path']}  {r['tipo']}  {r['size']}" for r in rows) + "\n",
            encoding="utf-8",
        )
        zip_dir(folder, DIST / f"{seg}.zip")
    for name, parent, prefixes in MICROS:
        folder = DIST / f"MICRO_{name}"
        folder.mkdir(exist_ok=True)
        n = 0
        for rec in assigned[parent] + assigned.get("00_UNASSIGNED", []):
            if any(matches(rec["path"], p) for p in prefixes):
                src = ROOT / rec["path"]
                if src.is_file():
                    copy_into(folder, src, rec["path"])
                    n += 1
        if n:
            zip_dir(folder, DIST / f"MICRO_{name}.zip")
    print(f"packed {total} files from {source_sha} -> {DIST}")


if __name__ == "__main__":
    main()
