---
name: eval-agentic-launch
description: >-
  Launch agentic Harbor evals through the OT-Agent unified eval listener
  (eval/unified_eval_listener.py) on any cluster: select models (query_unevaled_models.py /
  priority lists), wire the pinggy served-model tunnel, submit with the right preset + flags in tmux,
  then VERIFY the launch actually works via the 15-min infra sanity check (pinggy auth, Daytona→cluster
  api_base, vLLM POSTs, trial progression — catches "RUNNING but silently dead" jobs). Cluster-AGNOSTIC:
  per-cluster particulars (sbatch script, gpu-mem ceiling, concurrency, cert/tunnel, conda env, paths,
  Daytona key, pre-download) live in `.agents/ops/<cluster>/`. Use when asked to launch/relaunch agentic
  evals, or eval a model on a benchmark (terminal_bench_2 / dev_set_v2 / swebench / bfcl / aider).
---

# eval-agentic-launch

Launch agentic Harbor evals via the **unified eval listener** (`eval/unified_eval_listener.py`). Cluster-agnostic; read `.agents/ops/<cluster>/ops.md` first for the cluster's sbatch script, gpu-mem ceiling, concurrency, cert/tunnel, conda env, paths, Daytona eval-org key, and whether `--pre-download` is needed.

> **Front door: `python -m hpc.launch --job_type eval_listener …`.** Runs the listener's `main()` in-process after the launcher preamble (`detect_hpc` + `set_environment` → `DCFT`/`EXPERIMENTS_DIR`/`PYTHONPATH` + hosted-vllm/Supabase keys + `chdir` to repo root), so no manual `source hpc/dotenv/<cluster>.env` / `export PYTHONPATH` / `cd` is needed. Forwards the listener's ~50 flags verbatim (strips only `--job_type eval_listener`). The raw `python eval/unified_eval_listener.py …` fallback still works (same public API) but you own the preamble — if you ever see `FATAL: WORKDIR=... is not the OpenThoughts-Agent repo root`, you used the raw script from the wrong place; switch to the front door.

> **⚠ Secrets from `$DC_AGENT_SECRET_ENV`, never hardcoded in a script/config/commit.** The eval sbatch sources it (`~/secrets.env`; TACC `$SCRATCH/keys.env`) and reads the two Daytona eval-org keys: `DAYTONA_API_KEY` (org1) + `DAYTONA_DATA_API_KEY` (org2), 3:1-weighted (3/4 org2). Fails loudly (`:?`) if either is unset. A literal `dtn_…` key committed anywhere is a leak — rotate/revoke it, don't just fix-forward.

## 1. Select the models
- **Priority list** (default): a file in `eval/lists/` (`models_8b_*.txt`, `models_32b.txt`, `models_131k.txt`). Launch with `--require-priority-list --priority-file eval/lists/<file>`.
- **Find unevaled models** — `scripts/database/query_unevaled_models.py` (resolves benchmark families via the Supabase `duplicate_of` field, e.g. `dev_set_v2` ⊇ `DCAgent_dev_set_v2`/`dev_set_v2_2.0x`/`openthoughts-tblite`):
  ```bash
  python scripts/database/query_unevaled_models.py --benchmark <fam> --size <8|32> -o eval/lists/<file>.txt -v
  # needs SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
  ```

### `--require-priority-list` is LOAD-BEARING
`--priority-file` alone only changes sort order; the filter "skip models not in the list" lives behind `--require-priority-list` (`unified_eval_listener.py` ~L978). Without it the listener submits evals for **every unevaled model in the lookback window** (routinely 700+). Always pass both. If launched without it by accident: kill the listener **before** it leaves pre-download (submission is after `Pre-downloading…`), then confirm via `squeue`/`sacct --starttime=now-Nmin`. The listener python is a child of the `sshd: …@notty` session and survives the local ssh client dying — `pkill -9 -f unified_eval_listener.py` on the cluster to stop it.

### Benchmark = a `--preset` (one, not both with `--datasets`)
`tb2`=terminal_bench_2, `v2`=dev_set_v2, `dev`=dev_set_71_tasks, `swebench`, `bfcl`, `aider`. `--preset swebench` is the **random-100 subset** (`DCAgent/swebench_verified_eval_set` → `swebench-verified-random-100-folders`, n_concurrent 32), not the full set.

