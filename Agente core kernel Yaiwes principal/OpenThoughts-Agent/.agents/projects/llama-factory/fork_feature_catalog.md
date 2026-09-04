# LLaMA-Factory fork — feature catalog vs upstream `hiyouga/LLaMA-Factory`

> Durable record of what our fork (`/Users/benjaminfeuer/Documents/LLaMA-Factory`, remote `origin` =
> `mlfoundations/LLaMA-Factory`) carries over stock upstream (`hiyouga`, remote `upstream`). Authored
> 2026-07-01 from a git-archaeology + code audit. This IS the **migration-cost ledger** for any move to
> bare-upstream LLaMA-Factory or to another framework (axolotl) — everything here is port-or-lose.

## Divergence facts
- **Fork point:** upstream `13170577` == our-side `485d503d` — "[feat] support megatron-LM training by
  mcore_adapter (#9237)", **2025-10-26**. (The fork's history was **rewritten** — no shared SHA ancestry, the
  "Initial commit" SHAs differ — so `git merge-base upstream/main HEAD` is EMPTY. The fork point was recovered
  by **content matching** author-date+subject across both histories, not merge-base.)
- **Divergent commits:** **72 total (70 non-merge)**, **2025-11-22 → 2026-06-10**. A focused feature fork, NOT
  thousands of tracking cherry-picks. HEAD = `d91058f4`.
