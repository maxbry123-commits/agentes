---
name: eval-standard-launch
description: >-
  Launch the fixed Delphi #6279 RL-scaling-laws downstream MATH eval suite (MATH-500 / AIME24 /
  gsm8k via evalchemy + lm_eval) on CINECA Leonardo, for completed SFT / RL / base checkpoints.
  Covers finding which cells are newly-completed-but-uneval'd, the offline pre-download, the
  delphi_eval.sbatch invocation + RUN_NAME/STAGE convention, the load-bearing gotchas (chat-template
  override, 4k context, TP per head-count, MATH500/gsm8k split), and the SCORES.md tracker update.
  HF-upload-only — NEVER DB-register. Use when asked to eval Delphi #6279 SFT cells / update the
  scaling-laws score grid. Refs: experiments/active/delphi/rl-scaling-laws-6279/.
---

# eval-standard-launch

Downstream math-eval harness for **Delphi #6279 RL-scaling-laws** (task #215) — NOT the agentic tb2 eval listener. Scores Delphi checkpoints on **MATH-500 (1 seed) + AIME24 (10-seed mean±se) + gsm8k (strict+flex)** via `evalchemy`/`lm_eval` on Leonardo. **HF-upload only — NEVER DB-registered** (`project_delphi_sft_hf_only_no_db`).

## 0. Reference files (read these first — they are the source of truth)
Local notes dir: `/Users/benjaminfeuer/Documents/experiments/active/delphi/rl-scaling-laws-6279/`
- **`EVAL_CONVENTION.md`** — the fixed eval protocol (suites, seeds, naming §3.4, chat-template §2.5).
- **`delphi_eval.sbatch`** — the ONE eval job (all gotchas baked in; canonical). Cluster copy under `/leonardo_work/AIFAC_5C0_290/bfeuer00/…`.
- **`main_sft_evals/SCORES.md`** — master tracker for the **54-run main grid** (27 midtrained ckpts × 2 cold-starts: `magpie_lr1e5` math-strong / `wc386k_lr1e5` math-weak). Each row: HF model `laion/<basename>`, eval-job column, status (✅ done / ⏳ pending). The separate earlier cold-start grid lives in `coldstart_grid_evals/` (own `../eval/SCORES.md`).
- **`SFT_LEONARDO_INSTRUCTIONS.md`** — the SFT side (how cells get trained + uploaded).

## 1. What "newly completed" means
A cell is ready to eval when its **SFT model is uploaded to HF `laion/<basename>`** (Delphi SFT is HF-only; an uploaded repo = a finished cell). The work = the SCORES.md rows still **⏳ pending** whose `laion/<basename>` repo now **exists + is non-empty** (check via `huggingface_hub`/`hf`; `HF_TOKEN` from your secrets env — `.agents/secret.md`). Rows whose model isn't uploaded yet (e.g. most large `1e21`/`1e22` cells mid-training) are SKIPPED until done.

## 2. The launch (per cell)
```bash
# RUN_NAME = the exact SFT model basename; STAGE = sft (chat-template ON) | rl | base (template OFF)
RUN=delphi-9e19-p33m67-k0p20-lr83-a002-magpie_lr1e5-sft
sbatch --job-name="delphi-eval-$RUN" <leonardo>/delphi_eval.sbatch laion/$RUN $RUN sft
```
- **Model-specific `--job-name` is MANDATORY** (not the generic default) so squeue + `%x-%j.log` + `meta.env` map jobid→model 1:1. The script self-renames + emits a greppable `EVAL_JOBMAP` line + writes `<OUT>/meta.env`.
- Job shape: 1 node / 4 GPU (A100 64GB) / 8h / `boost_usr_prod`, conda env **`evalchemy-marin`**, runs from `/leonardo_work/AIFAC_5C0_290/bfeuer00/code/evalchemy-marin`. Output → `…/experiments/delphi-eval/<RUN_NAME>/`.

## 3. Pre-download is REQUIRED (compute is offline)
`delphi_eval.sbatch` runs `HF_HUB_OFFLINE=1` (Leonardo compute has no internet). **Pre-cache each model on the LOGIN node first** into `HF_HOME=HF_HUB_CACHE=/leonardo_work/AIFAC_5C0_290/bfeuer00/data/hub` (login nodes have direct internet). If a login-node `snapshot_download` risks the ~100s login-killer, use the notes' documented pre-download path (tmux / a small sbatch). The eval sbatch itself needs NO SSH tunnel (offline + pre-cached); only the pre-download touches the network.

