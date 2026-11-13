#!/usr/bin/env python3
"""
Analyze recorded browser-agent metrics and flag GHOST SUCCESS: tasks that
report "completed" but show no evidence of real work (errors-only, looped, or
zero productive mutation). A task ending without an exception is NOT proof the
goal was achieved, this is the independent reality check.

Usage:
  python3 scripts/analyze-browser-metrics.py [metrics_dir]
Defaults to $OPENSWARM_BROWSER_METRICS_DIR, else
~/Library/Application Support/OpenSwarm/data/browser_metrics (mac) or backend/data/.
"""

import json
import os
import statistics
import sys
from collections import Counter, defaultdict

# Tools that actually change page state (vs. read/meta). A "completed" task that
# never ran one of these did nothing but look around, suspicious.
PRODUCTIVE = {
    "BrowserClick", "BrowserClickIndex", "BrowserType", "BrowserNavigate",
    "BrowserPressKey", "BrowserBatch", "BrowserReplayRoute",
}


def _default_dir():
    env = os.environ.get("OPENSWARM_BROWSER_METRICS_DIR")
    if env:
        return env
    mac = os.path.expanduser("~/Library/Application Support/OpenSwarm/data/browser_metrics")
    if os.path.isdir(mac):
        return mac
    return os.path.join(os.path.dirname(__file__), "..", "backend", "data", "browser_metrics")


