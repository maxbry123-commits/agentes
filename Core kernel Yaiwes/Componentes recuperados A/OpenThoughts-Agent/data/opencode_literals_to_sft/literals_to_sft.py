#!/usr/bin/env python3
"""Rebuild an opencode agentic-trace dataset into a TRAIN==SERVE SFT dataset.

The opencode datagen trace datasets (e.g. ``penfever/nemotron-code-oracle-...-opencode-traces``)
store a LOSSY ``conversations`` field — no system message, an empty turn-0, no ``<tools>`` block,
tool calls as inline text, and tool results as ``role: user``. A model SFT'd on that field never
learns to condition on the task, the ``<tools>`` system block, or the opencode read/edit workflow,
and defaults to reflexive bash (the "densemixer swebench ~0" bug, ledger #2).

The full served prompt SURVIVES in the literal ``prompt_token_ids`` / ``completion_token_ids``
columns. This tool rebuilds each row into a structurally serve-shaped SFT example:

- a ``system`` turn = the opencode agent system prompt (recovered from ``prompt_token_ids[0]``),
- the ``tools`` schema (the 10 opencode functions), stored per-row so the training chat template
  renders the ``<tools>`` block exactly as the server does,
- a task-grounded ``user`` turn-0 (the problem statement, recovered from ``prompt_token_ids[0]``),
- **structured assistant ``tool_calls``** (parsed out of the literal completion — NOT inline text),
  with verbatim ``<think>`` reasoning preserved as the assistant ``content``,
- ``role: tool`` observation turns (NOT ``role: user``).

Rendered under the tools-aware Qwen3 chat template (byte-identical to what opencode serves),
this yields train==serve parity.

Output columns (schema is explicit → Arrow-safe):
- ``messages`` — list of ``{role, content, tool_calls: [{type, function: {name, arguments}}]}``.
  ``arguments`` is a JSON string for Arrow-uniformity; the SFT framework parses it to a dict
  before the chat template renders it (same path the server takes).
- ``tools`` — JSON string of the OpenAI tool list.
- ``task``, ``num_turns``, ``num_tool_calls``.

The correct tokenizer for decoding the LITERAL columns is the exact served (teacher) model — here
``Qwen/Qwen3.5-122B-A10B-FP8`` — auto-resolved from ``tokenizer_provenance.json`` (override
``--tokenizer``). Rows without literal tokens, or whose assistant-turn count does not match the
literal step count, are dropped (never emitted misaligned).

Examples:
  python -m data.opencode_literals_to_sft \
    --source_repo penfever/nemotron-code-oracle-filtered-qwen3.5-122b-131k-opencode-traces \
    --source_revision 6cc0c0b5ccec0792a61a98c384a1612bb38c2309 \
    --target_repo laion/nemotron-code-oracle-opencode-sft-serveparity

  # Dry-run: convert + structurally check + RENDER N rows under the student template (no upload).
  python -m data.opencode_literals_to_sft --source_repo <repo> \
    --student_model Qwen/Qwen3-30B-A3B-Thinking-2507 --validate 3

Provenance: this module was originally ``scripts/harbor/literal_traces_to_opencode_sft.py``
(the bug-ledger #2 serve-parity rebuild for the densemixer A/B SFT experiment). It was re-homed
here as reusable data-preprocessing code; the old path is now a thin re-export shim.
"""

from __future__ import annotations

import argparse
import json
import re

TOKENIZER_PROVENANCE_FILE = "tokenizer_provenance.json"
DEFAULT_TEACHER_TOKENIZER = "Qwen/Qwen3.5-122B-A10B-FP8"

# Qwen chat-template turn markers.
_TURN_RE = re.compile(r"<\|im_start\|>(\w+)\n(.*?)<\|im_end\|>", re.DOTALL)
_SPECIAL_TAIL_RE = re.compile(r"(<\|im_end\|>|<\|endoftext\|>)\s*$")
# XML tool-call format the teacher (Qwen3.5-122B) emits in the literal completion.
_TOOL_CALL_RE = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)
_FUNC_RE = re.compile(r"<function=([^>]+)>(.*)</function>", re.DOTALL)
_PARAM_RE = re.compile(r"<parameter=([^>]+)>\n?(.*?)\n?</parameter>", re.DOTALL)
# Fallback: the JSON tool-call form (harbor re-serializes some as {"name":..,"arguments":..}).
_TOOL_CALL_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


