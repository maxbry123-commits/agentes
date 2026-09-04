# Analysis Scripts

Utilities for analyzing RL/SFT training traces, evaluation results, and HuggingFace datasets.

## Behavioral Analysis Pipeline (orchestrator)

`analyze_rl_behavior.py` chains the scripts below into a single pipeline
keyed to four research questions:

| Question | Steps invoked |
|---|---|
| **Q1.** What model behaviors are changing as a result of RL? | `behavioral_delta` (macro counts + per-feature deltas sorted by magnitude) + optional `llm_judge_diff` (GPT-5 pairwise classification, opt-in with `--llm-judge`) + optional `update_hf_failure_modes` upstream |
| **Q2.** Are reward changes over time attributable to behavior or other factors? | `temporal_trace_analysis` (reward + behavioral small-multiples per bin) + `parse_skyrl_metrics` |
| **Q3.** Do behavioral changes persist in post-RL eval traces? | `eval_temporal_overlay` + `trace_pair_render` (collapsible HTML w/ diff cards) + `post_training_comparison` |
| **Q4.** Do those changes affect eval results? If not, is it expected? | `solve_rate_by_context` (+ Q1/Q3 outputs for interpretation) |

Each step writes into `--output-dir/<step>/` and is skipped if its output marker already exists (use `--force` to re-run, `--skip <names>` to opt out, `--only <names>` for a subset). The plan + cross-linked index land at `--output-dir/{pipeline_plan.json, INDEX.md}`.

**Fully manual:**

```
python -m scripts.analysis.analyze_rl_behavior \
    --rl-traces        penfever/rl-train-traces-foo \
    --baseline-eval    penfever/eval-pre-rl-foo \
    --post-rl-eval     penfever/eval-post-rl-foo \
    --post-rl-eval-ts  2026-05-28T18:30 \
    --baseline-eval-ts 2026-05-23T09:00 \
    --training-log-dir /scratch/skyrl-logs/foo/ \
    --output-dir       /Users/me/Documents/notes/rl-behavior-foo/
```

**With autofill** (recommended) — pass `--model-repo` and let the orchestrator query Supabase (`models` + `sandbox_jobs` tables) plus the HF Hub (`<model_repo>/training_logs/`) to fill in `--post-rl-eval`, `--post-rl-eval-ts`, `--baseline-eval`, `--baseline-eval-ts`, and `--training-log-dir`:

```
python -m scripts.analysis.analyze_rl_behavior \
    --rl-traces  https://huggingface.co/datasets/penfever/a3-rl-DCAgent_exp_rpt_e2egit-large \
    --model-repo https://huggingface.co/laion/a3-rl-DCAgent_exp_rpt_e2egit-large-15-8B \
    --output-dir /Users/me/Documents/notes/rl-behavior-foo/
```

The resolver:
- `--post-rl-eval` / `--baseline-eval` ← `sandbox_jobs.hf_traces_link` for the model & its base, with **pair selection** controlled by `--eval-selection`:
  - **`largest-delta`** (default) — collect all `(post, baseline)` pairs matched by `benchmark_id`, compute the score delta with `--eval-score-key` (default `accuracy`), pick the pair with the largest positive delta. Usually the most interesting benchmark to inspect since it's where RL learned the most.
  - **`largest-abs-delta`** — same but ranked by `|delta|`; catches large regressions too.
  - **`latest`** — most recent `sandbox_jobs(model_id).ended_at`; baseline matched by benchmark.
  - **`benchmark`** — pin to `--eval-benchmark <UUID-or-name>` and pick the latest matching job from each side.
- `--post-rl-eval-ts`  ← `models.training_end`
- `--baseline-eval-ts` ← `models.training_start`
- `--training-log-dir` ← `huggingface_hub.snapshot_download(<model_repo>, allow_patterns=["training_logs/**"])` if the repo has one, else stays unset

Add `--list-evals` to print all available `(post, baseline)` pairs with their score deltas and exit — useful for picking a specific `--eval-benchmark` to pin to:

```
python -m scripts.analysis.analyze_rl_behavior \
    --model-repo https://huggingface.co/laion/<your-rl-model> \
    --output-dir /tmp/probe --list-evals
```

Explicit CLI values still win on conflict — the resolver only fills blanks. A trace of what was resolved lands at `--output-dir/auto_resolve.json`. Disable the HF training_logs fetch with `--no-fetch-training-logs`.

Add `--annotate-failure-modes` to run `update_hf_failure_modes` on both eval repos before Q1 picks up the labels (requires `OPENAI_API_KEY`; can take hours on large datasets). Use `--dry-run` to print the plan without executing.

## New Analysis Tools

