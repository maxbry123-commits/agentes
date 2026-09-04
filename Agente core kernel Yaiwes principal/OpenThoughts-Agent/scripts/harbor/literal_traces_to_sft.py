#!/usr/bin/env python3
"""Convert a literal-token trace dataset into SFT conversations + a flat training string.

The opencode datagen trace datasets (produced by ``make_and_upload_trace_dataset`` on a
``--record_literal`` job) carry per-step ``prompt_token_ids`` / ``completion_token_ids``
alongside a text ``conversations`` column. This tool rebuilds each row as an SFT example
whose **assistant turns are decoded VERBATIM from the literal completion tokens** — so they
carry the model's real reasoning (``<think>…</think>``) and native tool calls
(``<tool_call><function=…>``), not harbor's re-serialized text. System + task turns are
decoded from the first-step prompt; tool/observation turns come from the trace's user turns.
Rows without literal tokens (or whose assistant-turn count does not match the literal step
count) are dropped rather than emitted misaligned.

The correct tokenizer is the EXACT one the engine served with (a same-family tokenizer
decodes word tokens to garbage). It is auto-resolved from the source dataset's
``tokenizer_provenance.json`` stamp (written by ``make_and_upload_trace_dataset``); override
with ``--tokenizer`` (an HF repo id, local dir, or ``gs://`` mirror prefix).

Output columns:
- ``conversations`` — ShareGPT ``[{from: system|human|gpt, value}]`` (or OpenAI
  ``[{role, content}]`` with ``--schema openai``).
- ``text`` — the flat conversation with Qwen ``<|im_start|>`` markers, **reasoning preserved
  on every turn** (the stock chat template strips ``<think>`` from history; this does not).
- ``task``, ``num_turns``.

Examples:
  # Auto-resolve tokenizer from the source's provenance stamp; upload PUBLIC.
  python -m scripts.harbor.literal_traces_to_sft \
    --source_repo penfever/nemotron-code-oracle-filtered-qwen3.5-122b-131k-opencode-traces \
    --target_repo laion/nemotron-code-oracle-qwen3.5-122b-opencode-sft

  # Dry-run: print + structurally check N converted rows, no upload.
  python -m scripts.harbor.literal_traces_to_sft --source_repo <repo> --validate 3
"""

from __future__ import annotations

import argparse
import re
import tempfile

TOKENIZER_PROVENANCE_FILE = "tokenizer_provenance.json"

# Qwen chat-template turn: <|im_start|>role\n ... <|im_end|>
_TURN_RE = re.compile(r"<\|im_start\|>(\w+)\n(.*?)<\|im_end\|>", re.DOTALL)
_SPECIAL_TAIL_RE = re.compile(r"(<\|im_end\|>|<\|endoftext\|>)\s*$")
_ROLE_TO_SHAREGPT = {
    "system": "system",
    "user": "human",
    "assistant": "gpt",
    "tool": "human",
}
# Tokenizer files pulled from a gs:// mirror prefix (enough to decode; no weights).
_TOKENIZER_FILES = (
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
)


def fix_orphan_think(text: str) -> str:
    """Prepend ``<think>`` when a completion has a closing ``</think>`` but no opener.

    The generation prompt primes ``<think>``, so the engine returns only the tokens AFTER
    it — the completion carries ``</think>`` with no opener. Mirrors harbor's exporter fix so
    the assistant content is a well-formed reasoning block.
    """
    if "</think>" in text and "<think>" not in text:
        return "<think>" + text
    return text


def clean_completion(text: str) -> str:
    """Strip the trailing turn-terminator special token from a decoded completion."""
    return _SPECIAL_TAIL_RE.sub("", text)


def leading_context_messages(prompt0_text: str) -> list[dict]:
    """All templated turns in the first-step prompt (system + initial user task).

    Returns ``[{role, content}]`` for every ``<|im_start|>role … <|im_end|>`` block in the
    decoded first prompt — i.e. the context the model saw before its first generation.
    """
    return [
        {"role": role, "content": content.strip()}
        for role, content in _TURN_RE.findall(prompt0_text)
    ]


def reconstruct_messages(row: dict, tok) -> list[dict] | None:
    """Rebuild OpenAI-style ``[{role, content}]`` for one row, or None if not convertible.

    - system + task: parsed from ``decode(prompt_token_ids[0])``.
    - assistant turn k: verbatim ``decode(completion_token_ids[k])`` (+ orphan-think fix,
      trailing-special strip).
    - observation before assistant k+1: the trace's ``k+1``-th user turn (environment text).

    Returns None when literals are absent/empty, the first prompt is missing, or the trace's
    assistant-turn count does not match the literal step count (alignment guard — never emit
    an assistant target bound to the wrong step).
    """
    completions = row.get("completion_token_ids")
    prompts = row.get("prompt_token_ids")
    conv = row.get("conversations") or []
    if not completions or not any(completions) or not prompts or not prompts[0]:
        return None

    n = len(completions)
    conv_assistants = [m for m in conv if m.get("role") == "assistant"]
    conv_users = [m for m in conv if m.get("role") == "user"]
    if len(conv_assistants) != n:
        return None

    messages = leading_context_messages(
        tok.decode(prompts[0], skip_special_tokens=False)
    )
    if not messages:
        return None

    for k in range(n):
        asst = clean_completion(
            fix_orphan_think(tok.decode(completions[k], skip_special_tokens=False))
        )
        messages.append({"role": "assistant", "content": asst})
        if k < n - 1 and (k + 1) < len(conv_users):
            obs = (conv_users[k + 1].get("content") or "").strip()
            if obs:
                messages.append({"role": "user", "content": obs})
    return messages


