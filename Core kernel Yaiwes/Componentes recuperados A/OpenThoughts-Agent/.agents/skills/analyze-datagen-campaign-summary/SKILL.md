---
name: analyze-datagen-campaign-summary
description: >-
  Build a clean per-dataset summary table/CSV for a datagen (trajectory-generation) campaign — one row per
  task source with Status (COMPLETED / FAILED / RUNNING / NOT STARTED), N Trials Completed, Mean Turns/Trace,
  Mean Tok/Trace, Mean Reward, and the HF trace-repo link. Use when asked to "summarize the campaign", "which
  datasets did we complete + their rewards/trials", "build a completion table/CSV", or to reconcile a prose
  tracker into auditable per-dataset metrics. Computes metrics by STREAMING each uploaded HF trace dataset
  (disk-bounded) and reusing the canonical OT-Agent analysis tools (scripts/analysis/utils.py:
  extract_conversation_text / count_turns / extract_reward) + the Qwen3-8B tokenizer; HF-ground-truths Status
  by probing each repo. Related skills: analyze-dataset-token-length (token method),
  analyze-job-history-iris (harbor Mean / trials from logs).
---

# analyze-datagen-campaign-summary

Turn a datagen campaign's **prose tracker** (e.g.
`~/Documents/experiments/{active,complete}/<campaign>/tracker.md`, whose per-dataset status lives in
sentences, not columns) into a **clean, auditable per-dataset table/CSV** with computed metrics. Built for the
`qwen3.5-122b-tt` 32k campaign but campaign-agnostic — swap the dataset list.

**Target columns:** `Datagen Model | Task Source | Status | N Trials Completed | Mean Turns / Trace | Mean Tok / Trace | Mean Reward | HF Repo Link`.

## Why this skill exists (the two traps)
1. **The tracker rarely has reward / turns / tokens.** Trackers record throughput (gen tok/s) + row counts in
   prose; **mean reward, mean turns, and mean tokens are almost never written down.** They must be COMPUTED
   from the uploaded HF trace datasets.
2. **Status in prose is stale/ambiguous** (a "RUNNING" row that actually finished; a "rescued" row with no
   clean repo name). **Ground-truth Status against HF**: if the trace repo exists with rows → COMPLETED
   (and its row count IS `N Trials Completed`); otherwise fall back to the tracker's status hint.

## The data model (uploaded OT-Agent trace dataset)
Each row of `penfever/<slug>-<model>-traces` is one trial/trace:
`{conversations: [{role,content},…], agent, model, model_provider, date, task, episode, run_id, trial_name, result, verifier_output}`.
- **N Trials Completed** = row count of the dataset (one row = one completed trace).
- **Mean Turns / Trace** = mean `count_turns(row)` = mean number of conversation messages (canonical
  definition in `scripts/analysis/utils.py`; total messages, not just assistant turns — state it in the notes).
- **Mean Tok / Trace** = mean Qwen3-8B token length of the whole conversation — **plain** method from the
  `analyze-dataset-token-length` skill: `tokenizer(extract_conversation_text(row), add_special_tokens=False)`.
  Tokenizer is **always `Qwen/Qwen3-8B`** for these datasets (their trace-dataset convention), regardless of
  the served model name (`model` field is `hosted_vllm/<numeric-id>`, not a usable tokenizer).
- **Mean Reward** = **Harbor-flat mean** of `result` via `mean_reward_per_trial` semantics: `extract_reward`
  each row (parses the `result` string, e.g. `"0.0"` → 0.0), **missing/non-numeric counts as 0.0**. This
  matches harbor's `<done>/<total> Mean:` accuracy exactly — do NOT drop nulls or the number won't reconcile.

## Reuse the canonical tools (do NOT reinvent)
`/Users/benjaminfeuer/Documents/OpenThoughts-Agent/scripts/analysis/utils.py`:
- `extract_conversation_text(record)` — conversation → full text to tokenize (handles `messages`/`conversations`).
- `count_turns(record)` — turns.
- `extract_reward(record)` — parses `result` → float|None. `mean_reward_per_trial(rows)` — Harbor-flat mean.
- `load_hf_trace_dataset(repo_id)` — non-streaming loader (fine for small repos; see disk note for large ones).

