# CHECKPOINT INVENTARIO E ÍNDICES V3

contract_id: YAIWES-INVENTORY-INDEXES-V3
run_timestamp: 2026-09-03T04:07:00Z
iteration: 8
phase: GAP_RECOVERY
verdict: RUNNING

repositories:
  total: 7
  pass: 6
  pass_repositories:
    - maxbry123-commits/nct-core
    - maxbry123-commits/router-universal-router-inteligente-
    - maxbry123-commits/Orquestador-Maxbry-
    - maxbry123-commits/frontend
    - maxbry123-commits/agentes
    - maxbry123-commits/Agentes-motores-Wordflow-YAIWES
  pending_repositories:
    - maxbry123-commits/osquestador-auditor

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
  - repository: maxbry123-commits/agentes
    audit_verdict: PASS
    base_run: 33699624351
    evidence_run: 33700146789
    evidence_artifact_digest: sha256:a5700ce3aa452c04122ded425a22f83baf9e71cf099dbf43ab6379eed71854cb
    manifest_rows: 335
    unique_versions: 260
    unique_canonical: 212
    gaps: 0
    insufficient_evidence: 0
    excluded_non_downloaded:
      - https://github.com/RUCAIBox/Math-Shepherd.git
      - https://github.com/explodinggradients/ragas.git
    notes:
      - 11 previous location GAPs have complete ZIP sequences in other verified download directories
      - HelpSteer2 and downloaded Hugging Face Math-Shepherd have URL + SHA40 + complete ZIP evidence
      - legacy explodinggradients/ragas row has no SHA/parts and no attributable version identity; no component invented
      - legacy run 33694014240 ended cancelled and was not reactivated
  - repository: maxbry123-commits/Agentes-motores-Wordflow-YAIWES
    audit_verdict: PASS
    base_localgit_run: 33698158009
    cancelled_zipmap_run: 33699206723
    fastpath_run: 33713657258
    fastpath_artifact_digest: sha256:b7c030269f08d3e907d8f803a76db763a40d0647a0853539d7c9d16c58c0f54a
    manifest_rows: 198
    unique_versions: 198
    complete: 198
    duplicate_relocated: 0
    gaps: 0
    insufficient_evidence: 0
    excluded_non_downloaded: 0

osquestador_auditor:
  manifest: Download code osquestador auditor memoria/RESEARCH_DOWNLOAD_MANIFEST.jsonl
  manifest_rows: 127
  expected_downloaded_universe: 126
  excluded_non_downloaded:
    - slug: wisemapping
      classification: EXCLUDED_NON_DOWNLOADED
      reason: SKIPPED without SHA/parts
  scoped_recovery_run: 33699966103
  scoped_recovery_status: SUCCESS
  scoped_recovery_artifact_digest: sha256:988a2c53b973654fb4a186b3c06dbbf6bdee5f5ff19425463ae9d74ff8ad089b
  cancelled_global_zipmap_run: 33702002739
  fastpath_run: 33713686705
  fastpath_status: SUCCESS
  fastpath_artifact_digest: sha256:25d51aeda8c7a88c3931e4a2502a11a3697650157380ad9ad3f81426e451a99f
  fastpath_result:
    unique_versions: 126
    complete: 120
    duplicate_relocated: 2
    gaps: 4
    insufficient_evidence: 0
    excluded_non_downloaded: 1
  isolated_gap4_evidence_run: 33713753728
  isolated_gap4_evidence_status: SUCCESS
  isolated_gap4_artifact_digest: sha256:966a87563e262766ab45b891c2da40d1374d2e9d513e0103f3806a55278646f5
  remaining_gaps:
    - slug: ladybug
      source: https://github.com/LadybugDB/ladybug.git
      source_commit: dd9ca6cc70f8e57add26d132cc0d386a87b326c9
      parts: 2
    - slug: kuzu
      source: https://github.com/kuzudb/kuzu.git
      source_commit: 89f0263cc7a1fd9c396d2c4953747a013556a7f9
      parts: 12
    - slug: HyperMem
      source: https://github.com/EverMind-AI/HyperMem.git
      source_commit: 15c700908f3ec64d6931f253695e42c679a4c958
      parts: 1
    - slug: airflow
      source: https://github.com/apache/airflow.git
      source_commit: b0721979b92e4cddc13afe294b5a034ec90d0e49
      parts: 9
  gap4_findings:
    - no ZIP candidate path for any of the four slugs exists anywhere in osquestador-auditor main tree
    - initial code-search cross-check across the seven contract repositories found no textual match for ladybug, kuzu, HyperMem or airflow
  provisional_verdict: GAP_4_PENDING_CROSS_REPO_LOCATION_PROOF_OR_REPAIR

