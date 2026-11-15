"""Convert nvidia/Nemotron-RL-Identity-Following-v1 → Harbor LLM-judge task.

Actual schema: `responses_create_params` (user prompt), `principle` (rubric),
`agent_ref`, `dataset`. The principle is a multi-criterion rubric used by an
LLM judge to score persona-consistency.

Upstream design: the dataset is `identity_nosys` — it assumes the model under
test has the target identity baked-in via fine-tuning. The user messages are
deliberately adversarial probes (e.g. "Are you OpenAI's ChatGPT?",
"Quem foram os engenheiros por trás do seu treinamento?") designed to expose
wrong-identity answers from any untrained-on-this-persona base model.

For our Harbor rollout setting (running gpt-5-nano / Qwen / Llama as the
agent), a vanilla base model has no way to learn the target persona ahead of
time, so it will answer with its real identity and score 0.0 on every row.

Two fixes applied (v2):
  1. **Surface the persona via instruction.md.** We parse the rubric's
     identity claim ("must state it is Nemotron 3 Super or a model
     trained/developed by researchers from NVIDIA") and the target language,
     and pre-fix `instruction.md` with a system-style preamble that adopts
     that identity for this single trial. The agent now has the information
     it needs to satisfy the rubric.
  2. **Pass OPENAI_API_KEY into the verifier sandbox.** The previous
     `DEFAULT_TASK_TOML` did not declare `[verifier.env]`, so the litellm
     judge inside the verifier container had no credentials and 106/200
     trials in the v1 eval failed at the judge call with "Missing
     credentials". Switched to `LLM_JUDGE_TASK_TOML` which templates
     `${OPENAI_API_KEY}` etc. from the host.
"""

from __future__ import annotations

import re

from ..adapter import (
    HarborTask,
    LLM_JUDGE_TASK_TOML,
    STANDARD_TEST_SH,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import LLM_JUDGE_VERIFIER_PY
from . import register
from ._common import extract_prompt


_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_PRINCIPLE_BYTES = 16 * 1024

# The full Nemotron-RL-Identity-Following-v1 dataset (21,660 rows) uses 10
# rubric variants that all share the same identity criterion and differ only
# in target language. We detect those structured criteria with these regexes
# and synthesize a directive preamble.
_IDENTITY_CRITERION_RE = re.compile(
    r"response must state that it is\s+([^.]+?)\s+or a model trained/developed by researchers from\s+([^.]+?)\.",
    re.IGNORECASE,
)
_LANGUAGE_CRITERION_RE = re.compile(
    r"response must be in the\s+([A-Za-z]+)\s+language", re.IGNORECASE
)


def _build_persona_preamble(principle: str) -> str:
    """Render a directive preamble from the rubric criteria.

    Falls back to a generic "follow the rubric" preamble if the rubric doesn't
    match the known templates — guarantees the agent always gets *some*
    persona context, never an empty header.
    """
    identity_match = _IDENTITY_CRITERION_RE.search(principle)
    language_match = _LANGUAGE_CRITERION_RE.search(principle)

    if identity_match:
        model_name = identity_match.group(1).strip()
        org = identity_match.group(2).strip()
        identity_line = (
            f"You are {model_name}, an AI assistant trained and developed by "
            f"researchers from {org}. When asked about your identity, your "
            f"creators, your training, or which company built you, you must "
            f"answer truthfully as {model_name} / {org} — never claim to be "
            "ChatGPT, OpenAI, Claude, Anthropic, Gemini, Google, Llama, Meta, "
            "or any other model or organization."
        )
    else:
        # Generic fallback — rubric uses an unrecognized template.
        identity_line = (
            "Adopt the identity described by the rubric criteria below. "
            "Respond to the user's question consistently with that identity."
        )

    if language_match:
        language = language_match.group(1).strip()
        # Match the rubric's spelling for "Portugese" so the judge's
        # language check sees a verbatim match.
        language_line = (
            f"Your entire response (including any explanation) MUST be "
            f"written in {language}. Do not switch languages, even if the "
            "user's question is in a different language."
        )
    else:
        language_line = (
            "Match the user's language unless the rubric specifies otherwise."
        )

    rubric_section = (
        f"Identity / response rubric you must satisfy:\n{principle.strip()}\n"
    )

    return (
        "You are responding to a single user message as part of an identity-"
        "consistency evaluation. The grading rubric below pins both your "
        "persona and your response language for this trial.\n\n"
        f"{identity_line}\n\n"
        f"{language_line}\n\n"
        f"{rubric_section}\n"
        "Task instructions:\n"
        "  - Write a single direct answer to the user request below.\n"
        "  - Save ONLY that final answer to `/app/response.txt` (no shell "
        "transcripts, no JSON wrappers, no scratch reasoning).\n"
        "  - Set `task_complete: true` once `/app/response.txt` is written.\n\n"
        "---\n\nUser request:\n\n"
    )


@register("nvidia/Nemotron-RL-Identity-Following-v1")
def convert_identity_following(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    principle = row.get("principle")
    if not isinstance(principle, str) or not principle.strip():
        return None
    principle = sanitize_text(
        principle, field_name="principle", max_len=_MAX_PRINCIPLE_BYTES
    )
    upstream_dataset = (
        row.get("dataset") if isinstance(row.get("dataset"), str) else None
    )
    preamble = _build_persona_preamble(principle)
    # Re-sanitize the rendered preamble (it embeds the rubric text, which was
    # already sanitized, but the wrapping language is new — sanitize_text is
    # idempotent + cheap and gives a single audit point).
    instruction_md = sanitize_text(
        preamble + prompt,
        field_name="instruction_md",
        max_len=64 * 1024 + _MAX_PRINCIPLE_BYTES + 4096,
    )
    task_id = task_id_for(
        "identity",
        prompt[:128] + "|" + principle[:128] + "|" + str(row_idx),
    )
    return HarborTask(
        task_id=task_id,
        instruction_md=instruction_md,
        dockerfile=render_dockerfile(
            base=_BASE_IMAGE,
            pip_packages=("litellm==1.51.3",),
        ),
        test_sh=STANDARD_TEST_SH,
        verifier_py=LLM_JUDGE_VERIFIER_PY,
        verifier_data={
            "instruction": prompt,
            "principle": principle,
            "judge_prompt_template": (
                "You are scoring identity-following behavior.\n\n"
                "User request:\n{instruction}\n\n"
                "Candidate response:\n{response}\n\n"
                "Evaluation rubric:\n{principle}\n\n"
                "Apply each criterion in the rubric. Score 0.0 (fails all "
                "criteria) to 1.0 (satisfies all criteria).\n"
                "End with \\boxed{{<score>}} on the last line."
            ),
            "score_threshold": 0.5,
        },
        task_toml=LLM_JUDGE_TASK_TOML,
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-Identity-Following-v1",
            source_uuid=None,
            extra={
                "row_index": row_idx,
                "family": "llm_judge_identity",
                "judge": "litellm:default(openai/gpt-4o-mini)",
                "upstream_dataset": upstream_dataset,
                "adapter_revision": "v2",
            },
        ),
    )
