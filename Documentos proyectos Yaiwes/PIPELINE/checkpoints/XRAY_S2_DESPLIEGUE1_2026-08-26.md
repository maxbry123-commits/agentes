# FORENSIC X-RAY — S2 / DESPLIEGUE 1 — 2026-08-26

## Scope
Cross-check of the uploaded/library deployment documents against the canonical repository files under `despliegue/` and the S2 plan contract. The canonical plan remains untouched.

## Sources audited
- `despliegue/INSTRUCCIONES_GROK_OPCION_A.md`
- `despliegue/manifests/deployment_01.yaml`
- `despliegue/auditoria/verification.yaml`
- `despliegue/auditoria/checksums.yaml`
- `despliegue/capability_registration.py`
- `extensions/wordflow/component_catalog.json`
- `extensions/wordflow/connect_catalog.json`
- Library documents `DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md`, `SALIDA_7_OBJETIVO_3_1_AUDITORIA_FORENSE_DEPLOYMENT.md`, `SALIDA_8_OBJETIVO_3_1_REPAIR_SPEC_DEPLOYMENT.md`, and related deployment/UOOS documents.

## Findings
1. **S2 plan contract is narrower than the later universal deployment specifications.** S2 requires materialization of Deployment 1 artifacts, catalog append, verification update, and preservation of the legacy hot path. It does not authorize claiming a real external push.
2. **Catalog append was actually completed.** `component_catalog.json` contains `code_programming_engine` and `code_programming_instance_pool`; `connect_catalog.json` contains `CONN.classifier_to_programming_engine` and `CONN.engine_to_intelligence_gateway`. Therefore the former S2 'append pending' statement was stale.
3. `deployment_01.yaml` still has `target_commit_sha: pending_after_push` and `validation_result: PENDING`. This is correct for an unapplied external deployment, but it must not be described as a remote deployment PASS.
4. `checksums.yaml` is still a placeholder. This is a deployment-evidence gap for a real external deployment, not a blocker for the S2 materialization contract.
5. The later deployment specifications require stronger gates: credential/account resolution, target permission preflight, expected_head, manifest hashes, remote readback, evidence, and a deterministic final verdict. Those requirements are not retroactively invented as S2 requirements; they are preserved as later deployment-contract gaps.
6. The uploaded deployment documents also identify real gaps: provider/account binding, expected_head, remote verification, HF explicit revision/readback, UOOS bridge, unknown mapping BLOCK, idempotency/transaction identity, partial-failure recovery, and adversarial tests. These remain explicit GAPs and are not falsely closed by S2.

## Repair performed for S2
- Verified the catalog append idempotency result in the real repository catalogs.
- Kept `extensions/wordflow/engine/code_path_runner.py` as the operational hot path.
- Kept `deployment_01.yaml` honest: no fabricated target commit, no fabricated remote verification.
- Updated the S2 checkpoint and deployment verification record to distinguish **S2 materialization PASS** from **external deployment apply/readback**, which remains outside this S2 contract unless a real Director push is requested.

## Acceptance
S2 is PASS for the executable plan's S2 contract because all required S2 artifacts exist, catalog registration is present, and the hot path remains intact. No claim is made that an external remote deployment was performed.

## Sheriff
- PLAN_UNTOUCHED: PASS
- ARTIFACTS_PRESENT: PASS
- CATALOG_APPEND_VERIFIED: PASS
- IDEMPOTENT_APPEND: PASS
- HOT_PATH_PRESERVED: PASS
- NO_SECRET_EXPOSED: PASS
- NO_FAKE_REMOTE_DEPLOYMENT: PASS
- NO_FAKE_PASS: PASS

## Remaining deployment-contract GAPs
- real external apply + remote readback
- populated deployment checksums/evidence
- full account/credential/permission preflight
- expected_head enforcement
- HF explicit revision + remote readback
- complete universal deployment engine/adversarial suite

These are not silently converted to PASS by S2.

## Decision
**S2 = PASS (materialization contract).**
