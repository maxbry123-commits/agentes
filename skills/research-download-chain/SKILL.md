---
name: research-download-chain
description: Repository-neutral deterministic download, archive, extraction, integrity, and forensic verification chain. Trigger on audited download/extraction tasks. Lock to forensic assets. Do not rewrite the packer.
metadata:
  type: workflow
  version: "1.6.0"
---

# Research Download Chain — generic forensic model

## Scope
Reusable and repository-neutral. Never embed a concrete target repository, organization, project codename, historical run/job ID, concrete repository catalog, or destination-specific URL. Target values belong only in the task contract, manifest, or LOCK assets.

## LOCK / contract
Read the active Contract 2, this skill, the packer LOCK and YAML LOCK before execution. Verify the LOCK blobs before changing execution code. Never rewrite a LOCK packer to repair a runtime failure.

## Absolute no-LFS policy
- Never execute, install, configure, uninstall, track, migrate, or invoke LFS.
- Checkout must use `lfs: false`.
- Detection signatures such as `git-lfs.github.com/spec/` and `filter=lfs` are allowed only as forensic indicators.
- Generated output containing LFS pointer/config material is FAIL CLOSED; never sanitize it into PASS.

## Source-to-destination identity and layout
- The destination branch is always `main` for the extraction target defined by the active contract.
- Every source repository is extracted into its own root directly under that destination `main`.
- The destination root name MUST be exactly the source repository name (`repository.name`), with no renamed, translated, or substituted canonical name.
- One source repository MUST map to exactly one destination root. Different repositories must never share or mix an extraction root.
- The active manifest must provide the source repository identity/name used for this mapping; the Skill itself remains repository-neutral.

Required generic layout:
```text
main/
├── <SOURCE_REPOSITORY_NAME_1>/
├── <SOURCE_REPOSITORY_NAME_2>/
└── <SOURCE_REPOSITORY_NAME_N>/
```

## Download and archive construction
- Use deterministic streaming/copy chunks of `8 MiB` unless the active contract explicitly specifies another value.
- Large repository payloads must be staged in a temporary clean root before archive creation.
- Create ZIP archives from the staged repository contents, then split oversized archives into sequential numbered parts when required by the active size limit.
- Part numbering MUST be contiguous and deterministic, starting at `0001`.
- Each part must remain within the active maximum archive-size bound.
- Record the expected part count in the manifest.
- Commits MAY be made by deterministic batches; when batching is used, preserve the manifest and source-to-destination identity for every component.
- Never treat an existing archive or extraction as evidence of a new rebuild.

## Clean-room rule
Delete prior generated archives, temporary sources, manifests that are explicitly rebuild-owned, and every extraction root covered by the active manifest before a forensic rebuild. Existing non-empty output is never evidence of a new extraction. `SKIP EXISTING` cannot be a PASS condition.

## Static preflight
Before dispatch:
1. parse YAML;
2. verify every workflow-referenced script exists;
3. run `py_compile` with `PYTHONDONTWRITEBYTECODE=1`;
4. AST-check retry helpers for direct self-recursion;
5. verify `lfs: false` and absence of operational LFS commands/env;
6. verify output roots are cleaned;
7. validate manifest schema/cardinality expectations;
8. verify scanners do not self-trigger on their own detection signatures;
9. ignore/delete generated `__pycache__` and `.pyc` from forensic scans;
10. validate archive and extraction paths;
11. validate every manifest repository has exactly one destination root named exactly as the source repository;
12. validate the destination branch is `main`.

## Retry model
Retry helpers execute the underlying operation directly. They must never call themselves directly. Required flow: clean temporary root → operation → return on success → bounded backoff on expected external failure → raise last error. Never retry an integrity assertion into PASS.

## Fresh-run rule
After changing YAML or execution code, create a NEW workflow run from the repaired commit. Do not use a historical re-run as proof that the repaired workflow was executed. Record run ID, attempt, commit SHA, and workflow SHA.

## Pre-job failure rule
If a workflow run becomes `failure` within seconds and its job has no executed steps, treat it as a **pre-job failure**, not as evidence that application code failed. Inspect check-run annotations / workflow validation metadata first. Do not patch download code until the runner has actually executed the relevant step. If annotations/logs are inaccessible, record the limitation explicitly and do not declare PASS.

## Concurrency rule
A concurrency group can leave a corrected run pending behind another run. Record active/pending runs before concluding that a new run has not started. Do not create uncontrolled duplicate runs.

## Final destination audit
The final audit is intentionally limited to the physical destination state:
- verify every expected ZIP part exists at the required destination location;
- verify the complete expected ZIP set is present according to the active manifest;
- verify every expected repository has been extracted;
- verify every extraction exists under its own repository root on destination branch `main`;
- verify the extraction root name is exactly the source repository name;
- verify repository extraction roots are not mixed or shared.

Do not add upstream tree reconstruction, `missing/extra/content_mismatch` comparison, `workflow_run` chaining, or other upstream-content forensic auditing to this final destination audit.

## EvidenceGate
PASS requires all:
- expected manifest cardinality and contiguous IDs;
- every expected ZIP part exists at the destination;
- exact archive-part count equals manifest `parts`;
- archive size limits respected;
- CRC and `unzip -tq` PASS;
- clean extraction roots exist and contain files;
- every repository has exactly one destination root on `main`;
- destination root name exactly equals source repository name;
- no repository extraction is mixed with another repository;
- no LFS material in generated outputs.

A green setup step or green workflow without the destination audit is not PASS.

## X-RAY cross-verification
A — source code behavior; B — workflow/script wiring; C — repaired commit executed; D — runtime steps executed; E — manifest/archive/extraction/destination state agree. PASS only if A+B+C+D+E all pass.

## Failure Ledger
Before every retry preserve:
```yaml
failure:
  target: "<OWNER>/<REPOSITORY>"
  workflow: "<WORKFLOW_FILE>"
  run_id: "<RUN_ID>"
  run_attempt: "<ATTEMPT>"
  commit_sha: "<SHA>"
  failed_step: "<STEP>"
  root_cause: "<ROOT_CAUSE>"
  repair_commit: "<SHA>"
  next_run_id: "<RUN_ID>"
  status: "OPEN|RESOLVED"
```
If logs are unavailable, retain the run/check IDs and exact API limitation; never fill missing evidence with assumptions.

## Archive verification
For every archive: existence → expected part count → size bound → CRC → `unzip -tq` → safe paths → clean extraction. Any failure is FAIL CLOSED.

## Repository-neutrality
Do not add concrete repository names, project names, historical run IDs, historical job IDs, destination URLs, or copied catalogs to this skill. Use placeholders and active manifests.

## LOOP
```text
inspect → evidence → first failure → root cause → patch → static validation → commit → fresh run → wait → destination audit → X-RAY → EvidenceGate → PASS?
NO: return to first failure
YES: next target
```
Terminate only when every target declared by Contract 2 has EvidenceGate PASS.
