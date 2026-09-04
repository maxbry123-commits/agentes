# Harbor — project overview + ops

The agent framework OT-Agent uses for **trace generation** (RL/SFT data) and **agentic eval**.

- **Repo:** local `/Users/benjaminfeuer/Documents/harbor`, branch **`main`** (`penfever/working` RETIRED 2026-07-17). Editable-installed on every cluster; synced via git (commit→push→`git pull`), never patched on the cluster.
- **⚠️ CANONICAL UPSTREAM = `marin-community/harbor`** (v0.7.0). Track/push **`main`** (dev flow is worktree → PR → `main`; see below). Other remotes (`laude`, `charlie`, `marianna`) are forks/mirrors — do not push to or pull from them. If a cluster `git pull` reports "Already up to date" but the fix isn't there, check `git remote get-url origin` points at `marin-community/harbor`.
- **CLI:** Typer app `harbor.cli.main:app` — `harbor run`, `harbor jobs start`, `harbor view`, `harbor trials start`.
- **Two OT-Agent uses:** (1) **datagen trace-gen** — run an agent over a task set, record rollout trajectories → HF dataset; (2) **agentic eval** — run an agent over a benchmark, verify, compute metrics. Both go through `hpc/launch.py` (`--job_type datagen`/`eval`) or the unified eval listener.

---

## Cluster clones + sync

The editable harbor install on each cluster lives in these clones — `git pull` here is how a laptop push goes live:
- **Jupiter:** `/e/scratch/jureap59/feuer1/harbor`
- **Leonardo:** `/leonardo_work/AIFAC_5C0_290/bfeuer00/code/harbor`

Both clones' `origin` MUST be `https://github.com/marin-community/harbor.git`. **Gotcha (fixed 2026-06-17):** both were found pointing at the stale fork `laude-institute/harbor` (frozen at an old commit), so `git pull` reported "Already up to date" while silently missing every new push. Repointed via `git remote set-url origin https://github.com/marin-community/harbor.git`. Deploy pattern (clone is editable → live for new processes after pull; **running jobs keep the old code until they restart**):
```bash
cd <clone> && git remote get-url origin   # MUST be marin-community/harbor
git fetch origin main && git pull --ff-only origin main   # migrate a stale clone: git checkout main && git pull first
git log -1 --oneline                       # confirm the expected HEAD
```

---

## Contributing to this fork (marin-community fork workflow)

Harbor is a **marin-community shared fork** — code contributions follow the marin-community fork workflow (shared with MarinSkyRL, evalchemy):

1. **Read `AGENTS.md` first.** Obey env/dev setup, test + lint entry points, PR norms.
2. **Follow the marin style conventions** (`uv run infra/pre-commit.py --all-files --fix`, `ty check`).
3. **Dev in an isolated worktree off a fresh branch from `main` → PR into `main`.** The `penfever/working` mega-consolidation branch is **RETIRED** — never commit to it or `main` directly.
4. **Iterate until ALL CI checks pass.** Diagnose + fix, never force past failures.
5. **Do NOT self-merge — return for approval.** No `Co-Authored-By` trailers; use the `agent-generated` PR label.

**Scope:** this applies ONLY to marin-community shared forks (harbor, MarinSkyRL, evalchemy). OT-Agent and the vllm fork keep their current norms (self-merge + trailers allowed).

---

## OT-Agent's harbor pin (`@main`, not a branch)

Two OT-Agent files pin harbor and must stay in sync: `pyproject.toml` (`harbor[daytona] @ git+…marin-community/harbor.git@main`) and `docker/Dockerfile.tpu` (`ENV HARBOR_COMMIT=<sha>` + `--force-reinstall`). The gpu-rl image's harbor pin lives in **MarinSkyRL** `docker/Dockerfile.gpu-rl`. `uv.lock` is the RUNTIME gate on iris workers (`uv sync --frozen`), so a harbor bump is a `uv lock --upgrade-package harbor` + commit, not only an image rebuild.

- **Pin is `@main`** (changed 2026-07-15 from `@penfever/working`). Harbor's repo has **auto-delete-head-branch ON**, so a squash-merge auto-deletes the merged branch — `@main` cannot be auto-deleted. Do not re-pin to a mergeable/deletable branch.
- The `pyproject.toml` pin resolves to main's floating HEAD; the Dockerfiles pin the concrete `HARBOR_COMMIT` sha (bump to main's HEAD on each rebuild).

