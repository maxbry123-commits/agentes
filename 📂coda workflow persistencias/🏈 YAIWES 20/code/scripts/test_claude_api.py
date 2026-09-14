#!/usr/bin/env python3
"""Test Claude Messages API connectivity via anthropic SDK (not Claude Code SDK)."""

from __future__ import annotations

import argparse
import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test Claude API format endpoint")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Anthropic-compatible base URL (e.g. https://xxx)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Claude model name (e.g. claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key for Anthropic-compatible endpoint",
    )
    parser.add_argument(
        "--prompt",
        default="请回复 OK，并简要说明你当前使用的模型。",
        help="Prompt sent to Claude messages API",
    )
    return parser.parse_args()


def resolve_config(args: argparse.Namespace) -> tuple[str | None, str | None, str | None]:
    base_url = args.base_url or os.getenv("ANTHROPIC_BASE_URL") or os.getenv("CLAUDE_BASE_URL")
    model = args.model or os.getenv("ANTHROPIC_MODEL") or os.getenv("CLAUDE_MODEL")
    api_key = (
        args.api_key
        or os.getenv("ANTHROPIC_AUTH_TOKEN")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("CLAUDE_API_KEY")
        or os.getenv("TOKENHUB_API_KEY")
    )
    return base_url, model, api_key


def main() -> int:
    load_dotenv()
    args = parse_args()
    base_url, model, api_key = resolve_config(args)

    if not api_key:
        print("[ERROR] Missing API key.")
        print("Set CLAUDE_API_KEY / ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY, or pass --api-key.")
        return 2

    if not model:
        print("[ERROR] Missing model.")
        print("Set CLAUDE_MODEL / ANTHROPIC_MODEL, or pass --model.")
        return 2

    print("=== Claude API Connectivity Test (anthropic SDK) ===")
    print(f"Base URL: {base_url or '(default anthropic endpoint)'}")
    print(f"Model   : {model}")

    client = Anthropic(api_key=api_key, base_url=base_url)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=128,
            messages=[
                {"role": "user", "content": args.prompt},
            ],
        )

        text_parts: list[str] = []
        for block in response.content:
            if getattr(block, "type", "") == "text":
                text_parts.append(getattr(block, "text", ""))

        print("\n[OK] Claude API call succeeded.")
        if text_parts:
            print("Response:")
            print("\n".join(part.strip() for part in text_parts if part.strip()))
        else:
            print("Response: (no text blocks)")
        return 0
    except Exception as exc:  # noqa: BLE001
        print("\n[FAIL] Claude API call failed.")
        print(f"Error type: {type(exc).__name__}")
        print(f"Error msg : {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
