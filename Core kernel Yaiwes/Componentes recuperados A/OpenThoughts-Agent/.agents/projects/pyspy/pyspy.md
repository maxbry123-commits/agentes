# py-spy live-capture — scoping a HANG on a live job (cluster-agnostic)

**What the operator means when they ask for this.** Phrases like *"go in with py-spy while the job is
alive,"* *"py-spy and inspect it live,"* *"scope the failure live,"* *"it's a 30-minute hang, just check
every N minutes and you'll catch it."* The failure is a **HANG** — a process that is alive-but-stuck, or a
periodic/timed stall — and the operator wants the **frozen call-stacks of the live processes**, captured
with py-spy on a **simple periodic cadence**, NOT another event-triggered watcher. This is a standing,
recurring request; treat it as "instrument the live job with py-spy now, before it dies."

## Why this, and why NOT a trigger-trap

- A **log grep / state-poll cannot see a hang.** The process reports `state=running` but is stuck; only a
  stack sampler (py-spy) shows WHERE. "RUNNING" is not "healthy."
- **Event-triggered traps** (fire py-spy when a log line matches) are **brittle and keep missing the fire** —
  wrong PID match, hash-based names that don't match, py-spy not installed on the host, or the
  failure→teardown window (often ~1 min) closing before the trap reacts. **A dead-simple periodic dump
  (every ~60–120 s, no trigger logic) is far more reliable:** even if it "misses" the exact onset, the last
  sample before teardown holds the frozen stack. When the operator says *"just check every N minutes,"* this
  is what they mean — and they're right.
- **Capture a HEALTHY baseline first** so the blip stack is interpretable by diff (who moved, and to where).

## The method

The ONLY cluster-specific part is **how you exec into the process's host** — that lives in
`.agents/ops/<cluster>/`:
- **k8s / iris-style** (no ssh): `kubectl exec -n <ns> <pod> -c <container> -- bash -lc '<cmd>'`.
- **SLURM** (Leonardo/TACC/EmpireAI): `ssh <node>` (or `srun` into the alloc) then run in the job's env.
Everything below is general.

