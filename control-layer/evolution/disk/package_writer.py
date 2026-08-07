"""Escribe Universal Plugin real en extensions/<domain>/<id>/."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ADAPTER_STUB = '''\"\"\"Auto-generated adapter stub · Evolution Engine.
Source: {source_id} · strategy: {strategy}
\"\"\"
from __future__ import annotations
from typing import Any, Mapping

CAPABILITIES = {capabilities!r}

def handle(capability: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(payload or {{}})
    if capability not in CAPABILITIES:
        return {{"ok": False, "error": f"unknown_capability:{{capability}}"}}
    return {{
        "ok": True,
        "capability": capability,
        "plugin": "{plugin_id}",
        "payload_echo": payload,
        "note": "stub_handler_replace_with_code_worker",
    }}

HANDLERS = {{c: (lambda p, _c=c: handle(_c, p)) for c in CAPABILITIES}}
'''

class PackageWriter:
    def __init__(self, extensions_root="extensions"):
        self.root = Path(extensions_root)

    def write(self, *, plugin_id, domain, placement_path, manifest, plan, evo_ir, simulation):
        leaf = plugin_id.split(".")[-1]
        out = self.root / Path(*domain.split("/")) / leaf
        out.mkdir(parents=True, exist_ok=True)
        caps = [c.get("id") if isinstance(c, dict) else str(c) for c in manifest.get("capabilities", [])]
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (out / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
        (out / "evo_ir.json").write_text(json.dumps(evo_ir, indent=2), encoding="utf-8")
        (out / "simulation.json").write_text(json.dumps(simulation, indent=2), encoding="utf-8")
        (out / "capabilities.json").write_text(json.dumps(caps, indent=2), encoding="utf-8")
        adapter = ADAPTER_STUB.format(source_id=manifest.get("id", plugin_id), strategy=plan.get("strategy", "absorb"), capabilities=caps, plugin_id=plugin_id)
        (out / "adapter.py").write_text(adapter, encoding="utf-8")
        (out / "__init__.py").write_text("from .adapter import HANDLERS, handle\n", encoding="utf-8")
        return out
