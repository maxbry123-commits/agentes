# CHECKPOINT INVENTARIO E ÍNDICES V3

contract_id: YAIWES-INVENTORY-INDEXES-V3
run_timestamp: 2026-09-03T01:03:00Z
iteration: 7
phase: GAP_RECOVERY
verdict: RUNNING

repositories:
  total: 7
  pass: 4
  pass_repositories:
    - maxbry123-commits/nct-core
    - maxbry123-commits/router-universal-router-inteligente-
    - maxbry123-commits/Orquestador-Maxbry-
    - maxbry123-commits/frontend
  pending_repositories:
    - maxbry123-commits/agentes
    - maxbry123-commits/osquestador-auditor
    - maxbry123-commits/Agentes-motores-Wordflow-YAIWES

verified_repositories:
  - repository: maxbry123-commits/nct-core
    audit_verdict: PASS
    downloaded_components: 43
    complete: 43
    gaps: 0
    skipped_in_component_universe: 0
    insufficient_evidence: 0
    recovery_run: 33694193995
    artifact_digest: sha256:3acadba3a8b42c888d6bdb8debfce659db8629563dc8006e1914688583d999e2
  - repository: maxbry123-commits/router-universal-router-inteligente-
    audit_verdict: PASS
    downloaded_components: 56
    complete: 55
    duplicate_relocated: 1
    gaps: 0
    skipped_in_component_universe: 0
    insufficient_evidence: 0
    recovery_run: 33694032348
  - repository: maxbry123-commits/Orquestador-Maxbry-
    audit_verdict: PASS
    downloaded_components: 0
    excluded_unassociated_archives: 5
    gaps: 0
    insufficient_evidence: 0
    provenance_run: 33694667205
  - repository: maxbry123-commits/frontend
    audit_verdict: PASS
    downloaded_components: 25
    complete: 25
    gaps: 0
    skipped_in_component_universe: 0
    insufficient_evidence: 0
    recovery_run: 33694616279

agentes:
  base_run: 33699624351
  base_run_status: SUCCESS
  base_artifact_digest: sha256:62f9e965fb0be619a17b343a53bac97377c2bf74778cf8b180f67488728c7379
  manifest_rows: 335
  excluded_non_downloaded:
    - source: https://github.com/RUCAIBox/Math-Shepherd.git
      classification: EXCLUDED_NON_DOWNLOADED
      reason: SKIPPED clone row without SHA/parts; no downloaded version established
  unique_versions: 260
  unique_canonical: 212
  base_complete: 199
  base_duplicate_relocated: 47
  base_gaps: 11
  base_insufficient_evidence: 3
  evidence_run: 33700146789
  evidence_run_status: SUCCESS
  evidence_artifact_digest: sha256:a5700ce3aa452c04122ded425a22f83baf9e71cf099dbf43ab6379eed71854cb
  recovery_findings:
    - all 11 base GAP slugs have complete ZIP sequences in other verified download directories; final remapping remains blocked by active legacy run gate
    - HelpSteer2 Hugging Face row has URL, 40-char SHA and complete ZIP sequence; previous INSUFFICIENT_EVIDENCE came from github.com-only source predicate
    - Math-Shepherd Hugging Face downloaded row has URL, 40-char SHA and complete ZIP sequence; previous INSUFFICIENT_EVIDENCE came from github.com-only source predicate
    - legacy https://github.com/explodinggradients/ragas.git row has no source_commit and no parts; recovery shows Ragas ZIPs but cannot prove a version identity for that legacy source, so it is excluded from the versioned downloaded-component universe rather than invented as a component
  preserved_active_run: 33694014240
  preserved_active_run_status: in_progress
  provisional_verdict: BLOCKED_ACTIVE_JOB

osquestador_auditor:
  manifest: Download code osquestador auditor memoria/RESEARCH_DOWNLOAD_MANIFEST.jsonl
  manifest_rows: 127
  expected_downloaded_universe: 126
  excluded_non_downloaded:
    - slug: wisemapping
      classification: EXCLUDED_NON_DOWNLOADED
      reason: SKIPPED without SHA/parts
  fast_run: 33699559368
  fast_run_conclusion: failure
  fast_run_failure_classification: TEMPLATE_TYPEERROR_NOT_DATA
  scoped_recovery_run: 33699966103
  scoped_recovery_status: SUCCESS
  scoped_recovery_artifact_digest: sha256:988a2c53b973654fb4a186b3c06dbbf6bdee5f5ff19425463ae9d74ff8ad089b
  scoped_recovery_result:
    unique_versions: 126
    complete: 40
    gaps: 86
    insufficient_evidence: 0
    excluded_non_downloaded: 1
  action_taken:
    workflow: .github/workflows/inventory-forensic-v3-recovery-global-zipmap-auditor.yml
    commit: 374282342a869b5f8bcab2c3e83af5b4a02fee6b
    run: 33702002739
    purpose: isolated read-only global ZIP/destination mapping for the 126-row downloaded universe
    status: in_progress
  preserved_original_run: 33693813584
  preserved_original_run_status: in_progress
  provisional_verdict: BLOCKED_ACTIVE_JOB_AND_86_SCOPED_GAPS