---

## Environment backends — `src/harbor/environments/`

Selected per-run (`--trace_env`/`--harbor_env`, or the YAML `environment.type`); lazy-loaded via
`environments/factory.py:EnvironmentFactory`. Backends: **daytona** (`daytona.py` + `daytona_utils.py` —
the production cloud-sandbox path), **docker** (`docker/`), **modal**, plus apptainer/enroot (HPC), e2b,
runloop, gke, tensorlake, apple_container.

**Daytona sandbox model** (the one we run): async REST SDK. Per trial: fetch the task Dockerfile →
`create_sandbox_from_image()` → `run_command()` in the live sandbox → `delete_sandbox()` (or snapshot).
**Snapshots** are named `harbor__<env_hash>` and are **shared across every run using those tasks** (keyed by
the sandbox-environment hash, not per-dataset) — see `.agents/projects/daytona/daytona.md` for the hard
org/per-launch caps and the prebuild flow (`hpc/snapshot_manager.py`). `daytona_utils.py` carries
exponential-backoff retry callbacks for transient errors; concurrency is gated by a semaphore in
`trial/queue.py`.

**Docker / Podman backend (local, no cloud).** For running trace-gen on a local/SLURM box without Daytona,
use `--trace-env docker` — `hpc/docker_runtime.py` auto-detects Docker vs Podman and sets `DOCKER_HOST`
(supports SSH tunnels to a remote daemon). Configs: `hpc/harbor_yaml/trace_docker_*.yaml`. Run via
`python -m data.local.run_tracegen --harbor-config hpc/harbor_yaml/trace_docker_<...>.yaml --tasks-input-path <dir> --trace-env docker`;
for SLURM+Podman `source docker/setup_docker_runtime.sh` first. Modal is the third backend (`--trace-env modal`).

---

## Terminus-2 agent — `src/harbor/agents/terminus_2/`

The production agent (`terminus_2.py`, ~1800 lines; tmux session mgmt + JSON/XML tool-call parsers +
asciinema recorder). Load-bearing behaviors:

- **Summarization** (`enable_summarize`, `proactive_summarization_threshold` default ~8000 free tokens): when context nears the limit, a subagent compresses history and the main chat is reset (trajectory file continues). **When `enable_summarize=false` (our RL/trace default for fidelity), NOTHING truncates the growing prompt** → context overflow (`VLLMValidationError: 32769 input tokens`); `max_input_tokens` is inert in that mode (see `.agents/skills/datagen-launch`). Notes: summarization fires on ~19–29% of trials and those trials solve 2–9× lower (confounded by harder/longer tasks); ~half the conversation text can be summarization bookkeeping.
- **Tool calling:** per-turn `debug.json`/`prompt.txt`/`response.txt`; parser (`json` or `xml`) → tmux exec → observation.
- **PRM hook (`turn_callback`):** invoked each episode; returning a **string** injects it (e.g. SkyRL's `prm/teacher_hint.py` → the literal `[HINT FROM TEACHER]:` marker prepended to the next observation), returning **True** requests early stop. See `.agents/skills/analyze-rl-behavior` for grepping hints.
- `store_all_messages`, `trajectory_config.{raw_content, linear_history}` control how much is persisted.

---

## Agentic ID-eval via the opencode (installed) harness + pinggy

Canonical recipe for evaluating a model with the **opencode installed-agent harness** instead of terminus-2. Cluster-agnostic core; the launch/monitor flow rides the unified eval listener (`.agents/skills/eval-agentic-launch`), per-cluster particulars live in `.agents/ops/<cluster>/`.

### When to use it (opencode, NOT terminus-2)

- **Match the eval harness to the training harness.** A model SFT'd (or RL'd) on **opencode traces** is evaluated with the **opencode** harness; the standard `tb2`/`v2`/`swebench` presets default to the **terminus-2** in-process agent (§Terminus-2 above) and are the wrong harness for an opencode-trained model.
- **Same discipline as the RL/opencode-datagen side:** opencode is an **installed agent** — its CLI runs **INSIDE the Daytona sandbox** and calls **back out** to the served vLLM. Harbor's in-process `RolloutDetail` never sees these calls (this is why literal-token capture needs a `RecordProxy`; §Literal-token trace datasets). Eval needs REWARD only, so no literal/TIS bridge is required — only the sandbox→served-model ingress.

