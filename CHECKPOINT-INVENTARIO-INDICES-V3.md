# CHECKPOINT INVENTARIO E ÍNDICES V3

contract_id: YAIWES-INVENTORY-INDEXES-V3
run_timestamp: 2026-09-02T23:12:00Z
iteration: 1
phase: GAP_RECOVERY

repositories:
  total: 7
  audited: 2
  pass: 0
  gaps: 2

components:
  discovered: 395
  unique: 252
  complete: 0
  relocated: 0
  skipped: 0
  gaps: 0
  insufficient_evidence: 395

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
    run_url: https://github.com/maxbry123-commits/agentes/actions/runs/33693716423
    run_id: 33693716423
    status: completed
    conclusion: success
    audit_verdict: GAP
    artifact: inventory-forensic-v3-agentes
    artifact_digest: sha256:19e3fb35975d17f2bb298f14a066f8cdbfb5ee79375808e9c30785f9885e682a
  - repository: maxbry123-commits/nct-core
    run_url: https://github.com/maxbry123-commits/nct-core/actions/runs/33693794321
    run_id: 33693794321
    status: in_progress
    conclusion: null
  - repository: maxbry123-commits/router-universal-router-inteligente-
    run_url: https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/runs/33693726004
    run_id: 33693726004
    status: completed
    conclusion: success
    audit_verdict: GAP
    artifact: inventory-forensic-v3-router-universal-router-inteligente-
    artifact_digest: sha256:0920b6f61913a6e7616930f2b692479b16393c76b8c55718671013e0ca4e8000
  - repository: maxbry123-commits/Orquestador-Maxbry-
    run_url: https://github.com/maxbry123-commits/Orquestador-Maxbry-/actions/runs/33693802223
    run_id: 33693802223
    status: in_progress
    conclusion: null
  - repository: maxbry123-commits/osquestador-auditor
    run_url: https://github.com/maxbry123-commits/osquestador-auditor/actions/runs/33693813584
    run_id: 33693813584
    status: in_progress
    conclusion: null
  - repository: maxbry123-commits/Agentes-motores-Wordflow-YAIWES
    run_url: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/actions/runs/33693743835
    run_id: 33693743835
    status: in_progress
    conclusion: null
  - repository: maxbry123-commits/frontend
    run_url: https://github.com/maxbry123-commits/frontend/actions/runs/33693820656
    run_id: 33693820656
    status: in_progress
    conclusion: null

pending_tasks:
  - id: GAP-AGENTES-ZIPMAP-001
    repository: maxbry123-commits/agentes
    gap: 338 manifest entries have valid source/SHA but destination and ZIP evidence were not mapped by the first V3 parser
    recovery: create isolated recovery workflow that maps manifest slug + parts to real ZIP/part paths and verifies exact counts/sizes
  - id: GAP-ROUTER-ZIPMAP-001
    repository: maxbry123-commits/router-universal-router-inteligente-
    gap: 57 manifest entries have valid source/SHA but destination and ZIP evidence were not mapped by the first V3 parser
    recovery: create isolated recovery workflow that maps manifest slug + parts to real ZIP/part paths and verifies exact counts/sizes
  - id: WAIT-NCT-001
    repository: maxbry123-commits/nct-core
    gap: workflow still active
    recovery: preserve run and verify artifact after completion
  - id: WAIT-ORQUESTADOR-001
    repository: maxbry123-commits/Orquestador-Maxbry-
    gap: workflow still active
    recovery: preserve run and verify artifact after completion
  - id: WAIT-AUDITOR-001
    repository: maxbry123-commits/osquestador-auditor
    gap: workflow still active
    recovery: preserve run and verify artifact after completion
  - id: WAIT-MOTORES-001
    repository: maxbry123-commits/Agentes-motores-Wordflow-YAIWES
    gap: workflow still active
    recovery: preserve run and verify artifact after completion
  - id: WAIT-FRONTEND-001
    repository: maxbry123-commits/frontend
    gap: workflow still active
    recovery: preserve run and verify artifact after completion

artifacts:
  global_index_url: null
  local_index_urls: []
  audit_report_url: null

verdict: RUNNING

## Evidence snapshot

- agentes: 11,516 files; 1,446 directories; 15 manifest-like JSON/JSONL files; 1,021 ZIP/part files; 338 manifest entries; 338 INSUFFICIENT_EVIDENCE pending ZIP/destination recovery.
- router: 405 files; 48 directories; 1 download manifest; 324 ZIP/part files; 57 manifest entries; 57 INSUFFICIENT_EVIDENCE pending ZIP/destination recovery.
- No active job is counted as PASS.
- Stage 2 indexes remain blocked until all seven audit artifacts are verified.
