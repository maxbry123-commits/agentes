# CODA persistence transform — role disabled

The upstream lateral-movement role is disabled in this transformed working tree.

Replacement responsibility:

`READ_HANDOFF → VALIDATE_DEPENDENCIES → ADVANCE_WORKFLOW_STATE → SAVE_CHECKPOINT`

This role may move **task state only** between CODA workflow links. It may not move between hosts, accounts, networks, or security boundaries, and may not execute remote commands or credentials. Original upstream material remains recoverable from `_archives`.
