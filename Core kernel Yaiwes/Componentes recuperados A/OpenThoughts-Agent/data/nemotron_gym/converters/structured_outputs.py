"""Convert nvidia/Nemotron-RL-instruction_following-structured_outputs.

Schema:
  - responses_create_params.input : messages
  - schema_str : str (a JSON Schema document)
  - schema_type : "json"
  - schema_fields_count : str (decimal)

The agent must emit JSON validating against the schema. The verifier uses
`jsonschema` Draft 2020-12 validation.
"""

from __future__ import annotations

import json

from ..adapter import (
    HarborTask,
    STANDARD_TEST_SH,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import JSON_SCHEMA_VERIFIER_PY
from . import register
from ._common import extract_prompt


_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_SCHEMA_BYTES = 64 * 1024
_INSTRUCTION_HEADER = (
    "You will produce a JSON document that validates against the schema "
    "described below. Write your final JSON to `/app/answer.txt`. The "
    "verifier parses your answer (optionally unwrapping a ```json fence) "
    "and validates against the schema with `jsonschema` Draft 2020-12.\n\n"
    "---\n\n"
)


@register("nvidia/Nemotron-RL-instruction_following-structured_outputs")
def convert_structured_outputs(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    schema_str = row.get("schema_str")
    if not isinstance(schema_str, str) or not schema_str.strip():
        return None
    if len(schema_str) > _MAX_SCHEMA_BYTES:
        return None
    try:
        schema = json.loads(schema_str)
    except json.JSONDecodeError:
        return None
    if not isinstance(schema, dict):
        return None
    task_id = task_id_for(
        "if-structured",
        sanitize_text(prompt[:256], field_name="prompt-tail", max_len=256)
        + "|"
        + str(row_idx),
    )
    return HarborTask(
        task_id=task_id,
        instruction_md=_INSTRUCTION_HEADER + prompt,
        dockerfile=render_dockerfile(
            base=_BASE_IMAGE,
            pip_packages=("jsonschema==4.23.0",),
        ),
        test_sh=STANDARD_TEST_SH,
        verifier_py=JSON_SCHEMA_VERIFIER_PY,
        verifier_data={"schema": schema, "schema_type": "json"},
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-instruction_following-structured_outputs",
            source_uuid=None,
            extra={
                "row_index": row_idx,
                "family": "structured_outputs",
                "schema_fields_count": row.get("schema_fields_count"),
            },
        ),
    )
