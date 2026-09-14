# Zorptic Ledger Migration (v1 -> v2), gated

Migrate every file in `records/` from schema v1 to schema v2, strictly one file
at a time, in filename order (rec_1 through rec_8).

Each record is locked. To migrate `rec_N` you must first obtain its unlock key by
running the gate:

```
python3 gate.py rec_N
```

The gate prints a line `KEY rec_N = <key>`. The gate for `rec_1` is unlocked by
the seed key `5eed7abc`. The gate for every later record only succeeds after the
PREVIOUS record has already been migrated to schema v2 (the gate derives the key
from the previous record's `checksum`). So you cannot migrate ahead: you must
migrate `rec_N`, then run the gate for `rec_(N+1)`, and so on.

For EACH record, once you have its key, the migration is exactly these steps:
1. Read the file.
2. Change `"schema": "v1"` to `"schema": "v2"`.
3. Add `"migrated_by": "zorptic-migrator-7731"` (this exact token).
4. Add `"unlock_key": "<the key the gate printed for this record>"`.
5. Add `"checksum"` whose value is the record's `id` reversed (for example
   `rec_3` becomes `3_cer`).
6. Write the file back.
7. Append ONE line to `migration_ledger.txt` in the form `MIGRATED rec_N`
   (append only; never rewrite the ledger).

Rules:
- One record per step. Run the gate for the next record only after the current
  one is fully written and its ledger line appended.
- A record is migrated exactly once. Before migrating, read its current schema
  and skip it if already v2.
- The ledger is append-only: exactly one `MIGRATED rec_N` line per record, in order.
