"""Convert nvidia/Nemotron-RL-QA-Abstention-v1.

Short-factoid QA with an abstention protocol. Every row carries:
  - question (str)  : the question.
  - answer (str)    : the GOLD answer.
  - responses_create_params.input : a [system, user] message pair. The single
    (dataset-wide constant) system prompt instructs the model to answer with
    JUST the answer in ``\boxed{...}``, and to output ``\boxed{[IDK]}`` instead
    of guessing when it does not know.

ABSTENTION SEMANTICS — determined empirically from the data (all 3150 rows):
  * Every row has a real, non-empty gold answer.
  * No gold is empty / null / an "[IDK]"/"unknown"-like token.
Therefore this is an ALL-ANSWERABLE dataset: the correct behavior on every row
is to PRODUCE THE BOXED GOLD, never to abstain. The ``[IDK]`` token exists in
the protocol (the model is allowed to abstain to avoid being wrong) but the
dataset never makes abstention the rewarded action. Grading is therefore
boxed-answer-matches-gold (normalized text equality).

The converter still detects an IDK-like / empty gold defensively: if such a row
ever appears (schema drift), it is encoded so that boxing the abstention token
scores 1 (``abstention_token`` set in verifier_data). On the current snapshot
this branch is never taken.

Grading is SELF-CONTAINED (QA_BOXED_MATCH_VERIFIER_PY) — no LLM/network. The
answers are short factoids (publishers, years, percentages, single nouns), so
normalized string comparison (lowercase, drop thousands-separators, strip
punctuation + articles, collapse whitespace) plus a contiguous token-subsequence
fallback in either direction grades them well without going so loose that
unrelated answers pass.
"""

from __future__ import annotations

from ..adapter import (
    HarborTask,
    STANDARD_TEST_SH,
    answer_delivery_guidance,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import QA_BOXED_MATCH_VERIFIER_PY
from . import register
from ._common import extract_prompt


_SOURCE = "nvidia/Nemotron-RL-QA-Abstention-v1"
_BASE_IMAGE = "python:3.11-slim-bookworm"
_ABSTENTION_TOKEN = "[IDK]"

_INSTRUCTION_HEADER = (
    "You will be given a question. Answer with JUST the answer (no explanation).\n\n"
    "Write your final answer to the path `/app/answer.txt` in `\\boxed{<answer>}` "
    "format (the verifier extracts the last `\\boxed{...}` it finds).\n\n"
    "If you do not know the answer, or you need more context or tools to answer "
    "it, write `\\boxed{[IDK]}` instead of guessing — it is better to abstain "
    "than to be wrong. (Note: every question in this set has a knowable answer, "
    "so abstaining will not earn credit; the option exists so you are not forced "
    "to guess.)\n\n"
    "---\n\n"
)

# Golds that would mean "the correct behavior is to abstain" (defensive — not
# present in the current snapshot).
_IDK_LIKE = {
    "",
    "idk",
    "[idk]",
    "i don't know",
    "i dont know",
    "unknown",
    "n/a",
    "none",
    "null",
    "unanswerable",
}


@register(_SOURCE)
def convert_qa_abstention(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    answer = row.get("answer")
    if not isinstance(answer, str):
        return None
    answer = answer.strip()

    is_abstain = answer.lower() in _IDK_LIKE
    if is_abstain:
        # Schema-drift branch: reward boxing the abstention token.
        expected = _ABSTENTION_TOKEN
        abstention_token = _ABSTENTION_TOKEN
    else:
        expected = sanitize_text(answer, field_name="answer", max_len=8 * 1024)
        abstention_token = None
    if not expected:
        return None

    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    task_id = task_id_for(
        "qa-abstention",
        (uuid or prompt[:128]) + "||" + expected,
    )
    instruction_md = (
        _INSTRUCTION_HEADER
        + prompt
        + answer_delivery_guidance(
            "/app/answer.txt", what="your answer in \\boxed{...} form"
        )
    )
    return HarborTask(
        task_id=task_id,
        instruction_md=instruction_md,
        dockerfile=render_dockerfile(base=_BASE_IMAGE),
        test_sh=STANDARD_TEST_SH,
        verifier_py=QA_BOXED_MATCH_VERIFIER_PY,
        verifier_data={
            "expected_answer": expected,
            "abstention_token": abstention_token,
        },
        metadata=render_metadata(
            source_dataset=_SOURCE,
            source_uuid=uuid,
            extra={
                "row_index": row_idx,
                "family": "qa_boxed_match",
                "domain": row.get("domain")
                if isinstance(row.get("domain"), str)
                else None,
                "answerable": not is_abstain,
            },
        ),
    )
