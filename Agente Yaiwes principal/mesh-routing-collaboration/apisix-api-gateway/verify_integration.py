from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
required = [
    ROOT / "apisix" / "core" / "version.lua",
    ROOT / "apisix" / "cli" / "apisix.lua",
    ROOT / "bin" / "apisix",
    ROOT / "utils",
    ROOT / "Makefile",
    ROOT / "apisix-master-0.rockspec",
    ROOT / "adapter.py",
    ROOT / "WIRING.json",
    ROOT / "ficha.apisix.v2.json",
]
missing = [str(p) for p in required if not p.exists()]
assert not missing, missing
wiring = json.loads((ROOT / "WIRING.json").read_text())
ficha = json.loads((ROOT / "ficha.apisix.v2.json").read_text())
assert wiring["fail_closed"] is True
assert wiring["classification"] == "C"
assert ficha["ejecucion"]["llm_ratio"] == 0.0
version_text = (ROOT / "apisix" / "core" / "version.lua").read_text()
assert 'VERSION = "3.18.0"' in version_text
print("APISIX_STATIC_VERIFY_PASS")
