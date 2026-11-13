"""
Intent Classifier — M-Mem Round 5 Stage 1
==========================================

A hybrid intent classifier with three runnable modes:

  * ``prototype``  — pure cosine-similarity against per-intent prototype
    banks. Zero LLM calls at query time.
  * ``llm``        — pure GPT-based classification using the Task 0.1
    verified prompt (``INTENT_CLASSIFY_SYSTEM`` /
    ``INTENT_CLASSIFY_USER_TEMPLATE``).
  * ``hybrid``     — prototype first-pass; on boundary cases (mid-range
    confidence OR close top-2 margin) fall back to the LLM.

The default ``classify()`` entry-point runs the hybrid mode and uses an
internal LRU-ish cache. Evaluation scripts that want cache-free, deterministic
per-mode runs should use :meth:`IntentClassifier._classify_no_cache`.

This file intentionally imports prototypes and the LLM prompt from their
approved sources (Task 0.1 / Task 0.2) — do not re-define them here.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

import numpy as np

from mmem.retrieval.intent_resources import (
    INTENT_CLASSIFY_SYSTEM,
    INTENT_CLASSIFY_USER_TEMPLATE,
    PROTOTYPES_GENERIC,
    PROTOTYPES_LOCOMO,
    get_all_prototypes,
)

__all__ = [
    "INTENT_TYPES",
    "IntentResult",
    "IntentClassifier",
]

INTENT_TYPES: list[str] = ["temporal", "causal", "multi_hop", "entity_centric"]


# ── Result dataclass ─────────────────────────────────────────────────────────


@dataclass
class IntentResult:
    """Outcome of a single intent-classification call."""

    hints: set[str]                          # all intents passing threshold (or {"general"})
    primary: str                             # top-1 intent, or "general" if none pass
    secondary: Optional[str]                 # top-2 intent if within `secondary_margin`
    confidences: dict[str, float]            # per-intent confidence (cosine or LLM score)
    classifier_used: str                     # "prototype" | "llm" | "none" | "fallback"
    matched_prototype: Optional[str] = None  # debug — best-matching prototype text (prototype mode)


# ── Classifier ───────────────────────────────────────────────────────────────


class IntentClassifier:
    """Hybrid prototype-first / LLM-fallback intent classifier.

    Parameters
    ----------
    embedder
        Any object exposing ``embed(text) -> np.ndarray`` returning an
        L2-normalized vector and ``embed_batch(list[str]) -> np.ndarray``
        returning an L2-normalized (N, D) matrix. ``EmbeddingModel`` fits.
    llm_client
        Any object exposing ``chat_json(prompt, system, temperature)`` and
        returning a dict of ``{intent: score}``. Optional — set to ``None``
        to disable LLM fallback (hybrid degenerates to prototype-only).
    high_conf_threshold
        Prototype confidence at/above which the prototype result is trusted
        in hybrid mode (no LLM fallback).
    margin_threshold
        Top1 minus top2 confidence margin required alongside
        ``high_conf_threshold`` before skipping the LLM.
    low_conf_threshold
        When every prototype confidence falls below this, the query is
        declared intent-less ({"general"} with ``classifier_used="none"``).
        Also used as the prototype-mode finalize-threshold.
    secondary_margin
        If top-1 passes threshold and top-2 is within this margin of top-1,
        top-2 is attached as a secondary hint.
    enable_llm_fallback
        If False, hybrid mode always returns the prototype result (with
        ``classifier_used="prototype"``).
    cache_size
        Maximum entries in the LRU-ish hybrid cache.
    """

    def __init__(
        self,
        embedder,
        llm_client=None,
        high_conf_threshold: float = 0.55,
        margin_threshold: float = 0.10,
        low_conf_threshold: float = 0.25,
        secondary_margin: float = 0.15,
        enable_llm_fallback: bool = True,
        cache_size: int = 1024,
    ) -> None:
        self.embedder = embedder
        self.llm_client = llm_client
        self.high_conf = float(high_conf_threshold)
        self.margin_threshold = float(margin_threshold)
        self.low_conf = float(low_conf_threshold)
        self.secondary_margin = float(secondary_margin)
        self.enable_llm_fallback = bool(enable_llm_fallback)
        self.cache_size = int(cache_size)

        self._cache: "OrderedDict[str, IntentResult]" = OrderedDict()

        # Prototype index: per-intent (N, D) L2-normalized matrix + original texts.
        self._prototype_matrices: dict[str, np.ndarray] = {}
        self._prototype_texts: dict[str, list[str]] = {}
        self._build_prototype_index()

    # ── Prototype index ─────────────────────────────────────────────────────

    def _build_prototype_index(self) -> None:
        all_prototypes = get_all_prototypes()
        for intent in INTENT_TYPES:
            texts = list(all_prototypes.get(intent, []))
            if not texts:
                continue
            matrix = self.embedder.embed_batch(texts)
            # Defensive: ensure L2-normalized rows even if embedder changes behaviour.
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1.0, norms)
            matrix = matrix / norms
            self._prototype_matrices[intent] = matrix.astype(np.float32, copy=False)
            self._prototype_texts[intent] = texts

    # ── Cache helpers ───────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> Optional[IntentResult]:
        if key not in self._cache:
            return None
        value = self._cache.pop(key)
        self._cache[key] = value  # LRU touch
        return value

    def _cache_put(self, key: str, value: IntentResult) -> None:
        if key in self._cache:
            del self._cache[key]
        self._cache[key] = value
        while len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)

    # ── Threshold-based hint finalization ───────────────────────────────────

    def _finalize_hints(
        self,
        confidences: dict[str, float],
        threshold: float,
    ) -> tuple[set[str], str, Optional[str]]:
        """Convert a confidence dict into ``(hints, primary, secondary)``.

        Rules:
          * If top-1 < ``threshold`` → ({"general"}, "general", None).
          * Else primary = top-1 intent.
          * If top-2 ≥ ``threshold`` AND top-1 minus top-2 < ``secondary_margin``
            → secondary = top-2, hints = {primary, secondary}.
          * Otherwise secondary = None, hints = {primary}.
        """
        sorted_items = sorted(confidences.items(), key=lambda kv: kv[1], reverse=True)
        if not sorted_items or sorted_items[0][1] < threshold:
            return ({"general"}, "general", None)

        primary, top_conf = sorted_items[0]
        if len(sorted_items) >= 2:
            secondary, second_conf = sorted_items[1]
            if second_conf >= threshold and (top_conf - second_conf) < self.secondary_margin:
                return ({primary, secondary}, primary, secondary)
        return ({primary}, primary, None)

    # ── Mode implementations ────────────────────────────────────────────────

    def _prototype_classify(self, query: str) -> IntentResult:
        """Max-over-prototypes cosine similarity per intent."""
        qvec = self.embedder.embed(query)
        qnorm = float(np.linalg.norm(qvec))
        if qnorm == 0.0:
            qvec = np.zeros_like(qvec)
        else:
            qvec = qvec / qnorm

        confidences: dict[str, float] = {k: 0.0 for k in INTENT_TYPES}
        best_prototype: dict[str, str] = {}
        for intent, matrix in self._prototype_matrices.items():
            sims = matrix @ qvec  # (N,)
            best_idx = int(np.argmax(sims))
            confidences[intent] = float(sims[best_idx])
            best_prototype[intent] = self._prototype_texts[intent][best_idx]

        hints, primary, secondary = self._finalize_hints(confidences, self.low_conf)
        matched = best_prototype.get(primary) if primary in INTENT_TYPES else None
        return IntentResult(
            hints=hints,
            primary=primary,
            secondary=secondary,
            confidences=confidences,
            classifier_used="prototype",
            matched_prototype=matched,
        )

    def _llm_classify(self, query: str) -> IntentResult:
        """Call Task 0.1's verified prompt and parse 4-intent confidences."""
        if self.llm_client is None:
            raise RuntimeError("IntentClassifier._llm_classify requires llm_client")

        user_msg = INTENT_CLASSIFY_USER_TEMPLATE.format(query=query)
        raw = self.llm_client.chat_json(
            prompt=user_msg,
            system=INTENT_CLASSIFY_SYSTEM,
            temperature=0.0,
        )
        if not isinstance(raw, dict):
            raise RuntimeError(f"LLM returned non-dict intent scores: {raw!r}")

        confidences = {k: float(raw.get(k, 0.0)) for k in INTENT_TYPES}
        # LLM scores are more discrete — use a slightly higher finalize threshold.
        hints, primary, secondary = self._finalize_hints(confidences, 0.30)
        return IntentResult(
            hints=hints,
            primary=primary,
            secondary=secondary,
            confidences=confidences,
            classifier_used="llm",
        )

    # ── Hybrid routing decision (shared by cached & no-cache paths) ────────

    def _hybrid_decide(self, query: str) -> IntentResult:
        proto_result = self._prototype_classify(query)
        sorted_confs = sorted(proto_result.confidences.values(), reverse=True)
        max_conf = sorted_confs[0] if sorted_confs else 0.0
        margin = sorted_confs[0] - sorted_confs[1] if len(sorted_confs) > 1 else 1.0

        # High confidence AND clearly dominant → trust prototype.
        if max_conf >= self.high_conf and margin >= self.margin_threshold:
            proto_result.classifier_used = "prototype"
            return proto_result

        # Everything weak → declare no intent.
        if max_conf < self.low_conf:
            return IntentResult(
                hints={"general"},
                primary="general",
                secondary=None,
                confidences=proto_result.confidences,
                classifier_used="none",
                matched_prototype=proto_result.matched_prototype,
            )

        # Boundary case → delegate to LLM when available; else keep prototype.
        if self.enable_llm_fallback and self.llm_client is not None:
            try:
                llm_result = self._llm_classify(query)
                llm_result.classifier_used = "llm"
                return llm_result
            except Exception:
                proto_result.classifier_used = "fallback"
                return proto_result

        proto_result.classifier_used = "prototype"
        return proto_result

    # ── Public API ─────────────────────────────────────────────────────────

    def classify(self, query: str) -> IntentResult:
        """Default hybrid classification with caching."""
        cached = self._cache_get(query)
        if cached is not None:
            return cached

        result = self._hybrid_decide(query)
        self._cache_put(query, result)
        return result

    def _classify_no_cache(self, query: str, mode: str) -> IntentResult:
        """Run a single mode without reading from or writing to the cache.

        Used by evaluation scripts that compare all three modes on the
        same query — caching across modes would let the hybrid result
        pollute subsequent prototype / llm runs.
        """
        if mode == "prototype":
            return self._prototype_classify(query)
        if mode == "llm":
            return self._llm_classify(query)
        if mode == "hybrid":
            return self._hybrid_decide(query)
        raise ValueError(f"Unknown mode: {mode!r} (expected prototype | llm | hybrid)")

    def clear_cache(self) -> None:
        self._cache.clear()