def to_sharegpt(messages: list[dict]) -> list[dict]:
    """Map OpenAI-style messages to ShareGPT ``[{from, value}]``."""
    return [
        {"from": _ROLE_TO_SHAREGPT.get(m["role"], "human"), "value": m["content"]}
        for m in messages
    ]


def render_text(messages: list[dict]) -> str:
    """Flatten messages to a Qwen-markered string, PRESERVING every turn's reasoning.

    The stock Qwen chat template strips ``<think>`` from history (an inference-time
    optimization), which would drop the per-turn reasoning that SFT wants to supervise. This
    hand-render keeps each assistant turn's verbatim ``<think>`` / ``<tool_call>`` content, so
    the flat ``text`` is lossless.
    """
    return "".join(
        f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in messages
    )


def build_record(row: dict, tok, *, schema: str = "sharegpt") -> dict | None:
    """Convert one trace row to an SFT record, or None if not convertible."""
    messages = reconstruct_messages(row, tok)
    if messages is None:
        return None
    conversations = messages if schema == "openai" else to_sharegpt(messages)
    return {
        "conversations": conversations,
        "text": render_text(messages),
        "task": row.get("task"),
        "num_turns": len(messages),
    }


# --------------------------------------------------------------------------- #
# I/O boundary
# --------------------------------------------------------------------------- #
def resolve_tokenizer_ref(
    source_repo: str, override: str | None, token: str | None
) -> str:
    """Return the tokenizer reference to load: ``--tokenizer`` override, else the stamp.

    Reads ``served_model`` from the source dataset's ``tokenizer_provenance.json`` (written by
    ``make_and_upload_trace_dataset``). Fails loud if neither is available — decoding literal
    token IDs with the wrong tokenizer yields garbage, so we never guess.
    """
    if override:
        return override
    import json

    from huggingface_hub import hf_hub_download

    try:
        path = hf_hub_download(
            source_repo, TOKENIZER_PROVENANCE_FILE, repo_type="dataset", token=token
        )
    except Exception as exc:  # noqa: BLE001 - surface a precise, actionable error
        raise SystemExit(
            f"No --tokenizer given and could not read {TOKENIZER_PROVENANCE_FILE} from "
            f"{source_repo} ({exc}). Pass --tokenizer <hf-repo|local-dir|gs://mirror> — the "
            "literal token IDs only decode with the exact served-model tokenizer."
        ) from exc
    served = json.loads(open(path).read()).get("served_model")
    if not served:
        raise SystemExit(
            f"{TOKENIZER_PROVENANCE_FILE} in {source_repo} has no 'served_model'; pass --tokenizer."
        )
    return served


def load_tokenizer(ref: str):
    """Load the tokenizer from an HF repo id, local dir, or ``gs://`` mirror prefix."""
    from transformers import AutoTokenizer

    if ref.startswith("gs://"):
        from upath import UPath

        tmp = tempfile.mkdtemp(prefix="sft_tok_")
        base = UPath(ref)
        for name in _TOKENIZER_FILES:
            src = base / name
            if src.exists():
                (UPath(tmp) / name).write_bytes(src.read_bytes())
        ref = tmp
    return AutoTokenizer.from_pretrained(ref)


def convert_dataset(
    source_repo: str, tok, *, schema: str, limit: int | None, token: str | None
):
    """Stream the source trace dataset and yield converted SFT records + conversion stats."""
    from datasets import load_dataset

    ds = load_dataset(source_repo, split="train", streaming=True, token=token)
    records: list[dict] = []
    seen = literal = converted = skipped = 0
    for row in ds:
        seen += 1
        if not (row.get("completion_token_ids") and any(row["completion_token_ids"])):
            continue
        literal += 1
        rec = build_record(row, tok, schema=schema)
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


