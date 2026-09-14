# CODA persistence transform — role disabled

The upstream evasion/OPSEC role is disabled in the transformed working tree.

Replacement responsibility:

`CHECK_POLICY → CHECK_RETRY_BOUNDS → RECORD_DECISION → FAIL_CLOSED_OR_HANDOFF`

The role is limited to workflow-policy compliance and observability. It must not conceal activity, bypass controls, evade detection, alter logs, or modify security tooling. Original upstream content remains recoverable from `_archives`.
