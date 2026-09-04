"""Convert nvidia/Nemotron-RL-ARC-AGI-v1 (transductive + python_inductive).

The dataset has two configs that share a schema (the `run.py` --dataset arg is
the bare repo id; the config is selected by --split-style suffix below). Both
carry:
  - responses_create_params.input : system + user messages. The system message
    defines the required output format.
  - train      : few-shot [{input, output}] grid pairs (grids = list[list[int]])
  - test_input : the puzzle input grid (list[list[int]])
  - expected_output : the GOLD output grid (list[list[int]])

transductive:
  System prompt asks for `\boxed{solution}` where solution is "an array of rows
  separated by newlines, values by spaces" (the dataset's own few-shot examples
  render rows as concatenated single digits, so the agent may emit either form).
  We grade by EXACT grid match: store expected_output, parse the agent's grid
  tolerantly (GRID_MATCH_VERIFIER_PY), reward 1 iff identical.

python_inductive:
  System prompt asks for a `def transform(grid) -> grid` function in a
  ```python``` fence. We grade by EXECUTING the agent's transform() on the held
  test_input inside the task sandbox and comparing to expected_output
  (GRID_TRANSFORM_VERIFIER_PY). numpy + scipy are installed in the Dockerfile
  (the dataset lists numpy/scipy/torch/itertools/collections as available; we
  install the two that the canonical example solutions use — torch is omitted as
  too heavy for a CPU grid-transform sandbox).

Both configs are registered under the SAME repo id. run.py looks up the
converter by exact dataset repo id, so we register a single dispatcher that
inspects row["variant"] (== "transductive" | "python_inductive") to pick the
grading path. This lets one `--dataset nvidia/Nemotron-RL-ARC-AGI-v1` invocation
work for whichever config was loaded.
"""

from __future__ import annotations

from ..adapter import (
    HarborTask,
    STANDARD_TEST_SH,
    answer_delivery_guidance,
    render_dockerfile,
    render_metadata,
    task_id_for,
)
from ..verifiers import GRID_MATCH_VERIFIER_PY, GRID_TRANSFORM_VERIFIER_PY
from . import register
from ._common import extract_prompt

_REPO = "nvidia/Nemotron-RL-ARC-AGI-v1"
_BASE_IMAGE = "python:3.11-slim-bookworm"

_TRANSDUCTIVE_HEADER = (
    "You are solving an ARC-AGI puzzle. Read the problem below, work out the "
    "rule that maps each input grid to its output grid, then write your final "
    "answer to the path `/app/answer.txt`.\n\n"
    "## Output grid format (REQUIRED — read carefully)\n"
    "Write the output grid as plain text: **one grid row per line**, and within "
    "each row the **cell values separated by single spaces** (each cell is a "
    "single digit 0-9). Do NOT use JSON, brackets, commas, or markdown fences. "
    "Do NOT concatenate the digits of a row together.\n\n"
    "For example, the 2-row by 3-column grid whose first row is 2,9,2 and "
    "second row is 0,1,0 must be written EXACTLY as:\n\n"
    "    2 9 2\n"
    "    0 1 0\n\n"
    "That is the entire content of `/app/answer.txt` for that example — two "
    "lines, three space-separated digits each. The grader parses this exact "
    "format and compares your grid to the gold output cell-by-cell; an extra "
    "row, a missing cell, or any wrong value scores 0.\n\n"
    "---\n\n"
)

_INDUCTIVE_HEADER = (
    "You are solving an ARC-AGI puzzle by writing Python code. Read the problem "
    "below, work out the rule that maps each input grid to its output grid, "
    "then write a Python file to the path `/app/solution.py` containing a "
    "function with signature `def transform(grid: list[list[int]]) -> "
    "list[list[int]]:` that implements the rule.\n\n"
    "The verifier imports your `transform` and runs it on a held-out test input, "
    "comparing the returned grid cell-by-cell to the gold output. Available "
    "imports inside the sandbox: numpy, scipy, itertools, collections. Do NOT "
    'include an `if __name__ == "__main__"` block. (You may instead place the '
    "fenced ```python ... ``` code block in `/app/answer.txt`; the verifier "
    "extracts the transform function from either location.)\n\n"
    "---\n\n"
)


