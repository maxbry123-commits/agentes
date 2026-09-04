import numpy as np
import pytest

from scripts.analysis.trace_metrics import parse_filter, tokenize_dataset


class _Tokenizer:
    def __call__(self, texts, *, add_special_tokens, return_length):
        assert add_special_tokens is False
        assert return_length is True
        return {"length": [len(text) for text in texts]}

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is True
        assert add_generation_prompt is False
        return list(range(sum(len(message["content"]) for message in messages)))


def test_tokenize_dataset_uses_shared_conversation_text_and_batches():
    dataset = [
        {"conversations": [{"role": "user", "content": "one"}]},
        {"conversations": [{"role": "user", "content": "two"}]},
    ]

    counts = tokenize_dataset(
        dataset,
        _Tokenizer(),
        representation="conversation_text",
        batch_size=1,
    )

    assert np.array_equal(counts, np.array([3, 3]))


def test_parse_filter_rejects_non_equality_filters():
    assert parse_filter("source==main") == ("source", "main")
    with pytest.raises(ValueError, match="column==value"):
        parse_filter("source=main")


def test_tokenize_dataset_keeps_serialized_and_chat_template_counts_separate():
    dataset = [{"conversations": [{"from": "human", "value": "one"}]}]

    assert np.array_equal(
        tokenize_dataset(dataset, _Tokenizer(), representation="serialized"),
        np.array([32]),
    )
    assert np.array_equal(
        tokenize_dataset(dataset, _Tokenizer(), representation="chat_template"),
        np.array([3]),
    )
