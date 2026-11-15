---
name: rl-job-health-deep-dive
description: >-
  Deep single-RL-job health probe → a KILL / NO-KILL / ERROR recommendation for the supervisor. Dispatched as a
  subagent on every monitor tick for RL jobs in NEW/UNTESTED settings (new config/geometry/model, "debug" or
  "smoke-test" flavor, first launches after a code/config change), and whenever a running job looks starved or
  wedged. Goes BEYOND state-poll + table metrics: captures the job's logs + trace_jobs + GPU view, then runs four
  gates — (A) liveness, (B) resource utilization / engine subscription, (C) rollout quality — and emits ONE
  evidence-backed verdict. The subagent NEVER kills — it recommends; the supervisor owns the kill. This skill holds
  the METHODOLOGY only; every cluster-access and codebase fact is a POINTER into .agents/ops/<cluster>/ and
  .agents/projects/<dep>/ (those are the single source of truth — do not re-encode them here, they go stale).
---

> ⚠ **Do not add comments to YAMLs. Report your recommendations directly to the supervisor.**

# rl-job-health-deep-dive

Probe **one RL job** when it is new or untested (config, geometry, model, image, debug/smoke launch, or first
launch after a change), or looks starved or wedged. This distinguishes genuine progress from a silent death.

**You are a SUBAGENT — you do NOT execute the kill** (standing guardrail: never kill a RUNNING job without explicit
permission). When genuinely uncertain, **prefer NO-KILL + escalate** — a wrongly-killed healthy run wastes a whole
bring-up; a wrongly-kept dead one wastes one sweep. **But if you couldn't get the evidence, the answer is `ERROR`,
not a hedged NO-KILL (see §0).**

---

## STEP 0 (DO THIS FIRST) — PULL THE LOGS LOCAL, THEN ANALYZE FROM FILES (mandatory; no live-grep dance)

**Before any gate, sync logs locally with this utility and analyze those files.** Do not make repeated live
`iris job logs` or `kubectl exec` greps the primary method.

```bash
set -a; source /Users/benjaminfeuer/Documents/secrets.env; set +a
PY=/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python
$PY /Users/benjaminfeuer/Documents/MarinSkyRL/infra/sync_rl_logs.py \
    /benjaminfeuer/<job> --cluster <cw-us-east-02a|cw-rno2a> [--run run-<ts>] [--dest DIR] [--trace-jobs]
# → ./<slug>-<run>/finelog.log   +   ./<slug>-<run>/ray_session_logs/
#   (+ ./<slug>-<run>/<slug>_trace_jobs.tar.gz when --trace-jobs is passed — the Harbor rollout
#      artifacts streamed into ONE archive; opt-in, since trace_jobs can be very large)
```

