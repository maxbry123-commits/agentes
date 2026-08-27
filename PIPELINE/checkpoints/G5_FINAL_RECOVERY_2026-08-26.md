# CHECKPOINT — G5 FINAL RECOVERY / DERIVED P01→P12

## 1. Restauración
- Repository: `maxbry123-commits/agentes`
- Branch: `main`
- Latest G5 implementation commit: `f1a1f332fb929ed4642599f31dbad7ddb772814b`
- Canonical runner: `extensions/wordflow/engine/code_path_runner.py`
- Canonical runner blob baseline: `f1c3e519e317d06352945b230ad4a03b02422ad5`

## 2. Forensic finding
The repository did not contain a verified historical p01_* … p12_* source set. This is recorded in `Refactoria/G5/source/CANONICAL_SOURCE.md`.

## 3. Recovery decision
The Director explicitly authorized creating the missing cable when the original source could not be recovered. The implementation is therefore a **derived modular cable**, not a claim that historical p01–p12 source was recovered.

## 4. Implemented cable
`p01 → p02 → p03 → p04 → p05 → p06 → p07 → p08 → p09 → p10 → p11 → p12`

Nodes:
- p01_context
- p02_pre_gate
- p03_quality_bar
- p04_goal_lock
- p05_policy_snapshot
- p06_cognitive
- p07_path_gateway
- p08_evidence
- p09_quality_dag
- p10_core_fc
- p11_forensic
- p12_closure

## 5. Anti-regression
- Existing `code_path_runner.py` was not modified.
- Existing goal_lock/cognitive_loop/evidence_packet implementations are reused.
- p12 invokes the canonical `run_code_path`; it does not replace it.
- Hot-path hash is checked by `.github/workflows/verify-g5-wordflow.yml`.

## 6. Tests
`Refactoria/G5/new/test_p01_p12.py` verifies deterministic p01–p12 ordering, fail-closed empty input, and canonical-runner delegation through a controlled test double.

## 7. GitHub verification
Workflow: `.github/workflows/verify-g5-wordflow.yml`

The workflow performs:
1. protected hot-path hash verification;
2. p01–p12 pytest suite;
3. twelve-node file verification;
4. real evidence artifact generation.

A PASS is recorded only by the GitHub Actions execution. This checkpoint does not fabricate a CI result before that execution exists.

## 8. Recovery procedure
If G5 fails:
1. restore/inspect `Refactoria/G5/source/CANONICAL_SOURCE.md`;
2. compare `pipeline_p01_p12.py` with the canonical runner SHA;
3. run `pytest -q Refactoria/G5/new/test_p01_p12.py`;
4. verify the twelve node files;
5. verify the protected runner hash;
6. rerun GitHub Actions;
7. update this checkpoint only from real evidence.
