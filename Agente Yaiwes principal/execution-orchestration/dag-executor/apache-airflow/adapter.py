from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
TASK_SDK = ROOT / "task-sdk" / "src"
DAG_SOURCE = TASK_SDK / "airflow" / "sdk" / "definitions" / "dag.py"


def _activate() -> None:
    for candidate in (TASK_SDK, SRC):
        p = str(candidate)
        if candidate.exists() and p not in sys.path:
            sys.path.insert(0, p)


def dag_factory(dag_id: str, *, schedule: Any = None):
    if not dag_id or not isinstance(dag_id, str):
        raise ValueError("dag_id must be a non-empty string")
    _activate()
    try:
        from airflow.sdk import DAG
    except Exception as exc:
        raise RuntimeError(f"Airflow import failed: {exc}") from exc
    return DAG(dag_id=dag_id, schedule=schedule)


def source_probe() -> dict:
    """Minimal upstream DAG boundary check without importing Airflow's full dependency graph."""
    if not DAG_SOURCE.exists():
        raise RuntimeError(f"Airflow DAG source missing: {DAG_SOURCE}")
    tree = ast.parse(DAG_SOURCE.read_text(encoding="utf-8"))
    dag_class = next((node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "DAG"), None)
    if dag_class is None:
        raise RuntimeError("Airflow DAG class not found in task-sdk source")
    try:
        dag_factory("")
    except ValueError:
        pass
    else:
        raise RuntimeError("Airflow adapter fail-closed dag_id validation failed")
    return {
        "ok": True,
        "component": "Apache-Airflow",
        "classification": "B",
        "dag_source": str(DAG_SOURCE.resolve()),
        "dag_class": dag_class.name,
        "fail_closed_empty_dag_id": True,
    }


def runtime_command() -> list[str]:
    """Compile only the real Task SDK DAG definition surface used by this adapter."""
    return [sys.executable, "-m", "compileall", "-q", str(DAG_SOURCE.parent)]


def runtime_cwd() -> str:
    return str(ROOT)
