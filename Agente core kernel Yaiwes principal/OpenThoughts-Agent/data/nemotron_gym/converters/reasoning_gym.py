"""Convert nvidia/Nemotron-RL-ReasoningGym-v1.

Each row has a question and an answer; the upstream Reasoning Gym library
provides per-task scorers. The verifier tries to load `reasoning_gym` and
dispatch to its scorer keyed on metadata.source_dataset; falls back to
normalized exact-match.
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
from ..verifiers import REASONING_GYM_VERIFIER_PY
from . import register
from ._common import extract_prompt


_BASE_IMAGE = "python:3.11-slim-bookworm"
_INSTRUCTION_HEADER = (
    "You are solving a procedurally-generated reasoning task from Reasoning "
    "Gym. Read the problem below and write your final answer to "
    "`/app/answer.txt`. The verifier will try the upstream Reasoning Gym "
    "scorer first, then fall back to normalized exact-match.\n\n"
    "---\n\n"
)
_MAX_METADATA_BYTES = 32 * 1024


def _safe_metadata_passthrough(md: object) -> dict:
    """Filter metadata to only JSON-safe values, capped in size."""
    if not isinstance(md, dict):
        return {}
    out: dict = {}
    for k, v in md.items():
        if not isinstance(k, str):
            continue
        try:
            json.dumps(v, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError):
            continue
        out[k] = v
    encoded = json.dumps(out, ensure_ascii=False, allow_nan=False)
    if len(encoded) > _MAX_METADATA_BYTES:
        return {"source_dataset": out.get("source_dataset")}
    return out


@register("nvidia/Nemotron-RL-ReasoningGym-v1")
def convert_reasoning_gym(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    question = row.get("question")
    answer = row.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        return None
    answer = sanitize_text(answer, field_name="answer", max_len=8 * 1024)
    if isinstance(question, str):
        question = sanitize_text(question, field_name="question", max_len=32 * 1024)
    else:
        question = ""
    rg_md = _safe_metadata_passthrough(row.get("metadata"))
    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    task_id = task_id_for("reasoning-gym", (uuid or prompt[:128]) + "|" + answer)
    return HarborTask(
        task_id=task_id,
        instruction_md=_INSTRUCTION_HEADER + prompt,
        dockerfile=render_dockerfile(
            base=_BASE_IMAGE,
            # `reasoning-gym==0.1.20` pulls in `pycosat==0.6.6` and
            # `cellpylib==2.4.0` which are sdist-only on PyPI. pycosat is a C
            # extension and needs gcc + Python headers to build; without them
            # the sandbox build fails with "process pip install ... did not
            # complete successfully: exit code: 1" (100% infra failure in v1).
            apt_packages=("build-essential", "python3-dev"),
            pip_packages=("reasoning-gym==0.1.20",),
        ),
        test_sh=STANDARD_TEST_SH,
        verifier_py=REASONING_GYM_VERIFIER_PY,
        verifier_data={
            "question": question,
            "answer": answer,
            "metadata": rg_md,
        },
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-ReasoningGym-v1",
            source_uuid=uuid,
            extra={
                "row_index": row_idx,
                "family": "reasoning_gym",
                "rg_source_dataset": rg_md.get("source_dataset"),
            },
        ),
    )
