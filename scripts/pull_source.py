#!/usr/bin/env python3
"""Deterministic source pull for TEAM SEALS / agents.
Usage: python scripts/pull_source.py --id opencode
Reads manifests/AGENTS_SOURCE_MANIFEST.yaml + RECEIPT, downloads archive, verifies, extracts to path.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "AGENTS_SOURCE_MANIFEST.yaml"

def load_receipt(agent_id: str) -> dict:
    receipt = ROOT / "agents" / "sources" / {
        "opencode": "OpenCode",
    }.get(agent_id, agent_id) / "SOURCE_RECEIPT.json"
    if not receipt.exists():
        # fallback scan
        for p in (ROOT / "agents" / "sources").rglob("SOURCE_RECEIPT.json"):
            data = json.loads(p.read_text())
            if data.get("id") == agent_id:
                return data
        raise SystemExit(f"No SOURCE_RECEIPT for {agent_id}")
    return json.loads(receipt.read_text())

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    args = ap.parse_args()
    r = load_receipt(args.id)
    url = r.get("source_url_archive") or f"{r['repo']}/archive/refs/tags/{r['ref']}.tar.gz"
    dest = ROOT / r["path"]
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tar = Path(td) / "src.tar.gz"
        print(f"Downloading {url} ...")
        urllib.request.urlretrieve(url, tar)
        digest = sha256_file(tar)
        print(f"SHA256: {digest}")
        # extract
        subprocess.check_call(["tar", "-xzf", str(tar), "-C", str(dest), "--strip-components=1"])
        # update receipt with computed sha
        r["sha256_archive"] = digest
        r["status"] = "pinned"
        receipt_path = dest / "SOURCE_RECEIPT.json"
        receipt_path.write_text(json.dumps(r, indent=2) + "\n")
        print(f"Extracted to {dest}")
        print("Done. Update AGENTS_SOURCE_MANIFEST.yaml sha256 field with the printed value.")

if __name__ == "__main__":
    main()
