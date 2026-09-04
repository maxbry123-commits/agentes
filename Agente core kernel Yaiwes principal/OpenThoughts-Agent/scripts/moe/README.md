# MoE expert-distribution profiler

`expert_distribution.py` is a **reference (ground-truth) profiler** for the
distribution of MoE expert calls in a Qwen3-MoE model. It runs the model through
plain HuggingFace `transformers` with forward hooks and tallies, per layer, which
experts the router selects for every token.

It is deliberately **independent of the vLLM capture path**. When the vLLM
R3-capture's expert counts look wrong, this profiler is the trusted baseline to
compare against: run the same model on the same inputs through this script — if
the numbers disagree, the vLLM capture is the bug, not the routing.

## How it works

Each sparse Qwen3-MoE decoder layer holds a `Qwen3MoeSparseMoeBlock` whose
`.gate` is a `Linear` producing per-token router logits `(num_tokens,
num_experts)`. The profiler registers a forward hook on every `.gate`, recomputes
the model's selection exactly (`softmax(logits) -> topk`), and accumulates the
selected expert indices per layer. (We hook the gate directly rather than relying
on `output_router_logits=True`, which only stacks logits for the train-time aux
loss and needs labels.) For a non-Qwen MoE it falls back to any `.gate` Linear
whose `out_features == num_experts`.

## Install / interpreter

Use the otagent env. Only `torch`, `transformers`, `numpy` are required;
`matplotlib` is optional (for `--plot`), `pandas` only for `.parquet` input.

```bash
/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python -m scripts.moe.expert_distribution --help
```

Run from the `OpenThoughts-Agent/` repo root so `-m scripts.moe...` resolves.

## Validate it runs (no download, CPU)

```bash
python -m scripts.moe.expert_distribution --self-test
```

This builds a tiny random `Qwen3MoeForCausalLM` (4 layers, 8 experts, top_k=2,
hidden=64) on CPU, runs synthetic prompts through it, and asserts: hooks fire on
every MoE layer; total selections == `tokens * top_k * num_moe_layers`;
forced-uniform load gives entropy 1.0 / Gini 0.0; forced-single-expert gives
entropy 0.0 / Gini (n-1)/n / dead == n-1. Exits non-zero on any failure.

## Expected dataset schema

`--dataset` accepts a **local `.jsonl` / `.parquet`** path or an **HF dataset id**.
Pass exactly one of:

- `--text-field <col>` — the column holds a raw string; tokenized directly.
- `--messages-field <col>` — the column holds a chat `messages` list of
  `{"role": ..., "content": ...}` dicts; the tokenizer **chat template** is applied.

The repo's agentic data is Harbor-format trace datasets. Their conversation
column (commonly `conversations`) is a list of role/content message dicts — use
`--messages-field conversations`. A plain JSONL of prompts works with
`--text-field text`. Rows are sampled **evenly spaced** across the dataset
(`--num-samples N`), each truncated to `--max-tokens`.

## Profile the real Qwen3-30B-A3B on the cluster

The 30B is cluster-only (it will not fit on the Mac). On a GPU node:

```bash
cd ~/OpenThoughts-Agent
python -m scripts.moe.expert_distribution \
    --model Qwen/Qwen3-30B-A3B \
    --dataset DCAgent/dev_set --split train \
    --messages-field conversations \
    --num-samples 64 --max-tokens 4096 \
    --dtype bfloat16 --device-map auto \
    --output ~/moe_qwen3_30b_a3b_devset.json \
    --plot --plot-prefix ~/moe_qwen3_30b_a3b
```

Swap `--model` for a local checkpoint path and `--dataset` for the agentic sample
you want to characterize. `--device-map auto` shards across visible GPUs.

## Outputs

- A human-readable table to **stdout**: global stats, the per-layer
  entropy/Gini distribution, the most-collapsed layers, and a per-layer table.
- A machine-readable `--output report.json` with `global`, `per_layer` (incl.
  raw `counts` per layer), the entropy/Gini distributions, and `most_collapsed_layers`.
- With `--plot`: `<prefix>_heatmap.png` (per-layer expert load) and
  `<prefix>_histogram.png` (global sorted load vs the uniform line). Degrades
  gracefully (warns, continues) if matplotlib is missing.

## Reading the numbers

Per layer **and** globally the profiler reports:

- **Per-expert counts + normalized load** — fraction of routed token-slots each
  expert received. Uniform load is `1 / num_experts`.
- **Normalized routing entropy** `H / log2(num_experts)` — **1.0 = perfectly
  uniform**, **0.0 = every slot to one expert**. The headline collapse signal.
- **Gini coefficient** of the load — **0 = perfectly equal**, **->1 = one expert
  takes everything**. Complements entropy (more sensitive to a few hogs).
- **Dead experts** — experts with zero selections. **Underused** — load below
  `0.1x` uniform (includes dead).
- **max / mean / min load** and **max/mean uniform-ratio** — concentration; e.g.
  `maxX = 8.0x` means the hottest expert is taking 8x its fair share.
- **Top / bottom-K experts** — the most- and least-loaded expert indices.

MoE collapse is **per-layer**, so trust the per-layer distribution and the
most-collapsed-layers list over the single global number — a few collapsed layers
can hide inside a healthy-looking global average.

### Interpreting agentic data

- Agentic-trace data legitimately routes **more concentrated** than natural text:
  it is narrow-domain (shell/code/tool-call tokens), so somewhat lower entropy and
  higher Gini than a web-text baseline is **expected, not a bug**. Compare against
  this profiler on natural text for the same model, not against an absolute
  threshold.
- A genuinely collapsed layer shows up as **low entropy + high Gini + several dead
  experts** consistently across the sample.
- **Capture-artifact red flag:** if the *same* expert set is selected for
  *every* token (perfectly identical per-token routing, e.g. entropy pinned at
  exactly the top_k floor with the rest dead), that is almost certainly a
  **capture artifact** (e.g. a broken vLLM R3-capture replaying one routing
  vector), **not** real routing. Real Qwen3-MoE routing always varies token to
  token even on narrow agentic data. That contrast — this HF reference shows
  token-varying routing while the vLLM capture shows an identical per-token set —
  is exactly what this profiler exists to expose.
```