### The opencode eval config

- **`hpc/harbor_yaml/eval/configs/eval_opencode_ctx32k.yaml`** — `agents[0].name: opencode`, `verifier.disable: false`, `n_attempts: 3`, `opencode_config.compaction: {auto: true, reserved: 16384}`, a `model_info` block (`max_input_tokens: 32768`, `max_output_tokens: 16384`, zero costs), and `model_name: vllm/override-at-runtime` (the sbatch overwrites this at launch). Modeled on `eval_openhands_ctx32k_toolcall_skyrl_full.yaml`.
- **32B-band models (incl. MoE `30b-a3b`)** use this same config — its `timeout_multiplier: 16.0` IS the 32B band; there is no separate 30B/32B opencode variant. The listener also independently resolves `EVAL_TIMEOUT_MULTIPLIER=16` for 32B-class models, consistent with the in-config value.
- **The opencode `agents[]` block MUST ride in the harbor `--config` file** (it is what makes the run an installed-agent run). Config-delivery is cluster-nuanced:
  - **TACC** delivers the harbor `--config` via the **listener's `--config-yaml <file>`** (resolved from `hpc/harbor_yaml/eval/configs/` → `EVAL_CONFIG_YAML` → `harbor jobs start --config`). TACC does **NOT** consume `EVAL_HARBOR_CONFIG`, and the listener never threads `--harbor-config` into any cluster's sbatch `--config` — it only parses `--harbor-config` for resource overrides (e.g. `timeout_multiplier`). So author the config under `configs/` (not `hpc/harbor_yaml/eval/`), where BOTH the sbatch AND the listener's `_resolve_agent_name_from_config_yaml` resolve it — both then agree the agent is opencode.
  - The `--harbor-config` resolution-order override (skill §2, resolution #1) is the Jupiter/installed-harness path; on TACC use `--config-yaml`.
- `dcagent_eval_config_no_override.yaml` is NOT passed for opencode — the opencode config is self-contained.

### The pinggy tunnel (installed-harness ONLY)

- **Why:** the installed harness in the Daytona sandbox reaches the served vLLM over a **public tunnel** (the sandbox has no route to the cluster's internal `10.*` serving IP). terminus-2 evals need NO tunnel (in-process; served-model reachability is internal) — do not pass `--pinggy_*` or consume a pair for them.
- **Flags:** `--pinggy_persistent_url <URL> --pinggy_token <TOKEN>` on the listener front door (forwarded to the sbatch as `EVAL_PINGGY_URL`/`EVAL_PINGGY_TOKEN`). **Use pairs 8/9/10 by default** (1–7 reserved) — one pair per concurrent leg.
- **⚠ The URL/token bank is PRIVILEGED.** Read the actual values at launch time from **`.agents/secret.md`** or **`notes/ot-agent/pinggy_bank.md`** (re-read before each launch; assignments shift). **NEVER inline a pinggy URL or token into a tracked doc/config/commit.**

### Launch flow (front-door listener + installed-agent sbatch branch)

- Launch through the unified eval listener front door (`python -m hpc.launch --job_type eval_listener --cluster-config <cluster> --preset <swebench|v2|tb2> --config-yaml eval_opencode_ctx32k.yaml --pinggy_persistent_url <URL> --pinggy_token <TOKEN> …`), one invocation per ID leg, staggered ~30–45 s (conda-plugin race guard; skill §4). The listener auto-allocates nodes + runs the serve preamble.
- The **eval sbatch's installed-agent branch** (gated on `IS_INSTALLED_AGENT`, derived from the config's `agents[0].name`; terminus-2/oracle/nop skip it so the terminus-2 path stays byte-identical) does the opencode-specific wiring:
  - Starts the **pinggy SSH tunnel** exposing `localhost:8000` vLLM, **verifies `/v1/models` and refuses (exit 1) if the tunnel is dead** (no rollout compute wasted); `cleanup()` kills the pinggy PID. On direct-egress clusters (Vista) the tunnel runs without proxychains.
  - Exports `OPENAI_BASE_URL=https://<pinggy>/v1`, `OPENCODE_DUMMY_KEY`, `OPENAI_API_KEY`, and injects `agents[0].model_name = vllm/$MODEL` into a **runtime config copy**, then runs `harbor jobs start --config <copy>` **WITHOUT `--agent`/`--model`** (harbor ignores `--model` unless `--agent` is also passed, and `--agent` would wipe the `agents[]` block).
- **Provider is `vllm/` (not `openai/`).** opencode registers the `vllm` provider via `@ai-sdk/openai-compatible` reading `OPENAI_BASE_URL`/`OPENCODE_DUMMY_KEY` (`agents/installed/opencode.py:_build_register_config_command`); `openai/` would hit the Responses API → vLLM 404. Served id = `$MODEL` (`build_vllm_cmd --served-model-name` defaults to `$MODEL`).
- **Daytona org:** installed-agent evals use the strict **DATA org** key (`DAYTONA_DATA_API_KEY`); gate this on `IS_INSTALLED_AGENT` so any terminus-2 evals sharing the sbatch keep their historical org distribution byte-identical.

### Thinking / context specifics (`-Thinking-` models, e.g. Qwen3-30B-A3B-Thinking)

- **Thinking is NATIVE to the `-Thinking-` chat template** — no `--enable-thinking`, no `--agent-kwarg`/`--agent-parser` needed. The model-registry `extra_body` agent_kwarg (auto-injected for the model) is harmlessly swallowed by the opencode base agent class (`**kwargs`).
- **Temperature** = the model's own `generation_config.json` default (vLLM honors it) — no override flag.
- **Context 32k** matches the config name and the served `max_model_len: 32768` from the model registry.

### Infra sanity checks (net-new opencode path — do NOT trust "RUNNING")

Run the skill's 15-min infra check on each leg once RUNNING; the in-sbatch verify only proves compute-node→vLLM, not the sandbox→model half:

1. **Pinggy auth** — `You are authenticated as …` in the cluster's `pinggy_<jobid>.log`; a growing traffic counter (`RB:/SB:/TC:`). `A tunnel with the same token … is already active` = server-side lock → relaunch on a different pair.
2. **Sandbox → model** — a trial's `config.json` `api_base` (opencode routing) MUST be the public **`https://*.a.pinggy.link/v1`**, NOT an internal `10.*` IP (internal IP = pinggy wasn't wired → relaunch).
3. **vLLM serving** — `POST /v1/chat/completions` 200s climbing (traffic arriving through the tunnel); instant-fail completions (`n_output_tokens: None`, `finished_at ≈ started_at`) = tunnel not carrying traffic.
4. **Trial progression** — trials advancing with non-instant completions.

