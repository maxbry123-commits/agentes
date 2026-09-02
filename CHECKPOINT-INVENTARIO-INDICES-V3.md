# CHECKPOINT INVENTARIO E ÍNDICES V3

contract_id: YAIWES-INVENTORY-INDEXES-V3
run_timestamp: 2026-09-02T23:16:00Z
iteration: 2
phase: GAP_RECOVERY

repositories:
  total: 7
  audited: 4
  pass: 0
  gaps: 4

components:
  discovered: 438
  unique: 291
  complete: 0
  relocated: 0
  skipped: 0
  gaps: 0
  insufficient_evidence: 438

repository_resolution:
  - requested: maxbry123-commits/osquestador
    result: 404
    resolved_repository: maxbry123-commits/Orquestador-Maxbry-
    evidence: account repository search for orquestador; public repo on owner; main exists
  - requested: maxbry123-commits/osquestador-auditor-memoria
    result: 404
    resolved_repository: maxbry123-commits/osquestador-auditor
    evidence: account repository search for osquestador auditor / auditor memoria; public repo on owner; root contains downloaded components and folders named osquestador auditor memoria

active_workflows:
  - repository: maxbry123-commits/agentes
    run_url: https://github.com/maxbry123-commits/agentes/actions/runs/33694014240
    run_id: 33694014240
    status: in_progress
    conclusion: null
    purpose: GAP-AGENTES-ZIPMAP-001
  - repository: maxbry123-commits/nct-core
    run_url: https://github.com/maxbry123-commits/nct-core/actions/runs/33694193995
    run_id: 33694193995
    status: in_progress
    conclusion: null
    purpose: GAP-NCT-ZIPMAP-001
  - repository: maxbry123-commits/router-universal-router-inteligente-
    run_url: https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/runs/33694032348
    run_id: 33694032348
    status: in_progress
    conclusion: null
    purpose: GAP-ROUTER-ZIPMAP-001
  - repository: maxbry123-commits/router-universal-router-inteligente-
    run_url: https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/runs/33694156546
    run_id: 33694156546
    status: in_progress
    conclusion: null
    purpose: additional isolated router ZIP-map recovery observed; do not cancel or duplicate
  - repository: maxbry123-commits/Orquestador-Maxbry-
    run_url: https://github.com/maxbry123-commits/Orquestador-Maxbry-/actions/runs/33694248287
    run_id: 33694248287
    status: in_progress
    conclusion: null
    purpose: GAP-ORQUESTADOR-PROVENANCE-001
  - repository: maxbry123-commits/osquestador-auditor
    run_url: https://github.com/maxbry123-commits/osquestador-auditor/actions/runs/33693813584
    run_id: 33693813584
    status: in_progress
    conclusion: null
    purpose: initial forensic inventory
  - repository: maxbry123-commits/Agentes-motores-Wordflow-YAIWES
    run_url: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/actions/runs/33693743835
    run_id: 33693743835
    status: in_progress
    conclusion: null
    purpose: initial forensic inventory
  - repository: maxbry123-commits/frontend
    run_url: https://github.com/maxbry123-commits/frontend/actions/runs/33693820656
    run_id: 33693820656
    status: in_progress
    conclusion: null
    purpose: initial forensic inventory

completed_initial_runs:
  - repository: maxbry123-commits/agentes
    run_url: https://github.com/maxbry123-commits/agentes/actions/runs/33693716423
    run_id: 33693716423
    conclusion: success
    audit_verdict: GAP
    artifact_digest: sha256:19e3fb35975d17f2bb298f14a066f8cdbfb5ee79375808e9c30785f9885e682a
  - repository: maxbry123-commits/router-universal-router-inteligente-
    run_url: https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/runs/33693726004
    run_id: 33693726004
    conclusion: success
    audit_verdict: GAP
    artifact_digest: sha256:0920b6f61913a6e7616930f2b692479b16393c76b8c55718671013e0ca4e8000
  - repository: maxbry123-commits/nct-core
    run_url: https://github.com/maxbry123-commits/nct-core/actions/runs/33693794321
    run_id: 33693794321
    conclusion: success
    audit_verdict: GAP
    artifact_digest: sha256:ce1fa5f47eea24543f0558d750c853badd9a0f36fa6762919cdd82d0f026eb3d
  - repository: maxbry123-commits/Orquestador-Maxbry-
    run_url: https://github.com/maxbry123-commits/Orquestador-Maxbry-/actions/runs/33693802223
    run_id: 33693802223
    conclusion: success
    audit_verdict: GAP
    artifact_digest: sha256:47d4938f9bafa756c4bdaa7203043963995699a95b52782bf56aea7b37a61a94

pending_tasks:
  - id: GAP-AGENTES-ZIPMAP-001
    repository: maxbry123-commits/agentes
    gap: 338 first-pass entries had source/SHA but no verified destination/ZIP mapping
    recovery: verify RESEARCH_DOWNLOAD_MANIFEST slug + parts against real ZIP paths; classify COMPLETE/RELOCATED/DUPLICATE_RELOCATED/GAP/SKIPPED
  - id: GAP-ROUTER-ZIPMAP-001
    repository: maxbry123-commits/router-universal-router-inteligente-
    gap: 57 first-pass entries had source/SHA but no verified destination/ZIP mapping
    recovery: ZIP-map workflows active
  - id: GAP-NCT-ZIPMAP-001
    repository: maxbry123-commits/nct-core
    gap: 43 first-pass entries had source/SHA but no verified destination/ZIP mapping
    recovery: ZIP-map workflow active
  - id: GAP-ORQUESTADOR-PROVENANCE-001
    repository: maxbry123-commits/Orquestador-Maxbry-
    gap: 0 download manifests; 5 ZIP archives present without source_url/source_commit proof
    recovery: provenance workflow scans Git history and textual references; do not infer component status from filename
  - id: WAIT-AUDITOR-001
    repository: maxbry123-commits/osquestador-auditor
    gap: initial workflow active
    recovery: preserve run and verify artifact after completion
  - id: WAIT-MOTORES-001
    repository: maxbry123-commits/Agentes-motores-Wordflow-YAIWES
    gap: initial workflow active
    recovery: preserve run and verify artifact after completion
  - id: WAIT-FRONTEND-001
    repository: maxbry123-commits/frontend
    gap: initial workflow active
    recovery: preserve run and verify artifact after completion

artifacts:
  global_index_url: null
  local_index_urls: []
  audit_report_url: null

verdict: RUNNING

## Current evidence snapshot

- agentes: 11,516 files; 1,446 directories; 1,021 ZIP/part files; 338 first-pass component rows; ZIP-map recovery active.
- router: 405 files; 48 directories; 324 ZIP/part files; 57 first-pass component rows; ZIP-map recovery active.
- nct-core: 359 files; 44 directories; 265 ZIP/part files; 43 first-pass component rows; ZIP-map recovery active.
- Orquestador-Maxbry-: 352 files; 55 directories; 5 ZIP archives; no download manifest; provenance recovery active.
- Active jobs are not PASS.
- Stage 2 indexes remain blocked.

## Iteration history

### Iteration 1 — 2026-09-02T23:12:00Z

- phase: GAP_RECOVERY
- repositories audited: 2/7
- verified PASS: 0
- first-pass rows: 395
- unique canonical IDs observed: 252
- confirmed gaps: agentes ZIP-map; router ZIP-map
- active initial runs: nct-core, Orquestador-Maxbry-, osquestador-auditor, Agentes-motores-Wordflow-YAIWES, frontend
- checkpoint commit before this update: da5755fd2def32ac2a82a8e80caf36d3116d11cd
