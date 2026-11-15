from __future__ import annotations

import re
from pathlib import Path

import yaiwes_real_workflow_chain_v63_core as core

SCHEMA = core.SCHEMA


def _component_roots_strict() -> dict[int, Path]:
    """Resolve only canonical YAIWES 01..24 component directories."""
    roots: dict[int, Path] = {}
    for child in core.base.ROOT.iterdir():
        if not child.is_dir():
            continue
        match = re.fullmatch(r"🏈\s+YAIWES\s+(\d{2})", child.name)
        if not match:
            continue
        ordinal = int(match.group(1))
        if 1 <= ordinal <= 24:
            if ordinal in roots:
                raise RuntimeError(f"duplicate canonical component: YAIWES {ordinal:02d}")
            roots[ordinal] = child
    expected = list(range(1, 25))
    if sorted(roots) != expected:
        missing = [i for i in expected if i not in roots]
        raise RuntimeError(f"missing canonical YAIWES components: {missing}")
    return roots


# Patch only component discovery. The V6.3 core keeps the audited per-component
# internal symbols, safe execution boundaries, persistence and hash handoffs.
core._component_roots_strict = _component_roots_strict
run_linear_chain = core.run_linear_chain


if __name__ == "__main__":
    state_root = core.base.ROOT / "🏈 cancha deportiva de fútbol" / ".yaiwes_canonical_runtime"
    report = run_linear_chain(
        state_root,
        "yaiwes-canonical-e2e",
        {
            "mode": "benign-research-persistence",
            "objective": "verify canonical 24-component linear internal workflow",
        },
    )
    print({
        "components": report["components"],
        "real_internal_workflows_executed": report["real_internal_workflows_executed"],
        "completed_internal_workflows": report["completed_internal_workflows"],
        "handoff_continuity": report["handoff_continuity"],
        "universal_plug_after_component_24": report["universal_plug_after_component_24"],
        "status": report["status"],
    })
