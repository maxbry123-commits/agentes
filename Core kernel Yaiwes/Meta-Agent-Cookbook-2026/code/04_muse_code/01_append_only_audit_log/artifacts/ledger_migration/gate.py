#!/usr/bin/env python3
"""Zorptic migration gate. Usage: python3 gate.py <rec_id>

Prints the UNLOCK KEY for <rec_id>. rec_1 is unlocked by the seed key in
MIGRATION.md. Every later record is unlocked only after the PREVIOUS record has
been migrated to schema v2 — the gate reads the previous record's `checksum`
field and derives this record's key from it. The gate sleeps ~5s (a slow
network hop, simulated) before returning the key.
"""
import sys, os, json, hashlib, time

def key_for(prev_checksum: str) -> str:
    return hashlib.sha256(("zorptic-" + prev_checksum).encode()).hexdigest()[:8]

rid = sys.argv[1]
n = int(rid.split("_")[1])
time.sleep(5)  # simulated slow gate lookup — the kill window
if n == 1:
    print("KEY rec_1 = 5eed7abc")   # seed key, also printed in MIGRATION.md
    sys.exit(0)
prev = f"records/rec_{n-1}.json"
with open(prev) as f:
    d = json.load(f)
if d.get("schema") != "v2" or "checksum" not in d:
    sys.stderr.write(f"LOCKED: {rid} cannot be unlocked until rec_{n-1} is migrated (schema v2 with checksum)\n")
    sys.exit(3)
print(f"KEY {rid} = {key_for(d['checksum'])}")