motores:
  repository: maxbry123-commits/Agentes-motores-Wordflow-YAIWES
  localgit_run: 33698158009
  localgit_status: SUCCESS
  localgit_result:
    discovered: 198
    complete: 0
    insufficient_evidence: 198
    root_cause: destination mapping only
  zip_destination_recovery_run: 33699206723
  zip_destination_recovery_status: in_progress
  provisional_verdict: BLOCKED_ACTIVE_JOB

active_inventory_jobs:
  count_known: 4
  runs:
    - repository: maxbry123-commits/agentes
      run: 33694014240
      status: in_progress
    - repository: maxbry123-commits/osquestador-auditor
      run: 33693813584
      status: in_progress
    - repository: maxbry123-commits/osquestador-auditor
      run: 33702002739
      status: in_progress
    - repository: maxbry123-commits/Agentes-motores-Wordflow-YAIWES
      run: 33699206723
      status: in_progress

stage_2_indexes:
  status: BLOCKED
  global_index_url: null
  local_index_urls: []
  audit_report_url: null
  reason: requires active_jobs=0 and 7/7 PASS with gaps=0 skipped=0 insufficient_evidence=0 inside downloaded universe

closure_gates:
  active_jobs: FAIL
  repositories_7_of_7_pass: FAIL
  gaps_zero: FAIL
  skipped_zero_inside_downloaded_universe: PASS_FOR_VERIFIED_SCOPE
  insufficient_evidence_zero: FAIL_PENDING_REMAP
  broken_links_zero: NOT_RUN
  four_pass_audit: NOT_RUN
  verified_closed: false

## Iteration 7 — 2026-09-03T01:03:00Z

- Preserved PASS state at 4/7.
- Downloaded and read agentes base artifact from run 33699624351 and GAP evidence artifact from run 33700146789.
- Confirmed agentes 11 GAPs have matching complete ZIP sequences elsewhere in the evidence trees; confirmed Hugging Face HelpSteer2 and Math-Shepherd false INSUFFICIENT classifications were caused by a github.com-only source predicate.
- Legacy explodinggradients/ragas row remains without SHA/parts. ZIP existence alone does not establish a version identity, so no component/version is invented from that row.
- Preserved agentes run 33694014240 because it remains in_progress.
- Downloaded and read auditor scoped artifact from run 33699966103: 126 downloaded versions, 40 COMPLETE, 86 GAP, 0 INSUFFICIENT, plus 1 excluded wisemapping SKIPPED row.
- Created isolated read-only auditor global ZIP/destination recovery workflow; commit 374282342a869b5f8bcab2c3e83af5b4a02fee6b; run 33702002739 is in_progress.
- Preserved auditor original run 33693813584 because it remains in_progress.
- Motores recovery run 33699206723 remains in_progress.
- No indexes generated and no repository newly promoted to PASS because active inventory jobs remain.

## Iteration 6 — supplied latest state

- PASS confirmed 4/7: nct-core, router-universal-router-inteligente-, Orquestador-Maxbry-, frontend.
- agentes run 33699624351 SUCCESS; 335 manifest rows; 1 GitHub Math-Shepherd SKIPPED excluded; 260 URL+SHA versions; 212 canonical URLs; 199 COMPLETE; 47 DUPLICATE_RELOCATED; 11 GAP; 3 INSUFFICIENT.
- Cross-check located complete ZIP sequences for all 11 agentes GAPs; Hugging Face HelpSteer2 and Math-Shepherd have valid URL+40-char SHA+ZIP and were false INSUFFICIENT under a github.com-only predicate.
- auditor manifest has 127 rows = 126 downloaded COMPLETE-intent rows + 1 wisemapping SKIPPED excluded; fast run 33699559368 failed from template TypeError, not data.
- motores localgit run 33698158009 SUCCESS but 198 INSUFFICIENT from destination mapping; ZIP/destination recovery 33699206723 active.
