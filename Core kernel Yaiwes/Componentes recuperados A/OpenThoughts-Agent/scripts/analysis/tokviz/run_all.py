"""run_all.py -- top-level orchestrator.

Runs the chat half directly (5 prompts x 2 models -> 10 HTML) and then drives
the agentic half (start shim, run swe-agent if Docker+install present, collect,
render). All HTML lands in config.OUTPUT_DIR (the foundation_models path).

The Qwen3.5 weights require transformers>=5, so the MODEL-EXECUTING scripts
should be run with the dedicated `tokviz-rt` interpreter:

    /Users/benjaminfeuer/miniconda3/envs/tokviz-rt/bin/python run_all.py

The rendering/orchestration code itself is env-agnostic and also imports fine
under otagent.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    # 1. chat half (in-process; uses the current interpreter for model exec)
    print("=" * 70)
    print("CHAT HALF")
    print("=" * 70)
    subprocess.run([sys.executable, str(HERE / "run_chat.py")], check=True)

    # 2. ensure toy repos exist
    print("\n" + "=" * 70)
    print("TOY REPOS")
    print("=" * 70)
    subprocess.run([sys.executable, str(HERE / "make_repos.py")], check=True)

    # 3. agentic half (starts shim subprocess itself)
    print("\n" + "=" * 70)
    print("AGENTIC HALF")
    print("=" * 70)
    subprocess.run([sys.executable, str(HERE / "run_agentic.py")], check=True)

    sys.path.insert(0, str(HERE))
    from config import OUTPUT_DIR as out

    files = sorted(out.glob("*.html"))
    print(f"\nDONE. {len(files)} HTML files in {out}:")
    for f in files:
        print("  ", f.name)


if __name__ == "__main__":
    main()
