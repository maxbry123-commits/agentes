"""Pipeline de despliegue completo — 5 pasos.
SOURCE: CAPA DE CONTROL 1 · organizador→desplegador→detector→subir→verificar
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from .organizador import organizar, write_plan
from .desplegador import desplegar
from .detector_version import detect
from .subir import subir
from .verificar import verificar, write_evidence


def run_deploy(project_root: str | Path, deploy_config: str | Path, staging: str | Path = ".staging") -> dict[str, Any]:
    root = Path(project_root)
    plan = organizar(root, deploy_config)
    write_plan(plan, root / "plan.json")

    if plan.sin_regla or plan.bloqueados:
        return {
            "ok": False,
            "step": "organizador",
            "SIN_REGLA": plan.sin_regla,
            "BLOQUEADOS": plan.bloqueados,
        }

    dep = desplegar(root, root / "plan.json", staging)
    if not dep.get("ok"):
        return {"ok": False, "step": "desplegador", **dep}

    ver = detect(staging)
    pre = subir(root)
    if not pre.get("ok"):
        return {"ok": False, "step": "subir", **pre}

    evidence = verificar(root, plan.mapped)
    write_evidence(evidence, root / "evidence.json")

    return {
        "ok": evidence.ok and pre.get("ok", False),
        "step": "done",
        "version_bump": ver.get("bump"),
        "upload_precheck": pre,
        "evidence_ok": evidence.ok,
        "files": evidence.files_count,
    }