**Resume of an installed-harness eval ALSO needs the tunnel** (the sandbox still calls back out) — the eval sbatch must bring the pinggy tunnel up on resume, same as a fresh launch.

---

## opencode `opencode.txt` — the per-turn record + turn-banking discriminator (RL/datagen debugging)

`opencode` runs as ONE subprocess (`agents/installed/opencode.py:run()`: `opencode run --format=json … | stdbuf -oL tee /logs/agent/opencode.txt`). Its JSON-lines event stream is the **per-turn on-disk record** — the analog of terminus-2's per-turn saves — streamed line-buffered as it goes. It is parsed into `trajectory.json` only by `populate_context_post_run`, which runs **after the subprocess returns**; a kill mid-generation preempts parsing (but the raw `opencode.txt` lines already on disk survive).

**Event schema** (stdout line `type`): `step_start`/`step_finish` delimit a turn, `tool_use` = a tool call, `reasoning` = CoT, `text` = assistant text, `error` = an error event.

**The turn-banking discriminator (use this, NOT `AgentTimeoutError`):**
- `step_finish > 0` → the model actually **banked turns** (completed model+tool cycles).
- `tool_use > 0` → it called tools.
- all-zero + a single `error` → it **never banked a turn**.
- `AgentTimeoutError` is a **benign harbor passthrough** (verifier still scores) — it is NEVER the signal for whether the model did work. A "0-reward / 0-completions" job is a **model** problem (banked turns but wrong answers, or gibberish generation) vs an **infra** problem depending on these counts, not on the timeout rate.

