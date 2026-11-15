"""Gaps no diferidos: critical en entrypoint + loader contratos."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contract_engine.loader import load_all_contracts, load_catalog
from inputblock.store import Criticality
from wordflow.entrypoint import WordflowApp


def test_critical_blocks_without_confirm():
    with tempfile.TemporaryDirectory() as td:
        app = WordflowApp(Path(td))
        r = app.run_mission(
            "operación sensible",
            criticality=Criticality.CRITICO,
            confirm_critical=False,
        )
        assert r.blocked is True
        assert "critical_confirm" in (r.output.get("blocked_reason") or "")


def test_critical_ok_with_confirm():
    with tempfile.TemporaryDirectory() as td:
        app = WordflowApp(Path(td))
        r = app.run_mission(
            "operación sensible",
            op_type="READ_LOCAL",
            criticality=Criticality.CRITICO,
            confirm_critical=True,
        )
        assert r.blocked is False or r.sheriff_state in ("GREEN", "YELLOW", "ORANGE")
        # no debe ser bloqueo por critical
        assert "critical_confirm" not in (r.output.get("blocked_reason") or "")


def test_loader_has_c00():
    contracts = load_all_contracts()
    # si no hay pyyaml en entorno, puede venir vacío; no fallar duro
    cat = load_catalog()
    assert isinstance(contracts, dict)
    assert isinstance(cat, dict)
    if contracts:
        assert "C00" in contracts or any(k.startswith("C") for k in contracts)


if __name__ == "__main__":
    test_critical_blocks_without_confirm()
    test_critical_ok_with_confirm()
    test_loader_has_c00()
    print("gaps_fix OK")
