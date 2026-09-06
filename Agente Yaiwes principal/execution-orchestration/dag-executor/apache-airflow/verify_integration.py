from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
required = [
    ROOT / "src" / "airflow" / "models" / "dag.py",
    ROOT / "src" / "airflow" / "__init__.py",
    ROOT / "pyproject.toml",
    ROOT / "adapter.py",
    ROOT / "WIRING.json",
    ROOT / "ficha.airflow.v2.json",
]
missing = [str(p) for p in required if not p.exists()]
assert not missing, missing
w = json.loads((ROOT / "WIRING.json").read_text())
f = json.loads((ROOT / "ficha.airflow.v2.json").read_text())
assert w["classification"] == "B" and w["fail_closed"] is True
assert f["ejecucion"]["llm_ratio"] == 0.0
pyproject = (ROOT / "pyproject.toml").read_text()
assert 'version = "3.4.0"' in pyproject
print("AIRFLOW_STATIC_VERIFY_PASS")