**⚠ Observability blind spot — `opencode.txt` is uploaded to `trials_dir` only on trial FINALIZE.** A trial killed mid-run whose "Failed to upload agent logs back to environment" step failed leaves **only `config.json`** in `trials_dir` (no `opencode.txt`, no `result.json`). So `opencode.txt present  <  trial dirs` means failed-upload/in-flight trials, and **their turn counts are UNOBSERVABLE from durable storage** — do NOT read a low present-count as "these trials did no work." A clean turn-count read requires a job whose trials finalize + upload cleanly.

**Teardown-403 signature (not a steady-state signal).** When an RL endpoint is torn down (job stopped/relaunched), in-flight trials' scoped tokens 403 on their next call — `opencode.txt` shows a single `{"type":"error", … "Forbidden: endpoint-scoped token cannot access this endpoint", statusCode 403}` (url `https://iris.oa.dev/proxy/t/<JWT sub=endpoint:…>/…/v1/chat/completions`) → opencode exits `NonZeroAgentExitCodeError`. Distinguish from a real steady-state failure by the error type + the timestamps clustering at the kill moment.

**Tool:** `scripts/iris/analyze_coreweave_rl_job_live.sh <pod-substr> turns` prints per-trial `step_finish`/`tool_use`/`reasoning`/`text`/`error` counts + a banked-turns verdict (remote-s3 or node-local trials_dir). **⚠ Leafgroup/megatron pod-name gotcha:** the k8s pod name truncates the job's readable version suffix (`iris-<user>-…-pymethods2test-<hash>-0`, no `-v13`), so the pod-derived default `trials_dir` misses it — pass `PEEK_TRIALS_S3=s3://marin-us-east-02a/iris/<full-job-name>/trace_jobs` explicitly for these jobs.

**Mac-side read of a terminal job's trace_jobs** (no live pod to exec): use the iris `cwobject.com` recipe (`.agents/ops/iris/ops.md §Scheduling`) — `iris-task-env` creds + `endpoint_url=https://cwobject.com` + `addressing_style=virtual`.

---

## Trial / trace data model

