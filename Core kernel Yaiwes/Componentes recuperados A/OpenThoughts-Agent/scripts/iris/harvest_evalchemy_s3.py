#!/usr/bin/env python3
"""Harvest evalchemy results and all artifacts from durable CoreWeave S3.

Reads runs from the LOTA object store (Mac-reachable external endpoint `cwobject.com`), saves
them locally under `./artifacts/<model>/<run>/…`, and prints harvested metrics. `--download`
is a complete run-artifact sync: result JSON, sample JSONL, logs, metadata, and any future
objects under the selected run prefix. This is the canonical harvester for the
marin-canonical-baseline-evals experiment — every value recorded in RESULTS.md is backed by
a file this script downloads.

WHAT IT EXTRACTS
  - tier1 (lm-eval-harness): gsm8k / mmlu / hellaswag / … accuracy per task
  - tier2 (evalchemy):       MATH500 · HumanEvalPlus · MBPPPlus · GPQADiamond · IFEval
  - AIME (3-seed policy):    per-seed 42/43/44 accuracy_avg -> mean ± pstdev.
                             §8 gate: ALL 3 seeds must be non-empty AND > 0; a seed == 0.0
                             across 42/43/44 = serve-death degeneration -> reported INVALID,
                             never recorded (LAUNCHER §7: a partial/degenerate is never a score).

CREDENTIALS (self-contained)
  Reads AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY from the in-cluster `iris-task-env` k8s Secret,
  so you do NOT pre-export AWS creds — but you MUST run with the East kubeconfig:
      export KUBECONFIG=~/.kube/coreweave-iris-gpu
  (CW/LOTA rejects path-style addressing -> we force virtual addressing on cwobject.com.)

USAGE
  export KUBECONFIG=~/.kube/coreweave-iris-gpu
  python scripts/iris/harvest_evalchemy_s3.py --list
  python scripts/iris/harvest_evalchemy_s3.py --model qwen-qwen3-30b-a3b-thinking-2507 --download
  python scripts/iris/harvest_evalchemy_s3.py --model <model-slug> --run <run-substring> --download

Model dirs are the s3-safe slugs (lower, '/' and '.' -> '-'), e.g. `qwen-qwen3-5-35b-a3b`,
`moonshotai-moonlight-16b-a3b-instruct`, `deepseek-ai-deepseek-v2-lite-chat`, `inclusionai-ling-lite`,
`penfever-grug-67b-a2b-sft-s2-thinking-step630`, `qwen-qwen3-next-80b-a3b-thinking`.
"""

import argparse
import json
import statistics as st
import sys
from pathlib import Path
from types import SimpleNamespace

from scripts.iris.coreweave_ops import CLUSTERS, kubectl_base, object_store_client

BUCKET = "marin-us-east-02a"
BASE = "iris/marinbase-eval/"
ENDPOINT = "https://cwobject.com"
DEFAULT_ARTIFACTS_DIR = (
    Path.home()
    / "Documents/experiments/complete/marin-canonical-baseline-evals/artifacts"
)
ART = DEFAULT_ARTIFACTS_DIR

INSCOPE = [
    "qwen-qwen3-5-35b-a3b",
    "qwen-qwen3-next-80b-a3b-thinking",
    "qwen-qwen3-30b-a3b-thinking-2507",
    "moonshotai-moonlight-16b-a3b-instruct",
    "deepseek-ai-deepseek-v2-lite-chat",
    "inclusionai-ling-lite",
    "penfever-grug-67b-a2b-sft-s2-thinking-step630",
]


def s3client():
    """Return the shared CoreWeave external object-store client.

    ``object_store_client`` reads the short-lived cluster secret without
    persisting it and uses cwobject.com's required virtual addressing.
    """
    cluster = CLUSTERS["cw-us-east-02a"]
    base = kubectl_base(cluster, SimpleNamespace(kubeconfig=None, kube_context=None))
    return object_store_client(base, cluster)


def listall(s3, prefix, delim=""):
    out, tok = [], None
    while True:
        kw = dict(Bucket=BUCKET, Prefix=prefix)
        if delim:
            kw["Delimiter"] = delim
        if tok:
            kw["ContinuationToken"] = tok
        r = s3.list_objects_v2(**kw)
        out += (
            [p["Prefix"] for p in r.get("CommonPrefixes", [])]
            if delim
            else [c["Key"] for c in r.get("Contents", [])]
        )
        if not r.get("IsTruncated"):
            return out
        tok = r["NextContinuationToken"]


def download(s3, key):
    dst = ART / key[len(BASE) :]
    dst.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(BUCKET, key, str(dst))
    return dst


def sync_run(s3, keys):
    """Mirror every S3 object from one selected run into the local artifact tree."""
    return {key: download(s3, key) for key in keys}


