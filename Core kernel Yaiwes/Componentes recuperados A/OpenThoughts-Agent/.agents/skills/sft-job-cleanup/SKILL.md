---
name: sft-job-cleanup
description: >-
  Publish + clean up a finished LLaMA-Factory SFT job on a no-internet HPC cluster (Jupiter/Leonardo):
  cancel pending retries, drop intermediate checkpoints, HF-upload the model to its configured
  --hub_model_id, register in Supabase via manual_db_push (--training-type SFT default), and free disk.
  Covers the 8B path (root safetensors, direct upload), the 32B/ZeRO-3 path (consolidate shards →
  safetensors first), the Qwen3.5 preprocessor_config copy, the don't-upload-partials policy, and the
  hf-upload gotchas (tmux not nohup, `hf upload` not `-large-folder`, Leonardo sbatch-tunnel not login node).
  Use when an SFT fine-tune finishes and needs uploading + registering, or "run the SFT cleanup checklist".
  Distinct from RL cleanup (rl-agentic-job-cleanup) and datagen cleanup (datagen-job-cleanup).
---

# sft-job-cleanup

After an SFT job completes on Jupiter or Leonardo, publish the model and clean up.

## Recognition heuristic — which path? (check the checkpoint root first)
```bash
ls $CHECKPOINTS_DIR/<job_name>/ | grep -E 'safetensors|global_step'
```
- Root `model-*.safetensors` → **8B path** (including Qwen3.5; no consolidation).
- `global_stepN/` plus `zero_to_fp32.py`, without root safetensors → **32B path** (consolidate ZeRO-3 shards).

## Cross-cutting upload rules (apply to both paths)
- **`hf upload`, NEVER `hf upload-large-folder`** (deprecated stub + deadlocks on HF LFS 429s). Wrap any non-trivial upload in **`tmux`**, not `nohup`/`disown`.
- **`--private` is a no-value flag** — omit it (default public); `--private false` is a CLI parse error.
- **Jupiter**: login node has direct internet → `hf upload` from the login node (in tmux) works.
- **Leonardo**: the login node SIGKILLs long processes at ~100s → use the **sbatch compute-node + SSH-tunnel** upload (`.agents/ops/leonardo/ops.md` "Leonardo HF Upload — Use sbatch, NOT the Login Node" / `sft-launch`).
- **Don't upload partials:** if training is below 100%, relaunch and auto-resume. Salvage-upload only with explicit approval, as `laion/<job_name>-<step>-<size>`.
- **Tokenizer sanity check:** `tokenizer_config.json` `extra_special_tokens` must be a dict, not a list; replace a list with `{}` before upload.
  ```bash
  python -c "import json;d=json.load(open('<ckpt>/tokenizer_config.json'));assert isinstance(d.get('extra_special_tokens',{}),dict), 'LIST — coerce to {}'"
  ```

---

## 8B SFT Job Cleanup Checklist

