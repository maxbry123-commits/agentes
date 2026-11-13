"""Convert nvidia/Nemotron-RL-coding-competitive_coding → Harbor tasks.

Schema (per inspection):
  - input: list of role/content messages
  - responses_create_params.unit_tests.inputs : list[str]
  - responses_create_params.unit_tests.outputs : list[str]
  - hash_id, dataset, source

Strategy: build a Harbor task whose verifier runs /app/solution.py against each
stdin/stdout test case (see verifiers/stdio_diff.py).

Limits enforced by adapter.sanitize_text() on each input/output string. We
additionally cap per-task test-case count to keep tarballs reasonable.
"""

from __future__ import annotations

from ..adapter import (
    HarborTask,
    STANDARD_TEST_SH,
    SanitizationError,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import STDIO_DIFF_VERIFIER_PY
from . import register
from ._common import extract_prompt


_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_TESTS_PER_TASK = 50
_MAX_TEST_BYTES = 64 * 1024


_INSTRUCTION_HEADER = (
    "You are solving a competitive programming problem. Read the problem below "
    "and write a Python 3 solution at `/app/solution.py`.\n\n"
    "The verifier will run `python3 /app/solution.py` once per test case, feeding "
    "each test's input on stdin and comparing your stdout against the expected "
    "output (trailing whitespace ignored). All test cases must match.\n\n"
    "---\n\n"
)


@register("nvidia/Nemotron-RL-coding-competitive_coding")
def convert_competitive_coding(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    # unit_tests live under `verifier_metadata` in the actual schema
    # (the dataset card's snippet showed them under responses_create_params,
    # but the parquet schema differs — verified by inspecting rev as of 2026-05).
    vm = row.get("verifier_metadata")
    unit_tests = vm.get("unit_tests") if isinstance(vm, dict) else None
    if not isinstance(unit_tests, dict):
        rcp = row.get("responses_create_params")
        if isinstance(rcp, dict):
            unit_tests = rcp.get("unit_tests")
    if not isinstance(unit_tests, dict):
        return None
    inputs = unit_tests.get("inputs", [])
    outputs = unit_tests.get("outputs", [])
    if not (isinstance(inputs, list) and isinstance(outputs, list)):
        return None
    if len(inputs) != len(outputs) or not inputs:
        return None
    inputs = inputs[:_MAX_TESTS_PER_TASK]
    outputs = outputs[:_MAX_TESTS_PER_TASK]
    san_inputs: list[str] = []
    san_outputs: list[str] = []
    for i, (inp, out) in enumerate(zip(inputs, outputs)):
        if not isinstance(inp, str) or not isinstance(out, str):
            raise SanitizationError(f"test {i}: non-string input/output")
        san_inputs.append(
            sanitize_text(inp, field_name=f"inputs[{i}]", max_len=_MAX_TEST_BYTES)
        )
        san_outputs.append(
            sanitize_text(out, field_name=f"outputs[{i}]", max_len=_MAX_TEST_BYTES)
        )
    instruction_md = _INSTRUCTION_HEADER + prompt
    dockerfile = render_dockerfile(base=_BASE_IMAGE)
    hid = row.get("hash_id") if isinstance(row.get("hash_id"), str) else None
    task_id = task_id_for("comp-coding", hid or (prompt[:128] + str(row_idx)))
    return HarborTask(
        task_id=task_id,
        instruction_md=instruction_md,
        dockerfile=dockerfile,
        test_sh=STANDARD_TEST_SH,
        verifier_py=STDIO_DIFF_VERIFIER_PY,
        verifier_data={"inputs": san_inputs, "outputs": san_outputs},
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-coding-competitive_coding",
            source_uuid=hid,
            extra={
                "row_index": row_idx,
                "family": "competitive_coding",
                "upstream_source": row.get("source"),
                "upstream_dataset": row.get("dataset"),
                "n_tests": len(san_inputs),
            },
        ),
    )