- **`RolloutDetail`** (`models/agent/rollout_detail.py`): per-turn `prompt_token_ids`, `completion_token_ids`, `logprobs`, and `extra: dict[str, list]` (provider fields like vLLM's `routed_experts`). Populated by **`Chat._accumulate_rollout_details()`** (`llms/chat.py`) after each LLM turn.
- **TIS length-parity guard** (commit `8737426c`): SkyRL zips `logprobs` onto `completion_token_ids` by position; if a turn's lengths mismatch, Harbor records an **empty logprob list** (not a silent mis-pair) so index alignment survives — downstream surfaces it via `tis/alignment_fail_count`. This is the harbor half of the TIS exact-alignment hardening (the SkyRL half is in `.agents/projects/marinskyrl/marinskyrl.md`).
- **`trajectory.json`** (per episode): ATIF `steps[]` with `source`/`message`/`tool_calls`; subagent (summarization) trajectories are separate files. `raw_content` dumps the raw LLM response instead of parsed tool_calls.
- **Per-trial footprint is large** — terminus-2 writes ~70–120 files/trial (3 per episode + subagent dirs); a 30k-trial job ≈ 2–3M FS entries. This is why trace export must prune (see below) and why GPFS hygiene matters.

---

## Harbor Job File Organization

Harbor eval jobs use a **single unified directory** per eval run at `$EVAL_JOBS_DIR/<run_tag>/`.
Run tags follow the format `eval-<SAFE_MODEL>_<SAFE_REPO>` (model first, `eval-` prefix).

A `trace_jobs/<run_tag>` symlink in the working dir points to the unified run dir so Harbor writes there directly.

**Contents of `$EVAL_JOBS_DIR/<run_tag>/`**:
- `<task_name>__<trial_id>/agent/trajectory.json` — full agent conversation trace
- `<task_name>__<trial_id>/exception.txt` — error traceback if the trial failed
- `<task_name>__<trial_id>/verifier/` — verifier output and reward
- `result.json` — aggregate results, exception stats, metrics
- `config.json` — Harbor run configuration
- `meta.env` — model, dataset, SLURM job ID, DB job ID
- `vllm.log` — vLLM server log
- `upload.log` — DB/HF upload log
- `slurm.log` — symlink to the SLURM output log

To debug DaytonaErrors or other trial failures, read `exception.txt` in the trial directory:
```bash
cat $EVAL_JOBS_DIR/<run_tag>/<task>__<id>/exception.txt
```

**Config mismatch on auto-resume**: If Harbor fails with `FileExistsError: Job directory ... already exists and cannot be resumed with a different config`, the run dir has a `config.json` from a previous run with different settings. To fix, delete only the specific stale run dir **after confirming no useful trials exist**:
```bash
# Check if the dir has any completed trials before deleting
ls $EVAL_JOBS_DIR/<run_tag>/*/result.json 2>/dev/null | wc -l
# If zero, safe to delete
rm -rf $EVAL_JOBS_DIR/<run_tag>
```

---

## Per-trial `TimingInfo` duty-cycle recipe (result.json — reusable across clusters)

Every harbor trial writes a **`result.json`** (`TrialResult`, `models/trial/result.py`) with per-phase `TimingInfo` blocks. This is the clean source for a per-trial **duty-cycle breakdown** (LLM-gen vs tool-exec vs sandbox-lifecycle vs verifier). It is a harbor artifact, so the recipe is cluster-agnostic; only the per-cluster access to the trials bucket differs (`.agents/ops/<cluster>/`).

**Discipline — aggregates only, never pull raw trials to the Mac.** Read a bounded sample (newest ~200 by `LastModified` for steady-state; ~500 for error tails) and print only computed medians/percentiles. When the bucket is in-cluster-only (CoreWeave LOTA), aggregate in-pod.

**`result.json` field → phase map** (each phase is a `TimingInfo {started_at, finished_at}`, UTC ISO):

| Field (path) | Phase | Duration |
|---|---|---|
| `started_at` / `finished_at` | **Trial total wall** | `finished_at − started_at` |
| `environment_setup` | **Sandbox create** | `TimingInfo` dur |
| `agent_setup` | agent setup | `TimingInfo` dur |
| `agent_execution` | **LLM-gen + tool-exec (combined)** | `TimingInfo` dur |
| `verifier` | verifier | `TimingInfo` dur |
| `agent_result.metadata.api_request_times_msec` | **LLM-gen ONLY** (list of per-call msec) | `Σ list ÷ 1000` → s |
| `exception_info.exception_type` | error class | — |

Derived: **Tool-exec** = `agent_execution − LLM-gen`. **Teardown/gap** = `finished_at − max(phase.finished_at)` (sub-second on healthy runs). **Frac LLM-gen** = LLM-gen / total; **frac sandbox** = (`environment_setup` + teardown-gap) / total.

**Interpretation:** LLM-gen ≫ sandbox (e.g. ~89% vs <1%) ⇒ LLM-turn-bound, not sandbox-churn — lever is `n_concurrent_trials` / buffer depth. A material sandbox fraction (>10%, or `environment_setup` >10 s tail) = real re-provision churn. Count trials with `verifier.finished_at > finished_at` — expected 0 (non-zero = release-race).

---

## SFT-ready traces with tool calling — `harbor traces export --sft-format`

The default trace export (the `conversations` column) is **lossy for tool-calling SFT** — a model trained on it never learns to condition on `role: tool` or structured `tool_calls`, so at serve time it won't emit structured tool calls and falls back to reflexive bash. Since PR #18 (`d2a92215`, on `main`), pass **`--sft-format`** to emit **serve-shaped rows straight from the trajectory** — no second-pass token decode.

### What the default `conversations` shape loses (why it hurts tool-calling SFT)

The legacy `conversations` field flattens the trajectory into a generic chat view:
- `role: system` → remapped to `role: user`.
- tool observations → `role: user` (not `role: tool`).
- structured `step.tool_calls` → flattened to inline `<tool_call>{json}</tool_call>` **text** inside the assistant message.
- a `<tools>…</tools>` block is embedded in the first system message.

SFT over that field teaches a text-blob tool protocol, not the real chat-template tool interface.

### `--sft-format`: serve-shaped `messages` from trajectory data

`export_traces(sft_format=True)` (CLI `--sft-format`) reshapes the SAME trajectory `steps[]` (ATIF `source`/`message`/`tool_calls`) into the shape the tools-aware chat template expects:
- **`role: system` preserved** (not mapped to user); **no `<tools>` block** embedded — tool defs belong in the template at SFT time, not baked into the data.
- **structured `tool_calls`** on assistant turns — OpenAI `{type: "function", function: {name, arguments}}`, with `arguments` as a **JSON string** (schema-uniform; the SFT framework parses it back to a dict before the template renders it).
- **`role: tool`** for tool observations.
- column key **`messages`** (not `conversations`); with `--sharegpt`, the derived column is `messages_sharegpt`.

Assistant text is the parsed trajectory message — a STRUCTURAL reshape, so it works on **any** trajectory and needs **no literal-token capture**. The default path (`--no-sft-format`) stays **byte-identical** to prior behavior.

```bash
# tool-aware SFT rows straight from a trials dir → HF
harbor traces export --path <trials-dir> --sft-format --push --repo <org>/<slug>-sft
# --sharegpt adds the messages_sharegpt column; --subagents includes summarizer traces
```

### `--sft-format` vs the literal-token path (§ below) — which to use

- **`--sft-format`** — the DEFAULT for tool-calling SFT. Structural, no capture needed, assistant text = parsed trajectory message. Use when you want the model to learn the `role: tool` + structured-`tool_calls` interface.
- **Literal-token → SFT** (`literal_traces_to_sft.py`, next section) — assistant turns decoded **verbatim from the tokens the engine actually served**. Requires a `--record_literal` job + the exact serving tokenizer. Use ONLY when you need byte-exact served text (train/serve TIS fidelity), not merely the structured shape. This is the older workaround `--sft-format` supersedes for the common case.

---

## Literal-token trace datasets (opencode datagen)

Canonical reference for the `--record_literal` opencode trace datasets and their downstream SFT use. Applies to the opencode-131k campaign (`penfever/<task>-qwen3.5-122b-131k-opencode-traces`).

### What the literal columns are

`make_and_upload_trace_dataset` on a `--record_literal` job emits three parallel columns alongside the text `conversations`:

- `prompt_token_ids`, `completion_token_ids` — **list-of-lists**, one inner list per agent step (turn). Verbatim tokens the serving engine emitted (RecordProxy capture, correlated by `literal_correlator.py`).
- `logprobs` — list-of-lists of floats, same shape.

A row is "literal-populated" when `prompt_token_ids` is non-empty.

### Capture + correlation

For installed agents like `opencode`, LLM calls happen INSIDE the Daytona sandbox, so Harbor's `RolloutDetail` never sees the token IDs. A co-located `RecordProxy` captures the real tokens into one job-global `literal.jsonl` (interleaving all concurrent trials). There is no join key (ai-sdk strips the upstream completion id); `literal_correlator.py` reconstructs attribution from content via message-prefix extension + count-sequence matching (verify-or-skip: omit rather than mis-attribute).

Low "literal yield" is usually a **capture ceiling**, not corruption: short/fast or early-failing interactions leave few records; long multi-turn debugging loops capture richly.

### Decoding the token IDs

The IDs only decode with the **EXACT tokenizer the engine served with** — for the 131k campaign: **`Qwen/Qwen3.5-122B-A10B-FP8`** (`Qwen2Tokenizer`, vocab 248044). A stock Qwen3 tokenizer (~152k vocab) decodes word tokens to garbage. GCS mirror: `gs://marin-models-us/ot-agent/models/Qwen/Qwen3.5-122B-A10B-FP8/` (pull `tokenizer.json`/`tokenizer_config.json`/`vocab.json`/`merges.txt`).

Always pass `--served_model Qwen/Qwen3.5-122B-A10B-FP8` on any literal upload/rescue — it stamps `tokenizer_provenance.json`. Decode per-turn with `skip_special_tokens=False` to keep `<|im_end|>`/`<tool_call>`/`<think>` markers.

### Rescue from GCS

The worker's end-of-job HF upload cannot be trusted for preemptible jobs. Every terminal job is rescued from banked GCS by the ops cron. Before rescuing a FAILED job, spot-check trials' `result.json`: if 100% errored with `steps: 0` (e.g. `NonZeroAgentExitCodeError` exit 127 = opencode binary absent), there is nothing to rescue — it needs a full re-run.

**Rescue:** rsync the outer `gs://marin-models-{us,eu}/ot-agent/<job>/` (so `logs/*_literal.jsonl` rides along), clear the target repo's partial `data/`, re-run the uploader with `--served_model`. Verify with `count_populated_literal_rows`.

### Literal traces → SFT

> For tool-calling SFT you usually want **`harbor traces export --sft-format`** (§ SFT-ready traces with tool calling) — structural, no literal capture needed. Use this literal path ONLY when you need assistant text decoded byte-exact from the served tokens (train/serve TIS fidelity).

`scripts/harbor/literal_traces_to_sft.py` converts a literal trace dataset into SFT data whose assistant turns are decoded verbatim from the literal completion tokens. Auto-resolves the tokenizer from `tokenizer_provenance.json`. Rows without literals, or whose assistant-turn count ≠ literal step count, are dropped. **LAION upload gotcha:** the `laion` org's PRIVATE storage quota is full — push SFT datasets PUBLIC.

---

## Resume + cross-cluster port

Two layers, easy to conflate:

- **Auto-resume** (`job.py` `Job.create()`): if `<job_dir>/config.json` exists, the run resumes — each existing trial dir is matched by strict Pydantic equality against the planned `TrialConfig` (any config drift → `FileExistsError`). **An errored trial still has a dir (with `exception_info` + no reward), so auto-resume treats it as complete and will NOT re-run it.** Re-launching the same run-tag with the same config is auto-resume.
- **`harbor jobs resume` (`cli/jobs.py:1375`) — the path that actually re-runs errored trials.** Walks trial dirs, reads each `result.json`, and **deletes any whose `exception_info.exception_type` is in `--filter-error-type`** so they re-run. `-f`/`--filter-error-type` is repeatable and **defaults to `["CancelledError"]`** — for non-cancelled errors you MUST pass the actual type(s) (bare Python class name: `DaytonaError`, `EnvironmentStartTimeoutError`, `DaytonaRateLimitError`). `AgentTimeoutError` is passthrough (verifier still scores it → has reward → counts VALID). Discover which types your errored trials carry via the aggregate `result.json`'s `exception_stats` map.
  - **Resuming an EVAL needs the served model live**, so it runs inside the eval sbatch (which brings vLLM up). The canonical eval sbatchs already wire `harbor jobs resume` with the standard error-type filters — just re-submit the same eval.
- **Port checklist** (`notes/harbor/port_checklist.md`): tiers what to port first when syncing harbor changes.

---

## Fork facts / load-bearing commits (now on `main`)

- **`94379963`** — `iter_trial_dirs` prunes the `os.walk` at the trial-dir level → trace export no longer GPFS-stat-storms on 30k-trial runs (the Step-8 cleanup fix; see `.agents/skills/rl-agentic-job-cleanup`).
- **`8737426c`** — the TIS per-turn logprob/token-id length-parity guard (above).
- **`ec508562`** (+ throttle follow-up `e05d569d`) — reap orphaned LiteLLM logging tasks on between-turns timeout/cancel → fixes the Ray ObjectRef-leak SIGABRT on AgentTimeout-heavy datasets (a separate bug class from the uvloop fix).
- Install: `pip install -e .` with extras `[daytona]`/`[modal]`/`[cloud]`/`[all]`.

---

## Key config surfaces (the `hpc/harbor_yaml/` YAMLs in OT-Agent)

`n_concurrent_trials` (concurrency / sandbox count — per-job Daytona ceiling ~128), `n_attempts`
(samples/task), agent `enable_summarize` / `max_input_tokens` / `store_all_messages` /
`trajectory_config.{raw_content,linear_history}`, `environment.type` (backend). Datagen configs under
`hpc/harbor_yaml/datagen/` (match the model's `max_model_len`: `ctx32k.yaml`/`ctx131k.yaml`), eval configs
under `hpc/harbor_yaml/eval/` (`eval_ctx32k_non_it.yaml` etc.). Recompute metrics offline:
`scripts/harbor/recompute_result_json.py <run_dir> --metrics-config <yaml>`.