**0. Cancel pending retries** (so stale restarts don't fire mid-upload):
```bash
squeue -u $USER --format='%i %j %T' | grep <job_name> | grep PENDING | awk '{print $1}' | xargs -r scancel
```

**1. Remove intermediate checkpoints** (don't upload cruft):
```bash
rm -rf $CHECKPOINTS_DIR/<job_name>/checkpoint-*  $CHECKPOINTS_DIR/<job_name>/.cache
```

**1b. Qwen3.5 only — copy `preprocessor_config.json` from the base model:**
```bash
cp /path/to/Qwen3.5-9B/preprocessor_config.json  $CHECKPOINTS_DIR/<job_name>/   # or the -27B base
```

**2. Upload model weights to HuggingFace.** **Naming:** full final upload (training reached 100%) → the configured `--hub_model_id` from the launch command (`laion/<descriptive_name>`, NO step/size suffix — do NOT use the job name verbatim). (Partial salvage, only-if-OK'd → `laion/<job_name>-<step>-<size>`.)
```bash
# Jupiter login node (direct internet). On LEONARDO use the §11 sbatch-tunnel — login-node hf upload dies at ~100s.
source ~/secrets.env
tmux new-session -d -s hf_upload_<short> \
    "source ~/secrets.env && hf upload <hub_model_id> $CHECKPOINTS_DIR/<job_name> . \
        --repo-type=model 2>&1 | tee $CHECKPOINTS_DIR/<job_name>/upload.log"
# tmux attach -t hf_upload_<short>  (Ctrl-b d to detach)
```
Wait for it to finish and verify the repo exists on HF Hub.

**3. Register in the unified DB** (SFT is the DEFAULT `--training-type`, no flag needed):
```bash
python scripts/database/manual_db_push.py \
  --hf-model-id <hub_model_id> --base-model <base_model_hf> \
  --dataset-name <dataset_name>          # comma-separated for multi-dataset → sets dataset_names
```
**SKIP for HF-only series** (e.g. Delphi #6279 — YAMLs set `enable_db_registration: false`; do not register, and do not pass an anchor as `--base-model` since that auto-creates a base-model row).

**4. Clean up the experiments dir** — only after 1–3 succeed:
```bash
rm -rf $EXPERIMENTS_DIR/<job_name>
```

---

## 32B SFT Job Cleanup Checklist (DeepSpeed ZeRO-3 — consolidate first)

For 32B ZeRO-3 SFT without `stage3_gather_16bit_weights_on_model_save: true`, consolidate shards before upload.

**0. Cancel pending retries** (same as 8B).

**1. Verify training reached 100%** — `trainer_log.jsonl` shows `current_steps == total_steps`. Default policy: don't salvage partials (relaunch + resume); only proceed if explicitly OK'd as a partial.

**2. Consolidate** ZeRO-3 shards → fp32 state_dict → safetensors:
```bash
python -m hpc.launch --job_type consolidate \
  --consolidate_input $CHECKPOINTS_DIR/<job_name> \
  --consolidate_output_repo <hub_model_id> \
  --consolidate_workdir <writable_workdir>/<job_name> \
  --time_limit 02:00:00 --num_nodes 1
```
Produces `<workdir>/<job_name>/final_repo/` with root-level weights, tokenizer, and config. Do not rely on its
final HF push; manually upload after `final_repo/` is complete.

**3. Manually upload from `final_repo/`** (NOT the original checkpoint dir — it still holds ZeRO-3 shards). Naming same as 8B (full → `--consolidate_output_repo`/`--hub_model_id`, no suffix):
```bash
# Jupiter login node. On LEONARDO use the §11 sbatch-tunnel (131GB → ~4 min). tmux; hf upload (not -large-folder).
source ~/secrets.env
tmux new-session -d -s hf_upload_<short> \
    "source ~/secrets.env && hf upload <hub_model_id> <consolidate_workdir>/<job_name>/final_repo . \
        --repo-type=model 2>&1 | tee <consolidate_workdir>/<job_name>/upload.log"
```

**4. Register in the unified DB** (same as 8B step 3; SFT is the default; skip for HF-only series).

**5. Clean up** — only after 2–4 succeed, remove BOTH the sharded checkpoint dir AND the consolidate workdir (32B sharded ckpt ~700GB + workdir ~200GB):
```bash
rm -rf $CHECKPOINTS_DIR/<job_name>  <consolidate_workdir>/<job_name>
```

> Launch-side details (preamble, configs, sbatch patching, the no-internet pre-download) live in the
> **`sft-launch`** skill (per-cluster particulars in `ops/<cluster>/ops.md §SFT`); this skill is the post-run publish + cleanup.

---

## Operating notes

- **Run full cleanup after a completed, 100% job:** cancel pending chain, drop checkpoints, upload, register, and
  clean the experiment directory. Flag obvious anomalies; cancellation of running jobs remains user-driven.
- **Multi-dataset DB registration:** pass the full comma-separated list to `--dataset-name` so `dataset_names` is populated (not just one `dataset_id`). Known limitation: the script stores it as a single string and does NOT trigger the `multiple_datasets` path (`dataset_id` ends up null) — verify the right field after registering. Single-dataset `--dataset-name` works fine and populates `dataset_id`.
- **Baseline model versioning (Sera/CoderForge):** flat monotonic `-v5`/`-v6`/`-v7` in HF repo names + README iteration tables, NOT nested `v4-v2`/`v4-v3`. In-flight runs keep their existing names; the NEXT retrain uses the new scheme (next Sera = v5, skipping v4 to avoid colliding with existing v4 artifacts).
