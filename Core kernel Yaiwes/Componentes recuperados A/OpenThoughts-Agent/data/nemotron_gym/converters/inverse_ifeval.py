"""Convert nvidia/Nemotron-RL-InverseIFEval-v1 → Harbor multi-criterion judge task.

"Inverse IFEval" = the prompt asks the model to follow UNUSUAL / counter-intuitive
formatting instructions that override its trained habits (e.g. "one continuous
string without spaces", "use '?|#' as the separator after every word", "write the
last word in uppercase and backwards").

Verified schema (2026-06, split `train`, 1000 rows):
  - `responses_create_params.input` : the instruction message (use extract_prompt).
  - `llm_judge` : ALWAYS non-empty list of 3-10 per-criterion judge specs, each
        {uid, content, pass_criteria="YES", source="system", is_misalignment_check=False}.
        Each `content` is a self-contained grading prompt embedding the
        instruction, a Standard/Reference Response, and exactly ONE criterion,
        ending with "Answer YES if the criterion is fully met, NO if not."
  - `instructions` : ALWAYS empty ([]) — no deterministic ifeval constraints to
        enforce, so grading is purely via the llm_judge specs.

Grading (see verifiers/inverse_ifeval_judge.py):
  - One judge call per criterion → YES/NO verdict.
  - Aggregation: ALL criteria must match their `pass_criteria` ("YES") for
    reward == 1 (no partial credit). Every formatting constraint is a hard
    requirement, so all-or-nothing is the faithful aggregation.
  - Threshold: implicit — a single failed criterion short-circuits to reward 0.
"""

from __future__ import annotations

from ..adapter import (
    HarborTask,
    LLM_JUDGE_TASK_TOML,
    STANDARD_TEST_SH,
    answer_delivery_guidance,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import INVERSE_IFEVAL_JUDGE_VERIFIER_PY
from . import register
from ._common import extract_prompt

_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_CRITERION_BYTES = 24 * 1024
_MAX_CRITERIA = 12  # dataset max observed is 10
_INSTRUCTION_HEADER = (
    "You must follow the formatting instructions in the task below EXACTLY, "
    "even when they are unusual or counter-intuitive. Write your final response "
    "text to the file `/app/response.txt` inside the sandbox.\n\n"
    "Important guidance:\n"
    "  - Every formatting constraint is a hard requirement. A graded checklist "
    "of criteria will be applied; missing ANY single constraint scores 0.\n"
    "  - Write ONLY the requested response to `/app/response.txt` — no "
    "metacommentary, no explanations, no extra whitespace unless asked.\n"
    "  - To write the response from a shell, use a heredoc, e.g.:\n"
    "        cat > /app/response.txt <<'EOF'\n"
    "        <your full response text here>\n"
    "        EOF\n"
    "  - Verify with `cat /app/response.txt` before marking the task complete. "
    "An LLM judge will then check your response against each formatting "
    "criterion.\n\n"
    "---\n\n"
)


@register("nvidia/Nemotron-RL-InverseIFEval-v1")
def convert_inverse_ifeval(row: dict, row_idx: int) -> HarborTask | None:
    # Prompt: the instruction the agent must follow.
    try:
        prompt = extract_prompt(row)
    except Exception:
        return None
    if not prompt.strip():
        return None

    # Primary grader: the llm_judge spec list (always non-empty for this dataset).
    raw_judge = row.get("llm_judge")
    if not isinstance(raw_judge, list) or not raw_judge:
        return None

    criteria: list[dict] = []
    for entry in raw_judge:
        if not isinstance(entry, dict):
            continue
        content = entry.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        content = sanitize_text(
            content, field_name="llm_judge.content", max_len=_MAX_CRITERION_BYTES
        )
        pass_crit = entry.get("pass_criteria", "YES")
        pass_crit = str(pass_crit).strip().upper() if pass_crit is not None else "YES"
        if pass_crit not in ("YES", "NO"):
            pass_crit = "YES"
        uid = entry.get("uid")
        criteria.append(
            {
                "uid": uid if isinstance(uid, int) else len(criteria) + 1,
                "content": content,
                "pass_criteria": pass_crit,
            }
        )
        if len(criteria) >= _MAX_CRITERIA:
            break

    if not criteria:
        # No usable grader — skip.
        return None

    rid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    if rid is None and isinstance(row.get("id"), (str, int)):
        rid = str(row["id"])

    task_id = task_id_for(
        "inverse-ifeval",
        (rid or prompt[:128]) + "|" + str(len(criteria)) + "|" + str(row_idx),
    )

    # Delivery contract: terminus-2 emits its answer as a chat reply by default
    # and never writes the file, so ~34% of trials failed with "Agent response
    # not found at /app/response.txt". Append the canonical heredoc HOW-to-write
    # guidance AFTER the (already-sanitized) prompt so it can never be truncated
    # away, and point at the EXACT path the judge reads (/app/response.txt).
    instruction_md = (
        _INSTRUCTION_HEADER
        + prompt
        + answer_delivery_guidance("/app/response.txt", what="your full response")
    )

    return HarborTask(
        task_id=task_id,
        instruction_md=instruction_md,
        dockerfile=render_dockerfile(
            base=_BASE_IMAGE,
            pip_packages=("litellm==1.51.3",),
        ),
        test_sh=STANDARD_TEST_SH,
        verifier_py=INVERSE_IFEVAL_JUDGE_VERIFIER_PY,
        task_toml=LLM_JUDGE_TASK_TOML,
        verifier_data={
            "instruction": prompt,
            "criteria": criteria,
        },
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-InverseIFEval-v1",
            source_uuid=rid,
            extra={
                "row_index": row_idx,
                "family": "llm_judge_inverse_ifeval",
                "judge": "litellm:default(openai/gpt-4o-mini)",
                "aggregation": "all_criteria_must_pass",
                "n_criteria": len(criteria),
                "language": row.get("language")
                if isinstance(row.get("language"), str)
                else None,
                "agent_ref": (
                    row.get("agent_ref", {}).get("name")
                    if isinstance(row.get("agent_ref"), dict)
                    else None
                ),
            },
        ),
    )
