"""Convert nvidia/Nemotron-RL-CFBench-v1 → Harbor HYBRID task.

CFBench (Complex / Constraint-Following Benchmark) rows mix two grading kinds:

  * `instructions` : IFEval-style structured constraints with inline kwargs and
    a relation vocabulary {"equal to","less than","more than","greater than",
    "at least","at most"}. Most are DETERMINISTIC.
  * `llm_judge`    : natural-language yes/no checks — SUBJECTIVE.

This converter produces a single HYBRID task graded by
`HYBRID_IFEVAL_JUDGE_VERIFIER_PY`, which runs the deterministic checks locally
AND an LLM judge over the subjective questions, combining them with the rule:

    reward = 1  iff  (all deterministic constraints pass)
                AND  (every judge question scores >= score_threshold)

Instruction-id routing
-----------------------
Each `instructions[*].instruction_id` is classified:

  * DET_IMPLEMENTED  — the hybrid verifier has a self-contained check. The raw
    constraint dict (instruction_id + inline kwargs) goes into
    `det_constraints`.
  * JUDGE_ROUTED     — inherently subjective (stylistic / situational /
    linguistic) OR ambiguous-unicode counting that a deterministic check cannot
    grade reliably across scripts. We DO NOT silently pass these: instead we
    render each into a natural-language yes/no question (via `_judge_question`)
    and append it to `judge_questions`, so the LLM judge grades it.

This keeps the brief's invariant: unsupported instruction_ids are never
silently treated as satisfied — they are either implemented deterministically
or explicitly checked by the judge.

Both degenerate cases are handled: a row with only `instructions` yields a
det-only / det+routed-judge task; a row with only `llm_judge` yields a
judge-only task.
"""

from __future__ import annotations

import json

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
from ..verifiers import HYBRID_IFEVAL_JUDGE_VERIFIER_PY
from . import register
from ._common import extract_prompt


_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_VDATA_BYTES = 256 * 1024
_SCORE_THRESHOLD = 0.7

# instruction_ids the hybrid verifier grades deterministically (must match the
# CONSTRAINTS dict in verifiers/hybrid_ifeval_judge.py).
DET_IMPLEMENTED = frozenset(
    {
        # length / counts
        "length_constraints:number_words",
        "length_constraints:number_characters",
        "length_constraints:unique_words",
        "length_constraints:word_repetition",
        "length_constraints:sentence_length",
        "length_constraints:word_length",
        "length_constraints:paragraph_length",
        "detectable_format:number_paragraphs",
        "detectable_format:sentence_count",
        "detectable_format:sentences_per_paragraph",
        "detectable_format:max_paragraph_length",
        # keywords
        "keywords:frequency",
        "keywords:word_count_different_numbers",
        "keywords:existence",
        "keywords:forbidden_words",
        "keywords:letter_frequency",
        "keywords:positioning",
        "keywords:palindrome_word",
        # startend
        "startend:end_checker",
        "startend:start_checker",
        "startend:wrap_checker",
        "startend:quotation",
        # detectable_format
        "detectable_format:title",
        "detectable_format:number_bullet_lists",
        "detectable_format:numbered_list",
        "detectable_format:multiple_sections",
        "detectable_format:table",
        "detectable_format:nested_list",
        "detectable_format:heading_depth",
        "detectable_format:json_format",
        # detectable_content
        "detectable_content:postscript",
        "detectable_content:number_placeholders",
        "detectable_content:numeric_inclusion",
        # punctuation
        "punctuation:no_comma",
        "punctuation:no_period",
        "punctuation:end_rule",
        "punctuation:question_exclaim",
        # change_case
        "change_case:lowercase",
        "change_case:all_caps",
        "change_case:first_letter_cap",
        "change_case:last_letter",
        "change_case:capital_word_frequency",
    }
)


# Human-readable phrasings for routing subjective / ambiguous instruction_ids
# into LLM-judge yes/no questions. `kw` is the inline constraint dict.
def _rel_phrase(kw: dict) -> str:
    rel = str(kw.get("relation", "")).strip()
    return rel or "exactly"


