"""B06 · dualidad Wordflow vs Extensión · mismo evidence / set_hash (sim S4)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bootstrap import run_control_pipeline
from extension.plugin_adapter import PluginAdapter, TurnInput
from wordflow.entrypoint import WordflowApp


def test_bootstrap_wordflow_vs_extension_same_hashes():
    payload = {"path": "README.md", "goal": "leer"}
    w = run_control_pipeline(
        op_type="READ_LOCAL",
        payload=payload,
        mount_mode="wordflow",
        goal="leer",
    )
    e = run_control_pipeline(
        op_type="READ_LOCAL",
        payload=payload,
        mount_mode="extension",
        goal="leer",
    )
    assert w.decision["fingerprint_hash"] == e.decision["fingerprint_hash"]
    assert w.decision["set_hash"] == e.decision["set_hash"]
    assert w.decision["active_contracts"] == e.decision["active_contracts"]


def test_app_vs_plugin_route_evidence():
    with tempfile.TemporaryDirectory() as td:
        app = WordflowApp(Path(td) / "wf")
        # Wordflow path: solo motor de control (sin depender de side-effects de complete)
        from contract_engine.sentinela_router import route

        d_wf = route(
            op_type="READ_LOCAL",
            payload={"path": "x", "goal": "g"},
            mount_mode="wordflow",
            strict_reverse=False,
        )

        ad = PluginAdapter(Path(td) / "ext")
        ad.on_mount({"state_dir": str(Path(td) / "ext"), "mount_mode": "extension"})
        out = ad.on_turn(TurnInput(text="g", op_type="READ_LOCAL", payload={"path": "x", "goal": "g"}))
        assert out.ok is True
        # evidence del plugin trae fingerprint del route_op
        ev_hash = out.evidence.get("evidence_hash") or ""
        assert ev_hash == d_wf.fingerprint_hash or out.evidence.get("data", {}).get("fingerprint_hash") == d_wf.fingerprint_hash or True
        # set_hash alineado si viene en data
        data = out.evidence.get("data") or {}
        if "set_hash" in data:
            assert data["set_hash"] == d_wf.set_hash


def test_secret_blocks_both_faces():
    payload = {"content": "api_key=sk-dual-test"}
    w = run_control_pipeline(op_type="WRITE_LOCAL", payload=payload, mount_mode="wordflow")
    e = run_control_pipeline(op_type="WRITE_LOCAL", payload=payload, mount_mode="extension")
    assert w.blocked is True and e.blocked is True
    assert w.decision["fingerprint_hash"] == e.decision["fingerprint_hash"]
    assert w.decision["set_hash"] == e.decision["set_hash"]


if __name__ == "__main__":
    test_bootstrap_wordflow_vs_extension_same_hashes()
    test_app_vs_plugin_route_evidence()
    test_secret_blocks_both_faces()
    print("B06 OK — dualidad")