It pulls both required sources:
- **`finelog.log`** = the aggregated controller/job stream — **this is where the terminating exception / NCCL timeout /
  `store->get(...) got error` / `Worker rank N received signal` lives.** The per-actor ray logs are frequently
  traceback-less (Ray's C++ core logs); a hang's root cause routinely appears ONLY in the finelog. Read this FIRST.
- **`ray_session_logs/`** = the per-actor `worker-*.out/.err` + `python-*`/raylet/gcs — for per-rank NCCL `Init
  COMPLETE`/`nranks`, weight-sync group construction, py-spy correlation, and the failing rank's own stderr.

Analyze files with `grep` or Python. For NCCL/weight-sync structure, run
`experiments/active/tasktrove-dq-sweep-opencode/artifacts/parse_collectives.py` on `ray_session_logs/`. The utility
is idempotent and selects kubeconfig by cluster.

Hand the supervisor the local file paths and quoted lines. Live probes are reserved for a py-spy on a still-running
wedge; all other analysis is file-based.

---

## §0. THE CONTRACT — evidence-or-ERROR (the load-bearing rule)

**Return `VERDICT: ERROR` whenever you could not obtain the evidence**: a required tool failed (auth / PATH /
resolver bug / timeout), a log can't be fetched or parsed, you can't separate policy-mesh from engine GPUs, or two
authoritative signals disagree and you can't reconcile them. Stop — give (a) the exact command you ran, (b) its exact
failure output, (c) what evidence is therefore missing, (d) what you *did* establish. **Do NOT emit KILL/NO-KILL,
do NOT default to NO-KILL, NEVER substitute a plausible guess for a missing measurement.**

**No gate verdict without its named, quoted artifact:**

| Gate | A PASS/FAIL requires you to have READ + QUOTED | else that gate is |
|---|---|---|
| A liveness | the authoritative state-poll line **and** the newest phase-Timer / step line + its timestamp | ERROR |
| B resources | per-rank GPU util **with policy ranks separated from engine ranks**, **and** the engine subscription line (running vs waiting vs the serving cap) | ERROR |
| C rollouts | actual reward values / trial exception files you OPENED (not a count you assumed) | ERROR |

### ⛔ Engine under-subscription is NEVER Daytona / duty-cycle / tools

When engines are under-subscribed or idle (`Running` low, `Waiting=0`, KV≈0, ⅓-TDP power) and the generation buffer
stalls, measure the **gen→dispatch→train pipeline** live:
- **RolloutCoordinator dispatch cores** — are the `num_coordinators` (K) coordinator processes CPU/GIL-pegged on
  `submit_batch`/`gather`/post-gather shaping? (py-spy / top them.) → dispatcher-bound → the lever is K, not n/npgw.
- **staleness/backpressure** — is generation throttled by `max_staleness_steps` because `policy_train` is the slow
  phase (training-bound)?
- **issued-vs-scheduled** — are `generate()` calls reaching the engine but `Waiting` stays 0 (engines drain
  instantly)? → the bottleneck is upstream dispatch rate, not engine capacity.

(The saturation-READ tuple + "SM-util% is a trap" in marinskyrl's "Saturating vLLM engines" section is still valid;
its CAUSAL "raise concurrency to beat the duty cycle" story is REFUTED — see the caveat there.) Diagnose while the
job is ALIVE (py-spy dies with it). A verdict on an unmeasured starvation is ERROR-quality.

---

## Resources you MUST use (this skill points; these docs are the truth)

**Read the relevant pointers first; this skill does not restate their contents.**

- **Cluster access, poll mechanics, log fetch, GPU-poll, node headroom, Daytona lifecycle, the tool failure
  modes** → `.agents/ops/<cluster>/`:
  - CoreWeave → **`ops/iris/ops.md`** — §Access (kubeconfig per cluster: East vs cw-rno2a), §Observability (the state-poll primitive `iris_ops.py`, JobState codes, finelog fetch, and the **Poll/tooling pitfalls**: rno2a `job summary` flakiness, the `*_ms` query columns, the `analyze_iris_harbor_job` `--config`/RL-output-dir limits, no server-side `job logs` grep), §Scheduling (gang/Kueue admission + node-headroom math), §Daytona (orgs, sandbox lifecycle, concurrency headroom), §Monitoring & debugging practices (incl. py-spy). Node shape → `ops/iris/ops.md`.
  - Leonardo → `ops/leonardo/ops.md`; TACC → `ops/tacc/ops.md`.
  - **Log-volume discipline** (memory `iris-log-resource-discipline`): state-poll for liveness, bounded/filtered fetch for metrics — never dump a long log into the Mac. Exact bounded-fetch commands in ops §Observability.
- **What the logs/config MEAN — the trainer/engine vocabulary, benign-vs-fault line, known failure modes, config
  semantics** → `.agents/projects/<dep>/`:
  - **`projects/marinskyrl/marinskyrl.md`** — the phase-Timer/step vocabulary, `[MoE-PATH]` grouped_mm-vs-for-loop, the colocated-engine/rank-0-logging deception, engine saturation (`n_concurrent_trials` scaling), the 80B GDN-GIL/HeartbeatMonitor death + FlashQLA, `SKYRL_W13_RELOAD_BRACKET` token-salad, `SKYRL_R3_RESIDENT`, the benign `prob_diff_mean` artifact, config-schema (Hydra struct) rules, runtime knobs. **Read the section matching what you're chasing — do not guess a log line's meaning.**
  - `projects/vllm/vllm.md` — the serve engine: MoE/DCP/R3 flags, `enforce_eager` (CUDA-graphs) throughput cliff, serving-throughput expectations, the benign engine heartbeats (`shm_broadcast … 60/600s`).
  - `projects/harbor/vllm/daytona/` — the rollout/trial layout, verifier/reward path, passthrough exceptions, sandbox failure modes.
- **Capture + poll scripts** (don't hand-roll): `scripts/iris/analyze_coreweave_rl_job_live.sh` (CoreWeave artifact pull),
  `scripts/iris/iris_ops.py` (state-poll), `scripts/iris/analyze_iris_harbor_job.py` (finelog science — mind the RL-job/rno2a limits in the ops note). The per-rung bring-up ladder is `rl-agentic-launch-iris` §8.

---

## §1. Inputs + capture

**Inputs** (from the dispatch; most derivable): cluster, job id, pod-name substring, model + size (dense vs MoE
active-B), the run's stage, and **what's "new/untested"** about it (scrutinize that hardest).

**Check restart burn first:** record `B burned / K max`, prior terminal errors, and whether failures repeat.
Repeated identical crashes are deterministically doomed; a recovered transient is benign. See `ops/<cluster>/` for mechanics.

**Capture the artifacts = STEP 0's `sync_rl_logs.py` (finelog + ray_session_logs) — already done before you reach
this gate.** Do NOT hand-roll a kubectl/R2 sync or a live `iris job logs` grep; work from the local files STEP 0
pulled. (`scripts/iris/analyze_coreweave_rl_job_live.sh` is still the tool for the per-trial `opencode.txt`/rollout view when you
need rollout-quality detail beyond the logs.) *What the phase-Timers / step counter / `[MoE-PATH]` markers mean* →
`projects/marinskyrl`. **The phase Timers are the progress truth — not a trace count, not a progress bar.** (0
trials at +15 min on a long-episode arm is normal, not "done" and not "dead.")

**⚡ ON ANY DEATH/WEDGE — READ BOTH `finelog.log` AND `ray_session_logs/` (STEP 0 pulled both). The root cause hides in ONE of them; which one varies.** Two failure classes, two homes:
- The **finelog** carries the aggregated **terminating exception / NCCL timeout** — e.g. `store->get('...') got error: wait timeout after 1800000ms` + the `collective_rpc`/`broadcastUniqueNCCLID` traceback of a het weight-sync bootstrap hang, or a `Worker rank N received signal`. The per-actor ray logs frequently do NOT carry this (worker-*.err may hold only a benign metrics-RPC line). **Read `finelog.log` FIRST** (grep it for `got error`/`timeout`/`Traceback`/`received signal`/`Init COMPLETE`).
- The **ray_session_logs** carry the per-actor detail: a vLLM `EngineCore` fatal, a Ray `ObjectLostError`/`OwnerDiedError`, an actor crash, per-rank NCCL `Init COMPLETE`/`nranks`, weight-sync group construction. Grep **`worker-*.out`/`worker-*.err`** (NOT `python-core-*.log`, Ray's traceback-less C++ core logs); for NCCL/weight-sync structure run `parse_collectives.py` on the dir (STEP 0). A colocated-engine job that dies `exit=0` with NO finelog traceback (only `Killed ray::IDLE/raylet/gcs`) has its killer here.
- **A "clean" `exit=0` teardown with node RAM low is NOT a verdict — it's a missing-evidence ERROR until you've read BOTH local files.** Worked examples: keep1-v22 (silent ~34-min death = vLLM `EngineDeadError` `reshape_and_cache_flash … Meta tensors` at first-step weight-sync, found in ray_session_logs); keep1-ncclnet (het weight-sync bootstrap hang = `store->get('/skyrl/skyrl//cuda//0')` 1800000ms timeout via `collective_rpc`, found ONLY in the finelog). Deeper background → `ops/iris/ops.md` §object-store / RAY ACTOR LOGS.

---

## §2. Gate A — Liveness (alive, or zombie/wedged/dead?)

**Liveness = authoritative state poll plus log freshness, never one log-string grep.** Use `ops/iris/…`
§Observability, then compare captured-log freshness with expected cadence and read wedge/death signatures.

> **⚠ Multi-mesh RL hides a wedged policy behind live engines (the colocated-engine deception).** On any
> FSDP×EP×CP RL job the vLLM engines + RolloutCoordinator are SEPARATE actors from the policy mesh — a hung policy
> collective can read `running / fresh-heartbeat / high-util` while doing nothing. The three signals that don't
> lie (Ray actor-death logs, the NCCL watchdog, is the TRAINER/DRIVER log ADVANCING with **policy-rank** GPUs
> separated from engine GPUs) and the exact strings to grep for each — **`projects/marinskyrl`** (colocated-engine
> deception + rank-0-logging trap) and **`projects/vllm`** (benign engine noise vs real `EngineDeadError`). Do not
> call Gate A PASS on a multi-mesh job without clearing all three.

**Gate A verdict:** DEAD/TERMINAL (state-poll failed/absent, 0 pods) → nothing to kill; report the root-cause
traceback + transient-vs-deterministic. WEDGED (running + a real hang signature + stale logs, no benign
explanation) → lean KILL (but if it's a *starvation* wedge, capture the live py-spy first — §0). **A py-spy
barrier-snapshot + a lone NCCL `Watchdog … ran for N ms` LOG LINE is NOT a wedge by itself** — a real tripped
watchdog ABORTS the process, so require pod-restarts==0 + an actual abort/terminal state + stalled FRESH logs (all
nodes) and reconcile the cited timeout against the run's timeline before calling wedge (the CW py-spy command + this
caveat: `ops/iris/…` §Monitoring & debugging practices). ALIVE + fresh → Gate B.

---

## §3. Gate B — Resource utilization + engine subscription (are the GPUs actually working?)

**Live-poll GPUs; separate policy ranks from engine ranks and never average them.** See `ops/<cluster>/` for commands.

- **Rollout/generation stage — the engine-subscription check (catch starvation EARLY, do not wait for a late
  step):** every engine should be **fed and generating**. The starvation signature is **engines under-subscribed**
  — few `Running` requests, `Waiting ≈ 0`, GPUs resident-but-~0%-util, the generation buffer barely filling (or a
  frozen `Generation Buffer Progress: N/M` heartbeat — same N, growing elapsed). That is NOT a Daytona fault (§0);
  the first hypothesis is **rollout concurrency too low to saturate the engines**, and the Daytona side has large
  concurrency headroom to scale into. *The saturation math (`n_concurrent_trials` = `2·num_parallel_generation_workers`
  + 32, scale them together) + why engines idle demand-starved* → **`projects/marinskyrl`** (Saturating vLLM
  engines). *Throughput-vs-hardware expectations + the `enforce_eager` CUDA-graph cliff to rule out first* →
  **`projects/vllm`** + the H100 node shape in `ops/iris/ops.md`. The opposite failure —
  `Waiting ≫ Running` with flat throughput — is over-subscription thrash. Report the concrete counts, not "looks fine."
- **Training/optimizer stage:** not VRAM-OOM (no OOM signature; mem not pinned at ceiling *while stalled*), not
  host/RAM-OOM (no `OOMKilled`), policy/ref ranks actually compute-bound (high util + power) during a step — all-0%
  with no log advance during "training" = wedge. *OOM-detection mechanics* → `ops/<cluster>/`; *host-RAM breakdown
  vocabulary + the 80B optimizer-spike danger window* → `projects/marinskyrl`.

**Gate B verdict:** engines under-subscribed/idle with a stalled buffer, throughput floored with `Running>0` and
`enforce_eager:false`, or a training-stage OOM / all-ranks-0%-no-progress → **lean KILL or a config fix** (for
under-subscription, the fix is usually a concurrency bump, not a kill). All engines fed + generating, or training
steps advancing without OOM → healthy; Gate C.

---

## §4. Gate C — Rollout quality (read the actual trace_jobs; use judgment)

State + GPUs can be green while the run produces garbage (e.g. a degraded weight-sync serving token-salad → all
reward-0 → no learning signal). **Read the literal rollouts**, qualitatively: trials INITIALIZING? COMPLETING
(count the reward markers — 0 completed at +15 min on a long arm is expected)? any rewards NON-ZERO? TURNS
completing (avg≈1 turn = dead-engine/broken-loop)? agent outputs sane (read 3–5)? verifiers scoring real attempts
vs erroring? *The trace/reward/verifier layout + the known failure fingerprints* (incoherent output ⇒
weight-sync/geometry fault — check `SKYRL_W13_RELOAD_BRACKET`; genuine infra exceptions — **name them from a trial
exception file you OPENED, don't assume**; ⚠ engine STARVATION is a §3 dispatch problem, NOT "every trial threw a
Daytona exception") → **`projects/harbor`** + **`projects/marinskyrl`** + `ops/iris/…` §Daytona.

> **⚠ 100% `AddTestsDirError` on a known-good dataset = a CONTAINER problem, not the dataset.** When every rollout
> batch fails `AddTestsDirError` ("Failed to add tests directory to environment") on a fresh/bespoke image but the
> dataset has run cleanly across prior experiments, the Daytona **sandbox is never built** (`self._sandbox is None`
> → "Sandbox not found. Please build the environment first.") and the verifier's `upload_dir` into the missing
> sandbox is what surfaces as `AddTestsDirError`. Root cause is usually **container TRANSITIVE-dep drift**, NOT
> Harbor and NOT the data: `harbor[daytona]` installed without `--no-deps` lets the Daytona SDK + its transitives
> (e.g. `websockets`, litellm) re-resolve against a changed base env (a transformers/megatron bump), breaking
> sandbox-create vs the last-good image. Diff the failing image's Daytona-path deps against the last-good working
> image, pin them back, and **validate sandbox-CREATE cheaply (a 1-pod throwaway that actually instantiates the
> sandbox) — an import smoke is NOT enough (the break is at create, not import) — before any GPU relaunch.** Prove
> any single-variable hypothesis (e.g. "wrong Harbor") with hard evidence before rebuilding on it.

**Gate C verdict:** incoherent/all-reward-0 from a serving/sync/verifier fault on a new geometry, or a path that
yields zero learning signal with no transient explanation → lean KILL (+ the fix). Trials completing with some
non-zero rewards, or coherent multi-turn attempts on genuinely-hard tasks even at low pass-rate → NO-KILL, learning.

---

## §4b. Per-trial duty-cycle breakdown (sandbox-churn quantification) — OPTIONAL DEEP PROBE

Run when an agentic RL job shows an **engine sawtooth** (inference `Running` peaks then troughs) and you must
decide whether each trial's throughput is capped by **LLM generation** vs **sandbox-lifecycle churn** vs
**tool-exec** vs **error/retry** — i.e. to put NUMBERS behind (or refute) a "sandbox churn" claim. **Never assert
"sandbox churn" from the sawtooth alone**; no numbers → `ERROR` per §0.

**Source + discipline:** the clean per-trial breakdown is each trial's `result.json` `TimingInfo` (NOT finelog).
The reusable recipe — field-to-phase map, duty-cycle fraction math, lease-race / burst≠churn checks (a **harbor**
trial artifact) — is in **`projects/harbor/ops.md` §"Per-trial `TimingInfo` duty-cycle recipe"**. On cw-rno2a
the trials bucket is in-cluster-only, so aggregate **in-pod** and transfer **aggregates only** (the cluster-specific
`kubectl exec` + boto3 access + trials path is in **`ops/iris/ops.md` §Observability** "Per-trial
`TimingInfo` duty-cycle read"). Read only a bounded sample (newest ~200 for the duty cycle, ~500 for error/re-provision tails).

**Compute + read (per trial, then median + p10/p90/max):**
- **frac LLM-gen / total** and **frac NOT-LLM / total** (the duty-cycle overhead); **frac tool-exec / total**;
  **frac sandbox-lifecycle / total** = (`environment_setup` + teardown-gap) / total = the **sandbox-churn tax**.
- **Interpretation:** **LLM-gen ≫ sandbox** (e.g. ~89% vs <1%) → the refill burst is **LLM-turn-bound, not churn**;
  the inference-subscription lever is `n_concurrent_trials` / generation-buffer depth (feed more trials to the
  engines), **NOT sandbox optimization**. A **material sandbox fraction** (create/teardown >~10%, or an
  `environment_setup` heavy >10 s tail) = real re-provision churn → carry the numbers to the verdict.
- **Lease / release-race check:** count trials with `verifier.finished_at > finished_at` — **expected 0** (harbor
  runs verifier before finalize; the shielded stop/delete follows). Non-zero = release-race signature. Teardown gap
  (`finished_at − last-phase-finish`) is sub-second on a clean run.
- **"Burst ≠ churn" rule:** bucket the exception breakdown by ~10-min `LastModified` slot. A **time-clustered**
  DaytonaAuth/401 spike (concentrated in one slot, absent before/after) is the **transient server-side 401 flake**
  (the `_sandbox_exec` hot-path missing a retry wrap — same root cause as the eval side), NOT steady-state sandbox
  lifecycle and NOT a lease race — report it as transient, do not KILL for it. Only a *steady* per-slot error rate
  is a standing fault.

*(Reference measurement + numbers: `agent_logs/2026-07-15_per-trial-dutycycle-measurement.md`.)*

---

## §5. Deliver ONE recommendation

```
RL-JOB-HEALTH — /benjaminfeuer/<job>  (<model>, <geometry>, <stage>)   captured: <dir>

VERDICT: KILL | NO-KILL | ERROR          confidence: high|medium|low
  (ERROR = couldn't get the evidence — §0. Give the failed command + its output + what's missing;
   do NOT emit KILL/NO-KILL and do NOT default to NO-KILL.)
Evidence I actually read: <quote the state-poll line; the policy-vs-engine util split; the engine
  subscription counts; the reward values / exception files. A blank row ⇒ that gate is ERROR, not PASS.>
Restarts: <B/K burned, remaining> — <none | same failure each attempt: … | transient, recovered>

Gate A (liveness):   PASS|FAIL|ERROR — <state-poll + log-freshness + any wedge/death signature>
Gate B (resources):  PASS|FAIL|ERROR — <policy-vs-engine util; engine subscription (Running/Waiting vs cap);
                     enforce_eager; OOM? — for under-subscription, the concurrency-bump fix + the live py-spy>
Gate C (rollouts):   PASS|FAIL|ERROR — <trials started/completed; rewards; turns; coherence; verifier sanity>

REASONING: <2–4 sentences — the load-bearing evidence, esp. for whatever was "new/untested">
NEXT STEPS: <if KILL: root cause + the concrete fix (config knob / weight-sync / image / infra) + relaunch-or-hold.
             if NO-KILL: what to watch next tick + the specific signal that would flip it.
             if ERROR: what to fix in the tooling/access so the next probe gets the evidence.>
```

**Verdict rules:**
- **KILL** if any gate is a hard FAIL with **no transient/benign explanation** — and you have the evidence. Always
  give root cause + the fix. A starvation/wedge KILL must include the **live py-spy** captured before the kill (§0),
  else it's ERROR-quality.
- **KILL (deterministically-doomed)** if restarts repeat the SAME failure each attempt — state `B/K` + the
  traceback + the fix that must land first.
- **NO-KILL** if all gates pass, OR the only failures have a legitimate transient/early-bring-up explanation.
  Say what you're waiting on + the flip signal.
- **ERROR** if you could not obtain a gate's required evidence (§0). Never launder it into a NO-KILL.

**You never run the kill.** The supervisor executes teardown + relaunch (per `rl-agentic-launch-iris` /
`rl-*-launch-*`) on the corrected setting. Log the probe + verdict to `~/Documents/agent_logs/` (dated).

---

## Operating notes
- This is the per-job read; `monitor-cron-sweep` is the breadth pass.
- Keep access/tooling facts in `.agents/ops/<cluster>/` and code/config semantics in `.agents/projects/<dep>/`.
- Never hand-edit a cluster. Diagnose and recommend; make fixes in the local clone.
