#!/usr/bin/env python
"""Reset Identity Memory to genesis-only state.

Keeps the 7 absolute_core genesis memories and all non-memory sections
(cognitive_state, personality, temporal, etc.). Removes all cognithor-
generated memories from memories.json.

Usage:
    python scripts/reset_identity_memories.py              # Dry run (default)
    python scripts/reset_identity_memories.py --execute     # Actually reset
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset Identity Memory to genesis-only.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the reset. Without this flag, only a dry run is shown.",
    )
    parser.add_argument(
        "--memories-file",
        type=str,
        default=None,
        help="Path to memories.json. Default: ~/.jarvis/identity/jarvis/memories.json",
    )
    args = parser.parse_args()

    # Locate memories.json
    if args.memories_file:
        mem_path = Path(args.memories_file)
    else:
        mem_path = Path.home() / ".jarvis" / "identity" / "jarvis" / "memories.json"

    if not mem_path.exists():
        print(f"[ERROR] File not found: {mem_path}")
        sys.exit(1)

    # Load
    with open(mem_path, encoding="utf-8") as f:
        data = json.load(f)

    memories = data.get("memories", {})
    total = len(memories)

    # Separate genesis from cognithor memories
    genesis = {}
    cognithor = {}
    for mid, mem in memories.items():
        if mem.get("is_absolute_core", False):
            genesis[mid] = mem
        else:
            cognithor[mid] = mem

    print(f"File: {mem_path}")
    print(f"Total memories: {total}")
    print(f"Genesis (keep): {len(genesis)}")
    print(f"Cognithor (remove): {len(cognithor)}")
    print()

    if not args.execute:
        print("[DRY RUN] No changes made. Use --execute to perform the reset.")
        return

    # Backup
    bak_path = mem_path.with_suffix(".json.bak")
    shutil.copy2(mem_path, bak_path)
    print(f"Backup created: {bak_path}")

    # Reset memories to genesis only
    data["memories"] = genesis

    # Atomic write
    tmp_path = mem_path.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp_path.replace(mem_path)

    print(
        f"[OK] Reset complete. {len(genesis)} genesis memories retained, {len(cognithor)} removed."
    )
    print()
    print("Note: ChromaDB VectorStore may still contain old embeddings.")
    print("They will be naturally replaced as new memories are created,")
    print("or you can delete the chromadb directory manually if desired:")
    print(f"  {mem_path.parent / 'chromadb'}")


if __name__ == "__main__":
    main()