# --------------------------------------------------------------------------- #
# System / tools / task recovery from the literal turn-0 prompt
# --------------------------------------------------------------------------- #
def parse_tools(prompt0_text: str) -> list[dict]:
    """Extract the OpenAI tool list from the ``<tools>...</tools>`` block (one JSON per line)."""
    m = re.search(r"<tools>\s*(.*?)\s*</tools>", prompt0_text, re.DOTALL)
    if not m:
        return []
    tools = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            tools.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return tools


def recover_system_content(teacher_system: str) -> str:
    """Recover the opencode system prompt from the teacher-rendered system message.

    The teacher template wraps the opencode system content in tool boilerplate:
    ``# Tools ... <tools>...</tools> ... If you choose to call a function ... <IMPORTANT>...
    </IMPORTANT>`` then the genuine opencode prompt (``You are opencode ...``). We strip the
    teacher tool boilerplate (the student template regenerates its own JSON-format tool
    instructions from the ``tools`` param) and keep only the opencode content.
    """
    idx = teacher_system.find("</IMPORTANT>")
    if idx != -1:
        return teacher_system[idx + len("</IMPORTANT>") :].lstrip()
    idx = teacher_system.find("You are opencode")
    if idx != -1:
        return teacher_system[idx:].lstrip()
    idx = teacher_system.find("</tools>")
    if idx != -1:
        return teacher_system[idx + len("</tools>") :].lstrip()
    return teacher_system.strip()


def leading_turns(prompt0_text: str) -> list[dict]:
    """All fully-closed templated turns in the first-step prompt (system + task user turn)."""
    return [
        {"role": r, "content": c.strip()} for r, c in _TURN_RE.findall(prompt0_text)
    ]


# --------------------------------------------------------------------------- #
# Assistant turn: verbatim reasoning content + structured tool_calls
# --------------------------------------------------------------------------- #
def fix_orphan_think(text: str) -> str:
    """Prepend ``<think>`` when a completion closes ``</think>`` with no opener (gen-prompt primes it)."""
    if "</think>" in text and "<think>" not in text:
        return "<think>\n" + text
    return text


def _coerce_arg(name: str, key: str, value: str, type_map: dict) -> object:
    """Type a parsed XML parameter value using the tool schema, else best-effort JSON."""
    t = type_map.get(name, {}).get(key)
    if t == "string":
        return value
    if t in ("integer", "number", "boolean", "object", "array"):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value
    # unknown declared type: keep strings as strings unless they cleanly parse to a scalar/container
    try:
        parsed = json.loads(value)
        return parsed if not isinstance(parsed, str) else value
    except (json.JSONDecodeError, ValueError):
        return value


def parse_tool_calls(asst_text: str, type_map: dict) -> list[dict]:
    """Parse ``<tool_call>`` blocks (teacher XML, JSON fallback) into structured tool_calls.

    Returns ``[{type: function, function: {name, arguments: <json-string>}}]``. ``arguments`` is a
    JSON string for Arrow-uniformity; the SFT framework parses it back to a dict before the chat
    template renders it (same path the server takes).
    """
    calls = []
    for block in _TOOL_CALL_RE.findall(asst_text):
        fm = _FUNC_RE.search(block)
        if fm:
            name = fm.group(1).strip()
            args = {}
            for pk, pv in _PARAM_RE.findall(fm.group(2)):
                args[pk.strip()] = _coerce_arg(name, pk.strip(), pv, type_map)
            calls.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": json.dumps(args, ensure_ascii=False),
                    },
                }
            )
            continue
        jm = _TOOL_CALL_JSON_RE.search(block)
        if jm:
            try:
                j = json.loads(jm.group(0))
                name = j.get("name")
                a = j.get("arguments", {})
                if name:
                    calls.append(
                        {
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": a
                                if isinstance(a, str)
                                else json.dumps(a, ensure_ascii=False),
                            },
                        }
                    )
            except json.JSONDecodeError:
                pass
    return calls


def strip_tool_calls(asst_text: str) -> str:
    """Remove ``<tool_call>...</tool_call>`` blocks, leaving reasoning + inter-tool text as content."""
    content = _TOOL_CALL_RE.sub("", asst_text)
    content = _SPECIAL_TAIL_RE.sub("", content)
    return content.strip()


