#!/usr/bin/env python3
"""Osquestador: inventory + audit agent snapshots + memory ledger."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents"
STATE = AGENTS / "_state"
LEDGER = ROOT / "memory" / "ledger.jsonl"

def load_json(p: Path):
    if not p.is_file():
        return None
    return json.loads(p.read_text())

def inventory():
    rows = []
    if STATE.is_dir():
        for p in sorted(STATE.glob("*.json")):
            d = load_json(p) or {}
            rows.append(f"{p.stem:24} {d.get('status','?'):8} {d.get('task','')}")
    for p in sorted(AGENTS.iterdir()):
        if p.name.startswith("_") or not p.is_dir():
            continue
        if not (STATE / f"{p.name}.json").exists():
            rows.append(f"{p.name:24} NO_STATE")
    print("\n".join(rows) if rows else "(empty)")

def audit(agent: str):
    base = AGENTS / agent
    checks = []
    def ok(name, cond, detail=""):
        checks.append(("OK" if cond else "FAIL", name, detail))
    ok("dir", base.is_dir())
    m = load_json(base / "manifest.json")
    ok("manifest", m is not None)
    ok("commit", (base / "source" / "commit.txt").is_file() or (m and m.get("identity", {}).get("commit")))
    ok("archive_sha", (base / "source" / "archive.sha256").is_file() or (m and m.get("source", {}).get("archive_sha256")))
    dist = list((base / "distribution" / "official").glob("*")) if (base / "distribution" / "official").is_dir() else []
    ok("dist_or_note", bool(dist) or (m and m.get("distribution")))
    st = load_json(STATE / f"{agent}.json")
    ok("state", st is not None)
    for s, n, d in checks:
        print(f"{s:4} {n} {d}")
    print("RESULT", "PASS" if all(c[0]=="OK" for c in checks) else "FAIL")

def memory_write(op: str, agent: str, status: str, note: str = ""):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "op": op, "agent": agent, "status": status, "note": note}
    with LEDGER.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    print("wrote", rec["ts"])

def memory_read(n: int = 20):
    if not LEDGER.is_file():
        print("(no ledger)"); return
    lines = LEDGER.read_text().splitlines()[-n:]
    print("\n".join(lines))

def main():
    if len(sys.argv) < 2:
        print("usage: inventory|audit <Id>|memory-read [N]|memory-write op agent status [note]"); return 2
    cmd = sys.argv[1]
    if cmd == "inventory": inventory()
    elif cmd == "audit" and len(sys.argv) > 2: audit(sys.argv[2])
    elif cmd == "memory-read": memory_read(int(sys.argv[2]) if len(sys.argv)>2 else 20)
    elif cmd == "memory-write" and len(sys.argv) >= 5:
        memory_write(sys.argv[2], sys.argv[3], sys.argv[4], " ".join(sys.argv[5:]))
    else:
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
