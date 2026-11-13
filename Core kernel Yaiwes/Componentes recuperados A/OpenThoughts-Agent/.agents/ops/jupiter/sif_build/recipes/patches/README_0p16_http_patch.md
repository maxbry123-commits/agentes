# vLLM `routed_experts` HTTP-serialization patch

**File:** `vllm_routed_experts_http_serialization.patch`
**Date:** 2026-06-04
**Purpose:** Plumb the inference-time MoE expert-selection mask (`routed_experts`)
into the OpenAI serving-layer HTTP responses (`/v1/chat/completions` and
`/v1/completions`, non-streaming). Unblocks the Stage-1 live capture rail for the
SkyRL router-replay port (see `../stage1_capture_rail_scope.md` Q1 and
`../fsdp2_ep_router_replay_port_plan.md` Stage 1).

This is **pure Python** (serving layer only) — NO recompile. The engine already
populates `CompletionOutput.routed_experts` in the target build; this patch only
adds the HTTP serialization step that rides alongside `token_ids`.

## What it changes

Strictly additive, None-default, flag-gated:
- Adds `routed_experts: list[list[list[int]]] | None = None` to
  `ChatCompletionResponseChoice` and `CompletionResponseChoice`.
- In the non-streaming choice-build sites, serializes
  `output.routed_experts.tolist()` only when `output.routed_experts is not None`
  (i.e. only when the server was launched with `--enable-return-routed-experts`).
  Otherwise the field stays `None` and the JSON is byte-identical to today.
- Shape: `[gen_len, num_moe_layers, top_k]` (generated tokens only).

**No-op for servers without the flag** (e.g. a3 RL rollout servers): the engine
leaves `routed_experts=None`, the serializer emits `None`, response unchanged.

## Scope notes / deliberate omissions

- **Generated-only.** Per-choice `routed_experts` carries the GENERATED portion
  (Stage-1's target — it rides Harbor's per-turn `extra`). `prompt_routed_experts`
  on the top-level response was **deliberately skipped**: the target build's
  `RequestOutput` has no `prompt_routed_experts` attribute (the engine does not
  expose the prompt split here), so it would NOT be a trivial mirror. Generated-only
  is sufficient for Stage 1. The prompt portion is a later prefill-replay concern.
- **Streaming/SSE not touched** — Harbor uses non-streaming; irrelevant.

## LAYOUT NOTE — which files map where (READ BEFORE APPLYING)

The original task assumed the env build used vLLM's OLDER *monolithic* serving
layout (`entrypoints/openai/serving_chat.py`, `serving_completion.py`,
`protocol.py`). **That was wrong for the actual env build.** The Jupiter
`envs/rl` vLLM build uses the SAME per-endpoint *subdir* layout as the
`v2-migration` reference fork:

```
vllm/entrypoints/openai/chat_completion/protocol.py
vllm/entrypoints/openai/chat_completion/serving.py
vllm/entrypoints/openai/completion/protocol.py
vllm/entrypoints/openai/completion/serving.py
```

So this patch's `a/`,`b/` paths already match the subdir layout. Apply from the
vllm package root with:

```
patch -p1 < vllm_routed_experts_http_serialization.patch
# or, if applying inside the site-packages vllm dir at .../site-packages :
#   git apply / patch -p1 against the vllm/ tree
```

If you ever apply this to a build that genuinely uses the monolithic layout, the
field-add maps to `protocol.py` (`ChatCompletionResponseChoice` /
`CompletionResponseChoice`) and the serialization maps to `serving_chat.py` /
`serving_completion.py` at the non-streaming choice-build sites (right after the
`token_ids=(as_list(output.token_ids) if request.return_token_ids else None)`
anchor). The logic is identical; only the file paths differ.

## Applied target (env, not git-tracked — edited in place)

`/e/scratch/jureap59/feuer1/OpenThoughts-Agent/envs/rl/lib/python3.12/site-packages/vllm/entrypoints/openai/`

Backups: each touched file copied to `<file>.pre_routed_experts.bak` in place.
