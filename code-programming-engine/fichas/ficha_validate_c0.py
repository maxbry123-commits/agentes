"""C0 — Validador de fichas del motor code-programming-engine.

No reescribe el enchufe universal. Solo valida que una ficha cumpla
el contrato mínimo (abi 2.0 / plantilla C0) antes de registrar un módulo.

Uso:
  from ficha_validate_c0 import validate_ficha, validate_ficha_file
  ok, errors = validate_ficha(dict_ficha)
  ok, errors = validate_ficha_file(Path("fichas/mi_ficha.json"))
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

REQUIRED_TOP = (
    "artifact_id",
    "version",
    "abi_version",
    "contrato",
    "ejecucion",
    "plane",
    "deterministic",
)

REQUIRED_CONTRATO = ("rol",)
REQUIRED_EJECUCION = ("kind", "transport", "entry_point")

VALID_ROLES = frozenset({"source", "transform", "sink", "service", "gate", "skill_pack"})
VALID_TRANSPORT = frozenset({"importlib", "http", "cli", "subprocess", "reference"})
VALID_PLANES = frozenset({"programming", "wordflow", "uoos", "deploy", "skills"})


def _get(d: Dict[str, Any], dotted: str) -> Any:
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def validate_ficha(ficha: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valida dict ficha. Fail-closed: cualquier fallo → ok=False."""
    errors: List[str] = []

    if not isinstance(ficha, dict):
        return False, ["ficha must be a dict"]

    for key in REQUIRED_TOP:
        if key not in ficha:
            errors.append(f"missing top-level field: {key}")

    contrato = ficha.get("contrato")
    if isinstance(contrato, dict):
        for key in REQUIRED_CONTRATO:
            if key not in contrato:
                errors.append(f"missing contrato.{key}")
        rol = contrato.get("rol")
        if rol is not None and rol not in VALID_ROLES:
            errors.append(f"contrato.rol invalid: {rol!r}; allowed={sorted(VALID_ROLES)}")
    elif "contrato" in ficha:
        errors.append("contrato must be an object")

    ejec = ficha.get("ejecucion")
    if isinstance(ejec, dict):
        for key in REQUIRED_EJECUCION:
            if key not in ejec or not ejec[key]:
                errors.append(f"missing or empty ejecucion.{key}")
        transport = ejec.get("transport")
        if transport is not None and transport not in VALID_TRANSPORT:
            errors.append(
                f"ejecucion.transport invalid: {transport!r}; allowed={sorted(VALID_TRANSPORT)}"
            )
        if ejec.get("kind") == "code" and not ejec.get("entry_point"):
            errors.append("ejecucion.kind=code requires entry_point")
    elif "ejecucion" in ficha:
        errors.append("ejecucion must be an object")

    plane = ficha.get("plane")
    if plane is not None and plane not in VALID_PLANES:
        errors.append(f"plane invalid: {plane!r}; allowed={sorted(VALID_PLANES)}")

    if "deterministic" in ficha and not isinstance(ficha.get("deterministic"), bool):
        errors.append("deterministic must be bool")

    abi = ficha.get("abi_version")
    if abi is not None and str(abi).split(".")[0] != "2":
        errors.append(f"abi_version major must be 2.x, got {abi!r}")

    artifact_id = ficha.get("artifact_id")
    if isinstance(artifact_id, str) and not artifact_id.strip():
        errors.append("artifact_id empty")

    if ficha.get("plane") == "programming" and ficha.get("mount_mode") == "embedded":
        errors.append(
            "Option A violation: programming plane cannot use mount_mode=embedded "
            "(motor lives outside kernel; use sidecar|reference)"
        )

    return (len(errors) == 0, errors)


def validate_ficha_file(path: Path | str) -> Tuple[bool, List[str]]:
    path = Path(path)
    if not path.exists():
        return False, [f"file not found: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, [f"read/parse error: {exc}"]
    return validate_ficha(data)


def validate_many(paths: List[Path | str]) -> Dict[str, Any]:
    """Valida varias fichas; summary fail-closed."""
    results = []
    all_ok = True
    for p in paths:
        ok, errors = validate_ficha_file(p)
        results.append({"path": str(p), "ok": ok, "errors": errors})
        if not ok:
            all_ok = False
    return {"ok": all_ok, "results": results}


if __name__ == "__main__":
    import sys

    targets = [Path(a) for a in sys.argv[1:]]
    if not targets:
        here = Path(__file__).resolve().parent
        targets = list(here.glob("ficha_*.json"))
        targets += list((here / "discover").glob("ficha_*.json")) if (here / "discover").exists() else []
    if not targets:
        print("usage: ficha_validate_c0.py <ficha.json> ...")
        sys.exit(2)
    summary = validate_many(targets)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    sys.exit(0 if summary["ok"] else 1)
