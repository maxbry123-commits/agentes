"""Loader de contratos YAML L1-L8 + catalog · 0% LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

_CONTRACTS_ROOT = Path(__file__).resolve().parents[1] / "contracts"


def _load_yaml_file(path: Path) -> Any:
    if yaml is None or not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_catalog(root: Path | None = None) -> dict[str, Any]:
    root = root or _CONTRACTS_ROOT
    data = _load_yaml_file(root / "catalog.yaml")
    return data if isinstance(data, dict) else {}


def load_all_contracts(root: Path | None = None) -> Dict[str, dict[str, Any]]:
    """Indexa id → contrato desde C00 y L*/contracts.yaml (+ stubs)."""
    root = root or _CONTRACTS_ROOT
    out: Dict[str, dict[str, Any]] = {}

    c00 = _load_yaml_file(root / "C00_governance.yaml")
    if isinstance(c00, dict) and c00.get("id"):
        out[str(c00["id"])] = c00

    for layer_dir in sorted(root.glob("L*")):
        if not layer_dir.is_dir():
            continue
        for yml in layer_dir.glob("*.yaml"):
            data = _load_yaml_file(yml)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("id"):
                        out[str(item["id"])] = item
            elif isinstance(data, dict) and data.get("id"):
                out[str(data["id"])] = data

    return out


def get_contract(contract_id: str, root: Path | None = None) -> Optional[dict[str, Any]]:
    return load_all_contracts(root).get(contract_id)


def list_implemented(root: Path | None = None) -> List[str]:
    cat = load_catalog(root)
    impl = cat.get("implementado") or []
    return [str(x) for x in impl]
