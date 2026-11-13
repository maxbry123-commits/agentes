"""Test Codex provider directly via ChatGPT OAuth credentials.

Requires prior login:
  uv run openagentd auth codex

Usage:
  uv run python -m manual.try_providers.try_codex
  uv run python -m manual.try_providers.try_codex --model gpt-5.4-mini --level low
  uv run python -m manual.try_providers.try_codex --no-stream
  uv run python -m manual.try_providers.try_codex --simple
"""

from __future__ import annotations

import argparse
import asyncio

from app.agent.providers.codex import CodexProvider
from manual.try_providers._common import (
    REASONING_PROMPT,
    SIMPLE_PROMPT,
    run_chat,
    run_stream,
)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test Codex provider")
    parser.add_argument("--model", default="gpt-5.4", help="Model (default: gpt-5.4)")
    parser.add_argument("--level", default=None, help="Thinking level: low|medium|high")
    parser.add_argument("--no-stream", action="store_true", help="Non-streaming chat()")
    parser.add_argument(
        "--simple", action="store_true", help="Use simple prompt instead of reasoning"
    )
    args = parser.parse_args()

    model_kwargs: dict[str, str] = {}
    if args.level:
        model_kwargs["thinking_level"] = args.level

    try:
        provider = CodexProvider(model=args.model, model_kwargs=model_kwargs)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        print("Run: uv run openagentd auth codex")
        return

    prompt = SIMPLE_PROMPT if args.simple else REASONING_PROMPT
    label = "codex"
    if args.level:
        label += f" thinking={args.level}"

    if args.no_stream:
        await run_chat(provider, prompt, label=label)
    else:
        await run_stream(provider, prompt, label=label)

    print(f"\n{'=' * 60}")
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
