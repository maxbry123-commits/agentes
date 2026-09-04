"""Convert the citation-formatting instruction-following dataset.

Dataset:
  - nvidia/Nemotron-RL-Instruction-Following-Citation-Formatting-v1

Every row carries a deterministic `verifier` dict of the shape::

    {"type": "string_match",
     "patterns": ["\\[ref:2\\]"],            # regex (re.escape of the markers)
     "expected_markers": ["[ref:2]"]}        # literal substrings

Across all 9540 rows the verifier is uniform: `type == "string_match"`, both
`patterns` and `expected_markers` are present and equal-length, and every
`patterns[i]` is exactly `re.escape(expected_markers[i])`. The grading is
ALL-must-match (the answer must cite every required source marker). There is no
`match_mode` field and no `any` variant in the data.

Because each pattern is a re.escape of its literal marker, an all-of substring
check over `expected_markers` is semantically identical to an all-of regex check
over `patterns`. We therefore reuse the self-contained `substring_match`
verifier with `mode=all_of` and `case_sensitive=True` (citation markers such as
`[web:3]` vs `[Web:3]` are meant to be distinct). No LLM judge — fully
deterministic.

Rows whose verifier type is not `string_match`, or which lack usable
markers/patterns, are skipped (returned as None) and counted by run.py.
"""

from __future__ import annotations

import re

from ..adapter import (
    HarborTask,
    STANDARD_TEST_SH,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import SUBSTRING_MATCH_VERIFIER_PY
from . import register
from ._common import extract_prompt


_DATASET = "nvidia/Nemotron-RL-Instruction-Following-Citation-Formatting-v1"
_BASE_IMAGE = "python:3.11-slim-bookworm"
_MARKER_MAX_LEN = 256
_MAX_MARKERS = 256

_INSTRUCTION_HEADER = (
    "You are running in a shell-based sandbox. Read the instruction below, "
    "which asks you to answer a question while citing source parts using "
    "inline citation markers (e.g. `[ref:2]`, `[web:3]`, `[source:6]`). "
    "Write your final, complete answer text to the file `/app/answer.txt`.\n\n"
    "The verifier reads ONLY `/app/answer.txt` and checks that EVERY required "
    "citation marker appears verbatim in your answer. Markers are matched as "
    "exact, case-sensitive substrings (brackets and the `web:`/`ref:`/`source:` "
    "prefix included), so reproduce them exactly as the instruction specifies. "
    "Anything you print to the terminal or describe in chat is ignored.\n\n"
    "Example of how to save your answer (run this in the shell after composing "
    "your response):\n\n"
    "```sh\n"
    "cat > /app/answer.txt <<'EOF'\n"
    "<your full answer text here, including every required [ref:N] marker>\n"
    "EOF\n"
    "```\n\n"
    "Verify the file exists and contains your answer with `cat /app/answer.txt` "
    "before finishing. If `/app/answer.txt` is missing, empty, or omits any "
    "required citation marker the task fails.\n\n"
    "---\n\n"
)


def _extract_markers(verifier: object) -> list[str] | None:
    """Pull the literal citation markers out of the row's verifier dict.

    Prefers `expected_markers` (literal substrings). Falls back to
    un-escaping `patterns` only when patterns are pure re.escape of a literal
    (no real regex metacharacters survive). Returns None if no usable markers.
    """
    if not isinstance(verifier, dict):
        return None
    if verifier.get("type") != "string_match":
        return None

    markers = verifier.get("expected_markers")
    if isinstance(markers, list) and markers:
        out: list[str] = []
        for m in markers:
            if not isinstance(m, str) or not m:
                return None
            out.append(m)
        return out

    # Fallback: derive literals from `patterns` when expected_markers is absent.
    patterns = verifier.get("patterns")
    if isinstance(patterns, list) and patterns:
        out = []
        for p in patterns:
            if not isinstance(p, str) or not p:
                return None
            # Only treat patterns that are plain re.escape of some literal.
            # Recover the literal by stripping backslash escapes; if the
            # round-trip doesn't reproduce the pattern, it's a real regex and
            # the substring verifier can't represent it -> skip the row.
            literal = re.sub(r"\\(.)", r"\1", p)
            if re.escape(literal) != p:
                return None
            out.append(literal)
        return out

    return None


@register(_DATASET)
def convert_citation_formatting(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)

    markers = _extract_markers(row.get("verifier"))
    if not markers:
        return None
    if len(markers) > _MAX_MARKERS:
        return None

    san_markers: list[str] = []
    for i, m in enumerate(markers):
        san_markers.append(
            sanitize_text(
                m, field_name=f"expected_markers[{i}]", max_len=_MARKER_MAX_LEN
            )
        )
    # Sanitization must not have altered the markers (control chars in a
    # citation marker would mean we can't faithfully check it).
    if san_markers != markers:
        return None

    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    task_id = task_id_for(
        _DATASET.split("/")[-1].lower(),
        (uuid or prompt[:128]) + "|" + "|".join(san_markers),
    )

    return HarborTask(
        task_id=task_id,
        instruction_md=_INSTRUCTION_HEADER + prompt,
        dockerfile=render_dockerfile(base=_BASE_IMAGE),
        test_sh=STANDARD_TEST_SH,
        verifier_py=SUBSTRING_MATCH_VERIFIER_PY,
        verifier_data={
            "mode": "all_of",
            "needles": san_markers,
            "case_sensitive": True,
        },
        metadata=render_metadata(
            source_dataset=_DATASET,
            source_uuid=uuid,
            extra={
                "row_index": row_idx,
                "family": "instruction_following",
                "task_type": "citation_formatting",
                "num_markers": len(san_markers),
            },
        ),
    )