def _dataset_card(source_repo: str, tokenizer_ref: str, schema: str) -> str:
    conv_desc = (
        "ShareGPT `[{from: system|human|gpt, value}]`"
        if schema == "sharegpt"
        else "OpenAI `[{role, content}]`"
    )
    return (
        "---\n"
        "tags:\n- sft\n- agent-traces\n- literal-tokens\nlanguage:\n- en\n---\n\n"
        "# Literal-token agent traces → SFT\n\n"
        f"SFT conversations distilled from `{source_repo}`. Each **assistant** turn is decoded "
        f"**verbatim** from the serving engine's literal completion token IDs with the exact "
        f"`{tokenizer_ref}` tokenizer — carrying the model's real reasoning (`<think>…</think>`) "
        "and native tool calls. System + task turns are decoded from the first-step prompt; "
        "tool/observation turns come from the trace. Rows without literal tokens are dropped.\n\n"
        "## Fields\n"
        f"- `conversations` — {conv_desc}.\n"
        "- `text` — flat conversation with Qwen `<|im_start|>` markers, reasoning preserved on "
        "every turn (the stock chat template strips `<think>` from history; this string does not).\n"
        "- `task`, `num_turns`.\n"
    )


def convert_and_upload(
    source_repo: str,
    target_repo: str,
    *,
    tokenizer_ref: str,
    tok,
    schema: str,
    private: bool,
    limit: int | None,
    token: str | None,
) -> None:
    """Convert the source trace dataset and push the SFT dataset (+ card) to ``target_repo``."""
    from datasets import Dataset
    from huggingface_hub import HfApi

    records, stats = convert_dataset(
        source_repo, tok, schema=schema, limit=limit, token=token
    )
    print(f"[convert] {stats}")
    if not records:
        raise SystemExit(
            "[convert] 0 rows converted — nothing to upload (no literal-bearing rows?)."
        )

    out = Dataset.from_list(records)
    print(f"[upload] pushing {len(out)} rows -> {target_repo} (private={private})")
    out.push_to_hub(target_repo, private=private, token=token)
    HfApi().upload_file(
        path_or_fileobj=_dataset_card(source_repo, tokenizer_ref, schema).encode(
            "utf-8"
        ),
        path_in_repo="README.md",
        repo_id=target_repo,
        repo_type="dataset",
        commit_message="Add dataset card",
        token=token,
    )
    print(f"[done] https://huggingface.co/datasets/{target_repo}  rows={len(out)}")


def _validate(
    source_repo: str, tok, *, schema: str, n_rows: int, token: str | None
) -> None:
    """Print + structurally check the first ``n_rows`` converted rows (no upload)."""
    records, stats = convert_dataset(
        source_repo, tok, schema=schema, limit=n_rows, token=token
    )
    from_key, val_key = (
        ("from", "value") if schema == "sharegpt" else ("role", "content")
    )
    sys_role = "system"
    asst_role = "gpt" if schema == "sharegpt" else "assistant"
    for i, rec in enumerate(records, 1):
        conv = rec["conversations"]
        print(f"\n===== row {i} | {len(conv)} msgs | task={rec['task']!r} =====")
        print("roles:", [m[from_key] for m in conv])
        for m in conv[:5]:
            print(f"  [{m[from_key]}] {m[val_key][:150]!r}")
        assert conv[0][from_key] == sys_role, "first turn is not the system prompt"
        assert any(m[from_key] == asst_role for m in conv), "no assistant turns"
        assert any(
            m[from_key] == asst_role and "<think>" in m[val_key] for m in conv
        ), "no reasoning"
        assert all(
            m[val_key] in rec["text"] for m in conv if m[from_key] == asst_role
        ), "assistant turn missing from text"
    print(f"\n[validate] {stats}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert a literal-token trace dataset into an SFT conversations dataset."
    )
    p.add_argument(
        "--source_repo",
        required=True,
        help="HF traces dataset with literal token columns",
    )
    p.add_argument(
        "--target_repo", help="Destination HF dataset repo (required unless --validate)"
    )
    p.add_argument(
        "--tokenizer",
        default=None,
        help="Tokenizer ref (HF repo id, local dir, or gs:// mirror). Default: auto-resolve "
        f"served_model from the source's {TOKENIZER_PROVENANCE_FILE}.",
    )
    p.add_argument(
        "--schema",
        choices=["sharegpt", "openai"],
        default="sharegpt",
        help="conversations schema",
    )
    p.add_argument(
        "--private", action="store_true", help="upload private (default: public)"
    )
    p.add_argument(
        "--limit", type=int, default=None, help="convert at most N rows (debug)"
    )
    p.add_argument(
        "--validate",
        type=int,
        default=0,
        help="print+check N converted rows, no upload",
    )
    return p.parse_args()


def main() -> None:
    import os

    args = _parse_args()
    token = os.environ.get("HF_TOKEN")
    tokenizer_ref = resolve_tokenizer_ref(args.source_repo, args.tokenizer, token)
    print(f"[tokenizer] using {tokenizer_ref}")
    tok = load_tokenizer(tokenizer_ref)

    if args.validate:
        _validate(
            args.source_repo, tok, schema=args.schema, n_rows=args.validate, token=token
        )
        return
    if not args.target_repo:
        raise SystemExit("--target_repo is required unless --validate is used.")
    convert_and_upload(
        args.source_repo,
        args.target_repo,
        tokenizer_ref=tokenizer_ref,
        tok=tok,
        schema=args.schema,
        private=bool(args.private),
        limit=args.limit,
        token=token,
    )


if __name__ == "__main__":
    main()
