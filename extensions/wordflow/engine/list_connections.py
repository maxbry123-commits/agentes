"""list_connections stub — S06/T06
Lee connect_catalog.json y component_catalog.json.
"""
from pathlib import Path
import json
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parents[1]

def list_connections() -> List[Dict[str, Any]]:
    path = ROOT / "connect_catalog.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("connections", [])

def list_components() -> List[Dict[str, Any]]:
    path = ROOT / "component_catalog.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("components", [])

if __name__ == "__main__":
    print("connections:", len(list_connections()))
    print("components:", len(list_components()))
