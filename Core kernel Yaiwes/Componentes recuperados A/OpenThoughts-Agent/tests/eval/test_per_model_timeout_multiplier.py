"""Regression: per-model harbor timeout multiplier resolves with precedence
    CLI > per-model baseline > size-inferred (own name, else Supabase base model) > 1.0.

The "2x for 8B" default was lost when the campaign migrated to the v6 root listener
(the size-inference lived only in the retired eval/jupiter listener), so every leg
landed at the harbor config's hardcoded 1.0. This restores it on the canonical path,
generalized to take the size signal from the Supabase BASE model when the eval model's
own name carries no size token (e.g. DCAgent/a1-* finetunes whose base is Qwen/Qwen3-8B).

The TIMEOUT keys on ACTIVE params (decode speed): an MoE "30B-A3B" times out like its 3B
active (2.0), NOT its 30B total (16.0). Memory-bound TP/DP sizing stays on TOTAL (asserted).

These tests pin (network-free — the base-model lookup is monkeypatched):
  (a) infer_size_timeout_multiplier (ACTIVE-keyed): dense 8B->2.0, dense 32B->16.0,
      MoE 30B-A3B->2.0 (active 3B, not total 30B), no-token->None;
  (b) per-model baseline timeout_multiplier resolves;
  (c) precedence CLI > per-model > size-inferred(own) > size-inferred(base) > 1.0;
  (d) a finetune with no own size token inherits 2.0 from its base model;
  (e) an explicit CLI value wins even over an 8B model's inferred 2.0.
"""

import types

import pytest

import eval.unified_eval_listener as L
from eval.unified_eval_listener import (
    EvalListener,
    infer_size_timeout_multiplier,
    get_baseline_timeout_multiplier,
    _resolve_model_size_b,
)

DEFAULT = L.DEFAULT_TIMEOUT_MULTIPLIER  # 1.0


@pytest.fixture(autouse=True)
def _no_network_base_lookup(monkeypatch):
    """Stub the Supabase base-model resolver: a1-* -> Qwen/Qwen3-8B, else None.
    Keeps the cache from leaking across tests."""
    monkeypatch.setattr(L, "_BASE_MODEL_NAME_CACHE", {})

    def fake_base(hf_model):
        if "a1-" in hf_model:
            return "Qwen/Qwen3-8B"
        if "a3-32b" in hf_model:
            return "Qwen/Qwen3-32B"
        return None

    monkeypatch.setattr(L, "resolve_base_model_name", fake_base)


def _listener(cli=None, global_tm=None):
    """Stub exposing the .config fields _resolve_timeout_multiplier reads, then bind
    the real (unbound) method. global_tm defaults to the CLI value or 1.0, matching
    build_config()."""
    if global_tm is None:
        global_tm = cli if cli is not None else DEFAULT
    cfg = types.SimpleNamespace(
        cli_timeout_multiplier=cli, timeout_multiplier=global_tm
    )
    stub = types.SimpleNamespace(config=cfg)
    stub._resolve_timeout_multiplier = EvalListener._resolve_timeout_multiplier.__get__(
        stub
    )
    return stub


# ---------------------------------------------------------------------------
# (a) infer_size_timeout_multiplier — pure size-token helper
# ---------------------------------------------------------------------------


def test_infer_8b_is_2x():
    assert infer_size_timeout_multiplier("Qwen/Qwen3-8B") == 2.0


def test_infer_small_is_2x():
    assert infer_size_timeout_multiplier("meta/Llama-3.2-1B") == 2.0


def test_infer_32b_is_16x():
    assert infer_size_timeout_multiplier("laion/foo-32b-rl") == 16.0


def test_infer_moe_uses_active_params():
    # MoE "30B-A3B": the ACTIVE 3B governs the TIMEOUT (decode speed), NOT the 30B total.
    # -> 2.0 (fast), the same bucket as a dense ~3B. (Was 16.0 under the old total-token rule.)
    assert infer_size_timeout_multiplier("Qwen/Qwen3-30B-A3B-Instruct") == 2.0