def _coerce_grid(value: object) -> list[list[int]] | None:
    """Coerce a grid to list[list[int]] of plain ints; return None if malformed."""
    if not isinstance(value, list) or not value:
        return None
    out: list[list[int]] = []
    for row in value:
        if not isinstance(row, list) or not row:
            return None
        try:
            out.append([int(v) for v in row])
        except (TypeError, ValueError):
            return None
    # Enforce ARC color range 0-9 (sanity; rejects garbage rows).
    for row in out:
        for v in row:
            if v < 0 or v > 9:
                return None
    return out


def _convert_transductive(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    expected = _coerce_grid(row.get("expected_output"))
    if expected is None:
        return None
    # Delivery guidance MUST be appended after the (possibly long) prompt so
    # the heredoc submission instructions are never cut by upstream truncation.
    instruction_md = (
        _TRANSDUCTIVE_HEADER
        + prompt
        + answer_delivery_guidance("/app/answer.txt", what="the output grid")
    )
    dockerfile = render_dockerfile(base=_BASE_IMAGE)
    pid = (
        row.get("problem_id")
        if isinstance(row.get("problem_id"), str)
        else str(row_idx)
    )
    task_id = task_id_for("arc-trans", f"{pid}|{row_idx}|" + repr(expected))
    return HarborTask(
        task_id=task_id,
        instruction_md=instruction_md,
        dockerfile=dockerfile,
        test_sh=STANDARD_TEST_SH,
        verifier_py=GRID_MATCH_VERIFIER_PY,
        verifier_data={"expected_output": expected},
        metadata=render_metadata(
            source_dataset=_REPO,
            source_uuid=(row.get("metadata") or {}).get("uuid")
            if isinstance(row.get("metadata"), dict)
            else None,
            extra={
                "row_index": row_idx,
                "family": "grid_match",
                "variant": "transductive",
                "problem_id": pid,
                "difficulty_bucket": row.get("difficulty_bucket")
                if isinstance(row.get("difficulty_bucket"), str)
                else None,
            },
        ),
    )


def _convert_inductive(row: dict, row_idx: int) -> HarborTask | None:
    prompt = extract_prompt(row)
    test_input = _coerce_grid(row.get("test_input"))
    expected = _coerce_grid(row.get("expected_output"))
    if test_input is None or expected is None:
        return None
    instruction_md = _INDUCTIVE_HEADER + prompt
    dockerfile = render_dockerfile(
        base=_BASE_IMAGE,
        pip_packages=("numpy==1.26.4", "scipy==1.11.4"),
    )
    pid = (
        row.get("problem_id")
        if isinstance(row.get("problem_id"), str)
        else str(row_idx)
    )
    task_id = task_id_for("arc-induct", f"{pid}|{row_idx}|" + repr(expected))
    return HarborTask(
        task_id=task_id,
        instruction_md=instruction_md,
        dockerfile=dockerfile,
        test_sh=STANDARD_TEST_SH,
        verifier_py=GRID_TRANSFORM_VERIFIER_PY,
        verifier_data={
            "test_cases": [{"input": test_input, "output": expected}],
        },
        metadata=render_metadata(
            source_dataset=_REPO,
            source_uuid=(row.get("metadata") or {}).get("uuid")
            if isinstance(row.get("metadata"), dict)
            else None,
            extra={
                "row_index": row_idx,
                "family": "grid_transform",
                "variant": "python_inductive",
                "problem_id": pid,
                "difficulty_bucket": row.get("difficulty_bucket")
                if isinstance(row.get("difficulty_bucket"), str)
                else None,
            },
        ),
    )


@register(_REPO)
def convert_arc_agi(row: dict, row_idx: int) -> HarborTask | None:
    """Dispatch on row['variant'] to the transductive or inductive grading path."""
    variant = row.get("variant")
    if variant == "python_inductive":
        return _convert_inductive(row, row_idx)
    if variant == "transductive":
        return _convert_transductive(row, row_idx)
    # Fallback: infer from the system prompt content.
    rcp = row.get("responses_create_params")
    sys_txt = ""
    if isinstance(rcp, dict):
        for m in rcp.get("input", []) or []:
            if isinstance(m, dict) and m.get("role") == "system":
                sys_txt = (
                    m.get("content", "") if isinstance(m.get("content"), str) else ""
                )
                break
    if "transform" in sys_txt and "Python" in sys_txt:
        return _convert_inductive(row, row_idx)
    return _convert_transductive(row, row_idx)