def load(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def ghost_verdict(task, events_for_task):
    """Return (is_ghost, [reasons]). Conservative: only flags 'completed' tasks
    that show no evidence the work happened."""
    if task.get("status") != "completed":
        return False, []
    reasons = []
    tools = [e["tool"] for e in events_for_task]
    productive = [t for t in tools if t in PRODUCTIVE]
    errs = sum(1 for e in events_for_task if not e.get("ok"))
    total = len(events_for_task)
    # A read/extract task legitimately has no state-changing action; its evidence
    # is that a READ tool actually returned content. So "no productive action" is
    # only a ghost when NO read returned data either (i.e. nothing real happened).
    _READ = {"BrowserGetText", "BrowserGetElements", "BrowserListInteractives",
             "BrowserListRoutes", "BrowserReplayRoute", "BrowserScreenshot", "BrowserEvaluate"}
    read_with_content = any(
        e["tool"] in _READ and e.get("ok") and (e.get("result_len", 0) or 0) > 0
        for e in events_for_task
    )
    if total == 0:
        reasons.append("completed with ZERO tool calls (model declared done without acting)")
    if total and not productive and not read_with_content:
        reasons.append("no state-changing action AND no read returned content, yet marked completed")
    if total and errs / total >= 0.5:
        reasons.append(f"{errs}/{total} tool calls errored but still marked completed")
    if any(e.get("is_loop") for e in events_for_task):
        reasons.append("loop detector fired during a 'completed' task")
    prod_ok = [e for e in events_for_task if e["tool"] in PRODUCTIVE and e.get("ok")]
    if productive and not prod_ok:
        reasons.append("every state-changing action errored, yet marked completed")
    return (len(reasons) > 0), reasons


def skill_layer_report(tasks, skill_events):
    """Did the learn/replay/trust layer ACTUALLY help, or is it silently
    thrashing? Measures the replay speedup on repeated tasks and flags the ghost
    where a task is done over and over but never reaches the no-LLM fast path."""
    print("\n=== SKILL LAYER (does learn/replay actually help?) ===")
    paths = Counter(t.get("path", "llm") for t in tasks)
    total = sum(paths.values())
    if total:
        for p in ("replay", "llm", "llm_fallback"):
            if paths.get(p):
                print(f"  {p:<13}{paths[p]:>4}  ({round(100*paths[p]/total)}% of finished tasks)")

    # Repeated tasks: group completed runs by signature, compare replay vs llm time.
    by_sig = defaultdict(list)
    for t in tasks:
        if t.get("completed") and t.get("task_sig"):
            by_sig[t["task_sig"]].append(t)
    repeated = {s: r for s, r in by_sig.items() if len(r) >= 2}
    helped, silent = [], []
    for sig, runs in repeated.items():
        rp = [t["total_ms"] for t in runs if t.get("path") == "replay"]
        lm = [t["total_ms"] for t in runs if t.get("path") in ("llm", "llm_fallback")]
        if rp and lm:
            speed = round((sum(lm) / len(lm)) / max(1, (sum(rp) / len(rp))), 1)
            helped.append((sig, len(runs), speed, round(sum(lm) / len(lm)), round(sum(rp) / len(rp))))
        elif not rp:
            silent.append((sig, len(runs)))
    if helped:
        print("\n  REPLAY SPEEDUP on repeated tasks (the win, measured):")
        for sig, n, speed, lm_ms, rp_ms in sorted(helped, key=lambda x: -x[2]):
            print(f"    {speed}x faster  ({lm_ms}ms LLM -> {rp_ms}ms replay, {n} runs)  {sig[:48]}")
    if silent:
        print("\n  ⚠️ SILENT NON-HELP (task repeated but NEVER hit the fast path):")
        print("     a repeat that never replays = the skill thrashed or won't distill;")
        print("     it still completes, but the speed win never lands. Investigate.")
        for sig, n in sorted(silent, key=lambda x: -x[1]):
            print(f"    x{n}  {sig[:60]}")
    if not helped and not silent:
        print("  (no task repeated yet, so no replay measurement available)")

    if not skill_events:
        return
    # Lifecycle rollup + thrash detector (re-learn loops that never promote).
    kinds = Counter(e.get("kind") for e in skill_events)
    print("\n  lifecycle:", "  ".join(f"{k}={kinds[k]}" for k in
          ("learn", "edit", "promote", "quarantine", "demote", "compose", "invalidate") if kinds.get(k)))
    per = defaultdict(Counter)
    for e in skill_events:
        per[f"{e.get('host')}::{e.get('task_sig')}"][e.get("kind")] += 1
    thrash = [(k, c) for k, c in per.items() if c["learn"] + c["edit"] >= 2 and c["promote"] == 0]
    if thrash:
        print("\n  ⚠️ THRASH (re-learned/edited >=2x but NEVER promoted to trusted):")
        for k, c in thrash:
            print(f"    {k[:60]}  learn={c['learn']} edit={c['edit']} quarantine={c['quarantine']}")
    if kinds.get("compose"):
        print(f"\n  composition: {kinds['compose']} skill(s) built on a proven sub-skill, "
              f"{kinds.get('invalidate', 0)} dependent(s) re-proofed after a foundation changed")


def playbook_report(tasks):
    """Does the tier-2 strategy playbook actually make judgment tasks cheaper over
    time? Compare LLM-path runs on a host BEFORE a playbook existed (cold) vs once
    it was seeded. The win is fewer exploration turns; flag a host where seeded
    runs are NOT cheaper (the 'memory looks active but doesn't help' ghost)."""
    from collections import defaultdict
    by_host = defaultdict(lambda: {"cold": [], "seeded": []})
    for t in tasks:
        if t.get("path") not in ("llm", "llm_fallback") or not t.get("completed"):
            continue
        host = (t.get("task_sig") or "").split(" ")[0] or t.get("browser_id", "?")
        bucket = "seeded" if t.get("playbook_seeded") else "cold"
        by_host[host][bucket].append(t.get("turns", 0) or 0)
    rows = {h: v for h, v in by_host.items() if v["cold"] and v["seeded"]}
    if not any(t.get("playbook_seeded") for t in tasks):
        return  # nothing seeded yet, no measurement to make
    print("\n=== STRATEGIC PLAYBOOK (does learned site-strategy cut exploration?) ===")
    seeded_total = sum(1 for t in tasks if t.get("playbook_seeded"))
    print(f"  runs seeded with a playbook: {seeded_total}")
    if not rows:
        print("  (no host yet has BOTH a cold and a seeded run to compare)")
        return
    for h, v in rows.items():
        cold = sum(v["cold"]) / len(v["cold"])
        seeded = sum(v["seeded"]) / len(v["seeded"])
        verdict = "HELPS" if seeded < cold else "⚠️ NOT HELPING"
        print(f"    {h[:40]:40} cold avg {cold:.1f} turns -> seeded avg {seeded:.1f} turns  {verdict}")


def latency_report(tasks):
    """Where a run's time actually goes, and which part a code change can move.

    Live-site wall clocks swing 5-12x on model turn count alone, so a wall-clock A/B needs ~30 runs
    per arm to say anything at all. Split it: llm_ms is the model's, tools_ms is the browser's, and
    the remainder is OURS (perception, waits, dispatch, bookkeeping). The spread column is the point.
    If wall swings 8x while ours swings 1.4x, then ours is the only column worth optimising against,
    and any speed claim measured on the wall was measuring the model's mood.
    """
    runs = [t for t in tasks
            if t.get("completed") and t.get("llm_ms") and t.get("path") in ("llm", "llm_fallback")]
    print("\n=== WHERE THE TIME GOES (completed model-path runs) ===")
    if len(runs) < 2:
        old = sum(1 for t in tasks if "other_ms" not in t)
        noloop = sum(1 for t in tasks if t.get("other_ms") is not None and not t.get("llm_ms"))
        print(f"  {len(runs)} qualifying run(s); need at least 2. Skipped: {old} recorded before the "
              f"split existed, {noloop} that never called the model (a script or replay answered).")
        return
    cols = [("wall", "total_ms"), ("llm", "llm_ms"), ("browser", "tools_ms"), ("OURS", "other_ms")]
    print(f"  {'part':<9}{'median':>9}{'min':>9}{'max':>9}{'spread':>9}   share")
    med_total = statistics.median([r["total_ms"] for r in runs]) or 1
    for label, key in cols:
        vals = sorted(r.get(key, 0) for r in runs)
        med, lo, hi = statistics.median(vals), vals[0], vals[-1]
        spread = f"{hi / lo:.1f}x" if lo > 0 else "n/a"
        print(f"  {label:<9}{round(med):>8}ms{lo:>8}ms{hi:>8}ms{spread:>9}   {round(100 * med / med_total):>3}%")
    print(f"  n={len(runs)} runs. A change to our code can only move the OURS row; judge it there.")


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else _default_dir()
    events = load(os.path.join(d, "events.jsonl"))
    tasks = load(os.path.join(d, "tasks.jsonl"))
    skill_events = load(os.path.join(d, "skill_events.jsonl"))
    print(f"metrics dir: {d}")
    print(f"events: {len(events)}  tasks: {len(tasks)}  skill_events: {len(skill_events)}\n")
    if not tasks and not events:
        print("No metrics recorded yet. Run some browser-agent tasks first.")
        return

    ev_by_session = defaultdict(list)
    for e in events:
        ev_by_session[e.get("session_id")].append(e)

    # Per-tier rollup across all events
    tier_calls, tier_ms, tier_err = Counter(), Counter(), Counter()
    for e in events:
        t = e.get("tier", "other")
        tier_calls[t] += 1
        tier_ms[t] += int(e.get("elapsed_ms", 0) or 0)
        if not e.get("ok"):
            tier_err[t] += 1

    print("=== PER-TIER (across all tool calls) ===")
    print(f"{'tier':<20}{'calls':>6}{'avg_ms':>9}{'err%':>7}")
    for t in sorted(tier_calls, key=lambda x: -tier_calls[x]):
        c = tier_calls[t]
        avg = round(tier_ms[t] / c, 1) if c else 0
        errp = round(100 * tier_err[t] / c, 1) if c else 0
        print(f"{t:<20}{c:>6}{avg:>9}{errp:>6}%")

    print("\n=== PER-TASK (completion, time, cost, ghost check) ===")
    completed = ghosts = 0
    all_errs = Counter()
    for tk in tasks:
        evs = ev_by_session.get(tk.get("session_id"), [])
        is_ghost, reasons = ghost_verdict(tk, evs)
        if tk.get("status") == "completed":
            completed += 1
        if is_ghost:
            ghosts += 1
        for err, n in tk.get("recurring_errors", []):
            all_errs[err] += n
        flag = "  ⚠️ GHOST" if is_ghost else ""
        print(f"- [{tk.get('status')}] {tk.get('total_ms')}ms turns={tk.get('turns')} "
              f"tools={tk.get('tool_calls')} tok_in={tk.get('tokens_in')} "
              f"tok_out={tk.get('tokens_out')} :: {str(tk.get('task'))[:60]}{flag}")
        for r in reasons:
            print(f"      ghost-reason: {r}")

    print("\n=== RECURRING ERRORS (top 10 across tasks) ===")
    for err, n in all_errs.most_common(10):
        print(f"  x{n}  {err}")

    print("\n=== SUMMARY ===")
    n = len(tasks)
    print(f"tasks: {n}  completed: {completed}  ghost-completed: {ghosts}")
    if n:
        avg_ms = round(sum(t.get("total_ms", 0) for t in tasks) / n)
        avg_tok = round(sum(t.get("tokens_in", 0) + t.get("tokens_out", 0) for t in tasks) / n)
        print(f"avg task time: {avg_ms}ms   avg tokens/task: {avg_tok}")
        print(f"honest completion rate: {round(100*(completed-ghosts)/n,1)}% "
              f"(completed minus ghosts)")

    latency_report(tasks)
    skill_layer_report(tasks, skill_events)
    playbook_report(tasks)


if __name__ == "__main__":
    main()
