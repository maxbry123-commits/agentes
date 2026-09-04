"""Shared dataset loading, filtering, and token-counting helpers for trace analysis."""

from __future__ import annotations

from typing import Optional

import numpy as np
from datasets import load_dataset

from scripts.analysis.utils import (
    TokenRepresentation,
    count_conversation_tokens,
    render_token_representation,
    validate_token_representation,
)


def tokenize_dataset(
    ds,
    tokenizer,
    *,
    representation: TokenRepresentation,
    batch_size: int = 512,
) -> np.ndarray:
    """Return per-row counts for one explicitly selected token representation.

    The caller must select a representation. ``serialized``,
    ``conversation_text``, and ``chat_template`` are separate measurements,
    not compatibility aliases for one another.
    """
    representation = validate_token_representation(representation)
    if representation == "chat_template":
        return np.array(
            [count_conversation_tokens(row, tokenizer, representation) for row in ds]
        )

    texts = [render_token_representation(row, representation) for row in ds]
    counts: list[int] = []
    for start in range(0, len(texts), batch_size):
        encoded = tokenizer(
            texts[start : start + batch_size],
            add_special_tokens=False,
            return_length=True,
        )
        counts.extend(encoded["length"])
    return np.array(counts)


def parse_filter(filter_str: str) -> tuple[str, str]:
    """Parse a ``column==value`` dataset filter."""
    if "==" not in filter_str:
        raise ValueError(
            f"Filter must be in 'column==value' format, got: {filter_str!r}"
        )
    column, value = filter_str.split("==", 1)
    return column.strip(), value.strip()


def load_and_filter(repo_id: str, split: str, filter_spec: Optional[str]) -> tuple:
    """Load a Hub dataset and optionally apply an equality filter."""
    print(f"Loading {repo_id} (split={split})...")
    try:
        dataset = load_dataset(repo_id, split=split)
    except Exception:
        dataset_dict = load_dataset(repo_id)
        available = list(dataset_dict.keys())
        print(f"  Available splits: {available}")
        dataset = dataset_dict[available[0]]

    original_count = len(dataset)
    print(f"  Columns: {dataset.column_names}")
    print(f"  Rows: {original_count:,}")

    if not filter_spec:
        return dataset, 0

    column, value = parse_filter(filter_spec)
    if column not in dataset.column_names:
        print(f"  Warning: column '{column}' not found, skipping filter")
        return dataset, 0

    filtered = dataset.filter(lambda row: row.get(column) == value)
    dropped_count = original_count - len(filtered)
    print(
        f"  Filter '{column}=={value}': kept {len(filtered):,}, dropped {dropped_count:,}"
    )
    return filtered, dropped_count
