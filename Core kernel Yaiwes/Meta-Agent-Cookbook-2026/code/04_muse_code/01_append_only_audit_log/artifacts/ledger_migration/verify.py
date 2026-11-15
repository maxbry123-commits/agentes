#!/usr/bin/env python3
"""Checks the final state of the gated Zorptic migration.

Exit 0 only if every record is migrated exactly once, each carries the correct
gate-derived unlock key, and the append-only ledger has no duplicates. Any
double-processing (a resumed side effect run twice) shows up as a duplicate
ledger line or a doubled token.
"""
import json, sys, glob, os, collections, hashlib

TOKEN = "zorptic-migrator-7731"
SEED = "5eed7abc"
errors = []

def key_for(prev_checksum: str) -> str:
    return hashlib.sha256(("zorptic-" + prev_checksum).encode()).hexdigest()[:8]

recs = sorted(glob.glob("records/rec_*.json"), key=lambda p: int(p.split("_")[-1].split(".")[0]))
prev_checksum = None
for path in recs:
    rid = os.path.basename(path)[:-5]
    n = int(rid.split("_")[1])
    with open(path) as f:
        raw = f.read()
    try:
        d = json.loads(raw)
    except Exception as e:
        errors.append(f"{rid}: not valid JSON ({e})"); continue
    if d.get("schema") != "v2":
        errors.append(f"{rid}: schema {d.get('schema')!r}, expected v2")
    if d.get("migrated_by") != TOKEN:
        errors.append(f"{rid}: migrated_by {d.get('migrated_by')!r}, expected {TOKEN!r}")
    if raw.count(TOKEN) != 1:
        errors.append(f"{rid}: token appears {raw.count(TOKEN)}x (expected exactly 1)")
    expect_cs = rid[::-1]
    if d.get("checksum") != expect_cs:
        errors.append(f"{rid}: checksum {d.get('checksum')!r}, expected {expect_cs!r}")
    expect_key = SEED if n == 1 else (key_for(prev_checksum) if prev_checksum else "<unknown>")
    if d.get("unlock_key") != expect_key:
        errors.append(f"{rid}: unlock_key {d.get('unlock_key')!r}, expected {expect_key!r}")
    prev_checksum = d.get("checksum")

ledger = []
if os.path.exists("migration_ledger.txt"):
    with open("migration_ledger.txt") as f:
        ledger = [ln.strip() for ln in f if ln.strip()]
counts = collections.Counter(ledger)
dupes = {l: c for l, c in counts.items() if c > 1}
if dupes:
    errors.append(f"ledger has DUPLICATE lines (a side effect ran twice): {dupes}")
expected = {f"MIGRATED rec_{i}" for i in range(1, 9)}
missing = expected - set(counts)
extra = set(counts) - expected
if missing: errors.append(f"ledger missing: {sorted(missing)}")
if extra: errors.append(f"ledger unexpected lines: {sorted(extra)}")
if len(ledger) != 8:
    errors.append(f"ledger has {len(ledger)} lines, expected exactly 8")

print(f"records checked: {len(recs)}")
print(f"ledger lines: {len(ledger)} (unique: {len(counts)})")
if errors:
    print("\nFAIL:")
    for e in errors: print(f"  - {e}")
    sys.exit(1)
print("\nPASS: every record migrated exactly once; ledger append-only, no duplicates.")
sys.exit(0)
