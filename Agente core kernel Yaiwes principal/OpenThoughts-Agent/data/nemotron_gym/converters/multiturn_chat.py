"""Convert nvidia/Nemotron-RL-Instruction-Following-MultiTurnChat-v1 → Harbor
multi-criterion rubric judge task.

This is the MultiChallenge-style instruction-following benchmark: each row is a
multi-turn conversation (system prompt + several user/assistant turns) that
ENDS on a user turn, and the agent's job is to produce the FINAL assistant
response that satisfies a rubric. Grading is inherently subjective
(tone/structure/instruction-retention checks), so we use an LLM judge — one
call per rubric criterion.

Verified schema (2026-06, split `train`, 2011 rows):
  - `responses_create_params.input` : the multi-turn conversation as a list of
        {role, content} messages (system/user/assistant), ALWAYS ending on a
        `user` turn (the agent answers it).
  - `context` : a flattened transcript ([SYSTEM]/[USER]/[ASSISTANT] ...) of the
        same conversation. We use THIS as the instruction body + judge context —
        it's a clean human-readable rendering of the full multi-turn dialogue.
  - `rubric` : ALWAYS non-empty list (sizes 1/2/4/5/6) of grading criteria, each
        {question, pass_criteria}. `pass_criteria` is mostly "YES" (5128) but
        sometimes "NO" (150 criteria across 57 rows) — a NO criterion checks a
        constraint the model should NOT do (e.g. "Did it overwrite the
        three-sentence constraint?" → pass_criteria=NO). Honored generically.
  - `metadata` : topic / sub-topic / challenge / persona / turns; provenance.

Grading (see verifiers/multiturn_rubric_judge.py):
  - One judge call per criterion. The judge sees the full conversation, the
    agent's final response, and the single criterion question → YES/NO.
  - Aggregation: ALL criteria must match their `pass_criteria` for reward == 1
    (no partial credit); one mismatch short-circuits to reward 0. This mirrors
    the all-or-nothing nature of instruction-following constraints.

We did NOT reuse INVERSE_IFEVAL_JUDGE_VERIFIER_PY: that verifier assumes each
criterion's `content` is a fully self-contained grading prompt that already
embeds the instruction + reference answer. Here each criterion is only a short
question, so the verifier itself must supply the conversation transcript +
candidate response to the judge — hence the dedicated multiturn_rubric_judge.
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
from ..verifiers import MULTITURN_RUBRIC_JUDGE_VERIFIER_PY
from . import register
from ._common import extract_prompt

_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_CONVERSATION_BYTES = (
    160 * 1024
)  # largest observed context ≈ 142KB; global cap is 256KB
_MAX_QUESTION_BYTES = 8 * 1024
_MAX_CRITERIA = 12  # dataset max observed is 6
_INSTRUCTION_HEADER = (
    "Below is a multi-turn conversation between a user and an AI assistant "
    "(system prompt + alternating user/assistant turns). The conversation ENDS "
    "on a user message. Your job is to write the assistant's FINAL response — "
    "the answer to that last user message — to the file `/app/response.txt` "
    "inside the sandbox.\n\n"
    "Important guidance:\n"
    "  - Stay in character and obey ALL instructions established anywhere in the "
    "conversation (the system prompt and every earlier turn), not just the last "
    "message. Persistent / first-turn formatting and behavioral instructions "
    "still apply.\n"
    "  - A graded checklist of rubric criteria will be applied to your final "
    "response, evaluated in the context of the full dialogue. Every criterion is "
    "a hard requirement; failing ANY single criterion scores 0.\n"
    "  - Write ONLY the assistant's final response to `/app/response.txt` — no "
    "metacommentary, no role labels, no restating of the conversation.\n"
    "  - To write the response from a shell, use a heredoc, e.g.:\n"
    "        cat > /app/response.txt <<'EOF'\n"
    "        <your full final assistant response here>\n"
    "        EOF\n"
    "  - Verify with `cat /app/response.txt` before marking the task complete. "
    "An LLM judge will then check your response against each rubric criterion.\n\n"
    "---\n\n"
)


@register("nvidia/Nemotron-RL-Instruction-Following-MultiTurnChat-v1")
def convert_multiturn_chat(row: dict, row_idx: int) -> HarborTask | None:
    # Conversation context: prefer the pre-flattened `context` transcript (clean
    # [SYSTEM]/[USER]/[ASSISTANT] rendering); fall back to reconstructing it from
    # responses_create_params.input via extract_prompt.
    conversation = None
    ctx = row.get("context")
    if isinstance(ctx, str) and ctx.strip():
        conversation = sanitize_text(
            ctx, field_name="context", max_len=_MAX_CONVERSATION_BYTES
        )
    if conversation is None:
        try:
            conversation = extract_prompt(row)
        except Exception:
            return None
    if not conversation.strip():
        return None

    # Rubric: the per-criterion grading checklist (always non-empty).
    raw_rubric = row.get("rubric")
    if not isinstance(raw_rubric, list) or not raw_rubric:
        return None

    criteria: list[dict] = []
    for entry in raw_rubric:
        if not isinstance(entry, dict):
            continue
        question = entry.get("question")
        if not isinstance(question, str) or not question.strip():
            continue
        question = sanitize_text(
            question, field_name="rubric.question", max_len=_MAX_QUESTION_BYTES
        )
        pass_crit = entry.get("pass_criteria", "YES")
        pass_crit = str(pass_crit).strip().upper() if pass_crit is not None else "YES"
        if pass_crit not in ("YES", "NO"):
            pass_crit = "YES"
        criteria.append(
            {
                "uid": len(criteria) + 1,
                "question": question,
                "pass_criteria": pass_crit,
            }
        )
        if len(criteria) >= _MAX_CRITERIA:
            break

    if not criteria:
        return None

    rid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    if rid is None and isinstance(row.get("task_id"), (str, int)):
        rid = str(row["task_id"])

    task_id = task_id_for(
        "multiturn-chat",
        (rid or conversation[:128]) + "|" + str(len(criteria)) + "|" + str(row_idx),
    )

    md = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}

    # Canonical delivery guidance appended AFTER the (possibly large, possibly
    # truncated) transcript so the HOW-to-submit heredoc is never cut. This is
    # the proven fix for terminus-2 emitting the answer as chat and never
    # writing the file — the verifier reads /app/response.txt only.
    instruction_md = (
        _INSTRUCTION_HEADER
        + conversation
        + answer_delivery_guidance(
            "/app/response.txt", what="your final response in the conversation"
        )
    )

    return HarborTask(
        task_id=task_id,
        instruction_md=instruction_md,
        dockerfile=render_dockerfile(
            base=_BASE_IMAGE,
            pip_packages=("litellm==1.51.3",),
        ),
        test_sh=STANDARD_TEST_SH,
        verifier_py=MULTITURN_RUBRIC_JUDGE_VERIFIER_PY,
        task_toml=LLM_JUDGE_TASK_TOML,
        verifier_data={
            "conversation": conversation,
            "instruction": conversation,
            "criteria": criteria,
        },
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-Instruction-Following-MultiTurnChat-v1",
            source_uuid=rid,
            extra={
                "row_index": row_idx,
                "family": "llm_judge_multiturn_rubric",
                "judge": "litellm:default(openai/gpt-4o-mini)",
                "aggregation": "all_criteria_must_pass",
                "n_criteria": len(criteria),
                "topic": md.get("topic") if isinstance(md.get("topic"), str) else None,
                "challenge": md.get("challenge")
                if isinstance(md.get("challenge"), str)
                else None,
                "turns": md.get("turns")
                if isinstance(md.get("turns"), (str, int))
                else None,
                "agent_ref": (
                    row.get("agent_ref", {}).get("name")
                    if isinstance(row.get("agent_ref"), dict)
                    else None
                ),
                "pass_rate": row.get("pass_rate")
                if isinstance(row.get("pass_rate"), (int, float))
                else None,
            },
        ),
    )
