"""Convert nvidia/Nemotron-RL-Agentic-SWE-Pivot-v1.

Single-step "pivot" on SWE agent trajectories. The agent is shown an in-progress
OpenHands / codeact SWE conversation (system + user issue + prior bash/edit tool
calls and their outputs) plus the catalogue of tools it may use, and must produce
the NEXT action. Grading compares that action to the row's `expected_action`.

Schema observations (full train split, 50,661 rows):
  - `expected_action` is **100% `function_call`** — there are NO `message` rows
    in this dataset (unlike the function-calling-pivot sibling). Every row is
    graded deterministically by the SWE tool-call verifier; no LLM judge is
    used.
  - `responses_create_params.input` is the conversation so far;
    `responses_create_params.tools` is the available tool catalogue.
  - Tool names span execute_bash / shell_command / bash / str_replace_editor /
    read_file / read / grep / grep_files / apply_patch / edit / todo_write /
    update_plan / finish / glob / list_dir / think.
  - Arguments are always valid JSON strings (0 unparseable in the full split).
    `command` / `path` / `old_str` / `new_str` / `pattern` values are long,
    exact strings. Numeric args (offset / limit / view_range / timeout) and
    structured args (todos, plan) also appear.

ARGUMENT-MATCHING SEMANTICS (the crux for SWE — see swe_tool_call_match.py):
  - tool name: exact, case-sensitive.
  - `security_risk` is DROPPED from both sides. It is a volatile, agent-self-
    assigned advisory label present in only ~42% of rows, with inconsistent
    values (LOW / MEDIUM / medium / even a free-text sentence). It is not part
    of the action semantics; grading on it would unfairly fail correct
    commands.
  - remaining argument keys must match exactly (same key set).
  - string values: case-sensitive (shell/code is case-sensitive — `cd
    /Workspace` != `cd /workspace`) but WHITESPACE-NORMALIZED (strip + collapse
    internal whitespace runs), so cosmetic spacing/indentation differences in
    an otherwise-identical command still pass.
  - non-string values (numbers, lists, nested dicts): exact equality.

This is faithful to a hard pivot: exact long-command matching is strict, so
pass rates will be low, but a wrong command still scores 0 and the correct
command (modulo spacing + the advisory risk label) scores 1.

Lossy by design: one decision step extracted from a multi-turn stateful rollout.
We do NOT execute tool side effects or run repo tests; prior tool calls/outputs
are surfaced as transcript context only.
"""

from __future__ import annotations

import json

from ..adapter import (
    HarborTask,
    STANDARD_TEST_SH,
    answer_delivery_guidance,
    render_dockerfile,
    render_metadata,
    sanitize_text,
    task_id_for,
)
from ..verifiers import SWE_TOOL_CALL_VERIFIER_PY
from . import register
from .agentic_function_calling_pivot import _render_tools, _render_transcript

_BASE_IMAGE = "python:3.11-slim-bookworm"
_SOURCE = "nvidia/Nemotron-RL-Agentic-SWE-Pivot-v1"

# Rendered SWE transcripts can be large (long file views, test outputs).
_TRANSCRIPT_MAX = 180 * 1024
_INSTR_MAX = 220 * 1024

_HEADER = (
    "You are an agentic software-engineering assistant operating in an "
    "OpenHands/codeact-style loop on a checked-out repository. Below is the "
    "conversation so far, including the user's task, any tools you have already "
    "called and their results, plus the catalogue of tools available to you. "
    "Decide the SINGLE next tool call to make.\n\n"
    "Write a JSON object to `/app/answer.txt` of exactly this form:\n\n"
    '    {"name": "<tool_name>", "arguments": { ... }}\n\n'
    "`name` must be one of the available tools (e.g. `execute_bash`, "
    "`str_replace_editor`, `grep_files`, `read_file`); `arguments` must be a "
    "JSON object with the exact argument keys/values that tool needs for this "
    "step. The verifier compares your tool name and arguments against the "
    "expected next action: tool name must match exactly, and argument values "
    "must match (shell commands and paths are case-sensitive but compared with "
    "whitespace normalized; an optional `security_risk` label is ignored). "
    "Emit ONLY the JSON object (it may be fenced in ```json), with no "
    "surrounding prose.\n\n"
    "Note: this is a single decision step extracted from a longer stateful "
    "rollout; prior tool calls shown below have already executed against the "
    "repository.\n\n"
    "===== TASK =====\n\n"
)


def _parse_expected_arguments(args: object) -> dict | None:
    if isinstance(args, dict):
        parsed = args
    elif isinstance(args, str):
        try:
            parsed = json.loads(args) if args.strip() else {}
        except Exception:
            return None
    else:
        return None
    if not isinstance(parsed, dict):
        return None
    # Ensure JSON-serializable (verifier_data must be JSON).
    try:
        json.dumps(parsed, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError):
        return None
    return parsed


@register(_SOURCE)
def convert_agentic_swe_pivot(row: dict, row_idx: int) -> HarborTask | None:
    ea = row.get("expected_action")
    if not isinstance(ea, dict):
        return None
    # This dataset is 100% function_call; skip anything else defensively.
    if ea.get("type") != "function_call":
        return None
    name = ea.get("name")
    if not isinstance(name, str) or not name:
        return None
    args = _parse_expected_arguments(ea.get("arguments"))
    if args is None:
        return None

    rcp = row.get("responses_create_params")
    if not isinstance(rcp, dict):
        return None
    transcript = _render_transcript(rcp.get("input"))
    if not transcript.strip():
        return None
    tools_md = _render_tools(rcp.get("tools"))

    trajectory_id = row.get("trajectory_id")
    info = row.get("info") if isinstance(row.get("info"), dict) else {}
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}

    body = f"Available tools:\n{tools_md}\n\nConversation so far:\n{transcript}"
    if len(body) > _TRANSCRIPT_MAX:
        body = body[:_TRANSCRIPT_MAX] + "\n\n[... transcript truncated ...]"

    expected = [{"name": name, "arguments": args}]
    # Teach the TERMINAL agent HOW to deliver the answer (write the JSON
    # tool-call object to /app/answer.txt via a shell heredoc). The existing
    # answer-format spec in _HEADER says WHAT to write; this says HOW. Appended
    # after transcript truncation so the delivery guidance is always present.
    delivery = answer_delivery_guidance(
        "/app/answer.txt",
        what="the JSON tool-call object (name + arguments)",
    )
    instruction = sanitize_text(
        _HEADER + body + delivery,
        field_name="instruction_md",
        max_len=_INSTR_MAX,
    )
    task_id = task_id_for(
        "agentic-swe-pivot",
        f"{trajectory_id}|{info.get('turn')}|{info.get('step')}|"
        + json.dumps(expected[0], sort_keys=True),
    )
    return HarborTask(
        task_id=task_id,
        instruction_md=instruction,
        dockerfile=render_dockerfile(base=_BASE_IMAGE),
        test_sh=STANDARD_TEST_SH,
        verifier_py=SWE_TOOL_CALL_VERIFIER_PY,
        verifier_data={"expected": expected},
        metadata=render_metadata(
            source_dataset=_SOURCE,
            source_uuid=None,
            extra={
                "row_index": row_idx,
                "family": "agentic_swe_pivot",
                "action_type": "function_call",
                "trajectory_id": trajectory_id,
                "turn": info.get("turn"),
                "step": info.get("step"),
                "depth": info.get("depth"),
                "expected_tool": name,
                "agent_cls": meta.get("agent_cls"),
                "instance_id": meta.get("instance_id"),
                "pass_rate": row.get("pass_rate"),
                "conversion_lossy": True,
            },
        ),
    )
