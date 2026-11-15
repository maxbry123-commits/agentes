"""Embedded verifier scripts.

Each function returns a Python source string (utf-8 text) that will be written
to `tests/verifier.py` inside a task tarball. The verifier:
  - Reads /tests/verifier_data.json
  - Reads agent output (typically /app/answer.txt or /app/solution.py)
  - Writes 0 or 1 to /logs/verifier/reward.txt
  - Prints diagnostics to stdout (captured by Harbor in test-stdout.txt)

These verifier scripts must not import anything not available in the task's
Dockerfile, and must never `exec`/`eval` any value from verifier_data.json.
"""

from .calendar_constraints import VERIFIER_PY as CALENDAR_VERIFIER_PY
from .equivalence_judge import VERIFIER_PY as EQUIVALENCE_JUDGE_VERIFIER_PY
from .grid_match import VERIFIER_PY as GRID_MATCH_VERIFIER_PY
from .grid_transform import VERIFIER_PY as GRID_TRANSFORM_VERIFIER_PY
from .hybrid_ifeval_judge import VERIFIER_PY as HYBRID_IFEVAL_JUDGE_VERIFIER_PY
from .ifeval_constraints import VERIFIER_PY as IFEVAL_VERIFIER_PY
from .injection_resist import VERIFIER_PY as INJECTION_RESIST_VERIFIER_PY
from .inverse_ifeval_judge import VERIFIER_PY as INVERSE_IFEVAL_JUDGE_VERIFIER_PY
from .json_schema import VERIFIER_PY as JSON_SCHEMA_VERIFIER_PY
from .llm_judge import VERIFIER_PY as LLM_JUDGE_VERIFIER_PY
from .math_boxed import VERIFIER_PY as MATH_BOXED_VERIFIER_PY
from .multiturn_rubric_judge import VERIFIER_PY as MULTITURN_RUBRIC_JUDGE_VERIFIER_PY
from .safety_judge import VERIFIER_PY as SAFETY_JUDGE_VERIFIER_PY
from .normalized_text import VERIFIER_PY as NORMALIZED_TEXT_VERIFIER_PY
from .numeric_compare import VERIFIER_PY as NUMERIC_COMPARE_VERIFIER_PY
from .qa_boxed_match import VERIFIER_PY as QA_BOXED_MATCH_VERIFIER_PY
from .reasoning_gym import VERIFIER_PY as REASONING_GYM_VERIFIER_PY
from .regex_count import VERIFIER_PY as REGEX_COUNT_VERIFIER_PY
from .regex_letter import VERIFIER_PY as REGEX_LETTER_VERIFIER_PY
from .stdio_diff import VERIFIER_PY as STDIO_DIFF_VERIFIER_PY
from .structured_format import VERIFIER_PY as STRUCTURED_FORMAT_VERIFIER_PY
from .substring_match import VERIFIER_PY as SUBSTRING_MATCH_VERIFIER_PY
from .swe_tool_call_match import VERIFIER_PY as SWE_TOOL_CALL_VERIFIER_PY
from .tool_call_match import VERIFIER_PY as TOOL_CALL_VERIFIER_PY

__all__ = [
    "CALENDAR_VERIFIER_PY",
    "EQUIVALENCE_JUDGE_VERIFIER_PY",
    "GRID_MATCH_VERIFIER_PY",
    "GRID_TRANSFORM_VERIFIER_PY",
    "HYBRID_IFEVAL_JUDGE_VERIFIER_PY",
    "IFEVAL_VERIFIER_PY",
    "INJECTION_RESIST_VERIFIER_PY",
    "INVERSE_IFEVAL_JUDGE_VERIFIER_PY",
    "JSON_SCHEMA_VERIFIER_PY",
    "LLM_JUDGE_VERIFIER_PY",
    "MATH_BOXED_VERIFIER_PY",
    "MULTITURN_RUBRIC_JUDGE_VERIFIER_PY",
    "SAFETY_JUDGE_VERIFIER_PY",
    "NORMALIZED_TEXT_VERIFIER_PY",
    "NUMERIC_COMPARE_VERIFIER_PY",
    "QA_BOXED_MATCH_VERIFIER_PY",
    "REASONING_GYM_VERIFIER_PY",
    "REGEX_COUNT_VERIFIER_PY",
    "REGEX_LETTER_VERIFIER_PY",
    "STDIO_DIFF_VERIFIER_PY",
    "STRUCTURED_FORMAT_VERIFIER_PY",
    "SUBSTRING_MATCH_VERIFIER_PY",
    "SWE_TOOL_CALL_VERIFIER_PY",
    "TOOL_CALL_VERIFIER_PY",
]