# --------------------------------------------------------------------------- #
# Row rebuild
# --------------------------------------------------------------------------- #
def build_row(row: dict, tok, *, drop_reasoning: bool = False) -> dict | None:
    """Rebuild one trace row into a serve-shaped SFT example, or None if not convertible."""
    completions = row.get("completion_token_ids")
    prompts = row.get("prompt_token_ids")
    conv = row.get("conversations") or []
    if not completions or not any(completions) or not prompts or not prompts[0]:
        return None

    n = len(completions)
    conv_assistants = [m for m in conv if m.get("role") == "assistant"]
    conv_users = [m for m in conv if m.get("role") == "user"]
    if len(conv_assistants) != n:
        return None  # alignment guard

    prompt0 = tok.decode(prompts[0], skip_special_tokens=False)
    lead = leading_turns(prompt0)
    if not lead or lead[0]["role"] != "system":
        return None
    tools = parse_tools(prompt0)
    if not tools:
        return None
    type_map = {}
    for t in tools:
        fn = t.get("function", {})
        props = (fn.get("parameters", {}) or {}).get("properties", {}) or {}
        type_map[fn.get("name")] = {k: (v or {}).get("type") for k, v in props.items()}

    system_content = recover_system_content(lead[0]["content"])
    task = next((m["content"] for m in lead[1:] if m["role"] == "user"), None)
    if not task:
        return None

    messages = [
        {"role": "system", "content": system_content, "tool_calls": []},
        {"role": "user", "content": task, "tool_calls": []},
    ]
    n_tool_calls = 0
    for k in range(n):
        asst = fix_orphan_think(tok.decode(completions[k], skip_special_tokens=False))
        tool_calls = parse_tool_calls(asst, type_map)
        content = strip_tool_calls(asst)
        if drop_reasoning and "</think>" in content:
            content = content.split("</think>")[-1].lstrip("\n")
        messages.append(
            {"role": "assistant", "content": content, "tool_calls": tool_calls}
        )
        n_tool_calls += len(tool_calls)
        if k < n - 1 and (k + 1) < len(conv_users):
            obs = (conv_users[k + 1].get("content") or "").strip()
            # strip a serialized <tool_response> wrapper if present (student template re-adds it)
            obs = re.sub(r"^<tool_response>\s*|\s*</tool_response>$", "", obs).strip()
            if obs:
                messages.append({"role": "tool", "content": obs, "tool_calls": []})
    return {
        "messages": messages,
        "tools": json.dumps(tools, ensure_ascii=False),
        "task": row.get("task"),
        "num_turns": len(messages),
        "num_tool_calls": n_tool_calls,
    }


# --------------------------------------------------------------------------- #
# I/O boundary
# --------------------------------------------------------------------------- #
def resolve_tokenizer_ref(
    source_repo: str, revision: str | None, override: str | None, token
) -> str:
    if override:
        return override
    from huggingface_hub import hf_hub_download

    try:
        path = hf_hub_download(
            source_repo,
            TOKENIZER_PROVENANCE_FILE,
            repo_type="dataset",
            revision=revision,
            token=token,
        )
        served = json.load(open(path)).get("served_model")
        if served:
            return served
    except Exception:  # noqa: BLE001
        pass
    return DEFAULT_TEACHER_TOKENIZER


def _features():
    from datasets import Features, Value

    tc = [
        {
            "type": Value("string"),
            "function": {"name": Value("string"), "arguments": Value("string")},
        }
    ]
    return Features(
        {
            "messages": [
                {"role": Value("string"), "content": Value("string"), "tool_calls": tc}
            ],
            "tools": Value("string"),
            "task": Value("string"),
            "num_turns": Value("int32"),
            "num_tool_calls": Value("int32"),
        }
    )


def convert(source_repo, revision, tok, *, limit, token, drop_reasoning=False):
    from datasets import load_dataset

    ds = load_dataset(
        source_repo, split="train", revision=revision, streaming=True, token=token
    )
    records = []
    seen = literal = converted = skipped = 0
    for row in ds:
        seen += 1
        if not (row.get("completion_token_ids") and any(row["completion_token_ids"])):
            continue
        literal += 1
        rec = build_row(row, tok, drop_reasoning=drop_reasoning)
        if rec is None:
            skipped += 1
            continue
        records.append(rec)
        converted += 1
        if converted % 500 == 0:
            print(f"  … {converted} converted ({seen} seen)")
        if limit and converted >= limit:
            break
    stats = {
        "seen": seen,
        "literal": literal,
        "converted": converted,
        "skipped_alignment": skipped,
    }
    return records, stats


