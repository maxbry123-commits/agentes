"""Convert nvidia/Nemotron-RL-Agentic-Function-Calling-Pivot-v1.

This is a SINGLE-STEP "pivot" dataset: the agent is shown a conversation so far
(system + user + prior assistant turns + prior tool calls and their outputs)
plus the set of tools it may use, and must produce the NEXT action. Grading
compares that action to the row's `expected_action`.

`expected_action` comes in two shapes (agent_ref:
`toolcall_schema_single_step_tool_use_with_argument_comparison_agent`):

  - {"type": "function_call", "name": "<tool>", "arguments": "<json-string>"}
      → the next action is a tool call. We grade it deterministically with the
        TOOL_CALL_VERIFIER (exact tool-name match + argument comparison: the
        emitted arguments dict must match the expected arguments dict, with
        string values compared case-insensitively / whitespace-trimmed).

  - {"type": "message", "content": "<assistant free text>"}
      → the next action is a plain assistant reply. These are long, free-form
        natural-language responses (median ~2.3k chars); exact / normalized
        matching is wrong, so we route them to the LLM-judge verifier, which
        scores semantic equivalence to the expected content.

Distribution (full train split, 9620 rows): ~4919 function_call, ~4701 message.

Lossy by design: this is one decision step extracted from a multi-turn stateful
rollout. We do NOT execute tool side effects; we surface the prior tool calls /
outputs as transcript context so the agent can make an informed next decision.
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
from ..verifiers import LLM_JUDGE_VERIFIER_PY, TOOL_CALL_VERIFIER_PY
from . import register


_BASE_IMAGE = "python:3.11-slim-bookworm"
_SOURCE = "nvidia/Nemotron-RL-Agentic-Function-Calling-Pivot-v1"

# Caps. Rendered transcripts can be large (max observed rcp json ~111KB);
# instruction_md cap in the adapter is 256KB, we use 200KB here and truncate the
# transcript body to leave headroom for the instruction scaffolding.
_TRANSCRIPT_MAX = 180 * 1024
_INSTR_MAX = 220 * 1024

_TOOLCALL_HEADER = (
    "You are an agentic function-calling assistant. Below is the conversation "
    "so far, including any tools you have already called and their results, "
    "plus the catalogue of tools available to you. Decide the SINGLE next tool "
    "call to make.\n\n"
    "Write a JSON object to `/app/answer.txt` of exactly this form:\n\n"
    '    {"name": "<tool_name>", "arguments": { ... }}\n\n'
    "`name` must be one of the available tools; `arguments` must be a JSON "
    "object with the exact argument keys/values that tool needs for this step. "
    "The verifier compares your tool name and arguments against the expected "
    "next call. Emit ONLY the JSON object (it may be fenced in ```json), with "
    "no surrounding prose.\n\n"
    "Note: this is a single decision step extracted from a longer stateful "
    "rollout; prior tool calls shown below have already executed.\n\n"
    "===== TASK =====\n\n"
)

_MESSAGE_HEADER = (
    "You are an agentic assistant. Below is the conversation so far, including "
    "any tools you have already called and their results, plus the catalogue "
    "of tools available to you. The correct next action here is a direct "
    "natural-language reply to the user (NOT a tool call).\n\n"
    "Write your reply as plain text to `/app/response.txt`. Address the user's "
    "most recent request given everything that has happened in the "
    "conversation. Your reply will be scored by an LLM judge against a "
    "reference answer for semantic equivalence (same intent, same key "
    "information, same recommended action).\n\n"
    "Save ONLY your final reply to `/app/response.txt` (no scratch reasoning, "
    "no JSON wrappers, no shell transcripts). Set `task_complete: true` once "
    "`/app/response.txt` is written.\n\n"
    "===== TASK =====\n\n"
)


def _as_text(value: object) -> str:
    """Flatten a content value (str | list-of-parts | other) to a string."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        pieces: list[str] = []
        for part in value:
            if isinstance(part, dict):
                t = part.get("text") or part.get("content")
                if isinstance(t, str):
                    pieces.append(t)
            elif isinstance(part, str):
                pieces.append(part)
        return "\n".join(pieces)
    return ""


