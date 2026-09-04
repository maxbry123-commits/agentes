"""Convert instruction_following datasets (4 variants).

All four carry an `instruction_id_list` of constraint names + per-constraint
`kwargs`. The IFEval-style verifier dispatches on instruction IDs.

Datasets covered:
  - nvidia/Nemotron-RL-instruction_following
  - nvidia/Nemotron-RL-instruction_following-structured_outputs
  - nvidia/Nemotron-RL-Instruction-Following-Calendar-v2
  - nvidia/Nemotron-RL-Instruction-Following-Adversarial-v1
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
from ..verifiers import IFEVAL_VERIFIER_PY
from . import register
from ._common import extract_prompt


_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_KWARGS_BYTES = 64 * 1024
_INSTRUCTION_HEADER = (
    "You are running in a shell-based sandbox. Read the instruction below and "
    "write your final, complete answer text to the file `/app/answer.txt`. "
    "The verifier reads ONLY `/app/answer.txt` — anything you print to the "
    "terminal or describe in chat is ignored. Your answer.txt must be the "
    "raw answer prose itself (not a wrapper, not a summary, not commentary), "
    "satisfying every formal constraint in the instruction (paragraph count, "
    "forbidden words, letter frequency, formatting markers, ...).\n\n"
    "Example of how to save your answer (run this in the shell after composing "
    "your response):\n\n"
    "```sh\n"
    "cat > /app/answer.txt <<'EOF'\n"
    "<your full answer text here>\n"
    "EOF\n"
    "```\n\n"
    "Verify the file exists and contains your answer with `cat /app/answer.txt` "
    "before finishing. If `/app/answer.txt` is missing or empty the task fails.\n\n"
    "---\n\n"
)


def _sanitize_kwargs(kwargs: object, *, field_name: str) -> list[dict]:
    """Coerce kwargs to a list of dicts of JSON-safe values.

    The Nemotron-Gym schema is `kwargs: list[dict | None]`. We:
      - reject anything that isn't a list
      - replace None entries with {}
      - drop non-JSON-serializable inner values
      - cap the JSON-encoded byte length
    """
    if not isinstance(kwargs, list):
        return []
    out: list[dict] = []
    for i, kw in enumerate(kwargs):
        if kw is None:
            out.append({})
            continue
        if not isinstance(kw, dict):
            out.append({})
            continue
        clean: dict = {}
        for k, v in kw.items():
            if not isinstance(k, str):
                continue
            try:
                json.dumps(v, ensure_ascii=False, allow_nan=False)
            except (TypeError, ValueError):
                continue
            clean[k] = v
        out.append(clean)
    encoded = json.dumps(out, ensure_ascii=False, allow_nan=False)
    if len(encoded) > _MAX_KWARGS_BYTES:
        raise ValueError(f"{field_name}: kwargs JSON too large ({len(encoded)} bytes)")
    return out


def _convert(row: dict, source_dataset: str, *, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    instructions = row.get("instruction_id_list")
    if not isinstance(instructions, list) or not instructions:
        return None
    san_instructions: list[str] = []
    for i, inst in enumerate(instructions):
        if not isinstance(inst, str):
            return None
        san_instructions.append(
            sanitize_text(inst, field_name=f"instruction_id_list[{i}]", max_len=256)
        )
    kwargs_list = _sanitize_kwargs(row.get("kwargs"), field_name="kwargs")
    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    rid = row.get("id")
    task_id = task_id_for(
        source_dataset.split("/")[-1],
        (uuid or str(rid) or prompt[:128]) + "|" + "|".join(san_instructions),
    )
    return HarborTask(
        task_id=task_id,
        instruction_md=_INSTRUCTION_HEADER + prompt,
        dockerfile=render_dockerfile(base=_BASE_IMAGE),
        test_sh=STANDARD_TEST_SH,
        verifier_py=IFEVAL_VERIFIER_PY,
        verifier_data={
            "instruction_id_list": san_instructions,
            "kwargs": kwargs_list,
        },
        metadata=render_metadata(
            source_dataset=source_dataset,
            source_uuid=uuid,
            extra={"row_index": row_idx, "family": "instruction_following"},
        ),
    )


@register("nvidia/Nemotron-RL-instruction_following")
def convert_instruction_following(row: dict, row_idx: int) -> HarborTask | None:
    return _convert(row, "nvidia/Nemotron-RL-instruction_following", row_idx=row_idx)


# Sibling datasets with materially different schemas live in dedicated modules:
#   - structured_outputs.py for `instruction_following-structured_outputs`
#     (JSON-schema validation)
#   - agent_calendar.py reused for `Instruction-Following-Calendar-v2`
#     (same exp_cal_state shape)
#   - Adversarial-v1 requires an LLM judge (rubric + judge_prompt_template);
#     intentionally not converted.