## 4. Load-bearing gotchas (all handled inside the sbatch — know them when debugging)
- **HOME is read-only on Leonardo (login AND compute).** The sbatch redirects HOME + flashinfer/triton/inductor/vLLM/XDG caches to a writable `…/delphi-eval/.cache/*`; without it every vLLM worker dies `PermissionError … /.cache/flashinfer`.
- **delphi_v0 chat-template override (sft/rl only):** the SFT/RL repos ship a plain 656-char Llama-3 template (the delphi ReasoningTemplate didn't persist into the repo) → evaluating as-is is a train/eval mismatch (empty think channel). The sbatch overrides the cached tokenizer's `chat_template` to `OpenThoughts-Agent/chat_templates/delphi_v0.jinja2` (idempotent, leaves `.plainbak`) before eval. `base` stage skips this (no template, raw completion).
- **`MAX_MODEL_LEN=4096`** (NOT the marin 32768 default): Delphi ckpts are 4k-cutoff with a malformed llama3 rope_scaling block; vLLM derives 4096 and HARD-rejects 32768. Generation pinned `MAX_GEN_TOKS=3584`. Comparability holds within the 4k cohort; flag any model exposing >4k.
- **`--max_tokens` MUST be pinned** to MAX_GEN_TOKS — MATH500/AIME24 are evalchemy chat_benchmarks whose max_new_tokens DEFAULTS to 32768 (not reached by `--gen_kwargs max_gen_toks`); unset → lm-eval computes `4096-32768 = negative` → truncates prompt to empty → `decoder prompt cannot be empty`.
- **TP per head-divisibility:** `num_attention_heads % TP == 0`. The small Delphi Qwen3 (14 heads) → **TP=2** (TP=4 hard-fails). Pin TP per model to the largest node-supported divisor of its head count.
- **MATH500 and gsm8k run as SEPARATE sequential processes** (not one `--tasks` call): MATH500 is an evalchemy chat_benchmark, gsm8k is lm-eval-native; in one process the second vLLM engine inits while the first is GPU-resident → OOM/WorkerProc fail and gsm8k is silently dropped. gsm8k runs via plain `lm_eval` (evalchemy double-builds the engine for native tasks → OOM on 64GB). AIME24 is its own pass.
- **`--verbosity INFO` is required** (evalchemy `getattr(logging, args.verbosity)`; default None → `AttributeError` after full vLLM init).
- **Idempotent skip:** `<OUT>/seed42` existing → the cell is skipped. If gsm8k failed after MATH500 wrote seed42, delete `<OUT>/seed42` (or re-run gsm8k by hand) — the skip keys on that dir.

## 5. After submit → tracking + consolidation
1. Confirm queued: `squeue -u bfeuer00 | grep delphi-eval`; collect job ids.
2. **Update `main_sft_evals/SCORES.md`**: set submitted rows' status → `🚀 eval submitted` + put the Leonardo job id in the eval-job column. Do NOT fabricate score cells (leave `—`); preserve the table format exactly.
3. On completion, per-model `results_*.json` rsync into `main_sft_evals/<basename>/`, scalar partials into `main_sft_evals/.partial/<basename>.json`, and SCORES.md is consolidated from them (MATH-500, AIME24 mean±se, gsm8k strict/flex, Raw). The #6279 deliverable = how MATH-500/AIME24/gsm8k move with (scale × mix) at each of the two starting points (does a strong-vs-weak math start change the midtraining ranking).

## 5b. Evaluate a (post-RL) checkpoint on the Delphi eval suite (reusable)
The *same* harness scores ANY standard Delphi checkpoint — base / post-SFT / **post-RL** — on the fixed suite (`EVAL_CONVENTION.md` §1.2: MATH500 1-seed + AIME24 10-seed mean±se + gsm8k strict/flex, pass@1, temp 0.7). `rl-standard-job-cleanup` defers to THIS section as its final step after the post-RL ckpt is HF-uploaded. The only deltas from §2 are the **STAGE token** and the **tracker the result lands in**:
1. **Point it at the HF-uploaded ckpt.** The ckpt is `laion/<run_name>-<BEST>-<size>B` (the repo `rl-standard-job-cleanup` §6 just published — weights at root). Pre-cache it on the login node first (§3), same as any cell.
2. **STAGE = `rl`** (chat-template ON — same delphi_v0 override as `sft`; only `base` skips it):
   ```bash
   RUN=<run_name>-<BEST>-<size>B
   sbatch --job-name="delphi-eval-$RUN" \
     /leonardo_work/AIFAC_5C0_290/bfeuer00/experiments/delphi-eval/delphi_eval.sbatch laion/$RUN $RUN rl
   ```
   Auto-TP=2 for the 30-head 9.7B Delphi Qwen3; `max_model_len=4096`/`max_gen_toks=3584`; all §4 gotchas (template override, 4k context, MATH500/gsm8k split, AIME24 10-seed pass) apply unchanged — baked into the canonical `delphi_eval.sbatch`. **One node / 4 GPU / 8h / `evalchemy-marin` env.**
3. **Results land in the RL tracker, not the SFT one.** Per-model output is `…/experiments/delphi-eval/<RUN>/seed{42..51}` + `meta.env`; consolidated scores go to **`main_rl_evals/SCORES.md`** (the post-RL tracker — keyed by (scale, mix, start-point) so SFT-vs-RL deltas line up against `main_sft_evals/`), via the same harvest path as §5 / `eval-standard-cleanup`. **HF-upload-only — NEVER DB** (the post-RL ckpt has no models DB row and this eval doesn't create one). After submit, add the row to `main_rl_evals/SCORES.md` set to `🚀 eval submitted` with the Leonardo job id; harvest per `eval-standard-cleanup`.

## 6. Leonardo SSH quoting traps (these bite repeatedly)
- Do NOT use parentheses inside a `bash -lc "..."` double-quoted string.
- Do NOT use single quotes inside the outer `ssh '...'` arg (a single quote closes it). Use escaped double-quotes / heredocs / plain words.
- Refresh the step-ca cert if any tunnel op needs it (per CLAUDE.md) — but offline eval sbatch + a login-node pre-download (direct internet) do not need the tunnel.
- Don't disturb the still-PENDING Delphi SFT dependency chain; evals are independent 1-node jobs.
