"""Convert nvidia/Nemotron-RL-Multichallenge-v1 → Harbor multi-criterion judge task.

MultiChallenge is a MULTI-TURN, persona-driven instruction-following benchmark.
Each row is a conversation (a persona system prompt + several user/assistant
turns) whose `responses_create_params.input` ALWAYS ends on a `user` turn — i.e.
the agent under test must produce the FINAL assistant response, which is then
graded against a list of yes/no criteria.

Verified schema (2026-06, two configs `advanced` + `vanilla`, splits `train`):
  - `responses_create_params.input` : multi-turn transcript (system persona +
        user/assistant turns), final message is the user request to respond to.
        Use it via extract_prompt; the FULL transcript is preserved when it fits
        the 64KB cap, otherwise a system+last-user trim fallback recovers it.
  - `llm_judge` : ALWAYS non-empty list of per-criterion judge specs, each
        {uid, content, pass_criteria, source, is_misalignment_check}. Each
        `content` is a SELF-CONTAINED grading prompt that re-embeds the entire
        conversation up to (but not including) the model's final response, then
        asks "Does the model's final response satisfy this criterion?" with the
        criterion text and an "Expected answer: YES/NO" line.
        advanced: 4-6 criteria/row (avg 4.0); vanilla: 1-2 criteria/row.
        `pass_criteria` is USUALLY "YES" but NOT always — a minority are "NO"
        (151/4169 advanced, 8/1335 vanilla). The verifier honors each spec's
        own pass_criteria, so this is handled faithfully.
  - `instructions` : ALWAYS empty ([]) — no deterministic ifeval constraints;
        grading is purely via the llm_judge specs.

Both configs share this repo id and have an IDENTICAL shape, so a single
registered converter handles both — run.py routes the config via its --config
flag at load time, not via a row field.

Grading (reuses verifiers/inverse_ifeval_judge.py):
  - One judge call per criterion → YES/NO verdict.
  - The criterion `content` already embeds the conversation; the verifier appends
    the agent's response (from /app/response.txt) under a "## Model's Response"
    section before sending to the judge, so the judge sees exactly what it needs.
  - Aggregation: EVERY criterion must match its own `pass_criteria` for
    reward == 1 (no partial credit). A single mismatch short-circuits to 0.

Cap handling:
  - The criterion `content` re-embeds the whole transcript and the criterion
    question is at the END, so truncating it would silently drop the question.
    We therefore size the per-criterion cap at the adapter's 256KB hard limit
    rather than the small Inverse-IFEval cap, and skip a row only if a criterion
    is so large that even sanitize_text rejects it (none observed).
  - The instruction.md prompt is separately capped at 64KB by extract_prompt;
    on overflow we fall back to system + final user turn (SysBench pattern),
    recovering the row rather than dropping it. The judge grading does not depend
    on instruction.md (the criterion content carries the full context), so a
    trimmed instruction never weakens grading — it only affects what the agent
    sees while composing.
"""

from __future__ import annotations