def _render_reasoning(summary: object) -> str:
    if isinstance(summary, list):
        out = []
        for s in summary:
            if isinstance(s, dict) and isinstance(s.get("text"), str):
                out.append(s["text"])
            elif isinstance(s, str):
                out.append(s)
        return "\n".join(out)
    if isinstance(summary, str):
        return summary
    return ""


def _render_transcript(input_items: object) -> str:
    """Render the responses-API `input` list into a readable transcript.

    Handles role-tagged turns (system/user/assistant) AND the responses-API
    item types: reasoning, function_call, function_call_output.
    """
    if not isinstance(input_items, list):
        return ""
    parts: list[str] = []
    for item in input_items:
        if not isinstance(item, dict):
            continue
        itype = item.get("type")
        role = item.get("role")
        if role in ("system", "user", "assistant", "developer"):
            text = _as_text(item.get("content"))
            if not text.strip():
                continue
            parts.append(f"[{role}]\n{text}")
        elif itype == "reasoning":
            text = _render_reasoning(item.get("summary"))
            if text.strip():
                parts.append(f"[assistant_reasoning]\n{text}")
        elif itype == "function_call":
            name = item.get("name", "?")
            args = item.get("arguments", "")
            if not isinstance(args, str):
                args = json.dumps(args, ensure_ascii=False)
            parts.append(f"[tool_call] {name}({args})")
        elif itype == "function_call_output":
            out = item.get("output", "")
            if not isinstance(out, str):
                out = json.dumps(out, ensure_ascii=False)
            parts.append(f"[tool_result]\n{out}")
        elif role:
            text = _as_text(item.get("content"))
            if text.strip():
                parts.append(f"[{role}]\n{text}")
    return "\n\n".join(parts)