def task_metrics(d):
    """Pull the scored metric(s) from one evalchemy/lm-eval results_*.json."""
    out = {}
    for task, vals in (d.get("results", {}) or {}).items():
        if not isinstance(vals, dict):
            continue
        for mk, mv in vals.items():
            kl = mk.lower()
            if (
                isinstance(mv, (int, float))
                and "stderr" not in kl
                and any(
                    s in kl
                    for s in (
                        "accuracy_avg",
                        "exact_match",
                        "pass@1",
                        "prompt-level",
                        "prompt_level",
                        "acc,",
                        "acc_norm",
                        "accuracy",
                        "python_pass@1",
                    )
                )
            ):
                out[f"{task}:{mk}"] = round(mv, 4)
    return out


def harvest_aime(s3, run_prefix, do_download, downloaded_paths=None):
    """AIME 3-seed μ±σ from a run's AIME24_seed4{2,3,4}/…/results_*.json. Returns (str, valid)."""
    vals = {}
    for seed in (42, 43, 44):
        keys = [
            k
            for k in listall(s3, f"{run_prefix}AIME24_seed{seed}/")
            if "results_" in k and k.endswith(".json")
        ]
        if not keys:
            vals[seed] = None
            continue
        p = (downloaded_paths or {}).get(keys[0]) if do_download else None
        if do_download and p is None:
            p = download(s3, keys[0])
        if p:
            d = json.load(open(p))
        else:
            d = json.loads(s3.get_object(Bucket=BUCKET, Key=keys[0])["Body"].read())
        vals[seed] = round(
            d.get("results", {}).get("AIME24", {}).get("accuracy_avg", 0.0), 4
        )
    got = [v for v in vals.values() if v is not None]
    valid = len(got) == 3 and all(v > 0 for v in got)
    if valid:
        mu, sd = st.mean(got) * 100, st.pstdev(got) * 100
        return f"AIME24 = {mu:.1f} ±{sd:.1f} (3s)   seeds42/43/44={got}", True
    return (
        f"AIME24 INVALID (degenerate/partial) seeds42/43/44={[vals[s] for s in (42, 43, 44)]} — do NOT record",
        False,
    )


def main():
    ap = argparse.ArgumentParser(
        description="Harvest marin-canonical baseline eval results from durable s3."
    )
    ap.add_argument("--model", help="s3 model slug (dir under iris/marinbase-eval/)")
    ap.add_argument("--all", action="store_true", help="all in-scope models")
    ap.add_argument(
        "--run",
        default="",
        help="substring filter on run-dir name (e.g. aime3, t2-, tier1)",
    )
    ap.add_argument(
        "--aime", action="store_true", help="compute 3-seed AIME μ±σ for matching runs"
    )
    ap.add_argument(
        "--download", action="store_true", help="mirror every selected run artifact"
    )
    ap.add_argument(
        "--samples",
        action="store_true",
        help="deprecated compatibility alias for --download",
    )
    ap.add_argument("--list", action="store_true", help="list model dirs and exit")
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_ARTIFACTS_DIR,
        help=f"local artifact destination (default: {DEFAULT_ARTIFACTS_DIR})",
    )
    a = ap.parse_args()
    global ART
    ART = a.output_dir.expanduser().resolve()
    s3 = s3client()

    if a.list:
        for m in listall(s3, BASE, delim="/"):
            print(" ", m[len(BASE) : -1])
        return

    do_download = a.download or a.samples
    models = (
        INSCOPE
        if a.all
        else ([a.model] if a.model else sys.exit("give --model, --all, or --list"))
    )
    for m in models:
        runs = [
            r
            for r in listall(s3, f"{BASE}{m}/", delim="/")
            if a.run in r.split("/")[-2]
        ]
        if not runs:
            print(f"\n## {m}: (no runs match --run '{a.run}')")
            continue
        print(f"\n## {m}")
        for run in runs:
            rn = run.split("/")[-2]
            keys = listall(s3, run)
            downloaded_paths = sync_run(s3, keys) if do_download else {}
            if a.aime and "aime" in rn.lower():
                msg, _ = harvest_aime(s3, run, do_download, downloaded_paths)
                print(f"  {rn}: {msg}")
                continue
            got = {}
            for k in keys:
                if "results_" in k and k.endswith(".json"):
                    p = downloaded_paths.get(k)
                    d = (
                        json.load(open(p))
                        if p
                        else json.loads(
                            s3.get_object(Bucket=BUCKET, Key=k)["Body"].read()
                        )
                    )
                    got.update(task_metrics(d))
            if got:
                print(f"  {rn}:")
                for kk in sorted(got):
                    print(f"     {kk} = {got[kk]}")
    if do_download:
        print(f"\n[harvest] artifacts saved under {ART}/")


if __name__ == "__main__":
    main()
