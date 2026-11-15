"""Convert nvidia/Nemotron-RL-SysBench-v1 → Harbor HYBRID task.

SysBench is SYSTEM-prompt constraint following: a rich system prompt sets rules,
and each row carries TWO kinds of checks the final response must satisfy:

  * `instructions` (list): IFEval-style structured constraints with an
    `instruction_id` + inline kwargs, e.g.
    ``{"instruction_id": "keywords:existence", "source": "system",
       "keywords": [...]}``. Most are DETERMINISTIC.
  * `llm_judge` (list): subjective yes/no checks, e.g.
    ``{"content": "Does the response avoid prescriptive language?",
       "source": "system", "uid": 2}``. Graded by an LLM judge.

Strategy (identical shape to the CFBench task): emit a single hybrid task that
reuses `verifiers/hybrid_ifeval_judge.py`. The verifier runs the deterministic
constraints (`det_constraints`) AND the judge questions (`judge_questions`) and
combines them:

    reward = 1  iff  (ALL deterministic pass)  AND  (ALL judge questions pass)

instruction_id routing (decided here, at conversion time):
  * Deterministic-checkable ids that the hybrid verifier implements → emitted as
    `det_constraints` (graded offline, no key).
  * Inherently SUBJECTIVE ids (`stylistic:*`, `situation:*`) → rewritten into a
    natural-language yes/no question appended to `judge_questions`, so they are
    STILL CHECKED by the judge (never silently passed).
  * Any id the verifier does not implement → also routed to the judge with a
    generic phrasing (fail-safe; the verifier fails CLOSED on unknown det ids,
    so we must not emit them as deterministic).

The system prompt is preserved verbatim in the task instruction (via
`extract_prompt`, which prefixes the `[system]` role), so constraints that refer
to system rules remain checkable by the agent and the judge.

Degenerate rows: SysBench always has at least judge questions (0 rows are
empty); rows with only judge questions (no deterministic instructions) grade on
the judge alone, rows with only deterministic instructions grade on those alone.
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
from ..verifiers import HYBRID_IFEVAL_JUDGE_VERIFIER_PY
from . import register
from ._common import PROMPT_MAX_LEN, extract_prompt


_SOURCE = "nvidia/Nemotron-RL-SysBench-v1"
_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_KW_BYTES = 64 * 1024
_MAX_QUESTIONS = 64
_MAX_CONSTRAINTS = 64

# Deterministic instruction_ids implemented by hybrid_ifeval_judge.py for
# SysBench. Anything NOT in this set is routed to the LLM judge (subjective or
# unimplemented) so we never emit a det_constraint the verifier fails closed on.
_DET_IDS = frozenset(
    {
        "keywords:existence",
        "keywords:forbidden_words",
        "keywords:frequency",
        "keywords:letter_frequency",
        "length_constraints:number_words",
        "length_constraints:number_characters",
        "length_constraints:unique_words",
        "length_constraints:sentence_length",
        "length_constraints:word_length",
        "length_constraints:word_repetition",
        "detectable_format:number_bullet_lists",
        "detectable_format:numbered_list",
        "detectable_format:number_paragraphs",
        "detectable_format:sentence_count",
        "detectable_format:sentences_per_paragraph",
        "detectable_format:table",
        "detectable_format:heading_depth",
        "detectable_format:nested_list",
        "detectable_format:json_format",
        "detectable_format:multiple_sections",
        "detectable_format:title",
        "detectable_format:max_paragraph_length",
        "detectable_format:sentence_endings",
        "detectable_content:number_placeholders",
        "detectable_content:numeric_inclusion",
        "detectable_content:postscript",
        "startend:start_checker",
        "startend:end_checker",
        "punctuation:no_comma",
        "punctuation:no_period",
        "punctuation:end_rule",
        "change_case:all_caps",
        "change_case:lowercase",
        "change_case:all_caps_target",
        "change_case:lowercase_target",
        "change_case:first_letter_cap_target",
        "change_case:first_letter_sentence",
        "change_case:last_letter",
        "change_case:alternating",
        "change_case:alternating_target",
        "change_case:capital_word_frequency",
    }
)

# Human-readable descriptions for routing subjective / unimplemented constraints
# to the judge as yes/no questions. `{kw}` placeholders are filled from kwargs.
_JUDGE_PHRASINGS = {
    "stylistic:tone_formality": "Does the response maintain a {tone_level} tone/formality level throughout?",
    "stylistic:emotional_tone": "Does the response convey a {emotion_type} emotional tone throughout?",
    "stylistic:politeness": "Does the response maintain a {politeness_degree} level of politeness throughout?",
    "stylistic:sentence_tone_consistency": "Is the tone of the response consistently {tone_type} across all sentences?",
    "stylistic:voice": "Is the response written predominantly in the {voice_type} voice?",
    "stylistic:literary_style": "Is the response written in a {style_type} literary style?",
    "stylistic:sensory_detail": "Does the response include sensory detail of type '{sense_type}' (relation {relation} {num_details})?",
    "stylistic:emotive_adjectives": "Does the response's use of emotive adjectives satisfy: {relation} {num_adjectives}?",
    "situation:audience_alignment": "Is the response appropriately aligned for a '{audience_type}' audience?",
    "situation:task_specific": "Does the response perform the task type '{task_type}' as required?",
    "situation:contextual_scenario": "Does the response fit the scenario '{scenario_type}'?",
    "situation:perspective": "Is the response written from the '{perspective_type}' perspective?",
    "situation:emotional_alignment": "Is the response emotionally aligned to be '{emotion_type}'?",
    "situation:role_based": "Does the response adopt the role/persona of a '{role_type}'?",
}


_INSTRUCTION_HEADER = (
    "You are running in a shell-based sandbox. Below is a SYSTEM prompt that "
    "sets rules for your behavior, followed by the conversation/request. Read "
    "ALL of it — many constraints are imposed by the system prompt itself "
    "(formatting, forbidden words, required sections, tone, persona, etc.).\n\n"
    "Write your final, complete response text to the file `/app/answer.txt`. "
    "The verifier reads ONLY `/app/answer.txt` — anything you print to the "
    "terminal or describe in chat is ignored. Your answer.txt must be the raw "
    "response prose itself (not a wrapper, not a summary), satisfying every "
    "formal constraint (paragraph/sentence counts, required keywords, forbidden "
    "words, start/end phrases, tables, headings, case rules, ...) AND the "
    "qualitative requirements (tone, scope, consistency) the system prompt "
    "imposes.\n\n"
    "Example of how to save your answer (run this in the shell after composing "
    "your response):\n\n"
    "```sh\n"
    "cat > /app/answer.txt <<'EOF'\n"
    "<your full response text here>\n"
    "EOF\n"
    "```\n\n"
    "Verify with `cat /app/answer.txt` before finishing. If `/app/answer.txt` "
    "is missing or empty the task fails.\n\n"
    "---\n\n"
)


def _build_prompt(row: dict) -> str | None:
    """Prompt builder that PRESERVES the system message.

    SysBench's `responses_create_params.input` is a multi-turn transcript
    (system + several user/assistant turns). The constraints apply to the final
    response, and the system message holds most of the rules — so the system
    turn MUST survive. `extract_prompt` keeps everything but fails (raises) when
    the full transcript exceeds the 64KB cap (~5% of rows). For those rows we
    fall back to system + final user turn (verified to fit under the cap for all
    observed rows), rather than dropping the row.
    """
    try:
        return extract_prompt(row)
    except SanitizationError:
        pass
    # Over-cap fallback: system turn(s) + the final user turn only.
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
    parts = sys_parts + ([last_user] if last_user else [])
    if not parts:
        return None
    joined = "\n\n".join(parts)
    try:
        return sanitize_text(joined, field_name="prompt", max_len=PROMPT_MAX_LEN)
    except SanitizationError:
        # As a last resort, keep just the system rules (truncated by cap check).
        if sys_parts:
            try:
                return sanitize_text(
                    "\n\n".join(sys_parts), field_name="prompt", max_len=PROMPT_MAX_LEN
                )
            except SanitizationError:
                return None
        return None


def _phrase_for(inst: dict) -> str:
    """Render a yes/no judge question for a non-deterministic instruction id."""
    iid = inst.get("instruction_id", "")
    template = _JUDGE_PHRASINGS.get(iid)
    kwargs = {
        k: v
        for k, v in inst.items()
        if k not in ("instruction_id", "source", "is_misalignment_check", "uid")
    }
    if template:
        try:
            text = template.format_map(_SafeDict(kwargs))
        except Exception:
            text = template
        return text
    # Generic fallback for any unmapped/unimplemented id.
    detail = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    base = f"Does the response satisfy the constraint '{iid}'"
    return f"{base} ({detail})?" if detail else f"{base}?"


class _SafeDict(dict):
    def __missing__(self, key):  # noqa: D401 - leave unknown placeholders intact
        return "{" + key + "}"


def _clean_constraint(inst: dict) -> dict | None:
    """Sanitize one deterministic instruction dict for verifier_data.

    Keeps `instruction_id` + JSON-safe inline kwargs; drops provenance keys.
    """
    iid = inst.get("instruction_id")
    if not isinstance(iid, str):
        return None
    out: dict = {
        "instruction_id": sanitize_text(iid, field_name="instruction_id", max_len=128)
    }
    for k, v in inst.items():
        if k in ("instruction_id", "source", "is_misalignment_check", "uid"):
            continue
        if not isinstance(k, str):
            continue
        # Only JSON-safe primitives / lists of primitives.
        if isinstance(v, str):
            out[k] = sanitize_text(v, field_name=f"kwargs.{k}", max_len=4096)
        elif (
            isinstance(v, bool)
            or isinstance(v, int)
            or isinstance(v, float)
            or v is None
        ):
            out[k] = v
        elif isinstance(v, list):
            clean_list = []
            for item in v:
                if isinstance(item, str):
                    clean_list.append(
                        sanitize_text(item, field_name=f"kwargs.{k}[]", max_len=2048)
                    )
                elif isinstance(item, (bool, int, float)) or item is None:
                    clean_list.append(item)
            out[k] = clean_list
        # silently drop nested dicts / unsupported types (none observed in data)
    return out


@register(_SOURCE)
def convert_sysbench(row: dict, row_idx: int) -> HarborTask | None:
    prompt = _build_prompt(row)
    if not prompt:
        return None

    instructions = row.get("instructions")
    llm_judge = row.get("llm_judge")
    if not isinstance(instructions, list):
        instructions = []
    if not isinstance(llm_judge, list):
        llm_judge = []

    det_constraints: list[dict] = []
    judge_questions: list[str] = []

    # Route instructions: deterministic vs judge.
    for inst in instructions:
        if not isinstance(inst, dict):
            continue
        iid = inst.get("instruction_id")
        if not isinstance(iid, str):
            continue
        if iid in _DET_IDS:
            cleaned = _clean_constraint(inst)
            if cleaned is not None:
                det_constraints.append(cleaned)
        else:
            # subjective or unimplemented → judge question
            q = _phrase_for(inst)
            judge_questions.append(sanitize_text(q, field_name="judge_q", max_len=2048))

    # llm_judge entries → judge questions (use their `content`).
    for j in llm_judge:
        if not isinstance(j, dict):
            continue
        content = j.get("content")
        if isinstance(content, str) and content.strip():
            judge_questions.append(
                sanitize_text(content, field_name="judge_q", max_len=2048)
            )

    # Degenerate guard: nothing to grade → skip.
    if not det_constraints and not judge_questions:
        return None

    # Cap sizes (keep verifier_data bounded; SysBench max observed = 12 inst / 29 judge).
    det_constraints = det_constraints[:_MAX_CONSTRAINTS]
    judge_questions = judge_questions[:_MAX_QUESTIONS]

    # Byte-cap the constraint payload defensively.
    import json as _json

    if len(_json.dumps(det_constraints, ensure_ascii=False)) > _MAX_KW_BYTES:
        return None

    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    rid = row.get("id")
    id_key = uuid or (str(rid) if rid is not None else prompt[:128])
    det_sig = "|".join(c.get("instruction_id", "") for c in det_constraints)
    task_id = task_id_for("sysbench", f"{id_key}|{det_sig}|{len(judge_questions)}")

    # Delivery guidance is APPENDED LAST (after the system-prompt-heavy prompt,
    # which is the part `_build_prompt` may truncate at PROMPT_MAX_LEN). This
    # guarantees the HOW-to-submit heredoc is never cut and is the final thing
    # the terminal agent reads — the proven fix for the ~32% delivery-miss where
    # terminus-2 emitted the answer as chat and never wrote /app/answer.txt.
    # Points at /app/answer.txt, the exact path hybrid_ifeval_judge.py reads.
    instruction_md = (
        _INSTRUCTION_HEADER
        + prompt
        + answer_delivery_guidance("/app/answer.txt", what="your full response")
    )

    return HarborTask(
        task_id=task_id,
        instruction_md=instruction_md,
        dockerfile=render_dockerfile(
            base=_BASE_IMAGE,
            pip_packages=("litellm==1.51.3",),
        ),
        test_sh=STANDARD_TEST_SH,
        verifier_py=HYBRID_IFEVAL_JUDGE_VERIFIER_PY,
        task_toml=LLM_JUDGE_TASK_TOML,
        verifier_data={
            "det_constraints": det_constraints,
            "judge_questions": judge_questions,
            "instruction": prompt,
            "score_threshold": 0.5,
        },
        metadata=render_metadata(
            source_dataset=_SOURCE,
            source_uuid=uuid,
            extra={
                "row_index": row_idx,
                "family": "hybrid_ifeval_judge_sysbench",
                "n_det_constraints": len(det_constraints),
                "n_judge_questions": len(judge_questions),
                "judge": "litellm:default(openai/gpt-4o-mini)",
            },
        ),
    )
