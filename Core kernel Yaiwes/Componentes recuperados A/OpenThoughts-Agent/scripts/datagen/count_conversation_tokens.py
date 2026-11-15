#!/usr/bin/env python3
"""Compute aggregate dataset tokens using one explicit conversation representation."""

from __future__ import annotations

import argparse
import sys

from datasets import load_dataset
from transformers import AutoTokenizer

from scripts.analysis.utils import (
    TOKEN_REPRESENTATIONS,
    count_conversation_tokens,
    serialize_conversation_value,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Given a HuggingFace dataset repo, load a split and report the aggregate "
            "token count using an explicitly selected conversation representation."
        )
    )
    parser.add_argument(
        "repo_id",
        help="Dataset repository on HuggingFace Hub (e.g. org/name).",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional dataset config/name.",
    )
    parser.add_argument(
        "--split",
        default="train",
        help="Dataset split to load (default: train).",
    )
    parser.add_argument(
        "--tokenizer",
        default="Qwen/Qwen3-8B",
        help="Tokenizer repo to use (default: Qwen/Qwen3-8B).",
    )
    parser.add_argument(
        "--representation",
        choices=TOKEN_REPRESENTATIONS,
        default="serialized",
        help=(
            "Token input to measure: serialized preserves the legacy compact JSON "
            "`conversations` count; conversation_text concatenates message text; "
            "chat_template uses the tokenizer's chat template (default: serialized)."
        ),
    )
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Forward trust_remote_code=True to AutoTokenizer.from_pretrained (needed for some custom tokenizers).",
    )
    return parser.parse_args()


def serialize_conversations(raw_value: object) -> str:
    """Backward-compatible name for the legacy serialized representation."""
    return serialize_conversation_value(raw_value)


def main() -> None:
    args = parse_args()

    print(
        f"[tokens] Loading dataset {args.repo_id} (split={args.split}, config={args.config})..."
    )
    dataset = (
        load_dataset(args.repo_id, args.config, split=args.split)
        if args.config
        else load_dataset(args.repo_id, split=args.split)
    )

    print(f"[tokens] Loading tokenizer {args.tokenizer}...")
    tokenizer = AutoTokenizer.from_pretrained(
        args.tokenizer,
        trust_remote_code=args.trust_remote_code or ("Qwen3" in args.tokenizer),
    )

    total_tokens = 0
    missing_count = 0
    invalid_count = 0

    print(f"[tokens] Iterating over samples (representation={args.representation})...")
    for example in dataset:
        if args.representation == "serialized" and "conversations" not in example:
            missing_count += 1
            continue
        try:
            total_tokens += count_conversation_tokens(
                example,
                tokenizer,
                args.representation,
            )
        except ValueError as exc:
            invalid_count += 1
            if invalid_count == 1:
                print(
                    f"[tokens] Warning: skipping invalid {args.representation} example: {exc}"
                )

    processed = len(dataset) if hasattr(dataset, "__len__") else "unknown"

    if missing_count:
        print(
            f"[tokens] Warning: skipped {missing_count} example(s) missing `conversations`."
        )
    if invalid_count:
        print(
            f"[tokens] Warning: skipped {invalid_count} invalid {args.representation} example(s)."
        )

    print(f"[tokens] Examples processed: {processed}")
    print(f"[tokens] Representation: {args.representation}")
    print(f"[tokens] Aggregate tokens: {total_tokens:,}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Interrupted.")
