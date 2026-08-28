# Wordflow X-Ray pipeline

The extraction and audit stages are intentionally separate.

1. `download-extract.yml` validates and extracts all ZIP parts, then uploads `wordflow-extraction-<run_id>`.
2. `audit-extraction.yml` is triggered by `workflow_run` only after `Download Extract` completes successfully and audits that artifact.

Do not use a shared concurrency group between these two workflows. GitHub documents `workflow_run` as the supported mechanism for chaining workflows after completion, and artifacts as the mechanism for sharing data between workflow runs/jobs.