def _render_tools(tools: object) -> str:
    """Render the available tool catalogue compactly."""
    if not isinstance(tools, list) or not tools:
        return "(no tools provided)"
    lines: list[str] = []
    for t in tools:
        if not isinstance(t, dict):
            continue
        name = t.get("name")
        if not isinstance(name, str):
            continue
        desc = t.get("description") if isinstance(t.get("description"), str) else ""
        params = t.get("parameters")
        try:
            params_json = (
                json.dumps(params, ensure_ascii=False) if params is not None else "{}"
            )
        except (TypeError, ValueError):
            params_json = "{}"
        lines.append(f"- {name}: {desc}\n    parameters: {params_json}")
    return "\n".join(lines) if lines else "(no tools provided)"


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
def convert_agentic_function_calling_pivot(
    row: dict, row_idx: int
) -> HarborTask | None:
    ea = row.get("expected_action")
    if not isinstance(ea, dict):
        return None
    ea_type = ea.get("type")

    rcp = row.get("responses_create_params")
    if not isinstance(rcp, dict):
        return None
    transcript = _render_transcript(rcp.get("input"))
    if not transcript.strip():
        return None
    tools_md = _render_tools(rcp.get("tools"))

    trajectory_id = row.get("trajectory_id")
    info = row.get("info") if isinstance(row.get("info"), dict) else {}

    body = f"Available tools:\n{tools_md}\n\nConversation so far:\n{transcript}"
    if len(body) > _TRANSCRIPT_MAX:
        body = body[:_TRANSCRIPT_MAX] + "\n\n[... transcript truncated ...]"

    if ea_type == "function_call":
        name = ea.get("name")
        if not isinstance(name, str) or not name:
            return None
        args = _parse_expected_arguments(ea.get("arguments"))
        if args is None:
            return None
        expected = [{"name": name, "arguments": args}]
        instruction = sanitize_text(
            _TOOLCALL_HEADER + body,
            field_name="instruction_md",
            max_len=_INSTR_MAX,
        ) + answer_delivery_guidance(
            "/app/answer.txt", what="the JSON tool-call object"
        )
        task_id = task_id_for(
            "agentic-fc-pivot",
            f"{trajectory_id}|{info.get('turn')}|{info.get('step')}|"
            + json.dumps(expected[0], sort_keys=True),
        )
        return HarborTask(
            task_id=task_id,
            instruction_md=instruction,
            dockerfile=render_dockerfile(base=_BASE_IMAGE),
            test_sh=STANDARD_TEST_SH,
            verifier_py=TOOL_CALL_VERIFIER_PY,
            verifier_data={"expected": expected},
            metadata=render_metadata(
                source_dataset=_SOURCE,
                source_uuid=None,
                extra={
                    "row_index": row_idx,
                    "family": "agentic_function_calling_pivot",
                    "action_type": "function_call",
                    "trajectory_id": trajectory_id,
                    "turn": info.get("turn"),
                    "step": info.get("step"),
                    "depth": info.get("depth"),
                    "expected_tool": name,
                    "conversion_lossy": True,
                },
            ),
        )

    if ea_type == "message":
        content = ea.get("content")
        if not isinstance(content, str) or not content.strip():
            return None
        content = sanitize_text(
            content, field_name="expected_content", max_len=64 * 1024
        )
        instruction = sanitize_text(
            _MESSAGE_HEADER + body,
            field_name="instruction_md",
            max_len=_INSTR_MAX,
        ) + answer_delivery_guidance("/app/response.txt", what="your reply")
        task_id = task_id_for(
            "agentic-msg-pivot",
            f"{trajectory_id}|{info.get('turn')}|{info.get('step')}|" + content[:256],
        )
        return HarborTask(
            task_id=task_id,
            instruction_md=instruction,
            dockerfile=render_dockerfile(
                base=_BASE_IMAGE,
                pip_packages=("litellm==1.51.3",),
            ),
            test_sh=STANDARD_TEST_SH,
            verifier_py=LLM_JUDGE_VERIFIER_PY,
            verifier_data={
                "instruction": (
                    "The assistant should reply to the user's most recent "
                    "request in the conversation. The reply must be a direct "
                    "natural-language message (not a tool call)."
                ),
                "principle": content,
                "judge_prompt_template": (
                    "You are scoring whether a candidate assistant reply is "
                    "semantically equivalent to a reference reply in an agentic "
                    "function-calling conversation.\n\n"
                    "Task context:\n{instruction}\n\n"
                    "Reference reply (the expected next message):\n{principle}\n\n"
                    "Candidate reply:\n{response}\n\n"
                    "Score how well the candidate matches the reference in "
                    "INTENT and KEY INFORMATION: does it convey the same "
                    "decision/recommendation, surface the same essential facts "
                    "or limitations, and ask for the same missing information? "
                    "Exact wording, formatting, and verbosity do NOT matter. "
                    "Score 0.0 (different intent / contradicts / omits the key "
                    "point) to 1.0 (same intent and key information).\n"
                    "End with \\boxed{{<score>}} on the last line."
                ),
                "score_threshold": 0.5,
            },
            task_toml=LLM_JUDGE_TASK_TOML,
            metadata=render_metadata(
                source_dataset=_SOURCE,
                source_uuid=None,
                extra={
                    "row_index": row_idx,
                    "family": "agentic_function_calling_pivot",
                    "action_type": "message",
                    "trajectory_id": trajectory_id,
                    "turn": info.get("turn"),
                    "step": info.get("step"),
                    "depth": info.get("depth"),
                    "judge": "litellm:default(openai/gpt-4o-mini)",
                    "conversion_lossy": True,
                },
            ),
        )

    # Unsupported / malformed expected_action type.
    return None
