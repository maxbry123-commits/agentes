"""opencode literals -> TRAIN==SERVE SFT dataset.

Rebuild an opencode agentic-trace dataset (whose lossy ``conversations`` field dropped the
system/tools/task prompt) into a serve-shaped SFT dataset, recovered from the literal
``prompt_token_ids`` / ``completion_token_ids`` columns. See ``literals_to_sft`` for the
full rationale and ``README.md`` for the end-to-end preprocessing chain.

CLI: ``python -m data.opencode_literals_to_sft --source_repo <repo> [--target_repo <repo>]``.
"""

from .literals_to_sft import (
    build_row,
    convert,
    leading_turns,
    main,
    parse_tool_calls,
    parse_tools,
    recover_system_content,
    resolve_tokenizer_ref,
    strip_tool_calls,
)

__all__ = [
    "build_row",
    "convert",
    "leading_turns",
    "main",
    "parse_tool_calls",
    "parse_tools",
    "recover_system_content",
    "resolve_tokenizer_ref",
    "strip_tool_calls",
]