from ..adapter import (
    HarborTask,
    LLM_JUDGE_TASK_TOML,
    STANDARD_TEST_SH,
    SanitizationError,
    answer_delivery_guidance,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import INVERSE_IFEVAL_JUDGE_VERIFIER_PY
from . import register
from ._common import PROMPT_MAX_LEN, extract_prompt

_SOURCE = "nvidia/Nemotron-RL-Multichallenge-v1"
_BASE_IMAGE = "python:3.11-slim-bookworm"
# The criterion content re-embeds the full conversation, with the actual
# criterion question at the very end — truncating it would drop the question.
# Use the adapter's 256KB hard cap so sanitize_text preserves the whole spec.
_MAX_CRITERION_BYTES = 256 * 1024
_MAX_CRITERIA = 16  # observed max is 6 (advanced); generous headroom.

_INSTRUCTION_HEADER = (
    "You are the assistant in the multi-turn conversation below. Read the FULL "
    "conversation, including the persona/system prompt and every prior turn, "
    "then write your next assistant response — the reply to the final user "
    "message — to the file `/app/response.txt` inside the sandbox.\n\n"
    "Important guidance:\n"
    "  - Stay in character per the persona/system prompt and honor EVERY "
    "instruction the user has given across ALL turns (including earlier turns "
    "the user may now be testing you on).\n"
    "  - A graded checklist of yes/no criteria will be applied to your final "
    "response by an LLM judge; ALL criteria must pass to score, so satisfy each "
    "stated and implied requirement.\n"
    "  - Write ONLY your assistant response to `/app/response.txt` — no "
    "metacommentary, no role labels, no explanation of what you did.\n"
    "  - To write the response from a shell, use a heredoc, e.g.:\n"
    "        cat > /app/response.txt <<'EOF'\n"
    "        <your full assistant response here>\n"
    "        EOF\n"
    "  - Verify with `cat /app/response.txt` before marking the task complete.\n\n"
    "---\n\n"
)


def _build_prompt(row: dict) -> str | None:
    """Extract the conversation prompt, with a trim fallback over the 64KB cap.

    Preferred: the full multi-turn transcript via extract_prompt (preserves the
    system persona + every prior turn). When that exceeds PROMPT_MAX_LEN it
    raises; for those long rows we fall back to system turn(s) + the final user
    turn, then to system-only, mirroring the SysBench recovery so the row is
    never dropped just for being long. Grading is unaffected because the judge
    criterion content carries the full conversation independently.
    """
    try:
        return extract_prompt(row)
    except SanitizationError:
        pass
    rcp = row.get("responses_create_params")
    msgs = rcp.get("input") if isinstance(rcp, dict) else None
    if not isinstance(msgs, list):
        return None
    sys_parts: list[str] = []
    last_user: str | None = None
    for m in msgs:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if not isinstance(content, str):
            continue
        if role == "system":
            sys_parts.append(f"[system]\n{content}")
        elif role == "user":
            last_user = content
    parts = sys_parts + ([f"[user]\n{last_user}"] if last_user else [])
    if not parts:
        return None
    joined = "\n\n".join(parts)
    try:
        return sanitize_text(joined, field_name="prompt", max_len=PROMPT_MAX_LEN)
    except SanitizationError:
        # Last resort: system rules only (and if THAT overflows, last user only).
        for fallback in ("\n\n".join(sys_parts), (last_user or "")):
            if not fallback:
                continue
            try:
                return sanitize_text(
                    fallback, field_name="prompt", max_len=PROMPT_MAX_LEN
                )
            except SanitizationError:
                continue
        return None


@register(_SOURCE)
def convert_multichallenge(row: dict, row_idx: int) -> HarborTask | None:
    prompt = _build_prompt(row)
    if not prompt or not prompt.strip():
        return None

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
        try:
            content = sanitize_text(
                content, field_name="llm_judge.content", max_len=_MAX_CRITERION_BYTES
            )
        except SanitizationError:
            # A criterion so large even the 256KB hard cap rejects it would lose
            # its trailing question if truncated, so skip just that criterion.
            continue
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
        return None

    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    rid = uuid
    if rid is None and isinstance(row.get("id"), (str, int)):
        rid = str(row["id"])

    task_id = task_id_for(
        "multichallenge",
        (rid or prompt[:128]) + "|" + str(len(criteria)) + "|" + str(row_idx),
    )

    return HarborTask(
        task_id=task_id,
        # Append the canonical delivery guidance AFTER the conversation context
        # (prompt), so the HOW-to-write-the-file heredoc is never lost to the
        # 64KB prompt truncation that can trim the middle/end of `prompt`.
        instruction_md=(
            _INSTRUCTION_HEADER
            + prompt
            + answer_delivery_guidance("/app/response.txt", what="your final response")
        ),
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
            source_dataset=_SOURCE,
            source_uuid=uuid,
            extra={
                "row_index": row_idx,
                "family": "llm_judge_multichallenge",
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
