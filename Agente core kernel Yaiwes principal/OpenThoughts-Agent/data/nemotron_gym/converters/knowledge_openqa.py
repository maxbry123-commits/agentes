"""Convert nvidia/Nemotron-RL-knowledge-openqa.

Schema: ``expected_answers`` is a list of free-form reference answers (often a
single string, sometimes several acceptable paraphrases). The references range
from short factoids (a number, a single noun) to long propositions (legal
holdings, technical claims, multi-clause sentences).

The original converter used the ``normalized_text`` verifier, which only checks
``expected in got`` after stripping case/punctuation/articles. That works for
SQuAD-style short factoids but is structurally broken for paraphrasable
long-form answers: an agent that produces a semantically-correct paraphrase
will never substring-match the reference. Empirically this produced ~3% solve
rate on this dataset (vs. 55-70% on its MCQA siblings).

The v2 converter routes openqa through the ``llm_judge`` verifier (same
pattern as ``safety.py`` / ``adversarial.py`` / ``identity_following.py``) and
hands the reference answer(s) to the judge as the rubric, so semantically-
equivalent paraphrases score correctly.
"""

from __future__ import annotations

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
_INSTRUCTION_HEADER = (
    "You are answering an open-ended question. Write your concise final answer "
    "to `/app/response.txt`. An LLM judge will compare your response to the "
    "reference answer(s) and score for semantic equivalence (paraphrases and "
    "alternative phrasings are acceptable as long as the substantive answer "
    "matches).\n\n"
    "---\n\n"
)

_JUDGE_SYSTEM_PROMPT = (
    "You are an impartial grader for open-ended factual / short-answer "
    "questions. The reference answer(s) capture the substantive correct "
    "answer; the candidate response is correct if it expresses the same "
    "answer, even if phrased differently. Ignore stylistic differences, "
    "verbosity, hedging, and extra (non-contradictory) detail. Score 0.0 if "
    "the candidate contradicts or is missing the substantive answer, 1.0 if "
    "it conveys the same answer as any reference. Provide your final score "
    "in \\boxed{<score>} on the last line."
)

_JUDGE_PROMPT_TEMPLATE = (
    "Question:\n{instruction}\n\n"
    "Reference answer(s) (any one is acceptable):\n{rubric}\n\n"
    "Candidate response:\n{response}\n\n"
    "Score from 0.0 (substantively wrong or missing) to 1.0 (matches a "
    "reference answer semantically). End with \\boxed{{<score>}} on the last "
    "line."
)


@register("nvidia/Nemotron-RL-knowledge-openqa")
def convert_openqa(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    raw_expected = row.get("expected_answers")
    if isinstance(row.get("expected_answer"), str):
        raw_expected = [row["expected_answer"]]
    if not isinstance(raw_expected, list) or not raw_expected:
        return None
    expected: list[str] = []
    for i, v in enumerate(raw_expected):
        if isinstance(v, str) and v.strip():
            expected.append(
                sanitize_text(v, field_name=f"expected_answers[{i}]", max_len=8 * 1024)
            )
    if not expected:
        return None
    # Format the reference answers as a numbered list so the judge sees each
    # acceptable alternative cleanly. Pack them into the `rubric` slot (matching
    # the existing `_format_rubric` helper in llm_judge.py: list of
    # {id, criteria} dicts) so the default template formatter renders them
    # uniformly.
    rubric = [{"id": f"ref{i + 1}", "criteria": e} for i, e in enumerate(expected)]
    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    task_id = task_id_for(
        "openqa",
        (uuid or prompt[:128]) + "|" + "||".join(expected[:3]),
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
        verifier_data={
            "instruction": prompt,
            "rubric": rubric,
            "judge_system_prompt": _JUDGE_SYSTEM_PROMPT,
            "judge_prompt_template": _JUDGE_PROMPT_TEMPLATE,
            "expected_answers": expected,  # retained for trace-side inspection
            "score_threshold": 0.5,
        },
        task_toml=LLM_JUDGE_TASK_TOML,
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-knowledge-openqa",
            source_uuid=uuid,
            extra={
                "row_index": row_idx,
                "family": "llm_judge_openqa",
                "judge": "litellm:default(openai/gpt-4o-mini)",
                "n_reference_answers": len(expected),
            },
        ),
    )
