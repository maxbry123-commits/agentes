# MarinSkyRL — framework facts & gotchas

The RL training framework. Cluster runtimes/SIFs live in `.agents/ops/<cluster>/`; live
project trackers (rollout-fanout, PR tracking, log-ratio v3, ray-workercrashed) stay as
memories.

---

## Source of truth

- **SoT = `marin-community/MarinSkyRL` branch `main`.** ⚠ The long-lived **`penfever/working` mono-branch is RETIRED** (2026-07-17) — accumulating everything on one branch caused drift and stranded fixes off `main`. Every change now lands via the **worktree → PR → `main` → report-to-supervisor** flow below; pins, refs, and cluster clones track **`main`** (the reviewed/merged state). For an unmerged fix under active test, pass it explicitly (`--skyrl-ref <branch>`) rather than mutating a shared branch.
- **`github.com/penfever/SkyRL` is OBSOLETE** (archived). All its features are in marin under squashed SHAs; marin additionally has TIS exact-alignment + mp-backend. Do NOT merge the fork — it re-applies old copies and risks regressing SoT.
- **Cluster clones** (all track `main`, editable-installed):
  - Jupiter: `/e/scratch/jureap59/feuer1/OpenThoughts-Agent/SkyRL` (editable from `.../SkyRL/skyrl-train`).
  - Leonardo: `/leonardo_work/AIFAC_5C0_290/bfeuer00/code/MarinSkyRL`.
  - Perlmutter / NYU Torch: realign when next used.
- **Sync:** merged PRs land on `main`; `git pull` (`main`) on the cluster (editable installs go live after pull). See `.agents/ops/jupiter/ENVIRONMENT_MAP.md` for baked-SIF facts.

---

## Contributing to this fork (marin-community fork workflow)

MarinSkyRL is a **marin-community shared fork** — code contributions follow the **marin-community fork contribution workflow** (shared with `harbor`, `evalchemy`), which is DIFFERENT from OT-Agent's:

