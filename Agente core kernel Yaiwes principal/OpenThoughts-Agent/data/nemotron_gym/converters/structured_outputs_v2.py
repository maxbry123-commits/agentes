"""Convert nvidia/Nemotron-RL-Instruction-Following-Structured-Outputs-v2 (v3 gen).

This is the refresh of the json-only
`nvidia/Nemotron-RL-instruction_following-structured_outputs`. The v2 repo
covers FIVE serialization formats, selected per-row by `schema_type`:
`json`, `yaml`, `toml`, `xml`, `csv`.

Schema (one row, as exposed via the streaming loader):
  - responses_create_params.input : messages (use `extract_prompt`)
  - schema_str   : str — ALWAYS a JSON-Schema document (schema_repr is "json"
                   across the whole dataset), regardless of schema_type.
  - schema_type  : "json" | "yaml" | "toml" | "xml" | "csv" — the OUTPUT
                   serialization format the agent must emit.
  - schema_fields_count : str (provenance)
  - agent_ref    : provenance

The agent writes its document to /app/answer.txt; the embedded
`STRUCTURED_FORMAT_VERIFIER_PY` parses it per `schema_type` and grades it.

Grading semantics (see verifiers/structured_format.py for the full writeup):
  - json / yaml / toml : FULL JSON-Schema validation (Draft 2020-12) after
    parsing to native python (dates coerced to strings for yaml/toml).
  - xml : STRUCTURAL — well-formed XML + all top-level required keys present as
    element tags/attributes. Types/nesting NOT enforced (no canonical
    JSON<->XML mapping).
  - csv : STRUCTURAL — parses as CSV (header + >=1 data row) + all top-level
    REQUIRED SCALAR keys present as columns. Nested keys + types NOT enforced
    (CSV is flat).
"""

from __future__ import annotations

import json

from ..adapter import (
    HarborTask,
    STANDARD_TEST_SH,
    answer_delivery_guidance,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import STRUCTURED_FORMAT_VERIFIER_PY
from . import register
from ._common import extract_prompt


_REPO = "nvidia/Nemotron-RL-Instruction-Following-Structured-Outputs-v2"
_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_SCHEMA_BYTES = 64 * 1024
_SUPPORTED = {"json", "yaml", "toml", "xml", "csv"}

# Per-format wording for where to write + how it's graded. Kept terse; the full
# prompt already embeds the response-format spec / schema.
_FORMAT_NOTE = {
    "json": (
        "Emit a JSON document that validates against the JSON Schema in the "
        "task. The verifier parses your answer (optionally unwrapping a ```json "
        "fence) and validates it with `jsonschema` Draft 2020-12."
    ),
    "yaml": (
        "Emit a YAML document representing data that conforms to the JSON "
        "Schema in the task. The verifier parses your YAML and validates the "
        "resulting structure with `jsonschema` Draft 2020-12 (date values are "
        "treated as strings)."
    ),
    "toml": (
        "Emit a TOML document representing data that conforms to the JSON "
        "Schema in the task. The verifier parses your TOML and validates the "
        "resulting structure with `jsonschema` Draft 2020-12 (date values are "
        "treated as strings)."
    ),
    "xml": (
        "Emit a single well-formed XML document representing data that follows "
        "the JSON Schema in the task. The verifier checks the answer is "
        "well-formed XML and that every top-level required field from the "
        "schema appears as an element (or attribute) in the document."
    ),
    "csv": (
        "Emit CSV data conforming to the schema: the first row must be column "
        "headers and at least one data row must follow (no markdown fencing). "
        "The verifier checks the CSV parses and that every top-level required "
        "scalar field from the schema appears as a column header."
    ),
}

_INSTRUCTION_HEADER_TMPL = (
    "You will produce a structured response. Write your final answer to "
    "`/app/answer.txt`.\n{note}\n\n---\n\n"
)

# Per-format `what=` phrasing for the answer-delivery guidance block.
_DELIVERY_WHAT = {
    "json": "your JSON document",
    "yaml": "your YAML document",
    "toml": "your TOML document",
    "xml": "your XML document",
    "csv": "your CSV data",
}


@register(_REPO)
def convert_structured_outputs_v2(row: dict, row_idx: int) -> HarborTask | None:
    schema_type = row.get("schema_type")
    if not isinstance(schema_type, str) or schema_type not in _SUPPORTED:
        # Unsupported / unknown schema_type -> skip (run.py counts it).
        return None

    schema_str = row.get("schema_str")
    if not isinstance(schema_str, str) or not schema_str.strip():
        return None
    if len(schema_str) > _MAX_SCHEMA_BYTES:
        return None
    try:
        schema = json.loads(schema_str)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(schema, dict):
        return None

    prompt = extract_prompt(row)

    note = _FORMAT_NOTE[schema_type]
    instruction = _INSTRUCTION_HEADER_TMPL.format(note=note) + prompt
    # Append the canonical terminal-agent delivery guidance LAST so it is never
    # truncated and the agent is told HOW to write /app/answer.txt (the path the
    # STRUCTURED_FORMAT_VERIFIER reads). Fixes the ~64% "answer.txt missing"
    # delivery bug where terminus-2 emitted its doc as chat instead of a file.
    instruction += answer_delivery_guidance(
        "/app/answer.txt", what=_DELIVERY_WHAT[schema_type]
    )

    task_id = task_id_for(
        "if-structured-v2",
        sanitize_text(prompt[:256], field_name="prompt-tail", max_len=256)
        + "|"
        + schema_type
        + "|"
        + str(row_idx),
    )

    # pyyaml needed for yaml rows; jsonschema for json/yaml/toml validation.
    # tomllib (toml), xml.etree (xml), csv (csv) are stdlib in py3.11.
    return HarborTask(
        task_id=task_id,
        instruction_md=instruction,
        dockerfile=render_dockerfile(
            base=_BASE_IMAGE,
            pip_packages=("jsonschema==4.23.0", "PyYAML==6.0.2"),
        ),
        test_sh=STANDARD_TEST_SH,
        verifier_py=STRUCTURED_FORMAT_VERIFIER_PY,
        verifier_data={"schema": schema, "schema_type": schema_type},
        metadata=render_metadata(
            source_dataset=_REPO,
            source_uuid=None,
            extra={
                "row_index": row_idx,
                "family": "structured_outputs_v2",
                "schema_type": schema_type,
                "schema_fields_count": row.get("schema_fields_count"),
            },
        ),
    )
