from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def compute_bleu1(reference: str, hypothesis: str) -> float:
    """Compute BLEU-1 with clipped unigram precision and brevity penalty."""
    ref_tokens = tokenize(reference)
    hyp_tokens = tokenize(hypothesis)
    if not ref_tokens or not hyp_tokens:
        return 0.0

    ref_counts = Counter(ref_tokens)
    hyp_counts = Counter(hyp_tokens)
    overlap = 0
    for tok, count in hyp_counts.items():
        overlap += min(count, ref_counts.get(tok, 0))

    precision = overlap / len(hyp_tokens)
    if len(hyp_tokens) >= len(ref_tokens):
        bp = 1.0
    else:
        bp = math.exp(1.0 - (len(ref_tokens) / max(len(hyp_tokens), 1)))
    return bp * precision


def compute_f1(reference: str, hypothesis: str) -> float:
    """Compute token-level F1."""
    ref_tokens = tokenize(reference)
    hyp_tokens = tokenize(hypothesis)
    if not ref_tokens or not hyp_tokens:
        return 0.0

    ref_counts = Counter(ref_tokens)
    hyp_counts = Counter(hyp_tokens)
    common = 0
    for tok, count in hyp_counts.items():
        common += min(count, ref_counts.get(tok, 0))
    if common == 0:
        return 0.0

    precision = common / len(hyp_tokens)
    recall = common / len(ref_tokens)
    return (2 * precision * recall) / (precision + recall)


def normalize_judge_label(raw: str) -> str:
    label = str(raw).strip().upper()
    if "CORRECT" in label:
        return "CORRECT"
    if "WRONG" in label:
        return "WRONG"
    return "UNKNOWN"


def compute_judge_score(results: list[dict[str, Any]]) -> float:
    judged = [r for r in results if normalize_judge_label(r.get("judge_label", "")) in {"CORRECT", "WRONG"}]
    if not judged:
        return 0.0
    correct = sum(1 for r in judged if normalize_judge_label(r.get("judge_label", "")) == "CORRECT")
    return correct / len(judged)

