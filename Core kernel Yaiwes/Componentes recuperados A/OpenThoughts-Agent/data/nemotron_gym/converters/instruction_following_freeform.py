"""Convert nvidia/Nemotron-RL-Instruction-Following-Free-Form-Formatting-v1.

Each row carries a `verifier` dict of the shape:
    {
      "type": "regex" | "inline_prose",
      "pattern_id": "<name>",
      "verify_regex": ["<regex>", ...],
      "verify_min_matches": <int>,
    }

Grading is fully deterministic: apply each regex (re.MULTILINE) to the agent's
answer and reward 1 iff the total match count >= verify_min_matches. See
verifiers/regex_count.py for the counting semantics (anchored regexes count
distinct matched LINES; inline regexes count occurrences; the two are summed).

Per the converter brief, rows whose verifier `type` is not `"regex"` are
skipped (the `inline_prose` rows, ~164/9037). The verifier itself would grade
them correctly, but we honor the spec's regex-only scope.
"""

from __future__ import annotations

from ..adapter import (
    HarborTask,
    STANDARD_TEST_SH,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import REGEX_COUNT_VERIFIER_PY
from . import register
from ._common import extract_prompt

_SOURCE = "nvidia/Nemotron-RL-Instruction-Following-Free-Form-Formatting-v1"
_BASE_IMAGE = "python:3.11-slim-bookworm"
_MAX_REGEX_LEN = 2048
_MAX_REGEXES = 32

_INSTRUCTION_HEADER = (
    "You are running in a shell-based sandbox. Read the instruction below and "
    "write your final, complete answer text to the file `/app/answer.txt`. "
    "The verifier reads ONLY `/app/answer.txt` — anything you print to the "
    "terminal or describe in chat is ignored. Your answer.txt must be the raw "
    "answer text itself (not a wrapper, not a summary, not commentary), "
    "following every formatting instruction exactly (line structure, "
    "delimiters, bullet/heading markers, quoting, spacing, ...).\n\n"
    "Example of how to save your answer (run this in the shell after composing "
    "your response):\n\n"
    "```sh\n"
    "cat > /app/answer.txt <<'EOF'\n"
    "<your full answer text here>\n"
    "EOF\n"
    "```\n\n"
    "Verify the file exists and contains your answer with `cat /app/answer.txt` "
    "before finishing. If `/app/answer.txt` is missing or empty the task fails.\n\n"
    "---\n\n"
)


@register(_SOURCE)
def convert_freeform_formatting(row: dict, row_idx: int) -> HarborTask | None:
    verifier = row.get("verifier")
    if not isinstance(verifier, dict):
        return None
    if verifier.get("type") != "regex":
        # inline_prose (or any other type) is out of scope per the brief.
        return None

    regexes = verifier.get("verify_regex")
    min_matches = verifier.get("verify_min_matches")
    if not isinstance(regexes, list) or not regexes:
        return None
    if len(regexes) > _MAX_REGEXES:
        return None
    san_regexes: list[str] = []
    for i, pat in enumerate(regexes):
        if not isinstance(pat, str) or not pat:
            return None
        if len(pat) > _MAX_REGEX_LEN:
            return None
        # sanitize_text strips control chars; regex source is plain text.
        san_regexes.append(
            sanitize_text(pat, field_name=f"verify_regex[{i}]", max_len=_MAX_REGEX_LEN)
        )
    if (
        not isinstance(min_matches, int)
        or isinstance(min_matches, bool)
        or min_matches < 1
    ):
        return None

    prompt = extract_prompt(row)
    pattern_id = verifier.get("pattern_id")
    pattern_id = pattern_id if isinstance(pattern_id, str) else ""

    task_id = task_id_for(
        "if-freeform",
        prompt[:256]
        + "|"
        + pattern_id
        + "|"
        + "".join(san_regexes)
        + f"|{min_matches}",
    )
    return HarborTask(
        task_id=task_id,
        instruction_md=_INSTRUCTION_HEADER + prompt,
        dockerfile=render_dockerfile(base=_BASE_IMAGE),
        test_sh=STANDARD_TEST_SH,
        verifier_py=REGEX_COUNT_VERIFIER_PY,
        verifier_data={
            "verify_regex": san_regexes,
            "verify_min_matches": min_matches,
        },
        metadata=render_metadata(
            source_dataset=_SOURCE,
            source_uuid=None,
            extra={
                "row_index": row_idx,
                "family": "instruction_following_freeform",
                "pattern_id": pattern_id,
            },
        ),
    )
