"""Regression: per-model baseline ``agent_kwargs`` reach ``EVAL_AGENT_KWARGS``
for that model, with precedence  CLI > per-model baseline > preset.

The listener carries a global merge(CLI, preset) on ``sbatch_params`` shared by
every model; a model that declares its OWN ``agent_kwargs`` in the baseline
config (e.g. the live nested thinking form for a thinking-capable model) gets
those spliced into the MIDDLE of the precedence chain and emitted as a per-model
``EVAL_AGENT_KWARGS`` override (via ``extra_env``, merged last in submit_eval).

These tests pin:
  (a) a per-model baseline agent_kwargs resolves to EVAL_AGENT_KWARGS for that model;
  (b) precedence CLI > per-model > preset (same-key dedup, more-specific wins);
  (c) a known NON-thinking baseline model (Qwen2.5-Coder-32B-Instruct) gets NO
      thinking kwarg;
  (d) the consolidated baseline file loads and the removed file is gone/unreferenced.
"""

import os
import types

import pytest

import eval.unified_eval_listener as L
from eval.unified_eval_listener import (
    EvalListener,
    get_baseline_agent_kwargs,
    merge_agent_kwargs,
    load_baseline_model_configs,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL = os.path.join(
    REPO_ROOT, "eval", "configs", "baseline_model_configs_minimal.yaml"
)

THINK = 'extra_body={"chat_template_kwargs":{"enable_thinking":true}}'
NOTHINK = 'extra_body={"chat_template_kwargs":{"enable_thinking":false}}'


@pytest.fixture
def baseline_configs(monkeypatch):
    """Load the real canonical baseline config with a clean module cache."""
    monkeypatch.setattr(L, "_BASELINE_MODEL_CONFIGS", None)
    monkeypatch.setattr(L, "_BASELINE_MODEL_PATTERNS", None)
    cfgs = load_baseline_model_configs(CANONICAL)
    yield cfgs


def _listener(cli=None, preset=None):
    """Build a stand-in object exposing the .config fields _resolve_agent_kwargs
    reads, then bind the real (unbound) method to it. Avoids constructing the
    full ListenerConfig/EvalListener (many unrelated required fields)."""
    cli = list(cli or [])
    preset = list(preset or [])
    cfg = types.SimpleNamespace(
        cli_agent_kwargs=cli,
        preset_agent_kwargs=preset,
        agent_kwargs=merge_agent_kwargs(cli, preset),
    )
    stub = types.SimpleNamespace(config=cfg)
    # Bind the real method so we exercise the production precedence logic.
    stub._resolve_agent_kwargs = EvalListener._resolve_agent_kwargs.__get__(stub)
    return stub


# ---------------------------------------------------------------------------
# merge_agent_kwargs — pure precedence helper
# ---------------------------------------------------------------------------


def test_merge_first_wins_by_key():
    assert merge_agent_kwargs([THINK], [NOTHINK]) == [THINK]


def test_merge_distinct_keys_preserved_in_order():
    assert merge_agent_kwargs(["parser=xml"], [THINK]) == ["parser=xml", THINK]


def test_merge_empty_lists():
    assert merge_agent_kwargs([], [], []) == []


# ---------------------------------------------------------------------------
# (a) per-model baseline agent_kwargs → resolved list
# ---------------------------------------------------------------------------


def test_thinking_model_carries_kwarg_in_yaml(baseline_configs):
    # Qwen3-32B is a hybrid-thinking model; it must declare the thinking kwarg.
    ak = get_baseline_agent_kwargs("Qwen/Qwen3-32B", baseline_configs)
    assert THINK in ak


def test_per_model_kwarg_reaches_resolution(baseline_configs):
    lst = _listener()  # no CLI, no preset
    resolved = lst._resolve_agent_kwargs("Qwen/Qwen3-32B", baseline_configs)
    assert THINK in resolved


# ---------------------------------------------------------------------------
# (b) precedence CLI > per-model > preset
# ---------------------------------------------------------------------------


def test_precedence_cli_overrides_per_model(baseline_configs):
    # CLI supplies extra_body=...false; the per-model thinking (extra_body=...true)
    # must NOT override the CLI (same key — CLI wins).
    lst = _listener(cli=[NOTHINK])
    resolved = lst._resolve_agent_kwargs("Qwen/Qwen3-32B", baseline_configs)
    assert resolved == [NOTHINK]
    assert THINK not in resolved


def test_precedence_per_model_overrides_preset(baseline_configs):
    # Preset supplies thinking=false; the per-model thinking=true must win
    # (per-model is more specific than preset). No CLI override present.
    lst = _listener(preset=[NOTHINK])
    resolved = lst._resolve_agent_kwargs("Qwen/Qwen3-32B", baseline_configs)
    assert resolved == [THINK]


def test_no_duplicate_keys_emitted(baseline_configs):
    lst = _listener(cli=[NOTHINK], preset=[NOTHINK])
    resolved = lst._resolve_agent_kwargs("Qwen/Qwen3-32B", baseline_configs)
    keys = [kw.split("=", 1)[0] for kw in resolved]
    assert len(keys) == len(set(keys)), f"duplicate kwarg keys: {resolved}"


# ---------------------------------------------------------------------------
# (c) NON-thinking model gets NO thinking kwarg
# ---------------------------------------------------------------------------


def test_qwen25_coder_is_non_thinking(baseline_configs):
    # Qwen2.5-Coder-32B-Instruct has no native thinking; it must carry NO
    # thinking agent-kwarg (it is only pattern-matched, never an explicit entry
    # with agent_kwargs).
    ak = get_baseline_agent_kwargs("Qwen/Qwen2.5-Coder-32B-Instruct", baseline_configs)
    assert ak == [], f"non-thinking model leaked agent_kwargs: {ak}"


def test_non_thinking_model_resolution_has_no_thinking(baseline_configs):
    lst = _listener()
    resolved = lst._resolve_agent_kwargs(
        "Qwen/Qwen2.5-Coder-32B-Instruct", baseline_configs
    )
    assert not any("enable_thinking" in kw for kw in resolved)
    # With no CLI/preset and no per-model override, it equals the (empty) global.
    assert resolved == list(lst.config.agent_kwargs)


def test_explicit_cli_thinking_overrides_even_non_thinking(baseline_configs):
    # Presets no longer carry thinking (it's per-model authoritative), so a
    # non-thinking model gets none by default (see the two tests above). But an
    # EXPLICIT CLI --agent-kwarg is a deliberate override and DOES apply to any
    # model — the merge layer can ADD a key, it just never SUBTRACTS one. That is
    # precisely why thinking lives in the per-model baseline config and NOT in
    # presets: only an intentional CLI override can force it onto a non-thinker.
    lst = _listener(cli=[THINK])
    resolved = lst._resolve_agent_kwargs(
        "Qwen/Qwen2.5-Coder-32B-Instruct", baseline_configs
    )
    assert resolved == [THINK]


# ---------------------------------------------------------------------------
# (d) consolidated file loads; removed file gone
# ---------------------------------------------------------------------------


def test_canonical_loads_and_old_file_removed():
    assert os.path.isfile(CANONICAL)
    old = os.path.join(REPO_ROOT, "eval", "baseline_model_configs.yaml")
    assert not os.path.exists(old), (
        "superseded eval/baseline_model_configs.yaml still present"
    )


def test_canonical_has_no_dangling_reference_to_removed_file():
    with open(CANONICAL) as f:
        head = f.read(4000)
    # Header should no longer point at the deleted original as a replacement target.
    assert "Drop-in replacement for eval/baseline_model_configs.yaml" not in head
