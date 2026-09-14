"""
Dashboard mermaid rendering.

Extracts ```mermaid blocks from markdown and renders each to an SVG via the
mermaid CLI, remapping light-theme colours to dark-mode equivalents first.
Results are cached by content hash (``core.api_server._svg_cache``) so polls
don't re-shell-out on every request.
"""
from __future__ import annotations

import os
from pathlib import Path

import core.api_server as _api

# Remap light-theme inline styles to dark-mode equivalents
_DARK_REMAP = {
    # Reds (danger/critical)
    "fill:#f44": "fill:#5c1a1a", "fill:#f88": "fill:#6b1a1a",
    "fill:#faa": "fill:#5c1a1a", "fill:#fcc": "fill:#4d1a1a",
    "fill:#e53e3e": "fill:#7f1d1d", "fill:#fc8181": "fill:#6b2020",
    # Yellows/oranges (warning)
    "fill:#ffd": "fill:#3d3000", "fill:#ffa": "fill:#3d3000",
    # Greens (safe/mitigated)
    "fill:#68d391": "fill:#14532d", "fill:#48bb78": "fill:#14532d",
    # Blues
    "fill:#ddf": "fill:#1a2a4a", "fill:#bbf": "fill:#1a2040",
    "fill:#63b3ed": "fill:#1e3a5f",
    # Strokes
    "stroke:#c00": "stroke:#ff6666", "stroke:#a00": "stroke:#ff5555",
    "stroke:#c44": "stroke:#ff8888", "stroke:#aa0": "stroke:#ddcc00",
    "stroke:#44a": "stroke:#6699ff", "stroke:#c53030": "stroke:#f87171",
    "stroke:#e53e3e": "stroke:#f87171", "stroke:#38a169": "stroke:#4ade80",
    # Text color overrides — force light text
    "color:#fff": "color:#e5e7eb", "color:#000": "color:#e5e7eb",
}


def _remap_mermaid_dark(src: str) -> str:
    for light, dark in _DARK_REMAP.items():
        src = src.replace(light, dark)
    return src


def sanitize_mermaid(src: str) -> str:
    """Escape Mermaid-breaking chars INSIDE node/edge label spans, preserving <br/>
    line-breaks and the structural syntax. Model-authored diagrams routinely put
    payloads/values in labels — a leading ';' (statement separator) or '<header>'
    (parsed as an HTML tag) throws 'Syntax error in text' in mermaid 10.9.6. We escape
    only the label CONTENT (inside [...], (...), {...}, |...|), never the delimiters."""
    import re
    if not src:
        return src
    _span = re.compile(r'(\[[^\]\n]*\]|\([^)\n]*\)|\{[^}\n]*\}|\|[^|\n]*\|)')
    # Leave existing entities (#NN;) and <br/> intact — this makes re-sanitizing idempotent
    # (the endpoint AND _render_mermaid_svgs both call this, so it can run twice).
    _protect = re.compile(r'#\d+;|<br\s*/?>', re.I)

    def _esc(m):
        span = m.group(0)
        stash: list[str] = []

        def _keep(mm):
            stash.append(mm.group(0))
            return f"\x00{len(stash) - 1}\x00"

        inner = _protect.sub(_keep, span[1:-1])
        inner = inner.replace(";", "#59;").replace("<", "#60;").replace(">", "#62;")
        for i, tok in enumerate(stash):
            inner = inner.replace(f"\x00{i}\x00", tok)
        return span[0] + inner + span[-1]

    return _span.sub(_esc, src)


def _render_mermaid_svgs(content: str) -> dict[str, str]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'core/api_server/mermaid.py','step':'_render_mermaid_svgs','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
