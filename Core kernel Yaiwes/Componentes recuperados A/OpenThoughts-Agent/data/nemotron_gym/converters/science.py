"""Convert nvidia/Nemotron-RL-Science-v1 → Harbor equivalence-LLM-judge task.

Schema (split `so_openq`, verified 2026-06):
  - problem (str)                : the open-ended science question.
  - expected_answer (str)        : the reference (gold) answer, often a paragraph.
  - responses_create_params(dict): `.input` chat messages; the prompt instructs
                                    the model to put its final answer in
                                    \\boxed{...}. Extracted via `extract_prompt`.
  - template_metadata (dict)     : `output_regex` for the \\boxed{...} answer.
  - verifier_type (str)          : 'equivalence_llm_judge'.
  - question_type='open', metadata{topic,subtopic,...}, uuid, used_in, license.

Grading strategy: these are open-ended science answers with a known *reference*
answer but no canonical surface form — deterministic string match would
spuriously fail equivalent paraphrases / different-but-correct derivations.
So we grade by EQUIVALENCE via an LLM judge: the verifier extracts the agent's
\\boxed{...} final answer and asks an OpenAI judge (gpt-4o-mini) whether it is
scientifically equivalent to `expected_answer`. The judge returns a boxed score
in [0,1]; score >= threshold (0.5) -> reward 1, else 0.

OPENAI_API_KEY is propagated into the verifier container via LLM_JUDGE_TASK_TOML.
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
from ..verifiers import EQUIVALENCE_JUDGE_VERIFIER_PY
from . import register
from ._common import extract_prompt


_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_ANSWER_BYTES = 32 * 1024

_INSTRUCTION_HEADER = (
    "You are answering an open-ended science question. Work through it and "
    "write your full answer to the file `/app/response.txt` inside the "
    "sandbox. Put your FINAL answer at the end of the response, enclosed in "
    "`\\boxed{...}` exactly as the question instructs — a grader will extract "
    "the boxed answer and compare it for scientific equivalence against a "
    "reference answer.\n\n"
    "To write the response from a shell, use a heredoc, e.g.:\n"
    "    cat > /app/response.txt <<'EOF'\n"
    "    <your full answer, ending with \\boxed{<final answer>}>\n"
    "    EOF\n"
    "Verify with `cat /app/response.txt` before completing. An empty or "
    "missing file scores 0.\n\n"
    "---\n\n"
)

_JUDGE_TEMPLATE = (
    "You are grading an open-ended science question by equivalence to a "
    "reference answer.\n\n"
    "Question:\n{instruction}\n\n"
    "Reference answer (gold):\n{reference_answer}\n\n"
    "Candidate answer (to grade):\n{candidate}\n\n"
    "Decide whether the candidate answer is scientifically equivalent to the "
    "reference answer — i.e. it conveys the same correct core "
    "explanation/result, even if phrased differently, more or less verbose, or "
    "using different but equivalent notation. It is NOT equivalent if it states "
    "a wrong mechanism, a wrong result, contradicts the reference, or omits the "
    "key point. Output 1.0 if equivalent (correct), 0.0 if not. Use an "
    "intermediate value only if partially correct.\n"
    "End with \\boxed{{<score>}} on the last line."
)


@register("nvidia/Nemotron-RL-Science-v1")
def convert_science(row: dict, row_idx: int) -> HarborTask | None:
    # Prompt: prefer the dataset's responses_create_params.input (carries the
    # explicit \boxed{} instruction); extract_prompt handles that shape.
    try:
        prompt = extract_prompt(row)
    except Exception:
        return None

    expected = row.get("expected_answer")
    if not isinstance(expected, str) or not expected.strip():
        return None
    expected = sanitize_text(
        expected, field_name="expected_answer", max_len=_MAX_ANSWER_BYTES
    )

    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    topic = meta.get("topic") if isinstance(meta.get("topic"), str) else None
    subtopic = meta.get("subtopic") if isinstance(meta.get("subtopic"), str) else None

    task_id = task_id_for(
        "science",
        (uuid or prompt[:128]) + "|" + expected[:128] + "|" + str(row_idx),
    )

    return HarborTask(
        task_id=task_id,
        instruction_md=_INSTRUCTION_HEADER + prompt,
        dockerfile=render_dockerfile(
            base=_BASE_IMAGE,
            pip_packages=("litellm==1.51.3",),
        ),
        test_sh=STANDARD_TEST_SH,
        verifier_py=EQUIVALENCE_JUDGE_VERIFIER_PY,
        verifier_data={
            "instruction": prompt,
            "reference_answer": expected,
            "judge_prompt_template": _JUDGE_TEMPLATE,
            "score_threshold": 0.5,
        },
        task_toml=LLM_JUDGE_TASK_TOML,
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-Science-v1",
            source_uuid=uuid,
            extra={
                "row_index": row_idx,
                "family": "equivalence_llm_judge_science",
                "judge": "litellm:default(openai/gpt-4o-mini)",
                "topic": topic,
                "subtopic": subtopic,
                "question_type": row.get("question_type"),
                "split": "so_openq",
            },
        ),
    )