Token-length details (methods, tokenizer, the metadata-confound trap) → the **`analyze-dataset-token-length`**
skill. If you'd rather source Mean Reward + trials from the **job logs** instead of the HF dataset (e.g. the
repo was never uploaded), the **`analyze-job-history-iris`** skill's `analyze_iris_harbor_job.py` sidecar carries
the harbor `Mean:` + `non_empty_trials` per job — but the uploaded dataset is the more reliable ground truth
for a COMPLETED row.

## ⚠ Handling the LARGE trace datasets (disk + bandwidth)
Some campaign datasets are big (tens of thousands of rows / hundreds of MB / dozens of shards). Full
`load_dataset` caches the whole parquet to `~/.cache/huggingface` → can blow local disk (a full disk **bricks
the supervisor** — see the disk-health rule in `supervisor-init`). So:
- **STREAM** (`load_dataset(repo, split="train", streaming=True)`) and accumulate in ONE pass — disk stays
  bounded (shards read on the fly, not cached whole).
- Point `HF_HOME` / `HF_DATASETS_CACHE` at the scratchpad and `df -h /` before launching; bandwidth is
  unavoidable (the conversations column is the bulk, needed for both turns and tokens) but streaming avoids
  the disk blowup.
- **Batch the tokenizer** (e.g. 128 texts) rather than per-row; `TOKENIZERS_PARALLELISM=false` to avoid the
  fork-after-tokenizer deadlock when parallelizing.
- **Parallelize across datasets** with a `ProcessPoolExecutor` (≈5 workers) — CPU-bound tokenization scales
  well; each worker streams its own datasets. **Checkpoint per-dataset to JSONL** so a crash/interrupt resumes
  instead of recomputing the expensive large ones.

## Procedure
1. **Build the dataset list from the campaign tracker.** One entry per task source:
   `(idx, task_source, candidate_hf_repo_or_None, status_hint, note)`. `candidate_hf_repo` = the exact
   `penfever/<slug>-…-traces` slug the tracker names (the slug transform is IRREGULAR — copy the stated repo,
   don't derive it). `status_hint` ∈ {COMPLETED, FAILED, RUNNING, NOT STARTED} (pending → NOT STARTED &
   repo=None; killed-not-rescued / blocked-skipped → FAILED & repo=None).
2. **Per dataset:** probe HF (`HfApi().dataset_info(repo)`); on 404 keep the hint + NULL metrics. Else stream,
   compute `n_trials`, `mean_turns`, `mean_tok` (Qwen3-8B), `mean_reward` (Harbor-flat), set Status=COMPLETED
   and `HF Repo Link = https://huggingface.co/datasets/<repo>`.
3. **Write the CSV** sorted by idx; NULL metrics render as empty cells, missing repo as `NULL`.
4. **VERIFY before delivering** (the user asked for it to be *correct*): spot-check that computed
   `n_trials` matches the tracker's stated row counts on a few datasets, and that a KNOWN-degenerate dataset
   reconciles (e.g. `qwen3.5-122b-tt` codenet-python-v2 mean reward ≈ 0.017 ↔ the tracker's "~2% pass-rate").
   Mean tokens should sit under the campaign's context window (32k here) for the vast majority.

## Definitions to state alongside the table (so it's auditable)
- **Datagen Model** = the trajectory-generation model (constant per campaign; e.g. `Qwen3.5-122B-A10B-FP8`),
  NOT the row's `model` field.
- **Mean Turns/Trace** = mean total conversation messages (`count_turns`).
- **Mean Tok/Trace** = mean Qwen3-8B plain token count of the full conversation.
- **Mean Reward** = Harbor-flat trial mean (missing/error = 0.0) — reconciles with the harbor `Mean:` line.
- **N Trials Completed** = uploaded productive rows (may be < tasks for partial/rescued jobs; note it).

## Cross-reference
- `analyze-dataset-token-length` — token-length method, Qwen3-8B convention, the metadata-confound trap.
- `analyze-job-history-iris` — harbor `Mean:` + productive-trial counts from job logs (alt metric source).
- `datagen-launch-iris` — how the trace datasets are produced/rescued/uploaded (upstream of this table).
- `scripts/analysis/utils.py` — the canonical extract/count/reward helpers this skill reuses.
