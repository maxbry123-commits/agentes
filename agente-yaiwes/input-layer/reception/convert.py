"""EXTRA T2/T2.1/T2.2/T2.3 — convert input_block. SDPA/MCR stubs. max_context config."""
from __future__ import annotations
from typing import Any
DEFAULT_MAX_CONTEXT = 20_000_000

def convert(input_block: dict[str, Any] | None, *, use_sdpa: bool = False, branch: str = "default", max_context: int = DEFAULT_MAX_CONTEXT) -> dict[str, Any]:
    if not isinstance(input_block, dict): return {"ok": False, "error": "INVALID_BLOCK"}
    text = str(input_block.get("raw_text") or input_block.get("text") or input_block.get("content") or "")
    path = "mcr" if branch == "mcr" else "default"
    return {"ok": True, "normalized": {"text": text.strip(), "keys": sorted(input_block.keys()), "source": input_block.get("source_type") or input_block.get("source")}, "use_sdpa": bool(use_sdpa), "branch": path, "max_context": int(max_context), "sdpa_stub": bool(use_sdpa), "mcr_stub": path == "mcr"}

def run_mcr(input_block: dict[str, Any] | None) -> dict[str, Any]: return convert(input_block, branch="mcr")
