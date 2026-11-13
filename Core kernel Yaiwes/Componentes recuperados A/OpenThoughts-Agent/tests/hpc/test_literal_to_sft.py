"""Tests for scripts/harbor/literal_traces_to_sft — literal traces -> SFT conversion.

Covers the pure reconstruction logic with a fake tokenizer (no model/network): the
verbatim-assistant rebuild, the orphan-<think> fix, trailing-special strip, system/task
parse from the first prompt, the alignment guard, and the reasoning-preserving text render.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.harbor.literal_traces_to_sft import (  # noqa: E402
    build_record,
    clean_completion,
    fix_orphan_think,
    leading_context_messages,
    reconstruct_messages,
    render_text,
    to_sharegpt,
)


class FakeTokenizer:
    """Maps a token-id tuple to a fixed decoded string (stand-in for the real tokenizer)."""

    def __init__(self, mapping: dict[tuple, str]):
        self.mapping = mapping

    def decode(self, ids, skip_special_tokens=False):  # noqa: ARG002 - signature parity
        return self.mapping[tuple(ids)]


# Prompt[0] as the model saw it: system + user task, then the assistant primer (no closing
# <|im_end|>, so the primer is NOT parsed as a turn).
_PROMPT0 = (
    "<|im_start|>system\nSYS PROMPT<|im_end|>\n"
    "<|im_start|>user\nTASK BODY<|im_end|>\n"
    "<|im_start|>assistant\n<think>\n"
)
# completion 0 is an orphan-think (opener primed away); completion 1 is well-formed.
_COMP0 = "reasoning A</think>\n\nanswer A<|im_end|>"
_COMP1 = "<think></think>\nanswer B<|im_end|>"


def _row():
    return {
        "prompt_token_ids": [[1], [9]],
        "completion_token_ids": [[2], [3]],
        "task": "t-1",
        "conversations": [
            {
                "role": "user",
                "content": "",
            },  # empty leading user (task lives in prompt[0])
            {"role": "assistant", "content": "x"},
            {"role": "user", "content": "OBS 1"},  # tool observation
            {"role": "assistant", "content": "y"},
        ],
    }


def _tok():
    return FakeTokenizer({(1,): _PROMPT0, (2,): _COMP0, (3,): _COMP1})


def test_fix_orphan_think():
    assert fix_orphan_think("foo</think>bar") == "<think>foo</think>bar"
    assert (
        fix_orphan_think("<think>foo</think>") == "<think>foo</think>"
    )  # already opened
    assert fix_orphan_think("no tags") == "no tags"


def test_clean_completion_strips_trailing_special():
    assert clean_completion("hello<|im_end|>") == "hello"
    assert clean_completion("hello<|endoftext|>\n") == "hello"
    assert clean_completion("mid<|im_end|>text") == "mid<|im_end|>text"  # only trailing


def test_leading_context_messages_parses_system_and_task():
    msgs = leading_context_messages(_PROMPT0)
    assert msgs == [
        {"role": "system", "content": "SYS PROMPT"},
        {"role": "user", "content": "TASK BODY"},
    ]


def test_reconstruct_messages_verbatim_assistants_and_observations():
    messages = reconstruct_messages(_row(), _tok())
    assert [m["role"] for m in messages] == [
        "system",
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    # assistant 0: orphan-think fixed + trailing <|im_end|> stripped
    assert messages[2]["content"] == "<think>reasoning A</think>\n\nanswer A"
    # observation between assistants comes from the trace's user turn
    assert messages[3]["content"] == "OBS 1"
    # assistant 1: already-formed think, trailing special stripped
    assert messages[4]["content"] == "<think></think>\nanswer B"


def test_alignment_guard_drops_mismatched_rows():
    row = _row()
    row["conversations"] = row["conversations"][:2]  # 1 assistant turn vs 2 completions
    assert reconstruct_messages(row, _tok()) is None


def test_no_literals_returns_none():
    row = _row()
    row["completion_token_ids"] = [[], []]
    assert reconstruct_messages(row, _tok()) is None


def test_to_sharegpt_role_mapping():
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "u"},
        {"role": "assistant", "content": "a"},
    ]
    assert to_sharegpt(messages) == [
        {"from": "system", "value": "s"},
        {"from": "human", "value": "u"},
        {"from": "gpt", "value": "a"},
    ]


def test_render_text_preserves_every_turn_reasoning():
    messages = reconstruct_messages(_row(), _tok())
    text = render_text(messages)
    # both assistant turns' <think> survive (stock template would strip the non-final one)
    assert text.count("<think>") == 2
    assert text.startswith("<|im_start|>system\nSYS PROMPT<|im_end|>\n")
    for m in messages:
        assert m["content"] in text  # lossless


def test_build_record_shapes():
    rec = build_record(_row(), _tok(), schema="sharegpt")
    assert rec["num_turns"] == 5
    assert rec["task"] == "t-1"
    assert rec["conversations"][0] == {"from": "system", "value": "SYS PROMPT"}
    assert rec["text"].count("<tool_call>") == 0  # none in this fixture

    rec_oai = build_record(_row(), _tok(), schema="openai")
    assert rec_oai["conversations"][0] == {"role": "system", "content": "SYS PROMPT"}