1. **Read `AGENTS.md` first.** Before editing any file, read the repo's `AGENTS.md` / `AGENTS-core.md` and obey it — env/dev setup, test + lint entry points, PR norms.
2. **Follow the marin style conventions.** Run the repo's marin-style lint/format/type gate (e.g. `uv run infra/pre-commit.py --all-files --fix`, `ty check`) and match its vendored-tree / marin-style checks.
3. **Dev in an ISOLATED WORKTREE off a FRESH branch from `main` → PR into `main`.** Every agent works in its own `git worktree` (the Agent tool's `isolation: "worktree"`, or a manual `git worktree add ../wt-<slug> -b <branch> main`) cut from `main` — parallel agents never collide, and there is no shared long-lived branch. One fresh feature branch per change; PR-per-change, small. ⚠ The `penfever/working` mega-consolidation branch is **RETIRED** — never commit to it, and never commit to `main` directly.
4. **Iterate on the PR until ALL tests are green.** Push fixes to the PR branch until every required CI check passes (marin-precommit, marin-style-sync, tests, …); diagnose + fix CI failures, never force past them.
5. **Do NOT self-merge — return for approval.** A SUBAGENT never merges a marin-community PR. Open it (green), then return to the SUPERVISOR, who surfaces it to the HUMAN for final approval + merge. (Shared upstream → human-in-the-loop on the merge; some of these repos allow same-author self-merge, which is exactly why this rule exists.)

Plus the standing norm: **no `Co-Authored-By` / self-crediting commit trailers** (the repo's AGENTS.md forbids them) — use the **`agent-generated` PR label** + the repo's PR-body format instead.

**Scope:** this applies ONLY to the marin-community shared forks (harbor, MarinSkyRL, evalchemy). **OT-Agent (`OpenThoughts-Agent` `penfever/working`) and the vllm fork keep their CURRENT norms** — the agent may commit + push + self-merge, and the `Co-Authored-By` / `Claude-Session` trailers stay.

---

## Config rules

### `n_concurrent_trials` vs `num_parallel_generation_workers` — heuristic, NOT a law

The `2 * num_parallel_generation_workers + 32` ratio is a heuristic, **not a derived relationship**. The two knobs are independent and govern different layers:
- `num_parallel_generation_workers` = trainer's `max_concurrent_generation_groups` bound (`fully_async_trainer.py:374`) + gen-buffer queue `maxsize`, constrained `≥ mini_batch_size`.
- `n_concurrent_trials` = the Daytona-sandbox TrialQueue semaphore, divided across `num_coordinators` (K) worker processes (`rollout_coordinator.py:117`).

**Tune the two empirically against the engine-saturation tuple (Waiting/KV/power/mem-BW), not locked at 2:1.** Do not auto-rewrite configs to this ratio.

### The engine "sawtooth" trough (Running→1) under fully_async is BENIGN backpressure while policy_train-bound

Per-engine `Running` sawtoothing PEAK(=engine cap)→TROUGH 1 with `Waiting=0` + KV near-floor is the gen-buffer's **backpressure working as designed** — NOT a supply bug, NOT parse-bound, NOT under-provisioned workers. **The one decider: `timing/wait_for_generation_buffer`.** ≈0 ⇒ generation is OFF the critical path ⇒ the trough is benign. Confirm: gen buffer sitting FULL at its cap, `staleness_mean ≪ cap`, `discard_rate 0`.
- **`npgw < n_concurrent_trials` is NOT a starve.** `npgw × n_samples_per_prompt ≫ n_concurrent_trials` → the Harbor orchestrator can always be kept full. Raising npgw does NOT lift the trough.
- **When a cheaper-training architecture flips the run inference-bound, the levers in order:** (1) `harbor.n_concurrent_trials` — the real engine-demand knob; (2) per-trial DUTY CYCLE — trials spend most wall-time in Daytona tool-exec, not awaiting the LLM (harbor poll-loop floor, fixed `ef42e75e`; + sandbox reuse). **NOT** npgw / `max_staleness_steps` / `max_buffered_groups`.

### Concurrency is a LOCKSTEP tuple — never permute `n_concurrent_trials` alone
`n_concurrent_trials` is the engine-DEMAND knob; realized throughput is capped by the **decode capacity = `max_num_seqs × num_inference_engines`** (KV-bound at long context). So concurrency ≫ decode slots buys NO throughput — the surplus trials just queue. **If you change concurrency, change the decode-capacity knobs (`max_num_seqs`, `num_inference_engines`) in LOCKSTEP against the engine-saturation tuple (Waiting / KV / power / mem-BW)** — never lower `n_concurrent_trials` in isolation as a symptom-patch (it hides the real bottleneck and de-tunes the run). The engine decode-caps at the slots regardless; concurrency sets demand, slots set supply.
- **⚠ Daytona sandbox idle-reap MUST be OFF for opencode (`auto_stop_interval_mins=0`).** harbor stops→deletes a sandbox with no **exec** for N min; **opencode drives the model over HTTP (`HARBOR_MODEL_ENDPOINT`), not sandbox exec**, so its model turns do NOT reset the idle timer (only bash-tool exec does; terminus-2 is exempt — it execs the model). With a nonzero interval, any trial that queues past the window (i.e. concurrency > decode slots) gets its sandbox reaped mid-trial → every trial fails **`Sandbox not found`** (0 rollouts; mimics a GIL stall AND a snapshot reap — it is neither). **`auto_stop_interval_mins=0` (never idle-stop) is the correct default** — a spurious `5` leaked into harbor main and was patched 2026-07-18. With idle-reap OFF, sandboxes persist through any queue depth, so `n_concurrent_trials` can be set to the demand target (e.g. 288) freely, decoupled from the slot count. (keep1-v8 root-cause + v9 fix: `.agents/projects/daytona/daytona.md`, `agent_logs/2026-07-18_cron-catch-keep1v8-sandbox-marinbase-vllm.md`.)

### opencode RL MUST bound `max_turns` (unbounded → looping → 0 completions)
An **opencode** agentic-RL config with **`max_turns: 999999`** (unbounded) DEADLOCKS the run: the `-Thinking-` / compaction-off opencode agent does NOT reliably self-terminate, so with the generator's turn cap removed it LOOPS past the `override_timeout_sec` wall → the verifier never runs → no `result.json` is written → **0 trial completions / no first policy step** (looks like a decode-capacity/throughput stall — the deep `Waiting` queue is loopers manufacturing fake demand, NOT a real capacity ceiling). Diagnose via Daytona REST: sandboxes aging PAST `override_timeout` and still `STARTED` = looping. Always set a bounded `max_turns` (fullgate went green at n=8 with `max_turns: 30` + `override_timeout_sec: 600`); never inherit `999999`.
**⚠ DEEPER BUG (under investigation 2026-07-18) — the kill/timeout path itself is broken for opencode:** v10's trials were alive at 51 min, PAST the 30-min `override_timeout` — so harbor's wall-clock kill did NOT terminate them. Lowering `override_timeout` does NOT help (a trial that ignored 1800 s ignores 600 s). **CONFIRMED insufficient (keep1-v11, 2026-07-18): `max_turns` is a NO-OP for opencode.** `opencode.py` wires NO turn cap (`CLI_FLAGS = --variant` only) — unlike the other 4 installed agents (claude_code/goose `max_turns`, hermes `max_turns:90`, trae `max_steps`) — AND opencode is a single detached `opencode run --format=json` `run_async` Daytona command (`environment.py:1595`) run WITHOUT `timeout_sec`. The only stop is `trial.py:336` `asyncio.wait_for(agent.run(), timeout=override_timeout_sec)`, but on timeout it cancels the LOCAL poll coroutine while `_poll_response`/`_sandbox_exec` have no `except CancelledError` that KILLS the remote command → the detached opencode keeps running. v11 (max_turns:30, override 600s) looped identically to v10: 193/200 sandboxes alive past 20 min. **The real fix is TWO harbor levers (worktree→PR→--harbor-ref):** (1) plumb the agent timeout into opencode's exec so the server-side `timeout {N}` wrapper kills it + add `except CancelledError → remote-kill` in `_poll_response`; (2) wire a real `max_turns` into `opencode.py` (native flag or count `step_finish` + process-group-kill). Reference for "what a healthy trial looks like": ~8 calls / ~13 min (`experiments/complete/rno2a-30b-coder-throughput`). (keep1-v10/v11 2026-07-18.)

### opencode (installed agent) REQUIRES `--ingress-mode controller` — NOT `direct` (sandbox-reachability)
**Confirmed with hard evidence 2026-07-21.** opencode is an INSTALLED agent that runs INSIDE the Daytona
sandbox and drives the model over HTTP (its `api_base`). `--ingress-mode direct` sets that `api_base` to the
**cluster-internal serving IP** (observed in the opencode trial `config.json`: `"api_base":
"http://10.168.192.223:8000/v1"`) — which the Daytona sandbox has **NO route to** (the sandbox only reaches
the served vLLM over a public tunnel). So on `direct`, every opencode model call hangs → **0-byte
`opencode.txt` (agent emits nothing), no engine activity (`Running: 0 reqs`), 1800 s `AgentTimeoutError`, 288
`config.json` / 0 `result.json`** (identical on the pre- and post-#80 images). **`--ingress-mode controller`
is REQUIRED** — it mints the public `iris.oa.dev/proxy/t/<token>/v1` capability URL that the sandbox CAN
reach (`run_rl.py` sets `++terminal_bench_config.agent_api_base=<minted proxy>` only in the controller
branch). This is exactly what `launch_rl_iris.py` autoconfigure derives (opencode→controller on CoreWeave);
overriding to `--ingress-mode direct` BREAKS opencode. **terminus-2 works on `direct` ONLY because it is an
IN-PROCESS agent** (the trainer process reaches the internal 10.* IP directly — no sandbox network hop).
⇒ **This REFUTES the earlier "opencode-direct 0-rollouts is opencode-specific, NOT ingress" premise — it IS
an ingress/reachability problem.** PR #80 (publish `OPENCODE_DUMMY_KEY` in direct too) closed a real but
INSUFFICIENT gap: a keyless agent refuses to start, but even with the key the direct `api_base` is
unreachable from the sandbox. opencode-RL is therefore genuinely coupled to the controller `/proxy/t` path
(the #7448 question); terminus-2 is not.

### Hydra struct — every run-YAML key must be declared in `ppo_base_config.yaml`

A run-YAML key not declared in the base struct `skyrl-train/skyrl_train/config/ppo_base_config.yaml` (at the launch's `--skyrl-ref`) is **REJECTED at config-parse**. OmegaConf loads the base in struct mode → `Could not override '<key>'. Key '<key>' is not in struct` → `HydraException` → driver exits 1 ~8–30 s after Ray-attach, **before `init_model`** (no NCCL, no training). Grep the finelog for `not in struct`.

- `yaml.safe_load` passing validates **syntax only**, not the struct. Before launching a config with any new/moved key, diff against the base: `git show <ref>:skyrl-train/skyrl_train/config/ppo_base_config.yaml` — every key you set must be declared there OR sit inside a passthrough (`{}`-typed) dict field.
- A knob needs BOTH a runtime reader AND a schema declaration. Adding only `.get("<key>", default)` makes it readable-if-present but **un-settable** (struct rejects at load before the `.get` runs). Example: `use_grouped_mm` reader without the `fsdp_config` schema decl (fixed `56cad1d7`, which declares `use_grouped_mm: false` in every `fsdp_config` block).
- **`optimizer_config` valid keys** = `optimizer, lr, adam_betas, weight_decay, max_grad_norm, offload_after_step, num_warmup_steps, scheduler, optimizer_kwargs`. Optimizer-specific params (e.g. `foreach: false`, the host-RAM CPU-Adam fix) go **nested under `optimizer_kwargs:`** (the `{}` passthrough), NOT bare — a bare `foreach:` is struct-rejected.

### `gradient_checkpointing_use_reentrant` — EVERY RL config must set it `true`

Non-reentrant (`use_reentrant: false`) uses PyTorch saved-tensor pack/unpack hooks; under **activation CPU-offload + SkyRL's async-actor threading** the thread-local hook stack push/pop mismatches → `SavedTensorHooks.cpp:69 INTERNAL ASSERT FAILED (is_initialized && !tls.stack.empty())` at the **gs1 backward** (pytorch#84864 / #90481). **Fix = `trainer.gradient_checkpointing_use_reentrant: true`** (reentrant checkpoint doesn't use the saved-tensor hooks). The `ppo_base_config.yaml` default is **STILL `false`** (`@56cad1d7`) — a config that forgets the line will hit the assert. Set it explicitly in every iris/jupiter RL YAML that uses cpu_offload.

---

## Training backend — Megatron is the default (cloud/iris/configs)

**Megatron is the default training backend for the production iris RL configs** (`cloud/iris/configs/*.yaml`), selected by `trainer.strategy: megatron` + a `megatron_config` block (`tensor_/pipeline_/context_/expert_model_parallel_size` + `expert_tensor_parallel_size`) under `trainer.policy` / `trainer.ref` (the preset ships via `ppo_base_config.yaml`'s hydra defaults). Chosen by the **Megatron-vs-FSDP2 backend comparison** (Qwen3-Coder-30B-A3B EP4): Megatron ~6.3× faster per compute-step — gs1 `policy_train` **600.8 s** (Megatron) vs **3699.6 s** (FSDP2 cpu-offload) / **6020.7 s** (FSDP2 no-offload). **FSDP2 remains the selectable alternate** (`trainer.strategy: fsdp2` + `fsdp_config`) — every FSDP2-specific fact below still applies to that path.

- **Validated geometry:** only 30B-A3B-EP4 = **TP4 / PP2 / CP1 / EP4 / ETP1** (16 training GPU) is empirically validated (east18). Other models' Megatron parallelism is DERIVED — deep-dive the first launch of each.
- **⚠ gs2 `recover_left_padding` OOM:** with `use_sample_packing: false`, Megatron OOMs at gs2 — the last-pipeline-stage post-process allocates a FRESH full-length full-vocab logits tensor (`megatron_utils.py:518`), and gs2's longer RL responses push it past free HBM. Mitigation = **`use_sample_packing: true`** (the default across iris configs since #32) — but UNVERIFIED at gs2 for Megatron; **no Megatron run has banked gs3 yet** (east18 died ~94 min, east19 OOM'd at gs2). Other levers: `micro_forward_batch_size_per_gpu=2` (asymmetric micro-batch vs the FSDP2 arm) or a bounded `logprob_chunk_size` in the megatron_config.
- **⚠ logprob-forward OOM on long sequences → `logprob_chunk_size` (default 1024 since PR #81).** The vocab-parallel logprob computation (`from_parallel_logits_to_logprobs` → `_compute_distributed_log_softmax`, `model_utils.py`) **upcasts logits to fp32** and, on the unchunked path (`DistributedLogprob`), materializes the WHOLE `[num_tokens, vocab//TP]` fp32 tensor at once — ~21 GiB for ONE 146k-token sequence at TP4 (`21.17 GiB ÷ 4 B ÷ (151936/4) ≈ 149k tokens`), plus its `.exp()` + subtraction temporaries. A long-trajectory agentic harness (**terminus-2**, `max_input_tokens 130000` + `max_output_tokens 16384` ≈ 146k, `store_all_messages`/`raw_content`/`interleaved_thinking`) therefore **OOMs at `global_step 1` in the training forward** on an 80 GB H100; a shorter-context harness (opencode) survives the IDENTICAL geometry (⇒ sequence-length-driven, NOT preemption/infra). **Signature to recognize:** state-5 FAILED with NO error string in the job record (the real killer is a `RayTaskError(OutOfMemoryError)` in the ray-actor `worker-*.err`, masked from the job log by a secondary `_pickle.PicklingError: Can't pickle RayTaskError(OutOfMemoryError)`). **Fix = the already-present `ChunkedDistributedLogprob` path** (chunked along the seq dim, fp32 cast INSIDE the chunk loop), plumbed via `trainer.{policy,ref}.megatron_config.logprob_chunk_size` and now **default 1024** (was `null`/unchunked). It is **numerically EXACT** (per-position log-softmax; chunking only splits independent seq positions — verified bit-identical fwd+bwd in `tests/cpu/distributed/test_logprob_chunking.py`), and for `seq ≤ chunk_size` it is a single iteration == unchunked, so short-seq runs are unaffected. PR #81 also fixed the wrapper so the **ref worker reads its OWN `trainer.ref.megatron_config.logprob_chunk_size`** (it previously read the policy key for both).
- **Weight-sync:** the Megatron→vLLM sync needs `SKYRL_W13_RELOAD_BRACKET=1` (default-on) for the FusedMoE w13 gate/up path; without it an early Megatron sync served token-salad (broken permuted policy → 0 banked). See the ops-doc W13 note.

---

## MoE + EP sharding — `fsdp_size` MUST divide `num_experts // ep_size`

When SkyRL shards the expert dim (dim-0 = `num_experts`) over BOTH the EP mesh axis AND FSDP:

> **`fsdp_size` must evenly divide `num_experts // ep_size`.**

For Qwen3-Next-80B-A3B: `num_experts=512`, `ep_size=8` → 64 experts/EP-rank. Valid `fsdp_size` ∈ {1,2,4,8,16,32,64}. **`fsdp_size=6` is INVALID** (64/6 uneven → [11,11,11,11,11,9]).

- **Failure signature:** completes rollout + all policy_train fwd/bwd, then dies at the FIRST Adam step with `RuntimeError: The size of tensor a (10) must match the size of tensor b (9) at non-singleton dimension 0` (`adam.py _single_tensor_adam`, `exp_avg.lerp_(grad)`) — a=even-PADDED FSDP2 local shard, b=UNpadded EP-backward reduce-scatter grad, disagreeing by one on a boundary rank. Deterministic, ~2.3h in.
- **Fix = FSDP=8** (64/8=8 even, also more sharding → fixes the OOM).
- **Guard:** `distributed/fsdp_utils.py` (`63cd2eb`) raises a fail-fast assertion at `create_device_mesh` if `(num_experts // ep_size) % fsdp_size != 0`.

---

## GDN (GatedDeltaNet) specifics

GDN layers exist in **Qwen3-Next-80B-A3B** (36 GDN layers) and **Qwen3.6-35B-A3B** (30 GDN layers). **Qwen3-Coder-30B-A3B is full-attention (no GDN)** — it does NOT hit any of the GDN issues below.

### 80B gs1 death = pure-torch GDN Python loop holds the GIL ~2h → SIGABRT. FIX = FlashQLA.

GDN's pure-torch chunk-recurrence (`transformers/models/qwen3_next/modeling_qwen3_next.py:442`) runs ~55,000 sequential Python iterations per forward micro-batch at `max_prompt_length=98304` → holds the GIL ~2h → the c10d HeartbeatMonitor SIGABRTs at 2× `TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC` (7200s). Both a stability bug AND the dominant throughput cost (Python-dispatch-bound, not GPU-bound).

- The slow path is active because: `mask_fla()` forces the (broken) fla wheel OFF; `SKYRL_GDN_FLASHQLA` unset; `flash_qla` not in the gpu-rl image.
- **Do NOT mask by raising `TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC`** — it only delays the abort while leaving the 2h cost. The GIL-hold IS the bug.
- **FIX = the fused FlashQLA tilelang GDN kernel** (`SKYRL_GDN_FLASHQLA=1` → `engage_flashqla`): one fused GPU kernel/GDN-layer replaces the Python loop. Needs `flash_qla 0.1.0+6ef4858` + tilelang 0.1.8 + apache-tvm-ffi 0.1.9 baked into the gpu-rl image for x86_64+sm_90, THEN a CP1 logprob-parity smoke, THEN relaunch with `--gdn-flashqla on`.
- **Diagnostic distinction:** real wedge (SIGABRT + stale logs + GPUs 0%) vs healthy compute-bound backward (GPUs high, timers advancing).

### 35B GDN + Context-Parallel (CP>1) HARD-CRASHES at forward

The Qwen3.6-35B-A3B GDN layers have **no CP-aware kernel** → `context_parallel_size > 1` **hard-crashes at the forward pass** (not merely numerically wrong): `RuntimeError: The expanded size of the tensor (33784) must match the existing size (16892) at non-singleton dimension 3` in `FSDPPolicyWorkerBase.forward()` → `fwd_logprobs_values_reward` — 33784 = 2×16892 = the CP=2 sequence-shard doubling the GDN attention mask; dies at step-1 forward (0 training steps).

⇒ **the 35B (GDN) model is CP=1 ONLY**; its CP>1 configs (EP8×CP2, EP8×CP4, EP16×CP2) are infeasible-by-inference. A trainable 35B-CP config needs a CP-aware GDN kernel + a CP1-vs-CP2 logprob-parity smoke (`tests/gpu/test_cp_logprob_parity.py`). The Stage-2 attn-backend pivot (sdpa/flex under CP) covers the *full-attn* path — it does NOT make GDN CP-correct.

### grouped-GEMM path logging

`fsdp_config.use_grouped_mm: true` swaps MoE blocks to the grouped-GEMM path at MODEL-LOAD and logs `[MoE] grouped-GEMM swap active` once per policy worker. **That log proves the swap was ARMED, not that grouped_mm actually RUNS the forward** — with EP the expert weights are DTensors routing to `_run_experts_grouped_mm`, but a cpu_offload/DTensor-strip can silently fall back to an eager for-loop.

- The proof is the once-per-forward `[MoE-PATH] …` log (added `56cad1d7`), but it **emits LATE in the forward** (~1.5h into the 80B's ~2h `fwd_logprobs` forward — it fires at the expert-forward, deep in the forward, NOT at `WORKER_FORWARD_ENTER`/forward-start). A probe BEFORE the expert-forward runs sees the swap flag but no `[MoE-PATH]` yet — that is NOT a broken instrument, just too-early. To check grouped_mm on the 80B, probe AFTER the forward is well underway (≥~1.5h in).
- vLLM's GENERATION engines use their own FusedMoE kernels, separate from this training grouped_mm path — engine throughput says nothing about the training path.

---

## TIS + TITO

### `trainer.algorithm.tito_full` (token-in-token-out) — resolution order

Declared `null` in `ppo_base_config.yaml` (`56cad1d7`). Resolution (`generators/utils.py::_tito_full_enabled`): (1) env `SKYRL_TITO_FULL` wins if set; else (2) explicit `tito_full: true/false`; else (3) **auto → defaults to `use_tis`** (TITO-full ON whenever TIS is on). TITO-full assembles the training response from the exact sampled token-ids end-to-end (vs the LCS text round-trip), driving `generate/tis/lcs_fallback_fraction` → ~0 (residual ~12% is irreducible masked-context retokenization, benign; a HIGH rate = target corruption). Non-TIS runs byte-identical (the whole TITO branch is skipped).

### TIS exact-alignment (validated)

`align_logprobs_by_token_ids()` zips vLLM logprobs onto training tokens **by token id** (Harbor `completion_token_ids`); `extract_token_ids_from_rollout_details()`; float logprob format no longer disables TIS; LCS is last-resort and RECORDS every fallback in `AlignmentStats` → metrics `generate/tis/{exact_match_fraction,lcs_fallback_fraction,unaligned_fraction,alignment_fail_count}`; `worker.py` emits per-step `tis/{imp_ratio_mean,imp_ratio_capped_fraction,log_ratio_abs_mean}` **keyset-identical on every rank** (all_reduce-safe). vLLM needs NO change (already emits token_ids+logprobs over `/chat/completions`).

- Commits: MarinSkyRL `11285333` + `d32022ee`; harbor `8737426c` (per-turn logprob/token-id length-parity guard in `Chat._accumulate_rollout_details` → empty-list-on-mismatch keeps index alignment).
- At an on-policy step (`staleness_max=0`, `log_ratio_abs_mean=0.0`): `tis/imp_ratio_mean≈0.79`, `tis/log_ratio_abs_mean≈0.094` nats (= inherent vLLM↔FSDP bf16 precision gap, what TIS corrects — not misalignment), `imp_ratio_capped_fraction≈0`. Smoke config: `hpc/skyrl_yaml/jupiter/extra/tis_smoke_0p6b.yaml`.
- `concatenate_generator_outputs` must merge via token-weighted merge (not `get_rollout_metrics`, which is reward/len only and drops `generate/tis/*` on the fully-async path).

---

## Collectives — `strategy.all_reduce(status)` requires IDENTICAL keys on every rank

`DistributedStrategy.all_reduce(data: dict)` does a separate NCCL all_reduce per key. If keys differ across ranks → NCCL **watchdog timeout** (`NumelIn=1` scalar is the giveaway).

- Fix pattern (`compute_log_ratio_diagnostics` v4, `69294ba5`): a `_log_ratio_diag_zero_metrics()` zeros fallback on early return + try/except at the call site.
- **Rule when touching `status` dict keys in `worker.py`:** every rank contributes the SAME key set every iteration — no conditional skips; data-dependent values that might fail get a sentinel under the same key, never omitted; wrap risky helpers in try/except with full-keyset fallback.

### Do NOT fire a full-PG collective from INSIDE `ppo_train` under fully_async + R3-decentral (FIXED `68ea066e`)

Under **fully_async + R3-decentral** the policy ranks do NOT co-arrive at ppo_train's top-of-body — staggered R3-chunk relocation means some ranks are IN ppo_train while others sit idle → a scalar all_reduce deadlocks (keyset is UNIFORM; the bug is collective PARTICIPATION desync).

- **Fix (`68ea066e`, objective-preserving):** precompute `Z` on the **DRIVER, collective-free** (`ppo_utils.compute_global_loss_denom`), stash in `data.metadata["global_loss_denom"]`; the worker READS it, falls back to legacy all_reduce only when absent. Gated on `is_fully_async` → sync RL byte-identical.
- **Durable rule:** any NEW cross-DP reduction for the loss/optimizer step must be hoisted to a **guaranteed co-arrival point** (the driver, or a barrier every rank provably reaches) — NEVER fired inline from `ppo_train`/the async loss loop.

---

## Runtime knobs — now FLAGS on the iris RL launcher (`cloud/iris/launch_rl_iris.py`, MarinSkyRL — sole/canonical launcher; the former OT-Agent `rl/cloud/launch_rl_iris.py` copy has been removed)

The `SKYRL_*` runtime knobs are first-class CLI flags (argparse group "MarinSkyRL runtime knobs"). The env var is retained as an override — precedence is **env/`extra_env` > flag > code default**. Every flag defaults to *unspecified*, so an all-defaults launch injects `{}` and the pod env is byte-identical to before; a config's `extra_env:` still wins over a flag. Footgun defaults were flipped ON so a config that FORGETS the line is now safe.

- **GDN path — `--gdn-mask-fla {auto,on,off}` (env `SKYRL_GDN_MASK_FLA`), default AUTO.** Default-ON, auto-derived from the model arch (`model_wrapper._gdn_mask_fla_enabled`): the pure-torch GatedDeltaNet path (the `fla` wheel is broken) auto-engages for GDN archs (Qwen3-Next / Qwen3.6-35B-A3B's GDN layers) and is a strict **no-op on dense** models. Set `--gdn-mask-fla on/off` (or the env) to force.
- **TIS served-id splice — `--tis-splice {on,off}` (canonical env `SKYRL_TIS_SPLICE`), default ON.** Uses vLLM's raw served `completion_token_ids` as the generated region so TIS tier-1 exact-by-id alignment holds (closes the think-block re-tokenization divergence). The two old knobs (`SKYRL_TIS_SERVED_ID_SPLICE` generalized + `SKYRL_QWEN3_5_TIS_SPLICE` empty-think special case) → one `_tis_splice_enabled()` policy (both legacy env names still honored). Byte-identical on non-thinking turns.
- **NCCL timeout — `--nccl-timeout-s` (env `SKYRL_WORKER_NCCL_TIMEOUT_IN_S`), default 1800.** Single accessor `constants.get_worker_nccl_timeout_s()` / `DEFAULT_WORKER_NCCL_TIMEOUT_IN_S=1800`.
- **R3 transport — `--r3-transport {by_value,resident,decentral}`, default `decentral`** (folds `SKYRL_R3_RESIDENT` + `SKYRL_R3_DECENTRAL`); `--r3-put-timeout-s` = `SKYRL_DISPATCH_PUT_TIMEOUT_S`.
- **Correctness knobs (default-ON), each now a flag:** `--forward-dispatch-fix`, `--weightsync-drain-barrier`, `--cp-require-right-align`, `--w13-reload-bracket` (pass `off` only for an A/B). Observability: `--host-ram-monitor`(+`-interval-s`). Feature: `--gdn-flashqla`, `--ep-loader-chunk-rows`.
- **REMOVED (dead):** `SKYRL_FWD_UNSHARD_FENCE`, the EPDIAG diagnostic family, `SKYRL_WEIGHT_SYNC_SERIALIZE`. Jupiter `extra/` configs still carry now-inert EPDIAG env lines (harmless).

---

## Known crashes & their fixes (factual)

### uvloop/libuv SIGABRT → force stock asyncio (BOTH driver + actors)

The libuv epoll SIGABRT under Daytona sandbox-teardown socket churn is fixed by **forcing CPython's stock asyncio SelectorEventLoop**, not by changing libuv. Ray installs uvloop in every worker via `try_install_uvloop()` (gated by `RAY_USE_UVLOOP`, default True); the SkyRL orchestrator is RTT-bound, so uvloop's throughput edge is moot.

- **Driver fix:** reset the policy at the top of **`BasePPOExp.run()`** (`main_base.py`), before its `asyncio.run()` calls — SkyRL `77fb0074`. Must be on the SHARED `BasePPOExp.run()`, NOT a per-example `skyrl_entrypoint`.
- **Actor fix (SkyRL `9e04851`):** also set `env_vars["RAY_USE_UVLOOP"]="0"` in `prepare_runtime_environment` (utils.py). **Use BOTH.**
- `set_event_loop_policy()` is deprecated Py3.12+; when removed, switch to `asyncio.run(coro, loop_factory=asyncio.SelectorEventLoop)`.
- Related but SEPARATE: the refcount-SIGABRT fix (harbor `ec508562` orphan-task reap + SkyRL `3b1708a0` gc backstop).

### MoE-RL first-step forward wedge → R3 transport (resident → decentral)

The MoE agentic-RL wedge at the first training-step forward: `rollout_routed_experts` `[B,seq,L,K]` shipped BY VALUE through every per-forward Ray task arg → Ray object-store spill → silent hang (a Ray-store wait, NOT an NCCL watchdog).

- **Root cause:** ~3.0 GB/dp-chunk even at uint8, naive dispatch re-serialized per actor (~16×/dp-group) → plasma cap overflow. Fix = uint8/int16 narrowing keyed to `num_experts` (int16 for >255 experts) + `MeshDispatch.dispatch` `ray.put`s each dp-chunk ONCE + shares the ObjectRef across the dp-group.
- **Current default = `SKYRL_R3_DECENTRAL` (ON, `e9b2f10d`):** routes routed-experts generation-worker → node-resident consumer so the head holds ~0 R3 (O(1) in model scale). Byte-identical, bounded-put fallback. Set `=0` for A/B.
- **`num_parallel_generation_workers: 128` across ALL iris configs** caps buffer + worker-held groups → footprint O(1) in model scale.
- A generation "worker" owns a GROUP (one prompt × n_samples, ~126 MiB with R3 at 80B), NOT a rollout. Workers ≫ vLLM working set only accumulate stale groups — bound it.
- The dp=1 put stall (gs1) loud-fails via `DispatchPutTimeoutError` (`d13c3586`, 600s bounded-put) — turned the silent 4.8h wedge into a 10-min failure.

### MoE served-policy token-salad on the RL update path → `SKYRL_W13_RELOAD_BRACKET` (FIXED `2bb70a88`)

A served MoE policy emitting incoherent CJK token-salad (100% reward-0) after a disaggregated weight sync = the FusedMoE **`w13` gate/up halves are in the wrong kernel order**. vLLM's initial from-disk load runs `process_weights_after_loading`, which for FusedMoE under **FlashInfer-CUTLASS / TRTLLM** (auto-selected on H100) applies `swap_w13_to_w31` (`[gate;up]→[up;gate]`). The RL update path did per-chunk `model.load_weights` with **no finalize**, reverting `w13` to checkpoint `[gate;up]` → the kernel reads the wrong halves → salad. **TRITON / AITER backends do NOT swap** → the same skip is harmless there.

- **Env var `SKYRL_W13_RELOAD_BRACKET`** (default `1`): brackets the multi-chunk sync in `fsdp_worker.broadcast_to_inference_engines` with `WorkerWrap.skyrl_begin/finish_weight_reload` (= vLLM `initialize/finalize_layerwise_reload`) so `process_weights_after_loading` runs **exactly once** post-sync. **Swap-inert on triton/dense → byte-identical there**, so leave it on.
- Scope: only the non-IPC, non-`_fuse_weights` broadcast path is bracketed. Diagnosis was MoE-specific × FlashInfer-CUTLASS × disaggregated-RL-update — NOT NCCL, NOT the gather, NOT placement.
- **Bring-up check:** engine log shows `initialize_layerwise_reload` / `finish_weight_reload`.
- **⚠ The MEGATRON backend's `broadcast_to_inference_engines` was MISSING this bracket** — the fix (`2bb70a88`) was wired ONLY into `fsdp_worker.broadcast_to_inference_engines`; `megatron_worker.broadcast_to_inference_engines` had no bracket. On the megatron backend (the iris-config default) the trainer syncs weights to the vLLM engines before the first generation, so on keep-1 the un-swapped `[gate;up]` overwrote the correctly-swapped from-disk load and was never finalized → the FlashInfer-CUTLASS kernel read transposed halves → 100% MoE rollout token-salad (all rewards 0; Qwen3-Coder-30B-A3B, keep1-v13). **Fixed by porting the identical non-IPC bracket into `megatron_worker.broadcast_to_inference_engines`** (rank-0 `begin_weight_reload()`+barrier before the `extract_weights` loop; barrier+`finish_weight_reload()` after; gated on `SKYRL_W13_RELOAD_BRACKET`, non-IPC path; mirrors `fsdp_worker.py:804-858`) — MarinSkyRL **PR #47**. **Load-bearing gotcha for ANY MoE RL on the megatron backend.**

### 80B placement init-OOM = two-PACK-PG race → `policy_strict_spread_pg`

Qwen3-Next-80B-A3B init-OOM was a **two-PACK-PG race** (inference PG + lazy policy PG, no anti-affinity, exactly-full 24 nodes → a policy worker lands on a vLLM-occupied GPU), **NOT** a ref-model issue (ref is correctly not instantiated, `use_ref_model=False`). Fix = opt-in **`policy_strict_spread_pg`** flag (SkyRL `6e3afc34`, OT-Agent `96df706f`): reserves the policy PG up front with STRICT_SPREAD. Default-off → all other RL byte-identical. The 80B yaml `hpc/skyrl_yaml/jupiter/extra/128GPU_qwen3_next_80b_a3b.yaml` sets it true.

### 80B gs1 optimizer-step NCCL hang (NEW code path)

At EP8×FSDP8×CP1, the FIRST backward+optimizer at 80B hangs at the **gs1 OPTIMIZER step** (`policy_train`): a `default_pg` ALLREDUCE `SeqNum=288606 NumelIn=1` (a barrier/grad-norm reduce) hangs → timeout → `mesh_fsdp _ALLGATHER_BASE SeqNum=6936` timeout → SIGABRT on FSDP policy worker → raylet worker-death cascade (failure_count stayed 0 → holds the gang wedged indefinitely; state-poll "running/16pods" is the colocated-vLLM-engine deception, not real progress). global_step never reaches 1. This is a NEW/untested code path, not an R3-store regression. (R3-store overflow is CLEARED — zero `DispatchPutTimeout`/`ObjectStoreFull`/`_ray_put_bounded` at any forward across the full run.)

---

## Resume / checkpoints

### Checkpoint pathing — ckpts are NESTED at `<rundir>/<job_name>/checkpoints/`, NOT the rundir top-level

```
<rundir>/                              # configs/ exports/ logs/ ray_logs/ sbatch/ wandb/ + an EMPTY top-level exports/
└── <job_name>/                        # the run subdir (same name as rundir leaf)
    ├── checkpoints/                   # ← FULL RESUMABLE CKPTS LIVE HERE (trainer.ckpt_path)
    │   ├── global_step_2/  global_step_4/  ...   # each: policy/ (FSDP shards) + trainer_state.pt + data_consumption_state.pt + generation_buffer_state.pt (~34MB)
    │   └── latest_ckpt_global_step.txt           # ← the step the restart resumes from
    ├── exports/                       # HF-format exports (trainer.export_path; cadence = hf_save_interval)
    └── trace_jobs/                    # per-rollout traces (HUNDREDS of thousands of files — NEVER find/du it)
```
- **Cadences are independent:** `trainer.ckpt_interval` (full resumable, e.g. 2) vs `trainer.hf_save_interval` (HF export, e.g. 5). Rendered values live in `configs/<job>_rl_config.json`.
- A glob of the rundir top-level finds nothing — the top-level `exports/` is empty. To check resume state: `cat <rundir>/<job_name>/checkpoints/latest_ckpt_global_step.txt`.
- Each ckpt persists `generation_buffer_state.pt` (the async rollout buffer), so `resume_mode=latest` restores the buffer too — relevant if a hang is *in* the buffer state (resume can re-trigger it).

### Resume overshoots `max_steps` — a step past the data ceiling is spurious

For the pymethods2test-large RL family: `epochs=2` × dataset/`train_batch_size=64` = exactly **80 optimizer steps**; configs set `max_steps=80` because that's the data ceiling. With `resume_mode=latest` + chained restarts, `global_step` does **not** hard-stop at 80 — it **overshoots** (observed 86). Steps 81→86 are **spurious** (re-runs exhausted data, "eternal-retry").

- A run reaching **step ≥80 is COMPLETE, not failed** → RL Cleanup Checklist, NOT fix-and-requeue.
- **Best-checkpoint selection must CAP candidates at step ≤80** (use ≤78 if a step-79+ greedy/eval-pass reward jump is present — that's an eval-checkpoint artifact, not learning).
- Errors in the 81–86 tail are noise (e.g. `VLLMValidationError: 32769 > 32768` near-budget BPE +1) — don't mis-diagnose.

### a3 RL resume (`--dry_run` regenerates the dedup config — RESOLVED `0b01a273`)

The launcher now (1) auto-resumes from the canonical run dir's `checkpoints/global_step_*` when present and `--overwrite_output_dir` was NOT passed (pins `ckpt_path`/`export_path`/`resume_mode=latest` as last-wins hydra overrides), and (2) routes `--dry_run` to a `<name>__dryrun` sibling so it can't seed the real dedup config. Pass `--overwrite_output_dir true` to force a fresh fork. (a3 series is CONCLUDED — no relaunch.)

---

## 80B RL is TRAINING-bound, and SkyRL FSDP is ALWAYS cross-node

The Qwen3-Next-80B-A3B production RL step (EP=8×FSDP=8, 32k, R3+TIS) is **training-bound, NOT gen-bound**. Measured step ≈ 17,000s (~4.7h): `policy_train` ~48%, `fwd_logprobs_values_reward` ~31%, `sync_weights` ~13%, `wait_for_generation_buffer` only ~7.5%.

- **SkyRL FSDP is cross-node regardless of `fsdp_size`.** `create_device_mesh` builds the mesh with `ep` innermost/contiguous (`mesh_shape=(ddp,fsdp,ep)`), so on 4-GPU/node Jupiter an FSDP group spans `fsdp_size` nodes. The ordering is deliberate for correctness (fsdp must precede ep so the composed expert DTensor slices ascending). The yaml comments claiming FSDP is "intra-node" are FACTUALLY WRONG.
- **EP=16×FSDP=4 does NOT restore intra-node FSDP** — throughput-neutral-to-worse. Do NOT switch EP/FSDP for speed.
- **The real speed lever** = make FSDP intra-node via a mesh-dim-reorder CODE change (fsdp last).

---

## FSDP2 Context-Parallel Stage 2 — attn-backend pivot

Branch `feuer/fsdp2-cp`. Added `trainer.attn_backend ∈ {auto,flash_attention_2,sdpa,flex}` (default `auto` = byte-identical to pre-Stage-2). `model_wrapper.py`: guarded flash import (`_HAS_FLASH` + shims that raise only if called) + `resolve_attn_implementation(...)`; CP (`context_parallel_size>1`) forces sdpa/flex, rejects flash varlen. Wired through policy/critic/ref. Tests: `test_attn_backend.py`, `test_sdpa_flash_parity.py`.

- **Parity:** sdpa@fp32 vs eager@fp32 logp 2.29e-3 (tight = correct); bf16 cross-kernel diffs (5e-2) are the bf16-quantization floor, not flash error.
- **GOTCHAS for GPU CP runs:**
  - **`/opt/SkyRL` baked-module shadow:** the SIF bakes SkyRL at `/opt/SkyRL`; bare `python script.py` imports it (not a worktree clone) → new kwargs silently ignored via `**kwargs`, both arms fall to eager (false pass). FIX: `apptainer exec --env PYTHONPATH=<worktree>/skyrl-train`; the GPU test asserts `model.config._attn_implementation` actually engaged.
  - Triton JIT gcc `-l:libcuda.so.1` link fail on compute node: `--env LIBRARY_PATH=/.singularity.d/libs`.
  - HF offline: prefetch into `/e/scratch/jureap59/feuer1/hf_cache`, `HF_HUB_OFFLINE=1`; `-p no:cacheprovider --confcutdir tests/cpu/<sub>` dodges the session-autouse `ray_init()` login-node hang.

---

## Engine saturation — root cause + how to READ it

The vLLM inference engines were starved by **harbor's client-side 1-second poll loop** (`_poll_response`), not Daytona, not engine count. Raising `n_concurrent_trials` cannot help (doubling n=128→256 stayed STARVED, tok/s FLAT). Daytona is FAST from CoreWeave (exec 0.15 s median; full HTTP call ~0.03 s). Per-turn residual ~79.5 s (78%) was harbor's `asyncio.sleep(1)` poll flooring every non-instant exec command at ≥1 s.

- **FIX (shipped):** (1) poll loop → `sleep(0.001 + random.uniform(0,0.001))` (harbor `ef42e75e`); (2) setup-timeout → tmux/asciinema baked into the snapshot (harbor `0729a3e9`). Measured payoff: `agent_setup` ~401 s → 0.41 s; `AgentSetupTimeout` 63% → 0%.
- On CoreWeave harbor is baked NON-editably into the gpu-rl image → harbor fixes need a kaniko rebuild + digest bump (SLURM harbor is editable → live on `git pull`). Build MULTI-LAYER (`SINGLE_SNAPSHOT=0`, max layer <8 GB).
- The gpu-rl / megatron image build is CANONICAL in MarinSkyRL: `docker/Dockerfile.gpu-rl` + `docker/build_gpu_rl_kaniko.sh`. `harbor[daytona]` is installed WITHOUT `--no-deps` — a base-env re-resolve drifts the Daytona SDK transitives; pin and validate sandbox-CREATE.
  - **The megatron image is built from `Dockerfile.gpu-rl` with `INSTALL_MEGATRON=1`, NOT from `Dockerfile.megatron`** — the latter is a dead 34-line CUDA/TE stub (no skyrl COPY, wired to no build; carries a redirect note). `Dockerfile.gpu-rl` **COPYs** `/opt/skyrl` (it does not `git clone` — any "gpu-rl git clones" comment is aspirational); a `git init`-after-COPY bake (GITSHA plumbed through `build_gpu_rl_kaniko.sh`) gives `/opt/skyrl` a `.git` so `--skyrl-ref` works on megatron images (verified: build log `/opt/skyrl git tree baked @ <sha>`).
  - **✅ Megatron backend is FULLY on `main`** (deps extra + lock merged via **#34**): both the megatron CODE files AND the `megatron` pyproject extra (`skyrl-train/pyproject.toml` `[project.optional-dependencies] megatron` — megatron-bridge 0.5.0 + megatron-core 0.18.0, `sys_platform==linux and platform_machine==x86_64`) + its `uv.lock` entries are on `main`. A megatron image now **builds directly off `main`** with `INSTALL_MEGATRON=1` — no feature-branch cherry-pick (the retired `d41bb73d` workaround is obsolete). transformers is pinned `>=5.8.1,<5.9` tree-wide (#34, megatron-bridge 0.5.0's requirement) so the fsdp2 + megatron backends train under an identical transformers.

### `nvidia-smi` SM-util% is a TRAP

Point-in-time SM-util reads **84–89% even when the engine is idle-waiting** — it only means "a kernel was resident during the sample." The trustworthy saturation tuple: **`Waiting`-queue depth + GPU KV-cache usage + power draw + memory-BW util**.
- Saturated ⇔ `Waiting > 0` AND KV off floor AND power near TDP (~700 W H100) AND mem-BW high.
- Under-fed ⇔ `Waiting = 0` always + KV ≈ 0 + power ≈ ⅓ TDP + mem-BW 2-5%.

### Daytona ORG routing

The agentic-RL grid must run on the **dedicated RL org (`DAYTONA_RL_API_KEY`, DataCompRL)**, NOT the shared `DAYTONA_API_KEY` (eval/datagen) org — the shared org's control plane self-saturates and throttles the eval campaign. The iris RL launcher re-sources `secrets.env` after any shell `export` (`cloud/iris/secrets_env.py`: file overrides shell), so a pre-launch `export DAYTONA_API_KEY=$DAYTONA_RL_API_KEY` is CLOBBERED — use the committed **`--daytona-api-key-env DAYTONA_RL_API_KEY`** flag (MarinSkyRL `cloud/iris/launch_rl_iris.py`; originally OT-Agent c6001bc1). VERIFY in-pod: `kubectl exec … printenv DAYTONA_API_KEY | sha1sum` == the RL key hash (NOT the shell before launch).

---

## Dependency stack — `skyrl-train/pyproject.toml` + `uv.lock`

Ground truth lives HERE, not in pyproject/lock comments (a stale `production runs cu130` comment caused a wrong-CUDA build; comments were purged in PR #19). Load-bearing pins:

- **CUDA line = cu128, NOT cu130.** `torch`/`torchvision` resolve from `pytorch-cu128`, `flashinfer-jit-cache` from `flashinfer-cu128`. cu128 supports Blackwell/sm_100, so one lock serves both the CoreWeave-H100 gpu-rl image AND the EmpireAI B200 (NGC-cu128) container. The gpu-rl Dockerfile is cu128 (`nvidia/cuda:12.8.0` + cu128-compiled wheels); a cu130 lock ABI-mismatches it. A cu130 pin was introduced speculatively in `e1cc7d51` and reverted in PR #19; cu130 was never prod.
- **`transformers>=4.56.0,<5`.** transformers 5 is breaking (peft 0.17 can't import); floor 4.56.0 = vLLM 0.20.2's floor.
- **`torch>=2.10` floor** carries the torch-native context-parallel API the CP path needs.
- **flash-attn is CPU-stubbed** via `FLASH_ATTENTION_SKIP_CUDA_BUILD=TRUE`: enough for CPU suites but NOT for real attention (fails at `import flash_attn_2_cuda`). Real builds happen out-of-band (gpu-rl image / production SIF). `[tool.uv.dependency-metadata]` declares flash-attn's requires-dist because its sdist computes metadata at build time needing torch → circularity makes `uv lock` fail otherwise.
- **flashinfer DOUBLE-PIN (gotcha).** vLLM 0.20.2 hard-pins `flashinfer-python==0.6.8.post1`; flashinfer RAISES if the jit-cache version differs → `flashinfer-jit-cache` MUST match, not float.
- **vllm is the ONLY inference extra.** sglang/mcore/flashrl were removed (each pinned a torch/transformers the base excludes). The `vllm` extra mirrors the production SIF: torch 2.11.0, vLLM 0.20.2rc0, flash-attn 2.6.3, torchvision 0.26.0.
- **torchtitan** (`git rev a1fdd7e`) is pure-python, installed by the `ep` extra (+ tyro from the lock). `deepep` = the Stage-5 perf backend, x86_64-only. Neither pins torch/vllm, so they're NOT in `[tool.uv].conflicts`.

---

## CI — `marin-nightly.yaml` (resolved 2026-07-15)

Upstream `main` (#2 `e1cc7d51`) deleted the old `SkyRL-GPU-E2E-CI` (which fast-failed on Anyscale auth) and added **`marin-nightly.yaml`** — a Marin-owned single-H100 GRPO nightly gate — plus restored PR CI (`cpu_ci.yaml`, `cpu_skyrl_tx.yaml`). Merged into `penfever/working` at `0d101151`.

---

## Diagnostics — how to read metrics

### `policy/rollout_train_prob_diff_mean` in the MILLIONS is a BENIGN SCALE ARTIFACT

Seen `policy/rollout_train_prob_diff_mean ≈ 7.5e6` on MoE grid runs — looks alarming but is a diagnostic-metric artifact; training is correct, R3 replay is faithful. Root: `trainer.py:~1521` computes `prob_diff = (rollout_logprobs[mask] − action_log_probs[mask]).exp().abs()` then `.mean()` — i.e. **`E[exp(logprob_diff)]` in LINEAR space**, which any fat tail dominates (a single token → millions; that's the std≫mean signature). Masked correctly (response tokens only), just exp-then-linear-mean.

- **The ACTUAL gradient signal is the log-space, aligned, cap-2.0 TIS path:** `policy/tis/imp_ratio_mean≈1.017`, `imp_ratio_capped_fraction≈1e-4`, `log_ratio_abs_mean≈0.06 nats`, `log_ratio_abs_p99≈0.21`, `generate/tis/exact_match_fraction≈0.99`, `raw_grad_norm≈4e-5` (stable — a BROKEN MoE router-replay instead gives `log_ratio_abs_max~19, policy_loss~1e4, raw_grad_norm~1e5`, per `trainer.py:1406-1417`). **Correctness check = the `policy/tis/*` + `raw_grad_norm` metrics, NOT `rollout_train_prob_diff_mean`.** Listed benign in the `monitor-job-tables` skill.

### Rollout/generate path is uniformly `AttributeError`-guarded

The ENTIRE agentic rollout/generate path is robustly guarded against `AttributeError`:
- `examples/terminal_bench/terminal_bench_generator.py`: `_process_trial_result` wrapped in `except (KeyError, AttributeError, TypeError)` (~L1284); an outer handler (~L799, `fb102ed`) catches errors raised DURING processing (e.g. jinja2 `TemplateError`) and coerces them to masked.
- `skyrl_train/generators/utils.py`: `get_response_ids_and_loss_mask_from_messages` (1031); `extract_{logprobs,token_ids,routed_experts}_from_rollout_details` (757-895) are None/dict/object-safe via `getattr`+`isinstance`.
- harbor `agents/terminus_2/terminus_2.py` + `llms/lite_llm.py`: `LLMResponse` fields all declared; response parsing `getattr`/`.get`-safe.

**Heuristic:** a deterministic rollout `AttributeError` is almost certainly raised inside a rollout DEPENDENCY (litellm / openai-SDK / daytona / uvloop) under the image's package pins, returned as an Exception from `asyncio.gather` and classified to `generate/errors/AttributeError`. Treat it as an IMAGE/env issue (a deps rebuild likely fixes it), NOT a MarinSkyRL/harbor source bug, unless a verbatim traceback points at first-party code. Confirm on the rebuilt gpu-rl image with rollout logs captured **live, in-window** — CoreWeave finelog retains only the init-phase log post-mortem.

### Rank-0 logging — "only rank 0 logged X" ≠ "only rank 0 RAN X"

Most skyrl-train worker diagnostic logs are **gated to rank 0** — `if torch.distributed.get_rank() == 0:` (e.g. `init_weight_sync_state`'s lines, `worker.py:452-463`) or tqdm `disable=not self.strategy.is_rank_0()` (`worker.py:1038,1533`). The collective itself runs on **all** ranks; only rank 0 emits the message. The iris finelog AGGREGATES every Ray actor's stdout into one stream tagged by actor `ip=`/`pid=`. **You CANNOT infer "only rank 0 reached code X" from "only rank 0 logged X" for a gated log.**

- Per-NODE pod logs (`pod_rank1..N`) only show the `start_rl_iris_controller` bootstrap — the actual rank-actors run on those nodes but log to the HEAD/finelog, so per-pod logs are NOT per-FSDP-rank views.
- **The one RELIABLE per-rank signal: `WORKER_FORWARD_ENTER rank={self._rank}` (`worker.py:534`) is deliberately UNGATED** — every rank that reaches `worker.forward` prints its own rank. So "only rank 0 printed `WORKER_FORWARD_ENTER`" genuinely DOES mean only rank 0 reached the forward. Trust THIS marker; do not trust the gated ones.
- **To localize a per-rank hang reliably:** (1) use UNGATED instrumentation (log `self._rank` unconditionally); (2) capture per-rank FR dumps for ALL pods, not just rank 0 (`TORCH_NCCL_DEBUG_INFO_TEMP_FILE` writes `/tmp/nccl_fr_rank<N>` on every node — `kubectl cp` from each pod BEFORE the kill reaps them); (3) per-rank faulthandler/SIGUSR1 py-stacks. A SUCCESSFUL run's logs make the best diff.