def _judge_question(iid: str, kw: dict) -> str:
    """Render a subjective/ambiguous instruction_id into a yes/no question."""
    g = kw.get
    # Tone / style / situation / linguistic families — describe the target.
    simple = {
        "stylistic:tone_formality": lambda: (
            f"Does the response use a {g('tone_level', 'formal')} tone?"
        ),
        "stylistic:voice": lambda: (
            f"Is the response written in the {g('voice_type', 'active')} voice?"
        ),
        "stylistic:literary_style": lambda: (
            f"Is the response written in a {g('style_type', '')} literary style?"
        ),
        "stylistic:sentence_tone_consistency": lambda: (
            f"Does the response maintain a consistent {g('tone_type', '')} tone across sentences?"
        ),
        "stylistic:emotional_tone": lambda: (
            f"Does the response convey a {g('emotion_type', '')} emotional tone?"
        ),
        "stylistic:politeness": lambda: (
            f"Does the response use a {g('politeness_degree', '')} level of politeness?"
        ),
        "stylistic:rhythm_pattern": lambda: (
            f"Does the response follow a {g('rhythm_type', '')} rhythmic pattern?"
        ),
        "stylistic:figurative_language": lambda: (
            f"Does the response use {g('figure_type', 'figurative language')} ({_rel_phrase(kw)} {g('num_occurrences', '')} times)?"
        ),
        "stylistic:emotive_adjectives": lambda: (
            f"Does the response use {_rel_phrase(kw)} {g('num_adjectives', g('num_emotive_adjectives', ''))} emotive adjectives?"
        ),
        "stylistic:sensory_detail": lambda: (
            f"Does the response include {_rel_phrase(kw)} {g('num_details', '')} {g('sense_type', 'sensory')} sensory details?"
        ),
        "situation:task_specific": lambda: (
            f"Does the response correctly perform the '{g('task_type', '')}' task as described in the instruction?"
        ),
        "situation:role_based": lambda: (
            f"Does the response stay in the '{g('role_type', g('scenario_type', ''))}' role described in the instruction?"
        ),
        "situation:audience_alignment": lambda: (
            f"Is the response appropriately tailored for a '{g('audience_type', '')}' audience?"
        ),
        "situation:perspective": lambda: (
            f"Is the response written from a '{g('perspective_type', '')}' perspective?"
        ),
        "situation:emotional_alignment": lambda: (
            f"Does the response align with a '{g('emotion_type', '')}' emotional state?"
        ),
        "situation:environment_setting": lambda: (
            f"Is the response consistent with a '{g('environment_type', '')}' environment/setting?"
        ),
        "situation:temporal_context": lambda: (
            f"Is the response consistent with the '{g('time_frame', '')}' time frame?"
        ),
        "situation:contextual_scenario": lambda: (
            f"Is the response consistent with the '{g('scenario_type', '')}' scenario?"
        ),
        "situation:cultural_context": lambda: (
            f"Is the response adapted to the '{g('culture_type', '')}' cultural context?"
        ),
        "linguistic:speech_act": lambda: (
            f"Does the response perform a '{g('act_type', g('speech_act_type', ''))}' speech act?"
        ),
        "linguistic:pragmatic_context": lambda: (
            f"Is the response appropriate for a '{g('context_type', '')}' pragmatic context?"
        ),
        "linguistic:grammatical_mood": lambda: (
            f"Is the response written in the '{g('mood_type', '')}' grammatical mood?"
        ),
        "linguistic:phonological_pattern": lambda: (
            f"Does the response follow a '{g('phonology_type', '')}' phonological pattern?"
        ),
        "linguistic:syntactic_pattern": lambda: (
            f"Does the response follow a '{g('pattern_type', '')}' syntactic pattern?"
        ),
        "linguistic:sound_symbolism": lambda: (
            f"Does the response use sound symbolism ({_rel_phrase(kw)} {g('num_symbolisms', '')} times)?"
        ),
        "linguistic:morphological_form": lambda: (
            f"Does the response use the '{g('form_type', '')}' morphological form?"
        ),
        # Ambiguous-unicode counting → judge instead of a brittle det check.
        "keywords:vowel_count": lambda: (
            f"Does the response contain {_rel_phrase(kw)} {g('num_vowels', '')} vowels?"
        ),
        "keywords:consonant_count": lambda: (
            f"Does the response contain {_rel_phrase(kw)} {g('num_consonants', '')} consonants?"
        ),
        "keywords:alliteration": lambda: (
            f"Does the response use alliteration with '{g('target_letter', '')}' ({_rel_phrase(kw)} {g('num_alliteration', '')} times)?"
        ),
        "change_case:case_ratio": lambda: (
            f"Is the fraction of uppercase letters in the response between {g('min_fraction', '')}% and {g('max_fraction', '')}%?"
        ),
        "change_case:vowel_consonant_balance": lambda: (
            f"Is the vowel-to-consonant ratio of the response between {g('min_fraction', '')} and {g('max_fraction', '')}?"
        ),
        "change_case:alternating": lambda: (
            "Does the response use alternating upper/lower case across its letters?"
        ),
        "change_case:alternating_target": lambda: (
            f"Does the response render the word '{g('target_string', '')}' in alternating case?"
        ),
        "change_case:first_letter_sentence": lambda: (
            "Does the first letter of every sentence in the response follow the required casing rule?"
        ),
        "change_case:all_caps_target": lambda: (
            f"Does the response render the word '{g('target_string', '')}' in ALL CAPS?"
        ),
        "change_case:lowercase_target": lambda: (
            f"Does the response render the phrase '{g('target_string', '')}' entirely in lowercase?"
        ),
        "change_case:first_letter_cap_target": lambda: (
            f"Does the response capitalize the first letter of each word in '{g('target_string', '')}'?"
        ),
        "length_constraints:avg_word_length": lambda: (
            f"Is the average word length of the response between {g('min_ratio', '')} and {g('max_ratio', '')} characters?"
        ),
        "detectable_format:sentence_endings": lambda: (
            f"Does the response use at least {g('min_variants', '')} distinct sentence-ending punctuation marks?"
        ),
    }
    fn = simple.get(iid)
    if fn is not None:
        return fn()
    # Generic fallback for any other id: describe it from its kwargs.
    kv = ", ".join(
        f"{k}={v}"
        for k, v in kw.items()
        if k not in ("instruction_id", "source", "is_misalignment_check", "uid")
    )
    return f"Does the response satisfy the constraint '{iid}'" + (
        f" ({kv})?" if kv else "?"
    )


