#!/usr/bin/env python3
"""Test model availability via OpenAI SDK compatible endpoint."""

from __future__ import annotations

import argparse
import os
import sys

from openai import OpenAI


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test an OpenAI-compatible model endpoint")
    parser.add_argument(
        "--base-url",
        default="https://tokenhub.tencentmaas.com/v1",
        help="OpenAI-compatible base URL",
    )
    parser.add_argument(
        "--model-id",
        default="ep-jsc7o0kw",
        help="Model ID used for API call",
    )
    parser.add_argument(
        "--model-name",
        default="MiniMax-M2.7",
        help="Model display name (for output only)",
    )
    parser.add_argument(
        "--prompt",
        default="请回复 OK，并简要说明你是哪个模型。",
        help="Prompt sent to the model",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key (defaults to TOKENHUB_API_KEY or OPENAI_API_KEY env var)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = args.api_key or os.getenv("TOKENHUB_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("[ERROR] Missing API key.")
        print("Set TOKENHUB_API_KEY or OPENAI_API_KEY, or pass --api-key.")
        return 2

    client = OpenAI(api_key=api_key, base_url=args.base_url)

    print("=== OpenAI SDK API Connectivity Test ===")
    print(f"Base URL   : {args.base_url}")
    print(f"Model Name : {args.model_name}")
    print(f"Model ID   : {args.model_id}")

    try:
        response = client.chat.completions.create(
            model=args.model_id,
            messages=[
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": args.prompt},
            ],
            max_tokens=128,
            temperature=0.2,
        )

        text = ""
        if response.choices and response.choices[0].message:
            text = response.choices[0].message.content or ""

        print("\n[OK] API call succeeded.")
        if text:
            print("Response:")
            print(text.strip())
        else:
            print("Response: (empty content)")
        return 0
    except Exception as exc:  # noqa: BLE001
        print("\n[FAIL] API call failed.")
        print(f"Error type: {type(exc).__name__}")
        print(f"Error msg : {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
