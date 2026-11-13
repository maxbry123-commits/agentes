#!/usr/bin/env python3
"""Deterministic G1 exporter; reuses the canonical build_symbol_index().

Method: Método de trabajo/registro de plugins/GUIA_REGISTRO_PLUGINS_Y_CABLEADO.md
This exporter is stable after registration; future wiring must use the registered
plugin/contract connection rather than editing the exported artifact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# Script entrypoints are launched from their own directory by Python. Register the
# repository root before importing the canonical plugin implementation so the
# exporter is reproducible both locally and in GitHub Actions.
sys.path.insert(0, str(ROOT))

from extensions.wordflow.standards.symbol_index import build_symbol_index

OUT = ROOT / "agente-yaiwes/control-governance/symbol-index-wiring-graph"
ROOTS = [ROOT / "extensions/wordflow/engine", ROOT / "extensions/wordflow/standards"]


def _relative_payload(payload: dict) -> dict:
    """Normalize scanner paths to repository-relative POSIX paths."""
    normalized: dict = {}
    for name, hits in payload.items():
        rows = []
        for hit in hits:
            raw = Path(str(hit["path"]))
            try:
                rel = raw.resolve().relative_to(ROOT.resolve()).as_posix()
            except ValueError:
                rel = raw.as_posix()
            rows.append({"name": hit["name"], "kind": hit["kind"], "path": rel, "lineno": hit["lineno"]})
        normalized[name] = rows
    return normalized


def main() -> None:
    idx = build_symbol_index(ROOTS, limit_files=500, use_cache=False, use_disk=False)
    payload = _relative_payload(idx.to_payload())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SYMBOL_INDEX_PROGRAMMING.json").write_text(json.dumps({"roots":[str(p.relative_to(ROOT)) for p in ROOTS], "symbols":payload}, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    lines = ["# SYMBOL INDEX — PROGRAMMING", "", "Generated deterministically by `Refactoria/G1/new/build_programming_symbol_index.py`.", "", "Roots:"]
    lines += [f"- `{p.relative_to(ROOT)}`" for p in ROOTS]
    lines += ["", f"Symbols indexed: {sum(len(v) for v in payload.values())}", "", "| Symbol | Kind | Path | Line |", "|---|---|---|---:|"]
    for name in sorted(payload):
        for hit in sorted(payload[name], key=lambda h:(h["path"], h["lineno"])):
            lines.append(f'| `{hit["name"]}` | {hit["kind"]} | `{hit["path"]}` | {hit["lineno"]} |')
    (OUT / "SYMBOL_INDEX_PROGRAMMING.md").write_text("\n".join(lines)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
