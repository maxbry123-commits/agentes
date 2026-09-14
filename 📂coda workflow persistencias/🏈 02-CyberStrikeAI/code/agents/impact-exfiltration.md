# CODA persistence transform — role disabled

This upstream offensive role is intentionally disabled in the transformed working tree.

It is replaced by a benign persistence responsibility:

`LOAD_STATE → REVIEW_PENDING_RESULTS → SAVE_CHECKPOINT → PREPARE_HANDOFF`

No data exfiltration, credential access, remote execution, payload generation, evasion, or offensive network action is permitted from this role. The original source remains reproducible from the component `_archives` and `DOWNLOAD_EXTRACT_MANIFEST.json`.
