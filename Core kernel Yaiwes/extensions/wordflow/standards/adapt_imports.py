"""G-W9 — reescritura mínima de imports al ADAPT (determinista)."""
from __future__ import annotations
from pathlib import Path
import re
from typing import Dict, List

def rewrite_imports(text: str, mapping: Dict[str, str]) -> str:
    """mapping: old_module_prefix → new_module_prefix"""
    out = text
    for old, new in mapping.items():
        out = re.sub(
            rf"^(from\s+){re.escape(old)}(\b)",
            rf"\g<1>{new}\2",
            out,
            flags=re.MULTILINE,
        )
        out = re.sub(
            rf"^(import\s+){re.escape(old)}(\b)",
            rf"\g<1>{new}\2",
            out,
            flags=re.MULTILINE,
        )
    return out

def adapt_file(src: Path, dest: Path, mapping: Dict[str, str]) -> List[str]:
    text = src.read_text(encoding="utf-8")
    new_text = rewrite_imports(text, mapping)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(new_text, encoding="utf-8")
    return [f"{k}->{v}" for k, v in mapping.items()]
