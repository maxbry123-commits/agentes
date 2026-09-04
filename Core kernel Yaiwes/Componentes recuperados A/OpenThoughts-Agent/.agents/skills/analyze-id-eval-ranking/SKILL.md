---
name: analyze-id-eval-ranking
description: >-
  Given a list of models (HF name stubs) that have valid agentic ID eval scores in Supabase,
  build a ranking table: raw per-benchmark accuracy on the 3 ID benchmarks (SWE-Bench-100,
  OT-TBLite=dev_set_v2, Terminal-Bench-2.0=tb2), HF links to each eval's trace dataset, and a
  NORMALIZED column = average per-benchmark z-score, ranked. Normalization matches the
  OpenThoughts-Agent paper (otagent-paper/02_arXiv/otagent.tex §Pipeline): per-benchmark z over
  the candidate set, averaged. Read-only. Use when asked to rank models / ablation arms by their
  ID evals the way the paper does.
---

# analyze-id-eval-ranking

Produce the paper's **ID ranking table** for an arbitrary set of models: raw scores on the three
in-distribution agentic benchmarks + HF trace links + a **normalized average z-score** column,
sorted by the normalized score. This reproduces the ranking method in
`otagent-paper/02_arXiv/otagent.tex` (§Pipeline / App. task-gen tables). **Read-only** — it never
writes Supabase.

## The three ID benchmarks (and their paper display names)

| paper name | Supabase `benchmarks.name` | task count `N` (for SE) |
|---|---|---|
| **SWE-Bench Verified (100)** | `swebench-verified-random-100-folders` | 100 |
| **OT-TBLite** | `dev_set_v2` (partial-credit) | — |
| **Terminal-Bench 2.0** | `terminal_bench_2` | 89 |

> ⚠ Mapping traps: **OT-TBLite IS `dev_set_v2`** (not a separate benchmark). **SWE-Bench-100 is the
> `-random-100-folders` subset, NOT full `swebench-verified`** (500, which is OOD). `terminal_bench_2`
> runs at `timeout_multiplier 2.0` → resolve its family + `dev_set_v2`'s family via `duplicate_of`
> (see `crud-otagent-supabase` §GOTCHA 2/3). `dev_set_v2` is partial-credit → its raw % still enters
> the mean and its z-score, but it has no clean binomial `N`.

## The normalization (must match the paper — otagent.tex §231)

> *"We compute the z-score of every candidate strategy's accuracy **across the stage's full candidate
> set** (subtracting the per-benchmark mean and dividing by its standard deviation), then average the
> three resulting per-benchmark z-scores."*

So, with the **candidate set = the input model list** (this is the population for mean/std — NOT a
global population):
1. For each benchmark `b`, over all candidate models with a score on `b`: `mean_b`, `std_b`.
2. `z[m,b] = (acc[m,b] − mean_b) / std_b`.
3. `normalized[m] = mean(z[m,b] over the 3 benchmarks the model has)`.
4. **Rank by `normalized` descending.**

`std` uses **population std (`ddof=0`, `numpy.std` default)** — the candidate set IS the full
population being compared. (Document this if you switch to sample std; it changes the magnitudes,
not the ordering, when all models have all 3 benchmarks.) Equal per-benchmark weight is the whole
point — don't weight by `N`.

## 0. Connect (read-only) + the model list

> **PREREQUISITE — read `.agents/skills/crud-otagent-supabase/SKILL.md` FIRST.** It is the source of
> truth for HOW to poll this Supabase and, critically, how to handle **duplicate / multiple candidate
> evals** for a (model, benchmark). This skill depends on it for four things:
> - **Connect + query** — `crud-otagent-supabase` §0 (local Mac, `otagent` env, `DC_AGENT_SECRET_ENV`,
>   service-role key for reads) and §Schema (`sandbox_jobs` = one row per model×benchmark eval;
>   `model_id`/`benchmark_id`/`metrics`/`stats`/`job_status`/`hf_traces_link`). PAGINATE (>1000 rows).
> - **`get_metric` shape-robust helper** (§GOTCHA 1) — `metrics` is list-OR-dict; NEVER index it
>   directly. Also pulls `accuracy_stderr` for the SE subscript.
> - **Duplicate/sibling pulls** (§GOTCHA 2) — the SAME model can have (a) multiple `sandbox_jobs`
>   rows per benchmark [a `Pending`/`Started` row AND a `Finished` row, or reruns], and (b) multiple
>   `models` rows [trainer auto-push + a manual `-<step>-<size>` row, or a duplicate]. So query models
>   by **`ilike` on a name stub, not exact match**, and UNION `sandbox_jobs` across all sibling
>   `model_id`s. And benchmark FAMILIES (§GOTCHA 3) resolve via `duplicate_of`.
> - **Which candidate eval to use when there are several** (§GOTCHA 2 rule 1 — the selection rule this
>   skill lives or dies by): keep only `Finished` rows with a non-null accuracy (`get_metric`);
>   **among ≥2 COMPLETE entries with IDENTICAL evaluation settings, AVERAGE them — do NOT pick max, do
>   NOT pick first.** Entries with DIFFERENT settings (a different `n_rep_eval` or harness) are NOT
>   "identical settings" → do not average across them; keep the canonical one (the terminus-2, n=3
>   ID-eval setting the paper uses). `crud-otagent-supabase`'s `get_model_scores()` recipe implements
>   exactly this union+average — mirror it.

