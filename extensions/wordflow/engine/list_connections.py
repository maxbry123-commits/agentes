"""list_connections — S06/T06

Lee de forma determinista connect_catalog.json y component_catalog.json.
COPY-FIRST: no inventa edges; solo materializa lectura del catálogo en disco.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
CONNECT_CATALOG = ROOT / "connect_catalog.json"
COMPONENT_CATALOG = ROOT / "component_catalog.json"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def list_connections(
    *,
    conn_type: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Devuelve connections del catálogo; filtros opcionales type/status."""
    data = _load_json(CONNECT_CATALOG)
    items = list(data.get("connections") or [])
    if conn_type:
        items = [c for c in items if c.get("type") == conn_type]
    if status:
        items = [c for c in items if c.get("status") == status]
    return items


def list_components() -> List[Dict[str, Any]]:
    data = _load_json(COMPONENT_CATALOG)
    comps = data.get("components")
    if isinstance(comps, list):
        return comps
    # component_catalog puede ser dict de secciones
    if isinstance(data, dict) and comps is None:
        return [{"key": k, "value": v} for k, v in data.items() if k != "version"]
    return []


def connection_ids() -> List[str]:
    return [str(c.get("id")) for c in list_connections() if c.get("id")]


def catalog_meta() -> Dict[str, Any]:
    data = _load_json(CONNECT_CATALOG)
    return {
        "version": data.get("version"),
        "source": data.get("source"),
        "task": data.get("task"),
        "count": len(data.get("connections") or []),
        "path": str(CONNECT_CATALOG),
    }


if __name__ == "__main__":
    meta = catalog_meta()
    conns = list_connections()
    print("meta:", meta)
    print("connections:", len(conns))
    print("ids:", connection_ids())
    print("components:", len(list_components()))