1. **Verify py-spy ATTACHES now, while healthy** — never discover a block at the worst moment.
   - Install if missing (it usually IS missing in job containers): `pip install py-spy` (prebuilt wheel; needs
     a writable env — try the job's venv pip too). Confirm `command -v py-spy`.
   - Test: `py-spy dump --pid <a-live-python-pid> --nonblocking`. **`--nonblocking` = don't pause the process**
     (safe on a live serving engine).
   - Needs **ptrace**: run as root or with `CAP_SYS_PTRACE` (most job containers have it). If ptrace is
     blocked, fall back to `kill -SIGQUIT <pid>` (dumps a Python traceback IFF faulthandler is enabled).
2. **Identify targets by CMDLINE, not by process/pod NAME** — names are hash-based and change on retry, which
   is exactly what breaks the auto-traps. `ps -eo pid,args | grep -E '<server>|<coordinator>|<proxy>'`. Target
   the processes whose hang matters: the model/engine **server**, the **driver/coordinator**, any **proxy**.
   Bonus: the captured cmdline often NAMES the culprit for a *timed* failure (e.g. a per-trial
   `override_timeout_sec=1800` = the exact 30-min stall) — read it.
3. **Run a SIMPLE periodic loop** (no trigger logic). Each iteration:
   - re-find the target host(s) + PIDs (robust to restart/rename),
   - `py-spy dump --pid <pid> --nonblocking` for each target,
   - capture **concurrent context that discriminates hang-vs-environment**: reachability of the endpoint the
     process talks to (`getent hosts <host>` + a timed `curl -m6 -w '%{http_code} conn=%{time_connect}'`),
     socket summary (`ss -s`) + fd count (`ls /proc/<pid>/fd | wc -l` — pool exhaustion), resource state
     (`nvidia-smi --query-gpu=utilization.gpu,memory.used`),
   - save TIMESTAMPED to scratch,
   - `sleep 60–120`; loop until the host/pods vanish (job terminal) or a max duration.
4. **Run the loop as a HARNESS-TRACKED background task**, NOT `nohup … &` inside a quick wrapper. A nohup child
   can be reaped, and — critically — you get **no exit notification**, so you'd miss the window. A tracked
   background task auto-notifies you the instant the job dies → you read the last dumps immediately.
5. **When it fails: diff the blip dump vs the healthy baseline.** Who moved, and where?
   - Engine stuck in a NEW stack (a CUDA / NCCL / lock call) + endpoint still reachable → **engine hang**.
   - Engine still idle-normal (e.g. a server busy-loop waiting on work), but the proxy/driver is in a
     connect-retry loop AND the concurrent DNS/curl FAILS → **endpoint / network / ingress** issue.
   - Proxy/driver stuck at high concurrency (a GIL/lock) → **proxy stall**.
   - fd / socket count exhausted → **connection-pool leak**.
   - For a *timed* failure, correlate the ~N-minute onset with a timeout/TTL from the captured cmdline/config.

## Reusable loop skeleton

```bash
#!/usr/bin/env bash
# Periodic py-spy on a live job. Cluster-agnostic EXCEPT the `hosts_of` / `exec_on` helpers,
# which wrap the cluster's exec mechanism (kubectl exec | ssh <node> | srun).
OUT=<scratch>/pyspy_<job>; mkdir -p "$OUT"
i=0
while [ "$i" -lt 40 ]; do
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  hosts=$(hosts_of "<job>")                 # re-find each iter (robust to restart)
  [ -z "$hosts" ] && { echo "[$ts] no hosts — job gone" >>"$OUT/loop.log"; break; }
  echo "[$ts] sampling $(echo "$hosts"|wc -l) (iter $i)" >>"$OUT/loop.log"
  for h in $hosts; do
    exec_on "$h" '
      PS=$(command -v py-spy || echo /usr/local/bin/py-spy)
      for pid in $(ps -eo pid,args | grep -iE "EngineCore|AsyncVLLM|coordinator|proxy|run_rl|<server>" \
                   | grep -v grep | awk "{print \$1}" | sort -u | head -8); do
        echo "=== PID $pid: $(ps -p $pid -o args= | head -c 90) ==="
        timeout 15 $PS dump --pid $pid --nonblocking 2>&1 | head -35
      done
      echo "### net/env ###"
      getent hosts <endpoint_host>
      curl -m6 -sS -o /dev/null -w "http=%{http_code} conn=%{time_connect}s\n" https://<endpoint>/ 
      ss -s | head -1; echo "fds=$(ls /proc/1/fd 2>/dev/null | wc -l)"
      nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader | head
    ' > "$OUT/${ts}_${h}.txt" 2>&1
  done
  i=$((i+1)); sleep 90
done
```

Launch it as a **tracked** background task. First iteration = the healthy baseline; keep it running through
the failure window. On the exit notification, read the newest `$OUT/*.txt` and diff against the baseline.

## Gotchas (learned the hard way)

- **py-spy is usually NOT pre-installed** in job containers → install it in step 1 (this is the #1 reason
  auto-traps "fire into nothing").
- **Match processes/hosts by cmdline, not hash-based names.**
- **`nohup … &` inside a wrapper** can be reaped and gives no exit notification → run the loop as a tracked
  background task.
- **`--nonblocking`** on a live serving process (don't pause a production engine mid-request).
- A ~1-min failure→teardown window means a ~90 s cadence catches it; tighten to ~30 s if you know the window.
- The concurrent net/DNS/fd/GPU capture in the SAME dump is what turns "the engine was unreachable" into a
  *diagnosis* (hang vs ingress vs pool-exhaustion) — always capture it alongside the stacks.

## Worked example

Origin (2026-07-18): a MarinSkyRL keep-1 RL job on CoreWeave/iris died at a *consistent ~32–35 min* with a
mass `httpx.ConnectError` (engine unreachable) — a HANG, not a crash. Event-traps kept missing it (py-spy
uninstalled; hash pod names). A per-90 s py-spy loop over the 4 pods (`EngineCore` / `AsyncVLLM` /
`RolloutCoordinator` / controller) + concurrent `iris.oa.dev` DNS/curl + `ss`/fd + `nvidia-smi`, run as a
tracked task, captured the healthy baseline (engine idle in its `shm_broadcast` busy-loop) and was positioned
to catch the blip stack. The captured cmdline surfaced the prime suspect: `override_timeout_sec=1800` (=30 min)
— a first-trial-wave mass-timeout thundering herd. (Cluster access mechanics: `.agents/ops/iris/ops.md` +
`scripts/iris/analyze_coreweave_rl_job_live.sh`.)