| Script | Question | Description |
|---|---|---|
| `behavioral_delta.py` | Q1 | Diff failure-mode + per-feature behavioral metrics between two trace datasets. Per-trace features (tool calls, tool errors, think tokens, response verbosity, code-fence density, self-correction phrases, premature stops, tool-call distribution by tool name) are sorted by magnitude of delta. Writes markdown + JSON sidecar. |
| `llm_judge_diff.py` | Q1 | GPT-5 (via `ajudge.llms.litellm_llm.LiteLLM`) pairwise classifier on same-task before/after trace pairs. Per pair: behavior-change paragraph + tags + confidence + winner + reason. Aggregates to a tag distribution + win-rate table + top-5 verbatim judgments. Caches per (task, before-trial, after-trial, model). |
| `trace_pair_render.py` | Q3 | Side-by-side HTML render of representative trials per common task. Diff summary card per pair; collapsible `<details>` messages with role-coded borders, expand/collapse-all buttons, pygments syntax-highlighted code fences, distinct `<think>` styling, labelled `<tool_call>` chips. Default open: first user msg + last assistant msg. |
| `eval_temporal_overlay.py` | Q3 | Extends `temporal_trace_analysis`: overlays eval-checkpoint markers on the RL-time reward curve. Co-located baseline / post-RL markers are auto-jittered horizontally so both stay visible. |
| `auto_resolve.py` | (orchestrator helper) | Given `(rl_traces, model_repo)`, looks up the model + its `sandbox_jobs` in Supabase and snapshots `<model_repo>/training_logs/` from HF to fill in the orchestrator's other flags automatically. |
| `analyze_rl_behavior.py` | (orchestrator) | Runs all of the above + the existing scripts in the right order, with resumability via output-marker detection. `--model-repo` triggers `auto_resolve`. `--llm-judge` enables the GPT-5 pair classifier. |

## Shared Utilities

| Module | Description |
|---|---|
| `utils.py` | Common helpers: `load_traces()` unified loader (HF/JSONL/dir), `Trace` dataclass with eager field caching, `task_id_of()`, `group_by_task()`, plus the original text/reward/error/date/token primitives |

## Live Iris Monitoring

| Script | Scope | Usage |
|---|---|---|
| `../iris/watch_iris_harbor.py` | Canonical read-only sweep of active Iris Harbor datagen and eval jobs; syncs to the shared Iris evidence-bundle root | `python scripts/iris/watch_iris_harbor.py` |
| `MarinSkyRL/scripts/iris/watch_coreweave_rl.py` | Canonical read-only sweep of active CoreWeave RL jobs; syncs Finelog, pod/Ray logs, and rollout artifacts to that same bundle root | Run from the MarinSkyRL checkout |

## Dataset & Context Analysis

| Script | Description | Usage |
|---|---|---|
| `context_length_compare.py` | Compare context length statistics and optionally write a log-scale distribution overlay across HF datasets | `python -m scripts.analysis.context_length_compare repo1 repo2 --plot context_lengths.png` |
| `solve_rate_by_context.py` | Solve/timeout/error rates binned by context length, with 3-panel plot | `python -m scripts.analysis.solve_rate_by_context repo1 repo2 --bins 0,16384,32768 --plot out.png` |
| `episode_distribution.py` | Plot episode count and tokens-per-turn distributions from HF trace datasets | `python -m scripts.analysis.episode_distribution repo1 repo2 --output out.png` |
| `filter_latest_episodes.py` | Keep only the latest episode per task in a trace dataset | `python scripts/analysis/filter_latest_episodes.py repo_id --output-jsonl out.jsonl` |
| `summarize_conversations.py` | Compute conversation stats (tokens, turns, rewards) from a JSONL file | `python scripts/analysis/summarize_conversations.py data.jsonl` |

## Training Analysis

| Script | Description | Usage |
|---|---|---|
| `parse_skyrl_metrics.py` | Parse SkyRL training logs, extract metrics and vLLM stats, generate CSV + markdown report | `python scripts/analysis/parse_skyrl_metrics.py log_folder/ output_folder/` |
| `temporal_trace_analysis.py` | Bin trace rows by timestamp to track agent improvement over training | `python scripts/analysis/temporal_trace_analysis.py repo_id --bin-hours 1` |

## Evaluation Analysis

| Script | Description | Usage |
|---|---|---|
| `trace_runtime_report.py` | Aggregate eval stage-runtime quantiles, agent-execution exception incidence, correlations, and PNG visualizations | `python scripts/analysis/trace_runtime_report.py --root results_dir/` |
| `failure_mode_analysis.py` | Use GPT-5 to classify failure modes in trace datasets | `python scripts/analysis/failure_mode_analysis.py repo_id --output report.md` |
| `update_hf_failure_modes.py` | Annotate HF dataset rows with GPT-5 failure-mode summaries | `python scripts/analysis/update_hf_failure_modes.py repo_id --push` |

## Debugging & Diagnostics

| Script | Description | Usage |
|---|---|---|
| `probe_model_thinking.py` | Probe a model with real environment prompts, test thinking behavior | `python -m scripts.analysis.probe_model_thinking --model model_id` |
| `submit_probe.sh` | SLURM wrapper for `probe_model_thinking.py` | `./scripts/analysis/submit_probe.sh --model model_id --partition gpu-h100` |
| `verify_sft_thinking.py` | Test how ReasoningTemplate handles thinking blocks in SFT data | `python scripts/analysis/verify_sft_thinking.py` |

## Batch Workflows

| Script | Description | Usage |
|---|---|---|

## Dependencies

Most scripts require:
- `datasets` (HuggingFace datasets library)
- `transformers` (for tokenizers, used by context length scripts)
- `numpy`, `matplotlib` (for statistics and plotting)

Optional:
- `tiktoken` (fallback token counting in `utils.py`)
- `openai` (for GPT-5 failure mode analysis)