active_inventory_jobs:
  count_known: 0

stage_2_indexes:
  status: BLOCKED
  global_index_url: null
  local_index_urls: []
  audit_report_url: null
  reason: requires 7/7 PASS with gaps=0 skipped=0 insufficient_evidence=0 inside downloaded universe

closure_gates:
  active_jobs: PASS
  repositories_7_of_7_pass: FAIL_6_OF_7
  gaps_zero: FAIL_4_AUDITOR
  skipped_zero_inside_downloaded_universe: PASS
  insufficient_evidence_zero: PASS
  broken_links_zero: NOT_RUN
  four_pass_audit: NOT_RUN
  verified_closed: false

## Iteration 8 — 2026-09-03T04:07:00Z

- Legacy agentes run 33694014240 and auditor original 33693813584 ended cancelled; neither was reactivated.
- Auditor global ZIP-map run 33702002739 ended cancelled during the expensive tree scan.
- Motores ZIP-map run 33699206723 ended cancelled during the expensive tree scan.
- Created isolated fast-path motores workflow; commit 2bd44105f9addea6fcd477f45868847c727762fd; run 33713657258 SUCCESS.
- Downloaded/read motores artifact sha256:b7c030269f08d3e907d8f803a76db763a40d0647a0853539d7c9d16c58c0f54a: 198 unique versions, 198 COMPLETE, 0 GAP, 0 INSUFFICIENT. Motores promoted PASS.
- Created isolated fast-path auditor workflow; commit a8c2178af860eddfb9aa241e780b622cfddc26de; run 33713686705 SUCCESS.
- Downloaded/read auditor fast-path artifact sha256:25d51aeda8c7a88c3931e4a2502a11a3697650157380ad9ad3f81426e451a99f: 126 unique versions, 120 COMPLETE, 2 DUPLICATE_RELOCATED, 4 GAP, 0 INSUFFICIENT, 1 wisemapping excluded non-downloaded.
- Created isolated four-GAP candidate evidence workflow; commit 492a6c07b9e721dcf4214ff2bf13c58d94d0a445; run 33713753728 SUCCESS.
- Downloaded/read gap4 artifact sha256:966a87563e262766ab45b891c2da40d1374d2e9d513e0103f3806a55278646f5: no ZIP candidates for ladybug, kuzu, HyperMem or airflow in auditor main tree.
- Agentes promoted PASS after its active-run gate disappeared and its previously read evidence resolved the 11 location GAPs and false Hugging Face INSUFFICIENT classifications without inventing the legacy ragas row.
- PASS state advanced from 4/7 to 6/7.
- Index stage remains blocked only by the four auditor location GAPs.

## Iteration 7 — 2026-09-03T01:03:00Z

- PASS preserved at 4/7 while four inventory jobs remained active.
- Agentes base/evidence artifacts read; 11 GAP ZIP sequences located; Hugging Face predicate defect identified; legacy ragas left unattributed.
- Auditor scoped artifact read: 126 downloaded versions, 40 COMPLETE, 86 GAP, 0 INSUFFICIENT, plus one excluded wisemapping row.
- Global auditor recovery and motores recovery were launched and preserved without reruns.

## Iteration 6 — supplied latest state

- PASS confirmed 4/7: nct-core, router-universal-router-inteligente-, Orquestador-Maxbry-, frontend.
- Agentes base run 33699624351 SUCCESS with 335 manifest rows; 260 URL+SHA versions; 11 GAP and 3 INSUFFICIENT before evidence recovery.
- Auditor manifest: 127 rows = 126 downloaded-intent + 1 wisemapping SKIPPED excluded.
- Motores localgit run 33698158009 SUCCESS but destination mapping left 198 INSUFFICIENT before recovery.
