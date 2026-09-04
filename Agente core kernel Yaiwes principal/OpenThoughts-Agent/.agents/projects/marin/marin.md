# marin (marin-community/marin) — repo facts & accepted practices

The main marin monorepo (JAX/Levanter training, the artifact/execution system, eval, tooling). Local clone =
ground truth at `/Users/benjaminfeuer/Documents/marin`. Related docs: `marin-executor/` (the retired
Executor → lazy `ArtifactStep`/`Artifact` system, post-#6649), `marinskyrl/` (the SkyRL RL fork),
`levanter/` (the JAX training engine).

---

## Publish a permanent research artifact as a static webpage (PR #6816 + #7084)

The sanctioned marin mechanism for a **durable public URL** to a permanent, shareable, code-fetchable static
webpage (analysis site, results dashboard, paper-companion page, self-contained HTML report).

**Mechanism:** `marin.publish.sites.publish_site()` (module `lib/marin/src/marin/publish/sites.py`) + the CLI
wrapper `scripts/ops/publish_site.py`. Uploads a single HTML file OR a multi-file directory (SPA — preserves
relative paths; the dir must contain `index.html`) to a public GCS bucket and registers it for discovery.

**Canonical invocation (CLI):**
```bash
cd <marin repo>
uv run scripts/ops/publish_site.py <report.html | ./site_dir/> \
    --user  <author-handle>       # lowercase-kebab namespace, e.g. penfever
    --slug  <site-slug>           # lowercase-kebab project id, e.g. moe-sharding-grid
    --version <YYYY.MM.DD[.N]>     # CalVer, e.g. 2026.07.10  (.N to disambiguate same-day)
    --title "Human Readable Title" # REQUIRED — shown in the discovery index
    --summary "one-line description"   # optional
```
**Python:** `from marin.publish.sites import publish_site; site = publish_site(source, user=…, slug=…,
version=…, title=…, summary="")` → `site.path` = the `gs://` dir.

**Where it lands / the public URL** (deterministic, address-by-convention — no separate registry lookup):
- Object: `gs://marin-public/<user>/<slug>/<version>/index.html` (+ a sibling `.artifact.json` record).
- **Public URL:** `https://storage.googleapis.com/marin-public/<user>/<slug>/<version>/index.html` (served
  `text/html`). Constants in `sites.py`: `PUBLIC_BUCKET="marin-public"`,
  `PUBLIC_URL_BASE="https://storage.googleapis.com/marin-public"`.
- Helpers: `site_uri(user, slug, version)` → the `gs://` dir; `site_url(user, slug, version)` → the public URL;
  `site_name(user, slug)` → the record name (`sites/<user>/<slug>`).

**Discovery + code-fetch:**
- Every publish upserts an entry `{name, version, url, title, summary}` into the central index
  `gs://marin-public/index.json` (a list — read it to enumerate all published sites).
- Fetch a published artifact back in code by its deterministic address: `Artifact.raw_load(site_uri(user,
  slug, version))` — no registry dependency.

**⚠ Gotchas / constraints:**
- **Last-writer-wins:** there is NO immutability guard — republishing the SAME `<user>/<slug>/<version>`
  overwrites. **Bump the `--version` (CalVer) to keep an immutable prior copy.** Treat a published version as
  frozen; new results → new version.
- **`index.json` is non-atomic** (read-modify-write) — avoid concurrent publishes racing the same index.
- **Use origin/main:** the Content-Type fix ("write site objects via `fs.open` so Content-Type sticks",
  PR #7084) landed AFTER the initial #6816 — pull recent `main` or pages may serve with the wrong MIME type.
- **Not everything is publishable:** `render_cluster_report` was deliberately NOT migrated (it can contain
  copyrighted corpus text) — do not publish raw corpus/eval text this way without a copyright check.
- **Requires** the marin repo env + GCS write auth to `gs://marin-public` (public-read bucket).

**Reference:** `docs/tutorials/publish-analysis-site.md` in the marin repo; PR #6816 (issue #6802) + #7084.

---

## Execution & artifacts — the ArtifactStep system (authority: `marin-executor/`)

marin's pipeline/execution layer, and the substrate the publish mechanism above rides on. **The eager
content-addressed `Executor` + `ExecutorStep` are RETIRED (PR #6649)** — replaced by lazy typed
**`ArtifactStep`**s (`marin.execution.lazy`): explicit **`name@version`** (CALVER) addressing instead of an
md5-of-the-config-tree, typed **`Artifact`** outputs (`LevanterCheckpoint`, `TokenizedCache`, …), with identity
(`build_config(ctx)`, pure over a `StepContext`) separated from execution (compute rides `remote(fn,
resources=…)`, not the graph node).

**Full detail lives in `.agents/projects/marin-executor/marin-executor.md`** — read it for:
- the retirement + the `ArtifactStep`/`remote(...)`/`name@version` migration model;
- the surviving **`StepRunner` distributed-lock SPMD deadlock (#7080)** and the sanctioned workaround — a direct
  `srun` launch via **`LevanterSlurmCluster`** (marin's first-class SLURM path; NOT a hack), i.e. ArtifactStep =
  identity/graph layer, `srun` = execution layer on non-Fray clusters;
- the legacy GCS `.executor_info` layout still used to recover OLD executor-launched runs (Delphi midtrains).

`publish_site` records each page as a typed `Artifact`, so a published site is code-fetchable by its
deterministic address via `Artifact.raw_load(site_uri(user, slug, version))` — the *same* typed-artifact system,
no separate registry lookup.

## Grug (67B-A2B) inference — 2 supported runtimes + the HF-BF16 export bridge

How to run inference on a Grug MoE checkpoint today (yonromai, issue #6811 / PR #6664). **Two runtimes, plus a one-time HF-safetensors export that bridges the Levanter checkpoint into vLLM.** No upstream-vLLM support — the **marin vLLM fork is MANDATORY** until the Grug arch stabilizes. The golden runnable reference for all of it is **`tests/vllm/e2e/`**.

- **Path 1 — Levanter/JAX** (reads the raw checkpoint directly, no export). Load via `levanter.checkpoint.load_checkpoint`, build the Grug `Transformer` under `levanter.grug.sharding.compact_grug_mesh`, bf16 forward. **⚠ After load, apply `pending_qb_betas` (`apply_pending_qb_betas`) — skip it and the logits are wrong.** Interactive entrypoints: `levanter.main.{inference_repl,sample_lm,eval_lm}`. Validated on GPU (H100) **and** TPU (v6e-4). Golden: `test_june_67b_a2b_levanter_inference.py`. → use when you just want logits/eval from the checkpoint.
- **The bridge — HF-BF16 export** (yonromai's "code in main"): `main_config.hf_checkpoint_converter().with_config_overrides({"dtype":"bfloat16"}).save_pretrained(...)` → `config.json` + `tokenizer.json` + all-BF16 safetensors. Golden: `test_june_67b_a2b_hf_bf16_export.py`.
- **Path 2 — marin vLLM fork** (serves the HF export, **NOT** the raw checkpoint). `pyproject.toml` pins: vLLM fork rev `a0b205f2afd5b33d01703a4cd9b18453d5286f39` + `runai-model-streamer[s3]==0.16.0` (the `runai_streamer` load-format auto-enables for `s3://` model paths); TPU also needs the tpu-inference fork `734d2842aa883c8f7bcff87a4b437a366f3adbc0` + `VLLM_TARGET_DEVICE=tpu` (routes through `tpu_inference.models.jax.grugmoe`). Serve `--model <export_uri> --data-parallel-size <N> --enable-expert-parallel --model-loader-extra-config '{"distributed":true}'`, then query `/v1/completions`. Parity vs the Levanter reference is tight (max-prob-err 0.008 / top-prob L1 0.012). Golden: `test_june_67b_a2b_vllm_s3_inference.py`. → use for an OpenAI-style serving endpoint / post-training rollouts.
- **⚠ Correctness only, not perf:** both paths are validated on one prompt / short decode against the same golden; **throughput/latency, TP/PP, and broad context are NOT yet validated** (#6664 caveats).
- **⚠ Both supported paths are INFERENCE-ONLY.** Path 1 is JAX; Path 2's `grugmoe.py` is a vLLM `FusedMoE` *inference* model. **Neither is a trainable PyTorch `GrugMoeForCausalLM`** — that remains the open gap for RL/SFT on Grug in a PyTorch framework (ties issue #7164). (SFT via the native Levanter `run_grug` path is the route we use — see the marin-67B-A2B-prelim-sft-eval experiment.)
- **Reference checkpoint** (July 2T cooldown, `step-42150`; native Levanter/JAX Equinox, FP32 params + `pending_qb_betas`): `gs://marin-us-central2/grug/moe_67b_a2b_d2560_ep1_rep8_bs1024_seq65536_sw2k_v4_2048_muon_cooldown_step39k-79ebf3/checkpoints/step-42150/` (canonical) · `s3://marin-us-east-02a/marin/grug/…step39k-79ebf3/checkpoints/step-42150/` (CoreWeave) · `gs://marin-us-east5/…/step-42150/` (us-east5-b). **HF-BF16 export already materialized:** `s3://marin-us-east-02a/marin/exports/grug/june-67b-a2b/step-42150/hf-bf16-vllm/781bc3291c81ce28/`.
- **Reference files:** `tests/vllm/e2e/june_67b_a2b.py` (identity + checkpoint/export URIs + loader); the 3 golden tests above; `tests/vllm/grugmoe_real_checkpoint_backend.py` (export/serve/JAX-ref backends); `experiments/grug/moe/model.py` (`GrugMoeHfConfig`, `to_hf_config`, `hf_checkpoint_converter`); `lib/marin/src/marin/inference/vllm_server.py` (`VllmEnvironment`, streaming load-format). Origin: PR #6664 ("Add GrugMoE support for TPU vLLM serving"), issue #6811.

### Snowball — first-class Levanter load-back of the June-67B-A2B HF export (PR #7227, MERGED 2026-07-16, part of #7219 / #7178)

**What it is:** a *pinned* Levanter `LmConfig`/`LmHeadModel` snapshot of the **June 67B A2B GrugMoE production recipe**, so the **existing HF-BF16 export** (the bridge above) is **discovered, loaded, forward-scored, and served through the standard Levanter stack + marin-serve** — without `trust_remote_code`. It is a NEW, self-contained module in **levanter proper**: `lib/levanter/src/levanter/models/snowball.py` (`@LmConfig.register_subclass("snowball")` → `SnowballConfig`; `SnowballLMHeadModel`; `GrugMoeHfConfig`, registered with `AutoConfig` as `model_type="grug_moe"`). Levanter cannot import `experiments/`, so Snowball is a *faithful copy* of `experiments/grug/moe/model.py`'s forward, reusing the shared `levanter.grug.*` primitives verbatim → bit-exact per-layer/logit parity vs the grug/moe Transformer (drift-guarded by `tests/test_snowball_grug_parity.py`).

**Scope of "supports":** it CONSUMES the HF-BF16 export; it does NOT produce it and does NOT replace the bespoke `hf_checkpoint_converter()...save_pretrained(...)` bridge. It pins ONE recipe (QB-routed 256/4 MoE, GatedNorm, XSA + per-head sigmoid gate, half-RoPE on short/sliding-window layers, NoPE + full-causal long layers, always-on shared expert, PKO off, `disable_long_rope`) and **rejects off-recipe checkpoints** (`_assert_snowball_recipe`: requires `model_type=grug_moe`, `grugmoe_attention_mode="production"`, artifact schema v1). The pinned shape defaults ARE the june_tpu config (`hidden_dim=2560`, `num_layers=26`, `num_experts=256`, `n/kv=20/5`, `sw=2048`, `max_seq_len=65536`, `qk_mult≈1.5703`); the vLLM goldens are `june_tpu_67b_a2b_step_42150_*`. **⇒ It targets the same June/`june_tpu_67b_a2b` checkpoint our SFT (Job 1/Job 2) produces** — validated for forward-parity against the `experiments/grug/moe` primitives, NOT the vendored `june_tpu_67b_a2b/moe` tree itself (it imports neither).

**Load API (marin-serve):** `converter = HFCheckpointConverter.from_hf(<export_uri>)` (now triggers `LmConfig.get_known_choices()` first so the `grug_moe` AutoConfig registration + candidate-converter discovery run — and skips gated defaults like `google/gemma-2b` that used to 401 and abort resolution) → `converter.load_pretrained(...)`. `from_state_dict` is the inverse of the canonical exporter keys (stacked experts, transposed Linears) and reshards each raw leaf to its grug spec so the FSDP-on-`data` layout survives load (else the 67B loads replicated → OOM). New `LmConfig.requires_explicit_mesh_axes` property (`True` for Snowball) tells marin-serve's Levanter backend to set `TrainerConfig.use_explicit_mesh_axes`. Runtime knob `moe_implementation="sonic"` (config.json doesn't carry it) for exact-tolerance GPU parity.

**Serving / parity:** fits + reproduces the full 67B on **8×H100** (`lax.cond` scan over stacked blocks → forward temp ~19 GiB vs 51 GiB OOM). New generic `test_snowball_backend_parity` scores BOTH marin-serve backends against 5 grug goldens (greedy-match + worst per-token prob-err) and **supersedes the two backend-specific 67B tests**: `levanter-gpu` (`LevanterBackend.load_model`+forward, worst 0.0012) and `vllm-gpu` (`VllmBackend.serve`+OpenAI-logprobs, greedy-match every prompt, worst 0.010). New `tests/vllm/e2e/test_snowball_67b_hf_logits.py`; deletes `test_june_67b_a2b_vllm_s3_inference.py`.

**Bounds / gaps (unchanged by Snowball):** (1) **INFERENCE-ONLY** — Snowball is a reimplementation of the *training graph* for load+forward+score parity; it is NOT trainable. SFT on Grug stays the native Levanter `run_grug` path on the `june_tpu_67b_a2b/moe` tree (the arch gap #7164 is not closed). (2) Full Levanter *generation*-serving still needs a paged `decode`/`initial_cache` for grug attention — `LevanterBackend.serve` raises for Snowball; use `load_model` for scoring, **vLLM for full generation/rollouts**. (3) It requires marin `main` **past the 7227 merge** — levanter is the in-tree workspace member `lib/levanter` (`marin-levanter`), so adopting Snowball is a monorepo `git pull` (no separate pin bump); our clone HEAD `52e4b3dd14` predates the merge.

**Relation to the 2-runtime picture:** Snowball is the **load-back/score/unified-serve layer**, orthogonal to the export bridge (which still creates the artifact) and complementary to the two runtimes — it makes the vLLM-fork export *also* loadable/scoreable in-Levanter and gives one parity harness across both marin-serve backends. **SFT export/eval flow note:** the post-SFT *eval/serve-back* step (not SFT training) is where Snowball fits — flag `sft-*` skills and the `marin-67B-A2B-prelim-sft-eval` experiment to prefer `from_hf(<export>)`+`load_pretrained` / marin-serve for in-Levanter eval of the export, once the clone is pulled past 7227. **Compat check before adopting:** confirm the SFT-produced export's `config.json` carries `model_type=grug_moe` + `grugmoe_attention_mode=production` + schema v1 (else `_assert_snowball_recipe` rejects it).

---

## GPU serve+eval (`serve_and_eval` / `IsolatedCudaVllm`) — Qwen GDN-model serve mitigation

The CoreWeave-GPU eval path is `experiments/evals/evalchemy/serve_and_eval.py`: a **serve child** = marin `VllmBackend` on H100×8 (`ServeSpec(gpu_type="H100", gpu_count=8, tpu_type=None, tensor_parallel_size=<TP>, max_model_len=…, vllm_extra_args=[…])`) + an **eval child** = the `:evalchemy-tpu` image as a CPU-only `eval.eval --model local-completions` client. lm-eval-harness runs THROUGH evalchemy (tier-1 tasks) and the chat benchmarks are tier-2 — same path, different `tasks` list.

**`IsolatedCudaVllm` (`VllmType.MARIN_FORK`) provisions stock CUDA vLLM via `uvx --from vllm[runai]==<v> --torch-backend cu128 vllm serve` — which LACKS `nvcc`.** Qwen **gated-delta-net (GDN)** MoEs — `Qwen/Qwen3.5-35B-A3B`, `Qwen/Qwen3-Next-80B-A3B-*` (arch `qwen_gdn_linear_attn`) — have a **FlashInfer GDN prefill kernel that is JIT-compiled at runtime and needs `nvcc`** → the serve child dies at warmup (`Could not find nvcc … cuda_home='/usr/local/cuda'`), the endpoint never registers (`RuntimeError: serve job … finished before registering endpoint`). A reduced-`gpu-memory-utilization` retry does NOT help — it's the kernel JIT, not OOM.

- **MITIGATION (maintainer-blessed — marin issue #7373, yonromai/rjpower): pass `--gdn-prefill-backend triton` via `ServeSpec.vllm_extra_args`.** This uses the triton GDN backend, skips the FlashInfer JIT, and needs no `nvcc`. Romain's explicitly-preferred calling-code fix — over auto-detecting the arch inside vLLM, and over installing `nvidia-cuda-nvcc` into the uvx sandbox (more flexible but brittle; cuda-binary discovery is a known pain, cf. the "find nvcc 13" cruft in Iris). rjpower: fine to disable FlashInfer GDN by default (= triton). **Applies to ANY GDN model served via the marin vLLM GPU path, including a future RL serve.**
- Our local driver `marin_evalchemy_gpu.py::_auto_serve_overrides` **auto-derives** `vllm_extra_args` from `config.json` (no hand-passed flags): `gated_delta_net`/`linear_attn`/Qwen3-Next/Qwen3.5 → `--gdn-prefill-backend triton`; a vision-wrapper (`vision_config` / `*ForConditionalGeneration`, e.g. Qwen3.5-35B) → `--limit-mm-per-prompt {"image":0,"video":0}`; `max_model_len` capped to `max_position_embeddings` (+ gen headroom) — e.g. Moonlight-16B native-caps at **8192** and needs `trust_remote_code`. (Local marin branch `feuer/marinbase-eval-cw-driver`; the executor uploads the working tree, so it carries into every launch + both tiers. NOT for upstream push — the upstream #7373 fix is the marin team's call.)