# ── Smoke test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Minimal smoke test — requires a real embedder and a real LLM.
    # Not a substitute for the proper comparison script.
    from mmem.utils.embedding import get_embedder
    from mmem.utils.llm import get_llm_client

    classifier = IntentClassifier(
        embedder=get_embedder(),
        llm_client=get_llm_client(),
    )
    total_protos = sum(m.shape[0] for m in classifier._prototype_matrices.values())
    print(f"Loaded {total_protos} prototypes across {len(classifier._prototype_matrices)} intents")
    print(f"  generic per intent: {[len(PROTOTYPES_GENERIC[i]) for i in INTENT_TYPES]}")
    print(f"  locomo  per intent: {[len(PROTOTYPES_LOCOMO.get(i, [])) for i in INTENT_TYPES]}")
    print()

    test_queries = [
        "When did Caroline go to the LGBTQ support group?",
        "Why did Jon decide to start his dance studio?",
        "Would Melanie likely enjoy the song The Four Seasons by Vivaldi?",
        "What is Caroline's job?",
        "Tell me more.",
    ]
    for q in test_queries:
        r = classifier.classify(q)
        print(f"Q: {q}")
        print(f"  primary={r.primary!r}  secondary={r.secondary!r}  via={r.classifier_used}")
        print(f"  confidences={ {k: round(v, 3) for k, v in r.confidences.items()} }")
        if r.matched_prototype:
            print(f"  matched prototype: {r.matched_prototype!r}")
        print()
