"""Deterministic G2 schema smoke-test.

Validates every C19 schema example against its own JSON Schema using jsonschema.
No production code is imported or modified.
"""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2] / ".." / "agente-yaiwes" / "code-programming-engine" / "schema-contracts-io"
SCHEMAS = sorted(ROOT.glob("C19_*.schema.json"))


def main() -> None:
    if not SCHEMAS:
        raise SystemExit("G2 FAIL: no C19 schemas found")
    for path in SCHEMAS:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        examples = schema.get("examples", [{}])
        for example in examples:
            Draft202012Validator(schema).validate(example)
        print(f"PASS {path.name}: {len(examples)} example(s)")
    print(f"G2 PASS: {len(SCHEMAS)} C19 schema(s) structurally valid and example-validated")


if __name__ == "__main__":
    main()
