"""T35 — validate_resource schema. No download."""
from __future__ import annotations

from typing import Any

KINDS = frozenset({"skill", "dataset", "adapter", "space", "model", "kernel", "file", "mcp"})
REQUIRED = ("resource_id", "kind")


def validate_resource(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"ok": False, "errors": ["NOT_OBJECT"]}
    errors: list[str] = []
    rid = data.get("resource_id") or data.get("id") or data.get("package_id")
    if not rid:
        errors.append("RESOURCE_ID_MISSING")
    kind = data.get("kind")
    if not kind:
        errors.append("KIND_MISSING")
    elif kind not in KINDS:
        errors.append("INVALID_KIND")
    source = data.get("source_uri") or data.get("source")
    if not source:
        errors.append("SOURCE_MISSING")
    return {"ok": len(errors) == 0, "errors": errors, "resource_id": rid, "kind": kind}


if __name__ == "__main__":
    bad = validate_resource({"kind": "nope"})
    assert bad["ok"] is False
    good = validate_resource({"resource_id": "s1", "kind": "skill", "source": "local:x"})
    assert good["ok"] is True
    print("ok", bad["errors"], good["ok"])
