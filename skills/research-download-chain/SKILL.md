---
name: research-download-chain
description: Repository-neutral deterministic download, archive, extraction, integrity, and forensic verification chain. Trigger on audited download/extraction tasks. Lock to forensic assets. Do not rewrite the packer.
metadata:
  type: workflow
  version: "1.7.1"
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
╠── <SOURCE_REPOSITORY_NAME_1>/
╠── <SOURCE_REPOSITORY_NAME_2>/
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
- `SKIP COMPLETE` if manifest status is COMPLETE and dest root has files. That is valid progress, not a new rebuild.

## Archive and extraction evidence
For every source repository, record a manifest entry containing at least:
- source repository identity and exact source repository name;
- destination branch (`main`);
- destination root (exactly the source repository name);
- expected ZIP part count;
- `files_extracted` count after extraction;
- extraction status.

## Clean-room rule
Do not delete COMPLETE zips, manifest lines, or extraction roots that already have files.
Do not wipe the queue to force a rebuild.
Clone/zip fail = SKIP + report + continue the queue. Do not raise-stop the job.

## Static preflight
Before dispatch only:
1. workflow YAML parses;
2. referenced script exists;
3. checkout `lfs: false`;
4. no operational LFS commands.
No curl to SKILL.md. No py_compile/AST/forensic scan as job steps.

## Retry model
Retry helpers execute the underlying operation directly. They must never call themselves directly. Bounded backoff then SKIP, not raise-stop the whole queue.

## Fresh-run rule
After changing YAML or execution code, create a NEW workflow run from the repaired commit. Do not use a historical re-run as proof that the repaired workflow was executed. Record run ID, attempt, commit SHA, and workflow SHA.

## Pre-job failure rule
If a workflow run becomes `failure` within seconds and its job has no executed steps, treat it as a **pre-job failure**, not as evidence that application code failed. Do not patch download code until the runner has actually executed the relevant step.

## Concurrency rule
One live run per workflow group. Zombie (`updated_at` frozen > 20 min) = cancel + one fresh dispatch. Do not stack duplicate runs.

## Final destination audit
Check dest `main` only: each COMPLETE slug has its own root named as the source repo. Missing slug = GAP list, not job kill.

## EvidenceGate
PASS when declared targets are COMPLETE in dest `main` or listed as SKIP with reason. A running job is not PASS. A green setup step is not PASS.

## LOOP
```text
inspect → first failure → edit lista|destino only → commit → dispatch → wait 20s → dest check → PASS?
NO: SKIP + next item; relanzar Gaps al final
YES: next target
```
Do not rewrite the packer. Edit list + destination only.
