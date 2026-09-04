---
name: sft-cleanup-hf-only
description: >-
  Clean up a completed NON-AGENTIC / HF-only SFT model — HF upload WITHOUT Supabase DB registration. The
  counterpart to sft-job-cleanup (which uploads AND registers). Use when a completed SFT cell belongs to an
  HF-only series (config `enable_db_registration: false`, or a known HF-only series like the Delphi #6279
  54-grid): upload the weights to laion/ and STOP — do NOT run manual_db_push. Covers cell→hub_model_id
  resolution (incl. the Delphi launch_54_map.tsv), the Leonardo sbatch-tunnel upload, and the downstream eval
  hand-off. For DB-registered models use sft-job-cleanup instead.
---

# sft-cleanup-hf-only

Publish the completed HF-only SFT model without Supabase registration. Use `sft-job-cleanup` for registered SFT.

## When to use
- A completed SFT cell whose config sets **`enable_db_registration: false`**, OR a known HF-only series (Delphi #6279 `delphi-*` cells).
- Discovered during a sweep, or "upload the completed Delphi cells (no DB)".
- If it's a normal registered SFT → use `sft-job-cleanup` (don't skip the DB step there).

## Procedure (per completed cell)
1. **Confirm HF-only completion.** Check `enable_db_registration: false` (or Delphi `delphi-*`) and final training progress.
2. **Cancel that cell's pending restart chain** (`squeue … | grep <job> | grep PENDING | awk … | xargs -r scancel`).
3. **Prepare weights:** 8B uses root `model.safetensors`; 32B/ZeRO-3 needs consolidation. Drop intermediate `checkpoint-*` and `.cache`.
4. **Resolve `hub_model_id`:**
   - **Delphi:** name is `laion/delphi-<base>-<recipe>_lr1e5-sft`; the authoritative cell→hub_model_id↔jobid map is `/leonardo_work/AIFAC_5C0_290/bfeuer00/experiments/delphi-prepared-tok/launch_54_map.tsv`. Resolve from there (don't guess).
   - Otherwise read the rendered launch config's `hub_model_id`.
   - Qwen3.5: copy `preprocessor_config.json` from the base model into the checkpoint before upload.
4b. **Check the tokenizer before upload:** `extra_special_tokens` in `tokenizer_config.json` must be a dict, not a list (`python -c "import json;d=json.load(open('<ckpt>/tokenizer_config.json'));assert isinstance(d.get('extra_special_tokens',{}),dict)"`). If it is a list, set it to `{}` and re-save; the RL/SkyRL loader expects a dict.
5. **Upload to HF** (public default):
   - **Leonardo:** use the **sbatch compute-node + SSH-tunnel** upload (`.agents/ops/leonardo/ops.md` "Leonardo HF Upload"; use `hf upload`, not `upload-large-folder`).
   - **Jupiter:** login node has direct internet → `hf upload` in tmux.
   - `source "$DC_AGENT_SECRET_ENV"` for `HF_TOKEN` (env var only — never inline).
6. **Do not run `manual_db_push.py`.**
7. **Clean** the cell's exp/checkpoint dir after the upload is verified (detached `rm` on GPFS; no `du`/`find`).
8. **Verify:** the `laion/<name>` repo exists with `model.safetensors` (>500MB) + tokenizer/config. Note the cell as done.

## Downstream chain (every sweep)
1. **SFT completes → HF upload** (this skill; no DB).
2. **upload completes → `eval-standard-launch`** on the series' eval grid for the newly-uploaded cell(s).
3. **eval completes → record scores in the experiment tracker** — for Delphi, append the cell's result to **`/Users/benjaminfeuer/Documents/experiments/active/delphi/rl-scaling-laws-6279/main_sft_evals/SCORES.md`**. Pull the score from the completed `delphi-eval/<RUN>/` output + the eval job's metrics.

Skip work already done.

### Delphi eval traps (carry into the eval hand-off)
- **`HF_HUB_ENABLE_HF_TRANSFER` MUST be 0/unset** when pre-caching the `-sft` repos into `$HF_HUB_CACHE` for eval — `hf_transfer` isn't in the `evalchemy` env, so `=1` leaves an EMPTY `.incomplete` blob (silent no-op). Verify the snapshot has `model.safetensors` (>500MB) before submitting.
- The `-sft` repos ship the chat template as a separate **`chat_template.jinja`** file (NOT in `tokenizer_config.json`'s `chat_template` key) — the eval sbatch's `delphi_v0` override reads/replaces that file.
- **Per-cell TP must divide `num_attention_heads`:** 9e18 heads=9→TP=1, 2e19 heads=11→TP=1, 3e19 heads=12→TP=2 (the sbatch's hardcoded TP=2 is WRONG for 9e18/2e19 — pass the optional TP_OVERRIDE 4th positional arg).

> Full Delphi series data: `project_delphi_sft_hf_only_no_db`; upload mechanics: `.agents/ops/leonardo/ops.md`.