def _clean_kwargs(inst: dict) -> dict:
    """Keep instruction_id + JSON-safe inline kwargs; drop provenance keys."""
    out: dict = {}
    for k, v in inst.items():
        if k in ("source", "is_misalignment_check", "uid"):
            continue
        if not isinstance(k, str):
            continue
        try:
            json.dumps(v, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError):
            continue
        out[k] = v
    return out


@register("nvidia/Nemotron-RL-CFBench-v1")
def convert_cfbench(row: dict, row_idx: int) -> HarborTask | None:
    try:
        prompt = extract_prompt(row)
    except Exception:
        return None

    instructions = row.get("instructions") or []
    llm_judge = row.get("llm_judge") or []
    if not isinstance(instructions, list):
        instructions = []
    if not isinstance(llm_judge, list):
        llm_judge = []

    det_constraints: list[dict] = []
    judge_questions: list[str] = []
    n_det = n_routed = 0

    for inst in instructions:
        if not isinstance(inst, dict):
            continue
        iid = inst.get("instruction_id")
        if not isinstance(iid, str):
            continue
        kw = _clean_kwargs(inst)
        if iid in DET_IMPLEMENTED:
            det_constraints.append(kw)
            n_det += 1
        else:
            q = sanitize_text(
                _judge_question(iid, kw), field_name="routed_q", max_len=1024
            )
            judge_questions.append(q)
            n_routed += 1

    # Subjective llm_judge questions from the dataset.
    n_subjective = 0
    for j in llm_judge:
        if not isinstance(j, dict):
            continue
        content = j.get("content")
        if isinstance(content, str) and content.strip():
            judge_questions.append(
                sanitize_text(content, field_name="judge_q", max_len=2048)
            )
            n_subjective += 1

    # Degenerate: nothing to grade -> skip.
    if not det_constraints and not judge_questions:
        return None

    verifier_data = {
        "det_constraints": det_constraints,
        "judge_questions": judge_questions,
        "instruction": prompt,
        "score_threshold": _SCORE_THRESHOLD,
    }
    encoded = json.dumps(verifier_data, ensure_ascii=False, allow_nan=False)
    if len(encoded) > _MAX_VDATA_BYTES:
        return None

    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    rid = row.get("id")
    task_id = task_id_for(
        "cfbench",
        (uuid or str(rid) or prompt[:128]) + f"|{row_idx}",
    )

    # If there are judge questions we need litellm + the judge TOML (key
    # propagation). A det-only row needs neither — keep it self-contained.
    if judge_questions:
        dockerfile = render_dockerfile(
            base=_BASE_IMAGE, pip_packages=("litellm==1.51.3",)
        )
        task_toml = LLM_JUDGE_TASK_TOML
    else:
        dockerfile = render_dockerfile(base=_BASE_IMAGE)
        task_toml = ""

    header = (
        "You are running in a shell-based sandbox. Read the instruction below "
        "and write your final, complete answer text to the file "
        "`/app/answer.txt`. The verifier reads ONLY `/app/answer.txt` — "
        "anything you print to the terminal or describe in chat is ignored. "
        "Your answer.txt must be the raw answer prose itself, satisfying every "
        "formal constraint in the instruction (counts, formatting markers, "
        "tone, ordering, ...). The response may need to be in a non-English "
        "language if the instruction is in that language.\n\n"
        "Save your answer from the shell with a heredoc, e.g.:\n\n"
        "```sh\n"
        "cat > /app/answer.txt <<'EOF'\n"
        "<your full answer text here>\n"
        "EOF\n"
        "```\n\n"
        "Verify with `cat /app/answer.txt` before finishing. If "
        "`/app/answer.txt` is missing or empty the task fails.\n\n"
        "---\n\n"
    )

    # Append the canonical answer-delivery guidance AFTER the prompt so it is
    # never lost to truncation. The header already mentions /app/answer.txt, but
    # ~29% of terminus-2 trials still emitted the answer as chat instead of
    # writing the file; the proven fix is the explicit heredoc HOW-to block at
    # the very end of the instruction. ASCII-only, appends cleanly to CJK/non-
    # English CFBench prompts.
    instruction_md = (
        header
        + prompt
        + answer_delivery_guidance("/app/answer.txt", what="your full response")
    )

    return HarborTask(
        task_id=task_id,
        instruction_md=instruction_md,
        dockerfile=dockerfile,
        test_sh=STANDARD_TEST_SH,
        verifier_py=HYBRID_IFEVAL_JUDGE_VERIFIER_PY,
        verifier_data=verifier_data,
        task_toml=task_toml,
        metadata=render_metadata(
            source_dataset="nvidia/Nemotron-RL-CFBench-v1",
            source_uuid=uuid,
            extra={
                "row_index": row_idx,
                "family": "hybrid_ifeval_judge",
                "n_det_constraints": n_det,
                "n_routed_to_judge": n_routed,
                "n_subjective_judge": n_subjective,
                "judge": "litellm:default(openai/gpt-4o-mini)"
                if judge_questions
                else "none",
                "score_threshold": _SCORE_THRESHOLD,
            },
        ),
    )
