from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"


def _activate() -> None:
    p = str(SRC)
    if p not in sys.path:
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
    _activate()
    try:
        import airflow
        from airflow.sdk import DAG
    except Exception as exc:
        raise RuntimeError(f"Airflow source probe failed: {exc}") from exc
    return {
        "airflow_file": str(Path(airflow.__file__).resolve()),
        "dag_module": DAG.__module__,
        "source_root": str(SRC.resolve()),
    }
