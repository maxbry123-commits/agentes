"""Convert nvidia/Nemotron-RL-agent-workplace_assistant.

CAVEAT: this dataset's upstream verifier is a stateful 26-tool / 5-database
agent environment that Harbor cannot reproduce. We convert to a *single-step
tool-call match* task: the agent emits a JSON `{name, arguments}` describing
the next tool call it would invoke; the verifier compares against the row's
`ground_truth` tool call(s).

This is lossy by design:
  - Multi-turn rollouts collapse to "first expected tool call"
  - Real tool-call side effects are not executed
  - "Equivalent but differently-keyed arguments" will mismatch
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
from ..verifiers import TOOL_CALL_VERIFIER_PY
from . import register
from ._common import extract_prompt


_BASE_IMAGE = "python:3.11-slim-bookworm"
_INSTRUCTION_HEADER = (
    "You are a workplace assistant agent. Read the conversation below. "
    "Decide what single tool you would invoke next, then write a JSON object "
    "to `/app/answer.txt` of the form:\n\n"
    '    {"name": "<tool_name>", "arguments": { ... }}\n\n'
    "The verifier compares your emitted name + arguments against the expected "
    "next-step call captured from the upstream environment.\n\n"
    "Note: this is a lossy single-step conversion of a multi-turn stateful "
    "task; do not assume side effects from prior steps persist.\n\n"
    "---\n\n"
)


def _coerce_expected(gt: object) -> list[dict] | None:
    if not isinstance(gt, list) or not gt:
        return None
    out: list[dict] = []
    for ec in gt:
        if not isinstance(ec, dict):
            continue
        name = ec.get("name")
        args = ec.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                continue
        if not isinstance(name, str) or not isinstance(args, dict):
            continue
        try:
            json.dumps(args, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError):
            continue
        out.append({"name": name, "arguments": args})
    return out or None


@register("nvidia/Nemotron-RL-agent-workplace_assistant")
def convert_agent_workplace(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    expected = _coerce_expected(row.get("ground_truth"))
    if expected is None:
        return None
    rid = row.get("id")
    cat = row.get("category") if isinstance(row.get("category"), str) else ""
    task_id = task_id_for(
        "agent-workplace",
        str(rid) + "|" + cat + "|" + json.dumps(expected[0], sort_keys=True),
    )
    instr = sanitize_text(
        _INSTRUCTION_HEADER + prompt, field_name="instruction", max_len=128 * 1024
    )
    return HarborTask(
        task_id=task_id,
        instruction_md=instr,
        dockerfile=render_dockerfile(base=_BASE_IMAGE),
        test_sh=STANDARD_TEST_SH,
        verifier_py=TOOL_CALL_VERIFIER_PY,
        verifier_data={"expected": expected},
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-agent-workplace_assistant",
            source_uuid=None,
            extra={
                "row_index": row_idx,
                "family": "agent_workplace",
                "category": cat,
                "n_expected_calls": len(expected),
                "conversion_lossy": True,
            },
        ),
    )