def test_infer_moe_35b_a3b_is_active_2x():
    # 35B total / 3B active -> active governs -> 2.0 (was 16.0).
    assert infer_size_timeout_multiplier("Qwen/Qwen3.6-35B-A3B") == 2.0


def test_infer_dense_30b_still_16x():
    # No active token -> total governs (unchanged): a 30B DENSE stays at 16.0.
    assert infer_size_timeout_multiplier("laion/foo-30b-rl") == 16.0


def test_infer_moe_large_active_out_of_band_is_none():
    # 235B/A22B: active 22B lands in the documented 15-27B GAP -> None (caller falls back).
    # Known limitation of the coarse buckets; no such model is currently in the eval set.
    assert infer_size_timeout_multiplier("Qwen/Qwen3-235B-A22B") is None


def test_tp_dp_sizing_stays_on_TOTAL_params_for_moe():
    # INVARIANT: parallelism sizing is MEMORY-bound (all experts must fit in VRAM), so it
    # must use TOTAL params even for an MoE — only the speed-bound TIMEOUT switched to active.
    # If this flips to 3.0, someone "fixed" _resolve_model_size_b to active -> OOM risk.
    assert _resolve_model_size_b("Qwen/Qwen3-30B-A3B-Instruct") == 30.0


def test_infer_no_token_is_none():
    assert infer_size_timeout_multiplier("DCAgent/a1-crosscodeeval_python") is None


def test_infer_out_of_band_is_none():
    # 70B is outside both documented bands -> None (caller leaves harbor default + logs).
    assert infer_size_timeout_multiplier("meta/Llama-3.1-70B") is None


# ---------------------------------------------------------------------------
# (b) per-model baseline field
# ---------------------------------------------------------------------------


def test_baseline_field_read():
    cfgs = {"Qwen/Qwen3-8B": {"timeout_multiplier": 4.0}}
    assert get_baseline_timeout_multiplier("Qwen/Qwen3-8B", cfgs) == 4.0


def test_baseline_field_absent_is_none():
    assert (
        get_baseline_timeout_multiplier("Qwen/Qwen3-8B", {"Qwen/Qwen3-8B": {}}) is None
    )


# ---------------------------------------------------------------------------
# (c)-(e) hybrid precedence on the real method
# ---------------------------------------------------------------------------


def test_own_name_size_resolves_without_supabase():
    # An 8B baseline carries its own token -> 2.0, no base lookup needed.
    assert _listener()._resolve_timeout_multiplier("Qwen/Qwen3-8B", {}) == 2.0


def test_finetune_inherits_size_from_base_model():
    # a1-* has no own token; base model Qwen/Qwen3-8B (8) -> 2.0.
    assert (
        _listener()._resolve_timeout_multiplier("DCAgent/a1-crosscodeeval_python", {})
        == 2.0
    )


def test_per_model_baseline_beats_size():
    cfgs = {"Qwen/Qwen3-8B": {"timeout_multiplier": 8.0}}
    assert _listener()._resolve_timeout_multiplier("Qwen/Qwen3-8B", cfgs) == 8.0


def test_cli_beats_per_model_and_size():
    cfgs = {"Qwen/Qwen3-8B": {"timeout_multiplier": 8.0}}
    assert _listener(cli=3.0)._resolve_timeout_multiplier("Qwen/Qwen3-8B", cfgs) == 3.0


def test_explicit_cli_one_overrides_inferred_two():
    # The decisive case the bug-fix preserves: a deliberate --timeout-multiplier 1.0
    # must win over an 8B model's inferred 2.0 (CLI is None-by-default, so a literal
    # 1.0 is an explicit override, not the silent global default).
    assert _listener(cli=1.0)._resolve_timeout_multiplier("DCAgent/a1-x", {}) == 1.0


def test_unknown_model_falls_back_to_default():
    # No CLI, no baseline, no own token, no base model -> the 1.0 default (+ WARN log).
    assert (
        _listener()._resolve_timeout_multiplier("mystery/model-no-size", {}) == DEFAULT
    )