### "ID evals" — launch all three legs
Each leg is a separate listener invocation (different n_concurrent/harbor-config, don't combine into one `--datasets`):

| leg | `--preset` | dataset (post-alias) | n_concurrent |
|---|---|---|---|
| SWE-bench-verified random-100 | `swebench` | `swebench-verified-random-100-folders` | 32 |
| dev_set_v2 | `v2` | `DCAgent/dev_set_v2` | 128 |
| terminal_bench_2 | `tb2` | `DCAgent2/terminal_bench_2` | 64 |

"Run the ID evals" = fire one listener per leg (§4) + the §5 infra check on each. (Full SWE-bench-verified and other benchmarks are OOD.) Scoring side (`crud-otagent-supabase`) uses the same 3-member set; `dev_set_v2` is partial-credit → counts toward the ID mean but excluded from the ID SE and model-vs-model ranking.

### Re-eval / parity test → `--force-eval`
By default the listener **Skips** any model with a `Finished`+metrics row (`reason=job finished`) — correct for cohort fill, but blocks a deliberate re-run. `--force-eval` bypasses that dedup and submits a fresh `sandbox_jobs` row (doesn't touch the existing row → no metrics-clearing, works across users). Pair with `--require-priority-list` + a single-model `--priority-file` so only the intended model is forced. `--stale-started-hours` does NOT override a `Finished` row (only re-ages `Started`). Distinct from `--force-reeval` (resume-path flag, see `eval-agentic-cleanup` check 4).

## 2. Harbor config + timeout multiplier (config-by-size — usually nothing to do)
**Do NOT pass `--harbor-config` for standard terminus-2 evals.** The listener selects the canonical config by model size and sets `EVAL_HARBOR_CONFIG` per-model:

| model size | selected config | timeout multiplier |
|---|---|---|
| 8B-class (≤ ~14B; 1.5B/7B/14B) | `hpc/harbor_yaml/eval/dcagent_eval_defaults.yaml` | 2× |
| 32B-class (~28–42B; incl. MoE `30b-a3b`) | `hpc/harbor_yaml/eval/dcagent_eval_defaults_32b.yaml` | 16× |
| out-of-band (70B/80B) or no size token | base default | 2× + logged note |

Size is read from the largest `\dB` token in the HF name. The multiplier flows as `EVAL_TIMEOUT_MULTIPLIER` and is recorded in the Pending row so dedup matches what ran. The deprecated `eval_ctx*_non_it*` / `ctx32k_non_it_16x_eval_.yaml` configs carry stale `*-drop-ei` metrics → `JobConfig ValidationError`.

**Resolution order (first wins):** (1) explicit `--harbor-config` / preset `harbor_config` — overrides size selection for **every** model (use for 131k context / `openhands_*` installed-harness); (2) per-model `timeout_multiplier:` in the registry (for names with no size token, e.g. a Qwen3-8B named `laion/GLM-4_7-swesmith-…`); (3) size-based table above. For a one-off `harbor jobs start`, point `--config` at the 8B/32B file.

## 3. Pinggy tunnel — installed-harness ONLY (not terminus-2)
**Skip for the default `terminus-2` agent** (every `eval_ctx*`/`*_non_it*` config; all `--preset`s). Do NOT pass `--pinggy_*` / consume a pair.

**Installed harnesses (opencode / `openhands_*`) run in the Daytona sandbox and call back out to the served model over a public pinggy tunnel.** The full recipe for the **opencode installed-harness + pinggy** ID-eval — the config (`eval_opencode_ctx32k.yaml`), config-delivery mechanism (`--config-yaml` on TACC vs `--harbor-config`), the `--pinggy_persistent_url`/`--pinggy_token` flags + pairs 8/9/10, the sbatch installed-agent tunnel/routing branch, the `vllm/` provider, `-Thinking-` model specifics, and the pinggy infra checks — lives in **`.agents/projects/harbor/ops.md` → "Agentic ID-eval via the opencode (installed) harness + pinggy"**. The privileged URL/token bank is in `.agents/secret.md` / `notes/ot-agent/pinggy_bank.md` (never inline it). Resume of an installed-harness eval also needs the tunnel — see `eval-agentic-cleanup` check 4.

## 4. Launch (in tmux — listener is long-running)

> **Concurrent-submit guard: ONE listener enqueues many legs; do NOT fire N concurrent `--once` processes.** A multi-leg refill is one invocation that submits each leg internally with a 1s `submission_delay` (`unified_eval_listener.py` L3204–3205). Firing N listener processes near-simultaneously on the login node races conda's lazily-imported plugin registry → a circular-import at activation. If multiple listener processes are truly required (incompatible n_concurrent), stagger them ~30–45s apart — never `&` them together. (Per-job `conda activate` inside the sbatch runs on independent compute nodes and never races.)

```bash
# inside tmux. The front door does the preamble (no manual source/PYTHONPATH).
python -m hpc.launch --job_type eval_listener \
  --cluster-config <cluster-name> \
  --preset <preset> \
  --require-priority-list --priority-file eval/lists/<file>.txt \
  --config-yaml dcagent_eval_config_no_override.yaml \
  [--agent-kwarg 'extra_body={"chat_template_kwargs":{"enable_thinking":true}}'] [--agent-parser json] [--max-output-tokens 16384] \
  [--pre-download] [--force-reeval] [--pinggy_persistent_url <URL> --pinggy_token <TOKEN>] \
  --once --verbose 2>&1 | tee eval/<cluster>/logs/<preset>_listener_$(date +%Y%m%d_%H%M%S).log
# Raw-script fallback (you own the preamble): from repo root, export PYTHONPATH="$PWD:${PYTHONPATH:-}", run python eval/unified_eval_listener.py … with the same flags.
```

- `--cluster-config` takes a **bare cluster name** (`leonardo`, `tacc`) resolved from `hpc.hpc`'s `eval_cluster_view` (a `.yaml` path still works as back-compat). Supplies sbatch_script/hardware/conda_envs/paths — so you no longer pass `--sbatch-script`/`--n-concurrent`/`--gpu-memory-util`.
- **Per-model serve config** (`conda_env`, `tensor_parallel_size`, `data_parallel_size`, `max_model_len`, `limit_mm_per_prompt`, `max_output_tokens`) comes from the shared registry **by default** — no flag. The cluster yaml's `hardware_profile:` (e.g. `gh200`) selects the per-cluster recipe; a per-cluster intrinsic delta is `name@<profile>`, a hardware delta is `variants: {<profile>: {…}}`. Confirm it loaded: listener logs `Model-config registry ENABLED` + `Loaded model registry: N model config(s)` + `Using conda env '<env>' for <model>`. `--baseline-model-configs` is deprecated (opt-out of the registry).
- **Edit per-model serve config in `model_config/<org>/<slug>.yaml`, NOT the generated `eval/configs/model_configs.yaml`** (auto-generated, carries a `# do NOT hand-edit` banner). Regenerate with `python scripts/generate_eval_registry.py` (drift gate: `--check`).
- **Thinking is per-model authoritative** (sourced from the registry via `agent_kwargs: [extra_body={…enable_thinking:true}]`); presets never carry thinking; there is no `--enable-thinking` flag. Override with `--agent-kwarg 'extra_body={"chat_template_kwargs":{"enable_thinking":true}}'` (precedence: CLI > registry > preset).

## 5. VERIFY the launch — 15-min infra sanity check (do NOT trust "RUNNING")
A job can report RUNNING while nothing happens (pinggy locked, launcher missing `--pinggy_*`, dead vLLM engine). **After launching, schedule a 15-min (`ScheduleWakeup delaySeconds: 900`) check** and re-arm each pass until the eval terminates / you have a verdict.

> Checks 1–2 are pinggy-path (installed-harness) ONLY — skip for terminus-2. For terminus-2, served-model reachability is proven by check 3. Checks 3–4 apply to every launch.

1. **Pinggy tunnel** (installed-harness) — pinggy auth `You are authenticated as …` + a growing `RB:/SB:/TC:` traffic counter. Full checks (auth, sandbox `api_base` = public `*.a.pinggy.link/v1` not `10.*`, relaunch-on-lock) → `.agents/projects/harbor/ops.md` § opencode + pinggy.
2. **Daytona → cluster** (installed-harness) — a trial's `config.json` `api_base` MUST be `https://*.a.pinggy.link/v1`, NOT `10.*.*.*` (see the harbor ops.md opencode+pinggy section).
3. **vLLM serving** — `POST /v1/chat/completions` count grows ≥ a few/min, `200 OK` dominates. `400` ratio > 15% → context overflow (`VLLMValidationError: input tokens …` → lower `max_input_tokens`/`max_output_tokens` in the harbor yaml).
4. **Trial progression** — count trials with `agent/` populated (active) and `result.json` (done). 30+ min with zero `agent/command-0/` (OpenHands) → setup stalled. Completions with `n_output_tokens: None` and `agent_execution.finished_at ≈ started_at` (instant-fail) = tunnel not carrying traffic despite a healthy-looking job.

Quick liveness (≈15 min after submit): `ssh <cluster> "squeue -u $USER --format='%.18i %.50j %.8T %.10M'"` then tail the newest log — vLLM health-check pass, (Leonardo) SSH tunnel up, `trial`/`reward` lines, no OOM/repeated DaytonaErrors.

## 6. Trial directory layout
`<run_tag>/<task>__<trial_id>/`: `config.json` (mtime≈start, has `api_base`), `trial.log`, `result.json` (timestamps + `verifier_result.rewards.reward` + `exception_info`), `exception.txt`, `agent/trajectory.json`, `verifier/{reward.txt,detailed_scores.json}`. Eval **cleanup + manual DB register + trace upload** → `eval-agentic-cleanup`.

## Other gotchas

- **`PermissionError: [Errno 13]` at `harbor/job.py … job_dir.mkdir()`** = a `jobs_dir` in the harbor config that another user owns. The canonical configs ship no `jobs_dir`; `eval_harbor.sbatch` passes `--jobs-dir "$EVAL_JOBS_DIR"` (per-user `…/ot-baf/eval_jobs`) which overrides the config. If you see this, confirm the sbatch has the `--jobs-dir` line; a hand-rolled `harbor jobs start` will reintroduce it. Resume is unaffected (takes `-p $RUN_DIR`).

- **A crashed eval leaves a non-terminal DB row blocking resubmission for 24h** (`reason=job in progress`). After a crash the row stays `started`; the listener only resubmits `started` rows older than `--stale-started-hours` (default 24h, `EVAL_LISTENER_STALE_HOURS`). Pass a small value (e.g. `--stale-started-hours 0.05` = 3 min) to force resubmit of the just-crashed attempt. Pending rows use `--stale-pending-hours` (default 6h, auto-cancels the stale SLURM job).

- **Jupiter: pass `--reservation reformo`** or eval jobs starve behind RL (the reservation holds ~128 nodes while the general booster pool is empty). `eval/jupiter/eval_harbor.sbatch` sets `--account reformo` but no `#SBATCH --reservation`. Check `scontrol show reservation` for the live name/expiry before relying on it (the flag errors if the reservation is dead). Rescue already-PENDING jobs: `scontrol update jobid=<j> reservation=reformo`.

- **`hosted_vllm/<org>/<model>` evals need harbor commit `0f5a6e9e`** (allows 2-slash org-qualified names — `validate_hosted_vllm_model_config` in `llms/utils.py`) and `model_info` supplied via `--agent-kwarg` (`{"max_input_tokens":…,"max_output_tokens":…,"input_cost_per_token":0,"output_cost_per_token":0}`; token limits from the served vLLM `max_model_len`, costs 0 = self-hosted). Both are wired by default into the `eval_harbor.sbatch` files via `EVAL_VLLM_MAX_MODEL_LEN` (default 32768) + `EVAL_MAX_OUTPUT_TOKENS` (default 16384) (OT-Agent commit `d0064011`). If org-model evals fast-fail (~9 min, 0 POST 200s, 0 trajectories, all N trials raise identically), confirm those commits are in the cluster's harbor clone.