- **Author split:** 69/72 are our lab (`Benjamin Feuer`/`penfever`); 3 inherited cherry-picks (OFT #8623;
  MoE-fix #9230; transformers-4.56.1 #9128).
- **⚠ Structural nuance — "we" has two layers.** The heavy engineering layer (**~8,600 lines / 76 files**:
  ALST, fp8, DB, CCE, QAT, DCP-checkpoint, FSDP-validator, MFU, smart-padding, dyn-RoPE) was added by the
  **mlfoundations fork BEFORE our fork point** (verified present in the `485d503d` tree). Our 69 local commits
  **harden** that layer (biggest theme: transformers-v5/trl compat, 16 commits; CCE-FSDP fixes, 12 commits;
  DB robustness, 5) + add **2 genuinely-new** local features (delphi template, Qwen3.5). So:
  - "features our FORK carries over stock hiyouga" = the full list below.
  - "features OUR LAB authored" = the hardening + delphi + Qwen3.5.

## (A) Confirmed big features
| Feature | What | Enable | Key files | Origin |
|---|---|---|---|---|
| **ALST / sequence parallelism** | Split one long seq (~200k tok) across GPUs for ultra-long-ctx full FT (DeepSpeed Arctic LST: Ulysses all-to-all attn + sharding dataloader). Legacy zigzag-ring/ulysses/llama3 modes removed. Needs DeepSpeed ≥0.17.2 + max-length padding to `cutoff_len`. | `sequence_parallel_size>1` + `sequence_parallel_mode=deepspeed-alst` + `alst_*` knobs | `model/model_utils/{alst_config,deepspeed_sequence_parallel,sequence_parallel}.py`, `train/alst_loss.py`, `data/processor/{alst_data_adapter,sequence_parallel}.py`; core patches to loader/sft-trainer/pt-trainer/dpo/parser | mlfoundations base + 5 ours (padding/pos-ids/resume fixes) |
| **fp8 training** | FP8 full-param SFT/PT on Hopper via Accelerate (torchao rowwise-scaled Linear; skips embed/lm_head/non-÷16). Works under DS + FSDP2. | `fp8=True`; `fp8_backend∈{auto,torchao,te,msamp}`; `fp8_enable_fsdp_float8_all_gather` | `train/fp8_utils.py`, `model_args.py`, parser; `examples/extras/fp8/*` | mlfoundations |
| **Unified DB / Supabase registration** | Auto-registers each finished model to a Supabase Postgres registry (name/base/dataset/type/hparams/wandb+S3 link) on HF push. Broader CRUD toolkit. | Env-driven (no flag): `SUPABASE_URL`+`SUPABASE_ANON_KEY`+`SUPABASE_SERVICE_ROLE_KEY` + `push_to_hub`+`hub_model_id` | `database/` package; ~110-line patch to `train/tuner.py` | mlfoundations base + 5 ours (robustness) |

## (B) Other substantive features (mlfoundations-origin unless noted)
| Feature | What | Enable | Origin/note |
|---|---|---|---|
| **CCE (Cut Cross-Entropy)** | Apple `cut_cross_entropy.linear_cross_entropy` from hidden states + lm_head weight — no full-logits materialization (151k-vocab Qwen3.x OOMs otherwise). | `use_cce=True` (SFT); needs `cut-cross-entropy`; incompatible w/ `use_dft_loss` | mlfoundations base + **our 12 fix commits** (FSDP FlatParameter, DS compat, lm_head forward-hook) — our biggest local churn |
| **QAT** | torchao Int8DynActInt4 (8da4w) fake-quant, optional delay N steps. | `enable_qat=True` + `qat_*` / `fake_quant_after_n_steps` | mlfoundations |
| **Checkpoint Manager + DCP** | PyTorch Distributed Checkpoint sharded save/load for FSDP (Stateful AppState, Gloo fallback); CLI merges DCP→`.pth`/HF. | auto under FSDP; `python -m scripts.dcp_convert` | mlfoundations (+ our ckpt-load fix) |
| **FSDP config validator** | Pydantic-validate an Accelerate FSDP YAML (enums, forbid-unknown, v1→v2 hints). | auto if `ACCELERATE_CONFIG_FILE`; `scripts/validate_fsdp_config.py` | mlfoundations |
| **MFU logging** | Model FLOPs Utilization profiling. | `include_mfu`, `mfu_profile_every`, `mfu_warmup_steps` | mlfoundations |
| **Smart / auto padding** | `pad_to_multiple_of: int\|"auto"\|null` auto-detect. | `pad_to_multiple_of: auto` | mlfoundations |
| **Dynamic YaRN RoPE + capacity** | `rope_scaling` string-enum (yarn/dynamic/llama3) or dict; `model_capacity` overrides max-pos-emb indep. of `cutoff_len`. | `rope_scaling:{rope_type:yarn,dynamic:true}` + `model_capacity` | mlfoundations + **our `45fea010`** |
| **fa3 / HF-kernels attn** | `attn` selects eager/sdpa/fa2/fa3 or HF-kernel names (vllm-flash-attn3). | `attn: fa3` | mlfoundations |
| **OFT** | Orthogonal Fine-Tuning PEFT method. | OFT finetuning args | **inherited cherry-pick** #8623 |
| **DS pin-memory + compile/Liger shims** | Workaround DeepSpeed pin_memory CUDA crash; mark Liger non-traceable to avoid dynamo breaks. | auto | mlfoundations helpers |

## (C) Our-lab-only (the 69 penfever commits)
- **Delphi chat template** (`60c6bb07`+`d91058f4`, Jun 2026) — **genuinely local, 0 at fork.** `DelphiReasoningTemplate`
  persists canonical `delphi_v0.jinja2` (4107-char think/tool protocol) as the saved `tokenizer.chat_template`;
  fixes save-time writing the slot-derived plain Llama-3 template + dropping the think/tool protocol (broke
  eval/RL/serving). `data/template.py`.
- **Qwen3.5 support** (4 commits) — `.[qwen3-5]` extra (flash-linear-attention + causal-conv1d for Gated
  DeltaNet), `mm_token_type_ids`/`get_rope_index` fixes.
- **transformers v5 / trl compat** (16 commits — largest local theme): is_safetensors/is_torch_sdpa removal,
  overwrite_output_dir getattr, use_cache→infer_use_cache argparse fix, conditional PPO import (trl≥0.20),
  create_optimizer model-arg, drop deepspeed<=0.18 bound.
- **Dataset cache / local-dir / data-args** (12 commits) — datasets_cache_dir respect, temp-dir cache for local
  dirs, datasets≥4.7.0 compat, dataset_names seeding, robust pre-download.
- **Deps / logging / misc** (8 commits) — loosen pins, quieter logs, drop numpy<2.0.0 & kernels==0.9.0 upper bounds.

## Bottom line
Our fork's value over stock hiyouga = **long-context full FT that stock can't do** (ALST → ~200k tok), **CCE**
(151k-vocab no-OOM), **fp8** + **QAT**, a **DCP** FSDP checkpoint save/convert path, an **FSDP validator**,
**MFU**, smart-padding, dynamic-YaRN RoPE — all wired to **auto-register every finished model into Supabase** on
HF push; plus our lab layer keeping it alive on **transformers v5 / trl** + **Qwen3.5** and the **delphi
think/tool chat-template** our eval/RL/serving depends on.

## Cross-framework coverage (vs axolotl) — see the section below / companion audit (2026-07-01)

## Cross-framework coverage: upstream axolotl (audited 2026-07-01)

> Feature-by-feature audit of our LF fork's 14 catalog features against a fresh upstream `axolotl-ai-cloud/axolotl`
> clone (HEAD `0bda5a1`, 2026-06-30). Method: grep + read of `src/axolotl/` (integrations, `utils/schemas/`,
> `utils/config/`, trainers, loaders, monkeypatch). "yes" only where the mechanism actually does the same job;
> a similarly-named thing that does something different is "partial" or "no" with a note. Paths cited are relative
> to `src/axolotl/`.

| # | Feature | In axolotl? | How | Parity notes |
|---|---|---|---|---|
| 1 | **ALST / long-seq parallelism** | **yes** | native — context/sequence parallel via **ring-flash-attn** | `context_parallel_size` (`sequence_parallel_degree` deprecated→aliased), `ring_attn_func` (varlen_llama3 / batch_ring / batch_stripe), `heads_k_stride`. `utils/ctx_managers/sequence_parallel.py`, `monkeypatch/ring_attn.py`, `utils/schemas/config.py:1084-1105`, validation.py:1600-1665. **Different mechanism**: axolotl = ring-flash-attn (Zhu-style ring/llama3 varlen); ours = DeepSpeed-ALST Ulysses all-to-all. Both split one long seq across GPUs for full-FT; axolotl's is CP-native (no DeepSpeed dependency), zigzag/stripe partially stubbed. Functional parity for the core goal; not the same kernel path. |
| 2 | **fp8 training** | **yes** | native config-flag — TorchAO Float8 | `fp8: true` + `fp8_enable_fsdp_float8_all_gather` (FSDP2 float8 all-gather). GPU-capability + torch≥2.11 + torchao/TE/ms-amp gate. `utils/schemas/config.py:563-573,1703-1766`, validation.py:427-444; `ao_adamw_fp8` optimizer (`core/builders/base.py:365`); also `attn_implementation: fp8`. Full parity — same TorchAO rowwise path, plus fp8 attention which our fork lacks. |
| 3 | **DB / Supabase auto-registration** | **no** | — | Zero hits for supabase / model-registry / postgres / push-to-registry anywhere in `src/axolotl/`. Has W&B / swanlab / lm_eval loggers and a Modal cloud CLI, but **no external model-registry auto-register on push**. This is a pure port-or-lose (it's our `database/` package). |
| 4 | **CCE — Cut Cross-Entropy** | **yes** | plugin-integration | `integrations/cut_cross_entropy/` (`CutCrossEntropyPlugin`); enable `cut_cross_entropy: true`; requires **axolotl's own fork** of `cut_cross_entropy` w/ transformers patch (`cce_patch`, per-arch `cce_forward`, incl. `qwen3_next`). Same Apple linear-cross-entropy no-full-logits mechanism as ours. Full parity (both are the Apple CCE; axolotl ships a maintained transformers-integration fork — the same integration effort our 12 fix-commits represent). |
| 5 | **QAT** | **yes** | native config — TorchAO fake-quant | `QATConfig` (`utils/schemas/quantization.py:31`): `weight_dtype`/`activation_dtype` (int8/fp8/int4 via `TorchAOQuantDType`), `group_size`, `quantize_embedding`, `fake_quant_after_n_steps`; `QATCallback` toggles `FakeQuantizedLinear`/`FakeQuantizedEmbedding` (`utils/callbacks/qat.py`). Full parity incl. the delay-N-steps knob; also a separate PTQ path + `llm_compressor` integration. |
| 6 | **DCP checkpoint manager** | **yes** | native — torch DCP + merge CLI | FSDP2 `SHARDED_STATE_DICT` DCP save in trainer (`core/trainers/base.py:804-848`, `train.py:307`), and a merge-to-HF CLI **`cli/merge_sharded_fsdp_weights.py`** (`dcp_to_torch_save` / `_EmptyStateDictLoadPlanner`). Same PyTorch Distributed Checkpoint sharded save/load + DCP→torch/HF convert as ours. Full parity (axolotl also handles the quantized-base / LoRA DCP edge cases). |
| 7 | **FSDP config validator** | **partial** | pydantic `FSDPConfig` schema, but validates axolotl's own `fsdp_config`, not an Accelerate YAML | `utils/schemas/fsdp.py` — typed/enum-validated FSDP schema (`fsdp_version`, `state_dict_type` Literal, `auto_wrap_policy` Literal, etc.) with a `model_validator`. Validates the **in-config `fsdp_config` block**; it does NOT ingest+validate a standalone Accelerate FSDP YAML file (in fact `cli/checks.py:22` *warns against* an external accelerate config). Ours validates the Accelerate YAML specifically → different target; overlapping intent. |
| 8 | **MFU logging** | **no** | — | Zero hits for mfu / model-flops-utilization / tflops / hardware_flops in `src/axolotl/`. No FLOPs-utilization profiling callback. Port-or-lose. |
| 9 | **Smart/auto padding** | **partial** | `pad_to_multiple_of: int` (no `"auto"`) | `utils/schemas/config.py:712` — plain `int \| None`; collators honor it (`utils/collators/batching.py:75-79`, dpo/mm collators). **No `"auto"` auto-detect mode** (ours accepts `int\|"auto"\|null`). Manual padding = yes; the auto-detect convenience = no. |
| 10 | **Dynamic YaRN RoPE + model_capacity** | **partial** | equivalent-different-mechanism | Top-level `rope_scaling` is **deprecated** (`utils/schemas/deprecated.py:36-43`) → you now set yarn/dynamic as a key under `model_config` overrides, passed straight into the HF config (HF then applies YaRN). Max-pos-emb is auto-bumped to `sequence_len` when exceeded (`loaders/model.py:370-381`) — that covers the `model_capacity` use-case implicitly. So YaRN IS reachable (via HF config), but there's **no dedicated string-enum knob** and no explicit `model_capacity` override decoupled from `sequence_len`. Reachable, less ergonomic; not a 1:1. |
| 11 | **fa3 / HF-kernels attn selector** | **yes** | native config — `attn_implementation` | `attn_implementation: flash_attention_3` plus hub-kernel paths (e.g. `kernels-community/flash-attn3`) passed through to transformers; also eager/sdpa/fa2/flex/xformers/sage/fp8 (`utils/schemas/config.py:822-833`). Full parity with our `attn` selector (fa3 + HF-kernel names). |
| 12 | **OFT** | **no** | — | **Zero** hits for `oft` / orthogonal-fine-tuning anywhere. `peft.py` schema has LoRA/LoftQ/DoRA-style knobs and a generic plugin `adapter` field, but no native OFT adapter. (Ours is inherited cherry-pick #8623.) Port-or-lose. |
| 13 | **Qwen3.5 / Gated-DeltaNet support** | **yes** | native monkeypatch + deps | `monkeypatch/models/qwen3_next/modeling.py` patches `Qwen3NextGatedDeltaNet.forward` → cu_seqlens into `chunk_gated_delta_rule`, uses `fla` (`fla.modules.convolution.causal_conv1d`) + transformers `is_causal_conv1d_available`; multipack registered for `qwen3_next` (`monkeypatch/multipack.py:24`, `loaders/patch_manager.py:485-490`); vLLM schema notes causal_conv1d for "Qwen3.5 hybrid linear attention". Same flash-linear-attention + causal-conv1d GDN path as ours. Full parity. |
| 14 | **Delphi chat template** | **no** (expected) | — | Our lab-specific think/tool jinja (`DelphiReasoningTemplate` / `delphi_v0.jinja2`). Not in axolotl (axolotl ships its own chat_templates dir but not ours). Expected absent — pure port. |

### COUNT
**9 of 14 present** — **8 full** (ALST/CP, fp8, CCE, QAT, DCP, fa3/HF-kernels, Qwen3.5-GDN, and — counting it as full — none of the partials) → precisely **7 full** (1, 2, 4, 5, 6, 11, 13) **+ 3 partial** (7 FSDP-validator, 9 auto-padding, 10 dyn-YaRN/capacity) **= 10 of 14 present (7 full / 3 partial)**; **4 absent** (3 DB/Supabase, 8 MFU, 12 OFT, 14 Delphi-template).

### Reverse gaps — what axolotl has that our LF fork lacks
- **densemixer** (`integrations/densemixer/`) — DenseMixer plugin: precise MoE router-gradient (dense forward through all experts for a correct top-k routing gradient) — improves MoE FT quality.
- **expert_parallel** (`integrations/expert_parallel/`) — replaces the MoE dispatch/combine path with **DeepEP** fused all-to-all kernels; sharded experts across GPUs (Ampere/Hopper + all-pairs NVLink). True expert-parallel MoE.
- **scattermoe / SonicMoE kernels** (`integrations/kernels/` + `libs/scattermoe_lora/`) — registers **ScatterMoE** (Triton grouped-GEMM, any CUDA) and a LoRA-aware **SonicMoE** (CUTLASS, Hopper) into transformers-v5's `experts_implementation` registry; `use_scattermoe: true`. Faster/lower-VRAM MoE expert GEMMs incl. NVFP4/FP8 quantized expert paths.
- **Other integrations we lack:** `kd` (knowledge distillation), `mora`, `spectrum` (SNR-targeted layer freezing), `grokfast`, `nemo_gym`, `diffusion`, `swanlab` + `lm_eval` loggers, `llm_compressor` (fine-tune sparsified models), `hatchery`, `liger`; plus GRPO/RL trainers, a Modal cloud CLI, and fp8 *attention*.

### Bottom line — migration feasibility LF-fork → axolotl
Most of our engineering layer **ports cleanly or is already native**: fp8, QAT, DCP (+ merge CLI), CCE, fa3/HF-kernel attn, and Qwen3.5 Gated-DeltaNet are all present with real parity, and long-context full-FT is covered by axolotl's ring-flash-attn context-parallel (a *different* mechanism than our DeepSpeed-ALST Ulysses, so config/kernel — not concept — is the port cost). We would **LOSE** four things outright — the Supabase auto-registration (our `database/` package, biggest re-port), MFU logging, native OFT, and the Delphi think/tool chat-template — and would **downgrade** three to workarounds (FSDP-validator only validates axolotl's own block not an Accelerate YAML; `pad_to_multiple_of` has no `"auto"`; YaRN is reachable only via HF `model_config` overrides with no `model_capacity` knob). Net **GAIN** is substantial on MoE — densemixer router-gradient, DeepEP expert-parallel, and ScatterMoE/SonicMoE kernels — plus KD, spectrum, GRPO/RL and richer quantization, so for MoE-heavy work axolotl is a strong target provided we re-port DB-registration, MFU, OFT, and the delphi template.