def _render_check(rec, student_model, token):
    """Render one rebuilt row under the STUDENT tools-aware template + report the parity signals."""
    from transformers import AutoTokenizer

    stok = AutoTokenizer.from_pretrained(
        student_model, token=token, trust_remote_code=True
    )
    tools = json.loads(rec["tools"])
    # String tool_call arguments must be parsed to dict before templating; mirror that here.
    msgs = json.loads(json.dumps(rec["messages"]))
    for m in msgs:
        for tc in m.get("tool_calls") or []:
            a = tc["function"]["arguments"]
            if isinstance(a, str):
                try:
                    tc["function"]["arguments"] = json.loads(a)
                except json.JSONDecodeError:
                    pass
        if not m.get("tool_calls"):
            m.pop("tool_calls", None)
    rendered = stok.apply_chat_template(
        msgs, tools=tools, tokenize=False, add_generation_prompt=False
    )
    return rendered


def main():
    import os

    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--source_repo", required=True)
    p.add_argument("--source_revision", default=None)
    p.add_argument("--target_repo", default=None)
    p.add_argument(
        "--target_revision_message", default="serve-parity rebuild from literal tokens"
    )
    p.add_argument(
        "--tokenizer",
        default=None,
        help="teacher tokenizer override (decodes literals)",
    )
    p.add_argument(
        "--student_model",
        default="Qwen/Qwen3-30B-A3B-Thinking-2507",
        help="student model whose tools-aware template renders the parity check",
    )
    p.add_argument("--private", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument(
        "--validate", type=int, default=0, help="convert+check+render N rows, no upload"
    )
    p.add_argument(
        "--drop_reasoning",
        action="store_true",
        help="drop <think> from assistant content (default: keep verbatim reasoning)",
    )
    args = p.parse_args()
    token = os.environ.get("HF_TOKEN")

    from transformers import AutoTokenizer

    tref = resolve_tokenizer_ref(
        args.source_repo, args.source_revision, args.tokenizer, token
    )
    print(f"[teacher tokenizer] {tref}")
    tok = AutoTokenizer.from_pretrained(tref, token=token, trust_remote_code=True)

    if args.validate:
        records, stats = convert(
            args.source_repo,
            args.source_revision,
            tok,
            limit=args.validate,
            token=token,
            drop_reasoning=args.drop_reasoning,
        )
        for i, rec in enumerate(records, 1):
            roles = [m["role"] for m in rec["messages"]]
            print(
                f"\n===== row {i} | {len(rec['messages'])} msgs | task={rec['task']!r} "
                f"| tool_calls={rec['num_tool_calls']} ====="
            )
            print("roles:", roles)
            assert (
                rec["messages"][0]["role"] == "system" and rec["messages"][0]["content"]
            ), "no system content"
            assert (
                rec["messages"][1]["role"] == "user" and rec["messages"][1]["content"]
            ), "no task turn"
            assert any(m["role"] == "assistant" for m in rec["messages"]), (
                "no assistant"
            )
            assert any(
                m["role"] == "assistant" and m["tool_calls"] for m in rec["messages"]
            ), "no structured tool_calls"
            assert "<tools>" not in rec["messages"][0]["content"], (
                "system still carries a <tools> block"
            )
            rendered = _render_check(rec, args.student_model, token)
            print("[render] len:", len(rendered))
            for probe in [
                "<|im_start|>system",
                "<tools>",
                "You may call one or more functions",
                "<|im_start|>user",
                "<tool_call>",
                '"arguments"',
                "<tool_response>",
                "<think>",
            ]:
                print(f"   rendered has {probe!r}: {probe in rendered}")
            print("[render HEAD :700]\n", rendered[:700])
            print(
                "[render around first tool_call]\n",
                rendered[
                    max(0, rendered.find("<tool_call>") - 120) : rendered.find(
                        "<tool_call>"
                    )
                    + 320
                ],
            )
            print(
                "[render around first tool_response]\n",
                rendered[
                    max(0, rendered.find("<tool_response>") - 60) : rendered.find(
                        "<tool_response>"
                    )
                    + 200
                ],
            )
        print(f"\n[validate] {stats}")
        return

    if not args.target_repo:
        raise SystemExit("--target_repo required unless --validate")
    from datasets import Dataset

    records, stats = convert(
        args.source_repo,
        args.source_revision,
        tok,
        limit=args.limit,
        token=token,
        drop_reasoning=args.drop_reasoning,
    )
    print(f"[convert] {stats}")
    if not records:
        raise SystemExit("[convert] 0 rows converted — nothing to upload.")
    out = Dataset.from_list(records, features=_features())
    print(f"[upload] {len(out)} rows -> {args.target_repo} (private={args.private})")
    out.push_to_hub(
        args.target_repo,
        private=args.private,
        token=token,
        commit_message=args.target_revision_message,
    )
    print(f"[done] https://huggingface.co/datasets/{args.target_repo} rows={len(out)}")


if __name__ == "__main__":
    main()
