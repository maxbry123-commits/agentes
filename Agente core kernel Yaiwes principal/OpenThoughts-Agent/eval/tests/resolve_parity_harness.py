#!/usr/bin/env python
"""Stage-0 parity harness for the eval model-config decoupling refactor.

Enumerates every (model x cluster) pair and dumps the FULLY-RESOLVED serve outputs
  (EVAL_VLLM_* env dict, conda_env, agent_kwargs list)
from the ACTUAL listener resolvers, to a stable-sorted JSON "golden" snapshot.

This is the load-bearing byte-identity gate for the migration: Stages 2/3/4 re-run
this in `--check` mode and assert the resolved triple is byte-identical to the golden
for every pair. A later refactor (registry/loader) flips `--check` FAIL->PASS WITHOUT
editing this harness, because it imports the real listener functions, not a reimpl.

Design notes (see notes/ot-agent/stage0_parity_harness_scope.md):
  * 4 cluster shapes: leonardo (gpus_per_node 4 -> minimal.yaml), tacc (1 -> tacc file),
    tacc-65k (1 -> 65k file), jupiter (4 -> minimal.yaml via CLI). gpus_per_node is read
    from the ACTUAL cluster yaml (the plan doc said jupiter=8; the live file is 4 -
    anchors drift, so we read the file, not the doc).
  * Memoization: `_BASELINE_MODEL_CONFIGS` / `_BASELINE_MODEL_PATTERNS` are module globals
    memoized on first load; we RESET them between clusters or cluster 2+ silently reuses
    cluster 1's configs.
  * Absence is load-bearing: the golden records the env dict EXACTLY as the resolver
    returns it (no materialized defaults); a missing EVAL_VLLM_* key must stay missing so
    the build_vllm_cmd.sh sbatch default applies.
  * Hermeticity: `resolve_base_model_name` (Supabase) is stubbed to None so the run is
    deterministic and reproducible offline. Old AND new code call the same stub, so this
    does not weaken the parity comparison - it only removes a flaky network dependency.
    DCFT is pinned so os.path.expandvars on extra_args expands identically.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# --- repo root on sys.path + deterministic env BEFORE importing the listener ---
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
# Pin DCFT to a FIXED, location-independent sentinel so the nemotron entry's ${DCFT} in
# extra_args expands identically regardless of WHERE the harness runs (repo root vs a git
# worktree). Using the repo root made the golden path-dependent (a worktree checkout expands
# ${DCFT} to a different absolute path and spuriously fails --check); a stable sentinel keeps
# the resolved env byte-comparable everywhere. os.environ (not setdefault) so an inherited
# DCFT can't perturb the golden.
os.environ["DCFT"] = "/__DCFT__"

import yaml  # noqa: E402

import eval.unified_eval_listener as uel  # noqa: E402


# Cluster shapes. gpus_per_node is read from the cluster yaml.
#   baseline_file    -> the LEGACY load_baseline_model_configs path (Stage 0 / pre-migration).
#   registry_profile -> when set (incl. "" / "default"), this cluster resolves via the NEW
#                       load_model_registry(eval/configs/model_configs.yaml, profile) path
#                       (mirrors the post-migration listener); the golden is UNCHANGED, so
#                       --check still asserts byte-identity vs the Stage-0 legacy snapshot.
# jupiter has NO `baseline_model_configs:` pointer -> legacy loads minimal.yaml via the CLI flag.
# A cluster migrated to the registry sets registry_profile and ignores baseline_file.
_REGISTRY_PATH = "eval/configs/model_configs.yaml"
_CLUSTER_SHAPES = [
    # Stage 2: leonardo + jupiter flipped to the registry (no variant -> base entries).
    {
        "name": "leonardo",
        "cluster_yaml": "eval/clusters/leonardo.yaml",
        "baseline_file": "eval/configs/baseline_model_configs_minimal.yaml",
        "registry_profile": "default",
    },
    # Stage 3: tacc + tacc-65k flipped to the registry under the Vista hardware profiles
    # (gh200 / gh200-65k) — divergent models are flat name@<profile> standalone entries.
    {
        "name": "tacc",
        "cluster_yaml": "eval/clusters/tacc.yaml",
        "baseline_file": "eval/clusters/tacc_baseline_model_configs.yaml",
        "registry_profile": "gh200",
    },
    {
        "name": "tacc-65k",
        "cluster_yaml": "eval/clusters/tacc.yaml",
        "baseline_file": "eval/clusters/tacc_baseline_model_configs_65k.yaml",
        "registry_profile": "gh200-65k",
    },
    {
        "name": "jupiter",
        "cluster_yaml": "eval/clusters/jupiter.yaml",
        "baseline_file": "eval/configs/baseline_model_configs_minimal.yaml",
        "registry_profile": "default",
    },
]

# Synthetic names crafted to exercise EVERY pattern regex in the baseline files, regardless
# of which real models happen to be in the eval lists. Keyed so a coverage check can assert
# each pattern matched >= 1 sampled name.
_PATTERN_PROBE_NAMES = [
    "probe/qwen3.5-foo",  # minimal pattern: (?i)qwen3\.5
    "probe/qwen3.6-foo",  # (does NOT match qwen3\.5; lands on 32B? no -> catch-all/none)
    "probe/foo-32b-131k",  # minimal: (?i)(?:32b.*(131k|-lc)|(131k|-lc).*32b)
    "probe/131k-foo-32B",  # same combined pattern, other order
    "probe/some-32B-model",  # (?i)32[Bb]
    "probe/foo-131k",  # 131k|-lc$
    "probe/foo-lc",  # 131k|-lc$ (the -lc$ alternative)
    "probe/plain-7b-model",  # matches nothing in minimal; TACC catch-all .*
    "probe/another-random-model",  # TACC catch-all .*
]


def _load_eval_list_names() -> list[str]:
    """Every unique real HF model name referenced in eval/lists/*.txt (lines with a '/')."""
    names: set[str] = set()
    lists_dir = _REPO_ROOT / "eval" / "lists"
    for txt in sorted(lists_dir.glob("*.txt")):
        for raw in txt.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "/" not in line:
                continue
            names.add(line)
    return sorted(names)


def _gpus_per_node(cluster_yaml: str) -> int:
    data = yaml.safe_load((_REPO_ROOT / cluster_yaml).read_text()) or {}
    return int((data.get("hardware") or {}).get("gpus_per_node", 8) or 8)


def _reset_baseline_memo() -> None:
    uel._BASELINE_MODEL_CONFIGS = None
    uel._BASELINE_MODEL_PATTERNS = None


def _resolve_one(hf_model: str, configs: dict) -> dict:
    """Resolved serve triple for one model on the currently-set cluster, via the REAL resolvers."""
    return {
        "env": uel.get_vllm_env_overrides(hf_model, configs),
        "conda_env": uel.get_conda_env_override(hf_model, configs),
        "agent_kwargs": uel.get_baseline_agent_kwargs(hf_model, configs),
    }


def build_snapshot() -> dict:
    """Resolve every (model x cluster) pair into a stable-sorted nested dict."""
    # Hermetic + deterministic: no Supabase base-model lookups (offline-safe; identical old/new).
    uel.resolve_base_model_name = lambda hf_model: None  # type: ignore[assignment]
    # The size/family caches may already hold entries from a prior import; clear them.
    uel._BASE_MODEL_NAME_CACHE.clear()

    eval_list_names = _load_eval_list_names()

    snapshot: dict = {"_meta": {}, "clusters": {}}
    coverage: dict = {}

    for shape in _CLUSTER_SHAPES:
        cluster_name = shape["name"]
        gpn = _gpus_per_node(shape["cluster_yaml"])
        registry_profile = shape.get("registry_profile")
        baseline_file = shape["baseline_file"]
        # Set the ONLY cluster-config field the resolver chain reads (L608).
        uel._CLUSTER_CONFIG = {"hardware": {"gpus_per_node": gpn}}
        _reset_baseline_memo()
        if registry_profile is not None:
            # NEW path: shared registry + this cluster's hardware profile.
            profile = None if registry_profile == "default" else registry_profile
            configs = uel.load_model_registry(str(_REPO_ROOT / _REGISTRY_PATH), profile)
        else:
            # LEGACY path (untouched, authoritative pre-migration).
            configs = uel.load_baseline_model_configs(str(_REPO_ROOT / baseline_file))

        # Pair universe for this cluster: every exact/group entry + pattern probes + eval-list names.
        exact_names = sorted(configs.keys())
        all_names = sorted(
            set(exact_names) | set(_PATTERN_PROBE_NAMES) | set(eval_list_names)
        )

        resolved: dict = {}
        for name in all_names:
            resolved[name] = _resolve_one(name, configs)

        # Coverage: which patterns got exercised by >=1 sampled name.
        pats = uel._BASELINE_MODEL_PATTERNS or []
        pat_hits = {p.get("match", ""): 0 for p in pats}
        import re as _re

        for name in all_names:
            if name in configs:
                continue  # exact/group win -> doesn't exercise a pattern
            for p in pats:
                m = p.get("match", "")
                if m and _re.search(m, name):
                    pat_hits[m] += 1
                    break  # first-match-wins, mirror the resolver
        coverage[cluster_name] = {
            "gpus_per_node": gpn,
            "source": (
                f"registry[{registry_profile}]"
                if registry_profile is not None
                else f"legacy:{baseline_file}"
            ),
            "n_exact_entries": len(exact_names),
            "n_patterns": len(pats),
            "n_pairs_resolved": len(all_names),
            "pattern_hits": pat_hits,
        }
        snapshot["clusters"][cluster_name] = resolved

    snapshot["_meta"] = {
        "n_eval_list_names": len(eval_list_names),
        "n_pattern_probes": len(_PATTERN_PROBE_NAMES),
        "coverage": coverage,
    }
    return snapshot


def _canonical_json(obj: dict) -> str:
    """Stable, byte-deterministic JSON (sorted keys, fixed separators)."""
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _diff_resolved(golden: dict, current: dict) -> list[str]:
    """Per-(cluster, model, field/key) byte diffs between two snapshots' `clusters` blocks."""
    diffs: list[str] = []
    g_cl, c_cl = golden.get("clusters", {}), current.get("clusters", {})
    for cluster in sorted(set(g_cl) | set(c_cl)):
        g_models = g_cl.get(cluster, {})
        c_models = c_cl.get(cluster, {})
        for model in sorted(set(g_models) | set(c_models)):
            gm = g_models.get(model)
            cm = c_models.get(model)
            if gm is None:
                diffs.append(
                    f"[{cluster}] {model}: present in CURRENT, absent in GOLDEN"
                )
                continue
            if cm is None:
                diffs.append(
                    f"[{cluster}] {model}: present in GOLDEN, absent in CURRENT"
                )
                continue
            # conda_env / agent_kwargs
            for field in ("conda_env", "agent_kwargs"):
                if gm.get(field) != cm.get(field):
                    diffs.append(
                        f"[{cluster}] {model}.{field}: GOLDEN={gm.get(field)!r} CURRENT={cm.get(field)!r}"
                    )
            # env dict, including key ABSENCE (a key present in one and absent in the other is a diff)
            g_env, c_env = gm.get("env", {}), cm.get("env", {})
            for k in sorted(set(g_env) | set(c_env)):
                gv = g_env.get(k, "<ABSENT>")
                cv = c_env.get(k, "<ABSENT>")
                if gv != cv:
                    diffs.append(
                        f"[{cluster}] {model}.env[{k}]: GOLDEN={gv!r} CURRENT={cv!r}"
                    )
    return diffs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--write",
        metavar="PATH",
        help="resolve all pairs and WRITE the golden JSON here",
    )
    ap.add_argument(
        "--check",
        metavar="GOLDEN",
        help="resolve all pairs and DIFF against this golden; nonzero on any diff",
    )
    args = ap.parse_args()

    if not args.write and not args.check:
        ap.error("one of --write / --check is required")

    snapshot = build_snapshot()
    cov = snapshot["_meta"]["coverage"]

    # Coverage summary to stderr (always).
    total_pairs = sum(c["n_pairs_resolved"] for c in cov.values())
    print(
        f"== Stage-0 parity harness: {len(cov)} cluster shapes, {total_pairs} (model x cluster) pairs ==",
        file=sys.stderr,
    )
    for cl, c in cov.items():
        unhit = [m for m, n in c["pattern_hits"].items() if n == 0]
        print(
            f"  {cl}: gpus_per_node={c['gpus_per_node']} source={c['source']} "
            f"exact={c['n_exact_entries']} patterns={c['n_patterns']} pairs={c['n_pairs_resolved']} "
            f"pattern_hits={c['pattern_hits']}"
            + (f"  [UNEXERCISED PATTERNS: {unhit}]" if unhit else ""),
            file=sys.stderr,
        )

    if args.write:
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_canonical_json(snapshot))
        print(f"WROTE golden: {out} ({total_pairs} pairs)", file=sys.stderr)
        return 0

    # --check
    golden = json.loads(Path(args.check).read_text())
    diffs = _diff_resolved(golden, snapshot)
    if diffs:
        print(
            f"PARITY FAIL: {len(diffs)} byte-diff(s) vs {args.check}:", file=sys.stderr
        )
        for d in diffs:
            print(f"  {d}", file=sys.stderr)
        return 1
    print(
        f"PARITY OK: byte-identical vs {args.check} across {total_pairs} pairs.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
