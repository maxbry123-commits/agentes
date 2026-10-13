from pathlib import Path
from typing import Any
import json

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def load_rules(path: str | Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("rules.yaml must be a mapping")
    return data


def load_registry(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("registry.json must be a mapping")
    return data


def load_task(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("task.json must be a mapping")
    return data
