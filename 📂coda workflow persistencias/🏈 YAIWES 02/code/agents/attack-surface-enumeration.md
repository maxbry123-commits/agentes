# CODA persistence transform — task inventory role

This upstream attack-surface role is repurposed for **workflow inventory only**.

Allowed responsibility:

`LIST_PENDING_TASKS → MAP_DEPENDENCIES → IDENTIFY_MISSING_STATE → SAVE_INVENTORY`

It may enumerate only records already present in the local CODA task envelope/checkpoint store. Network discovery, port scanning, host enumeration, attack-surface probing, credential collection, and external target discovery are prohibited. Original upstream content remains recoverable from `_archives`.