**Input = a list of model name stubs.** Either passed directly, or derived from an experiment dir:
read its tracker (`~/Documents/experiments/*/<name>/*tracker*.md` / `DESIGN.md` / the HF-upload log)
for the model HF names/stubs that ablation produced (`laion/…`, `DCAgent*/…`, bare run-names).

## 1. Pull each model's 3 ID scores (sibling- + family-aware, averaged)

```python
import numpy as np
ID = {"swebench-verified-random-100-folders":"SWE-Bench-100",
      "dev_set_v2":"OT-TBLite", "terminal_bench_2":"Terminal-Bench-2.0"}

bm  = {b["id"]: b for b in c.table("benchmarks").select("id,name,duplicate_of").execute().data}
name2canon = {}                                  # benchmark name -> canonical ID-set name (via duplicate_of)
for b in bm.values():
    canon = b; seen=set()
    while canon.get("duplicate_of") and canon["duplicate_of"] in bm and canon["id"] not in seen:
        seen.add(canon["id"]); canon = bm[canon["duplicate_of"]]
    if canon["name"] in ID: name2canon[b["name"]] = canon["name"]
    if b["name"] in ID:     name2canon[b["name"]] = b["name"]

def id_scores(stub):
    """-> {canon_bench: {'acc':float,'se':float|None,'trace':url|None}} averaging Finished repeats."""
    mods = c.table("models").select("id,name").ilike("name", f"%{stub}%").execute().data   # sibling rows
    perb = {}                                          # canon bench -> list of (acc, se, trace)
    for m in mods:
        for j in c.table("sandbox_jobs").select("benchmark_id,metrics,job_status,hf_traces_link") \
                   .eq("model_id", m["id"]).execute().data:
            canon = name2canon.get(bm.get(j["benchmark_id"],{}).get("name"))
            if canon is None: continue                  # not one of the 3 ID benchmarks
            acc = get_metric(j["metrics"])
            if j["job_status"] != "Finished" or acc is None: continue   # real score only
            se  = get_metric(j["metrics"], "accuracy_stderr")
            perb.setdefault(canon, []).append((acc, se, j.get("hf_traces_link")))
    out = {}
    for canon, entries in perb.items():                # AVERAGE identical-setting complete repeats
        accs=[e[0] for e in entries]
        out[canon] = {"acc": sum(accs)/len(accs),
                      "se":  next((e[1] for e in entries if e[1] is not None), None),
                      "trace": next((e[2] for e in entries if e[2]), None)}   # first non-null trace link
    return out, mods

scores = {stub: id_scores(stub) for stub in MODEL_STUBS}
```

### 1a. Selecting the canonical eval when repeats are NOT identical-setting (load-bearing)

In practice a (model, benchmark) often has **several** Finished rows that are **not** identical-setting,
so the "average identical repeats" branch does NOT apply — you must pick the **canonical clean**
measurement (per `crud-otagent-supabase` §GOTCHA 2 rule 1's "different settings → keep the canonical
one"). Detect and EXCLUDE the non-canonical ones (validated grid-exact on the RL ablation, 2026-07-09):

- **Summarization-buggy (deflated) runs** — a run with non-trivial
  `stats.evals.*.exception_stats.SummarizationTimeoutError` scored lower because of the summarization
  bug, not the model. Drop it in favor of the post-fix clean run.
- **Degenerate broken-serving-batch runs** — an implausibly low value from all-zero-reward batches
  (e.g. `dev_set_v2` 1.0–1.7% when the clean grid value is ~12%). Drop.
- **Drifted eval generations** — the same clean setting re-run weeks apart can differ materially
  (e.g. `dev_set_v2` 20.5%@2026-06-29 vs 9.8%@2026-07-08). Do NOT average across generations; keep the
  study's **canonical measurement** (the earliest clean post-fix run, matching the experiment's
  `id_eval_grid.md` / `ABLATION_DEFINITIONS.md`). Averaging here would mix generations and desync from
  the grid.
