"""ficha.v2 loader → register capability — T10

ADAPT of existing CapabilityRegistry. Identifiers follow real fichas:
artifact_id OR id OR name; abi_version OR version (PATCH3 B1).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_ID_KEYS = ("artifact_id", "id", "name")
_VER_KEYS = ("abi_version", "version")


class CapabilityRegistry:
    def __init__(self) -> None:
        self._caps: Dict[str, Dict[str, Any]] = {}

    def register(self, cap_id: str, ficha: Dict[str, Any]) -> None:
        self._caps[cap_id] = ficha

    def get(self, cap_id: str) -> Optional[Dict[str, Any]]:
        return self._caps.get(cap_id)

    def list(self) -> List[str]:
        return list(self._caps.keys())


def _first_present(data: Dict[str, Any], keys: tuple[str, ...]) -> Optional[str]:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip() != "":
            return str(value)
    return None


def ficha_id(data: Dict[str, Any], fallback: Optional[str] = None) -> Optional[str]:
    found = _first_present(data, _ID_KEYS)
    if found is not None:
        return found
    return fallback


def validate_ficha(data: dict) -> list[str]:
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["ficha must be a dict"]
    if ficha_id(data) is None:
        errors.append("missing identifier: artifact_id OR id OR name")
    if _first_present(data, _VER_KEYS) is None:
        errors.append("missing version: abi_version OR version")
    return errors


def load_ficha(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"ficha inválida: {path}")
    return data


def register_capability(ficha: dict, registry: dict | CapabilityRegistry | None = None) -> dict:
    errors = validate_ficha(ficha)
    if errors:
        raise ValueError("ficha inválida: " + "; ".join(errors))
    cap_id = ficha_id(ficha)
    assert cap_id is not None
    if registry is None:
        target: Dict[str, Any] = {}
        target[cap_id] = ficha
        return target
    if isinstance(registry, CapabilityRegistry):
        registry.register(cap_id, ficha)
        return {cap_id: ficha}
    if isinstance(registry, dict):
        registry[cap_id] = ficha
        return registry
    raise TypeError(f"unsupported registry type: {type(registry)!r}")


def load_and_register(path: Path, registry: CapabilityRegistry) -> str:
    path = Path(path)
    ficha = load_ficha(path)
    errors = validate_ficha(ficha)
    if errors:
        raise ValueError("ficha inválida: " + "; ".join(errors))
    cap_id = ficha_id(ficha, fallback=path.stem)
    assert cap_id is not None
    registry.register(str(cap_id), ficha)
    return str(cap_id)


default_cap_registry = CapabilityRegistry()


def _package_ficha() -> Path:
    return Path(__file__).resolve().parent / "ficha.v2.json"


if __name__ == "__main__":
    ficha_path = _package_ficha()
    data = load_ficha(ficha_path)
    errs = validate_ficha(data)
    if errs:
        raise SystemExit("FAIL validate: " + "; ".join(errs))
    cap_id = load_and_register(ficha_path, default_cap_registry)
    print(f"{cap_id} OK")
