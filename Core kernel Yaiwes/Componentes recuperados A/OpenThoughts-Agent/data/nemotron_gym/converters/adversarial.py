"""Convert nvidia/Nemotron-RL-Instruction-Following-Adversarial-v1 → LLM-judge.

Actual schema: `responses_create_params` (prompt), `rubric` (list of
{id, criteria}), `reference_response`, `judge_prompt_template`,
`judge_system_prompt`. Each task carries a hand-authored judge prompt template;
we pass it through verbatim, with placeholders {instruction}, {response},
{rubric} resolved at runtime.
"""

from __future__ import annotations

import json

from ..adapter import (
    HarborTask,
    LLM_JUDGE_TASK_TOML,
    STANDARD_TEST_SH,
    SanitizationError,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import LLM_JUDGE_VERIFIER_PY
from . import register
from ._common import extract_prompt


_BASE_IMAGE = "python:3.11-slim-bookworm"
_INSTRUCTION_HEADER = (
    "Follow the (possibly adversarial) instruction below. Write your final "
    "response to `/app/response.txt`. An LLM judge will score your response "
    "against the rubric extracted from the upstream task.\n\n"
    "---\n\n"
)
_MAX_TEMPLATE_BYTES = 32 * 1024
_MAX_RUBRIC_ITEMS = 50


def _sanitize_rubric(rubric: object) -> list[dict]:
    if not isinstance(rubric, list):
        return []
    out: list[dict] = []
    for i, item in enumerate(rubric[:_MAX_RUBRIC_ITEMS]):
        if not isinstance(item, dict):
            continue
        rid = item.get("id")
        crit = item.get("criteria")
        if not isinstance(rid, str) or not isinstance(crit, str):
            continue
        out.append(
            {
                "id": sanitize_text(rid, field_name=f"rubric[{i}].id", max_len=64),
                "criteria": sanitize_text(
                    crit, field_name=f"rubric[{i}].criteria", max_len=4 * 1024
                ),
            }
        )
    return out


@register("nvidia/Nemotron-RL-Instruction-Following-Adversarial-v1")
def convert_adversarial(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    rubric = _sanitize_rubric(row.get("rubric"))
    if not rubric:
        return None
    template = row.get("judge_prompt_template")
    if isinstance(template, str) and 0 < len(template) <= _MAX_TEMPLATE_BYTES:
        try:
            template = sanitize_text(
                template,
                field_name="judge_prompt_template",
                max_len=_MAX_TEMPLATE_BYTES,
            )
        except SanitizationError:
            template = None
    else:
        template = None
    system_prompt = row.get("judge_system_prompt")
    if isinstance(system_prompt, str) and 0 < len(system_prompt) <= _MAX_TEMPLATE_BYTES:
        try:
            system_prompt = sanitize_text(
                system_prompt,
                field_name="judge_system_prompt",
                max_len=_MAX_TEMPLATE_BYTES,
            )
        except SanitizationError:
            system_prompt = None
    else:
        system_prompt = None
    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    tid = row.get("task_id")
    verifier_data = {
        "instruction": prompt,
        "rubric": rubric,
        "score_threshold": 0.5,
    }
    if template is not None:
        verifier_data["judge_prompt_template"] = template
    if system_prompt is not None:
        verifier_data["judge_system_prompt"] = system_prompt
    task_id = task_id_for(
        "adversarial",
        (uuid or str(tid) or prompt[:128])
        + "|"
        + json.dumps([r["id"] for r in rubric]),
    )
    return HarborTask(
        task_id=task_id,
        instruction_md=_INSTRUCTION_HEADER + prompt,
        dockerfile=render_dockerfile(
            base=_BASE_IMAGE,
            pip_packages=("litellm==1.51.3",),
        ),
        test_sh=STANDARD_TEST_SH,
        verifier_py=LLM_JUDGE_VERIFIER_PY,
        verifier_data=verifier_data,
        task_toml=LLM_JUDGE_TASK_TOML,
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-Instruction-Following-Adversarial-v1",
            source_uuid=uuid,
            extra={
                "row_index": row_idx,
                "family": "llm_judge_adversarial",
                "judge": "litellm:default(openai/gpt-4o-mini)",
                "n_rubric_items": len(rubric),
            },
        ),
    )
