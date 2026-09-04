"""Convert nvidia/Nemotron-RL-litmus-bench-v0.1 (molecular property prediction).

Schema (one row):
  - responses_create_params.input : messages (the prompt carries a SMILES string
    and asks for a molecular property as a single integer / 0|1).
  - expected_answer : float  (the gold value; always integer-valued in practice)
  - property_type   : str    one of {count, fragment, bool, presence}
  - property        : str    e.g. 'Num5MemberRings'
  - smiles, chembl_id, method : str (provenance)
  - use_box_format  : bool   whether the prompt asked for \\boxed{...} format

All four property_types carry an integer-valued gold (count/fragment are
non-negative integer counts; bool/presence are 0/1). Grading is a pure numeric
comparison against the stored gold via the shared numeric_compare verifier,
which extracts the last numeric token from /app/answer.txt (and also unwraps
\\boxed{...}). The double-parentheses ((answer)) format used by most rows works
fine since the verifier takes the last numeric token regardless. Because golds
are exact integers we use a tiny absolute tolerance (0.5 would be too loose
since adjacent integers are valid distractors).

No rdkit is needed in the task image — grading does not recompute the property,
it compares against the stored gold.
"""

from __future__ import annotations

from ..adapter import (
    HarborTask,
    STANDARD_TEST_SH,
    render_dockerfile,
    render_metadata,
    task_id_for,
)
from ..verifiers import NUMERIC_COMPARE_VERIFIER_PY
from . import register
from ._common import extract_prompt

_BASE_IMAGE = "python:3.11-slim-bookworm"
_SOURCE = "nvidia/Nemotron-RL-litmus-bench-v0.1"

_INSTRUCTION_HEADER = (
    "You are a chemistry expert analyzing a molecule given by its SMILES "
    "string. Read the task below, reason carefully, and write your final "
    "answer to the path `/app/answer.txt`.\n\n"
    "The answer must be a single integer. Follow the answer-format "
    "instruction stated in the task (e.g. enclose it in double parentheses "
    "`((answer))`{boxed_note}). The verifier reads `/app/answer.txt` and "
    "compares the last numeric value it finds against the reference, so make "
    "sure the final number on the last line is your intended answer.\n\n"
    "---\n\n"
)

_BOXED_NOTE = ", or inside `\\boxed{...}`"


@register(_SOURCE)
def convert_litmus_bench(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)

    expected = row.get("expected_answer")
    if not isinstance(expected, (int, float)) or isinstance(expected, bool):
        # bool is a subclass of int but never the stored type here; guard anyway.
        if not isinstance(expected, (int, float)):
            return None
    expected = float(expected)

    property_type = row.get("property_type")
    if not isinstance(property_type, str):
        property_type = None
    prop = row.get("property") if isinstance(row.get("property"), str) else None
    use_box = bool(row.get("use_box_format"))

    boxed_note = _BOXED_NOTE if use_box else ""
    header = _INSTRUCTION_HEADER.format(boxed_note=boxed_note)
    instruction_md = header + prompt

    dockerfile = render_dockerfile(base=_BASE_IMAGE)

    uuid = row.get("uuid") if isinstance(row.get("uuid"), str) else None
    task_id = task_id_for(
        "litmus-bench",
        (uuid or "") + "||" + prompt[:128] + "||" + repr(expected) + "|" + str(row_idx),
    )

    return HarborTask(
        task_id=task_id,
        instruction_md=instruction_md,
        dockerfile=dockerfile,
        test_sh=STANDARD_TEST_SH,
        verifier_py=NUMERIC_COMPARE_VERIFIER_PY,
        verifier_data={
            "expected_value": expected,
            # Golds are exact integers; adjacent integers are valid distractors,
            # so keep the tolerance well under 1.0.
            "tolerance_abs": 1e-3,
            "tolerance_rel": 0.0,
        },
        metadata=render_metadata(
            source_dataset=_SOURCE,
            source_uuid=uuid,
            extra={
                "row_index": row_idx,
                "family": "numeric_compare",
                "property_type": property_type,
                "property": prop,
                "chembl_id": row.get("chembl_id")
                if isinstance(row.get("chembl_id"), str)
                else None,
                "method": row.get("method")
                if isinstance(row.get("method"), str)
                else None,
                "use_box_format": use_box,
            },
        ),
    )