- Always prefer the canonical harness setting (terminus-2, `timeout_multiplier=2.0`, n=3).

**Cross-check the result against the experiment's own grid** (`id_eval_grid.md` /
`COMPARISON_*.md`) — every ranked cell should reproduce it exactly; a mismatch means you picked a
non-canonical run. If the clean/canonical value the grid cites is **not present in `sandbox_jobs`**
(only superseded pre-fix rows exist), treat that benchmark as MISSING for §2 (flag it) rather than
substituting a deflated row.

## 2. Validity gate — flag models missing any ID benchmark

A model is **ID-valid** only if it has a Finished score on **all three** ID benchmarks. Report (do
NOT silently drop) any input model missing ≥1 — the normalization population must be the models that
actually have the benchmark (partial models distort `mean_b`/`std_b`). Decide explicitly: rank only
the fully-ID-complete models (default), and list the incomplete ones separately with their gaps.

## 3. Normalize + rank

```python
complete = {s:(sc,_m) for s,(sc,_m) in scores.items() if all(b in sc for b in ID)}
acc = {b: {s: complete[s][0][b]["acc"] for s in complete} for b in ID}      # per-benchmark accs
z   = {}
for b in ID:
    vals = np.array(list(acc[b].values()), float)
    mu, sd = vals.mean(), vals.std(ddof=0)                                  # population std
    z[b] = {s: (acc[b][s]-mu)/sd if sd>0 else 0.0 for s in acc[b]}
norm = {s: float(np.mean([z[b][s] for b in ID])) for s in complete}
raw  = {s: float(np.mean([acc[b][s] for b in ID])) for s in complete}
ranking = sorted(complete, key=lambda s: norm[s], reverse=True)
```

## 4. Emit the table

Columns (match the paper's layout): **Rank · Model · SWE-Bench-100 (%) · OT-TBLite (%) ·
Terminal-Bench-2.0 (%) · Raw avg (%) · Normalized (z) · Trace links**. Per-benchmark cell = raw
accuracy % (append `±SE` from `accuracy_stderr` when present). The **Trace links** column carries the
per-benchmark `hf_traces_link` URLs (swe / v2 / tb2) — the same field the leaderboard uses; a missing
link → note "—". Sort by `Normalized` desc; number the ranks.

- Emit **markdown** (and optionally a CSV alongside) to the experiment dir when run on one, e.g.
  `<experiment>/id_eval_ranking.md`. Also print a one-line summary (N models ranked, N flagged
  incomplete).
- Report `normalized` to 2 decimals with sign (e.g. `+0.49`, `−0.57`) like the paper; raw % to 2 dp.

## Guardrails

- **Read-only.** Never write Supabase. (For trace-link *repair*, that's `crud-otagent-supabase`
  §hf_traces_link — a different, write task.)
- **Population = the candidate set** (the input models), per-benchmark. Not a global mean. If the
  input list changes, the z-scores change — that is by design (relative ranking).
- **All three benchmarks equal weight** — average the z-scores, never weight by `N` or by raw range.
- **Averaging repeats:** average identical-setting Finished repeats; sibling-`models`-aware (`ilike`)
  + family-aware (`duplicate_of`) per `crud-otagent-supabase` §GOTCHA 2/3. Don't pick max/first.
- **Benchmark mapping:** OT-TBLite=`dev_set_v2`; SWE-Bench-100=`-random-100-folders` (NOT full 500);
  tb2=`terminal_bench_2`. Getting SWE wrong silently swaps an OOD benchmark into the ID ranking.
- **Flag, don't drop, incomplete models** — surface any input model lacking all 3 ID scores.

## Related

- **`crud-otagent-supabase`** — the schema, `get_metric`, sibling/family resolution, `hf_traces_link`,
  the ID/OOD master list. This skill is a read-only consumer of it.
- **`otagent-paper/02_arXiv/otagent.tex`** — the normalization source of truth (§Pipeline, App.
  task-gen full tables). Re-read if the method changes.
