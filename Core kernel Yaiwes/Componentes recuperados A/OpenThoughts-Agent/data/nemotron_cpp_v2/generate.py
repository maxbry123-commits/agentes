#!/usr/bin/env python3
"""Generate the snapshot-safe, oracle-validated nemotron-cpp-v2 Harbor dataset.

Pipeline (Stages 2+4 of datagen-create-task-dataset, fused because the oracle
gate is also the keep-filter):
  1. read DCAgent/exp_rpt_nemotron-cpp (5000 gzip-tar task rows)
  2. transform each task -> agent-linked test + gold header (data/nemotron_cpp_v2/transform.py)
  3. VALIDATE each transformed task LOCALLY under Docker (gcc:13+libgtest-dev):
       keep iff  gold(/app/<hdr>=header) -> reward 1  AND  empty(/app empty) -> reward 0
  4. assemble kept tasks into Harbor dirs (shared Dockerfile => 1 snapshot) and
     write them to --out-dir; optionally convert to parquet + upload to HF.

Usage:
  python -m data.nemotron_cpp_v2.generate --out-dir /tmp/nemo_v2_tasks \\
      [--limit N] [--workers 8] [--docker-image nemo-cpp-gtest:v2] \\
      [--target-repo laion/exp_rpt_nemotron-cpp-v2] [--no-upload]
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

from data.nemotron_cpp_v2 import templates as T
from data.nemotron_cpp_v2.transform import transform

SRC_REPO = "DCAgent/exp_rpt_nemotron-cpp"
PREFIX = "nemotron-cpp-v2"


# --------------------------------------------------------------------------
# source IO
# --------------------------------------------------------------------------
def _read_member(tf: tarfile.TarFile, suffix: str) -> str | None:
    for m in tf.getmembers():
        if m.name.endswith(suffix):
            f = tf.extractfile(m)
            return f.read().decode("utf-8", "replace") if f else None
    return None


def load_source() -> pd.DataFrame:
    p = hf_hub_download(SRC_REPO, "tasks.parquet", repo_type="dataset")
    return pd.read_parquet(p)


def extract_task(blob: bytes) -> tuple[str, str, str]:
    tf = tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz")
    instr = _read_member(tf, "instruction.md") or ""
    test = _read_member(tf, "test_solution.cpp") or ""
    meta = _read_member(tf, "metadata.json") or "{}"
    return instr, test, meta


# --------------------------------------------------------------------------
# local Docker validation (the oracle gate / keep-filter)
# --------------------------------------------------------------------------
def _docker_reward(
    image: str, new_test: str, hdr: str, header_content: str | None
) -> int:
    """Mirror tests/test.sh exactly. Return reward (0/1)."""
    with tempfile.TemporaryDirectory() as d:
        dd = Path(d)
        (dd / "tests").mkdir()
        (dd / "app").mkdir()
        (dd / "tests" / "test_solution.cpp").write_text(new_test)
        if header_content is not None:
            (dd / "app" / hdr).write_text(header_content)
        cmd = (
            "cd /work/app; "
            "g++ -std=c++17 -I/work/app -o /tmp/r /work/tests/test_solution.cpp "
            "-lgtest -lgtest_main -pthread 2>/work/cc.log || { echo R0_COMPILE; exit 0; }; "
            "/tmp/r --gtest_output=json:/work/g.json >/work/run.log 2>&1; "
            "python3 -c \"import json;d=json.load(open('/work/g.json'));"
            "t=int(d.get('tests',0));f=int(d.get('failures',0))+int(d.get('errors',0));"
            "print('R1' if (t>0 and f==0) else 'R0')\" 2>/dev/null || echo R0"
        )
        try:
            r = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{dd}:/work",
                    image,
                    "bash",
                    "-c",
                    cmd,
                ],
                capture_output=True,
                text=True,
                timeout=240,
            )
        except subprocess.TimeoutExpired:
            return 0
        return 1 if re.search(r"\bR1\b", r.stdout + r.stderr) else 0


def validate_task(image: str, art: dict) -> tuple[bool, str]:
    """Keep iff gold->1 AND empty->0."""
    gold = _docker_reward(image, art["new_test"], art["hdr"], art["header_src"])
    if gold != 1:
        return False, "gold_not_1"
    empty = _docker_reward(image, art["new_test"], art["hdr"], None)
    if empty != 0:
        return False, "empty_not_0"
    return True, "ok"


# --------------------------------------------------------------------------
# task-dir assembly
# --------------------------------------------------------------------------
def write_task_dir(
    out_root: Path, task_id: str, instr: str, meta_json: str, art: dict
) -> None:
    d = out_root / task_id
    (d / "environment").mkdir(parents=True, exist_ok=True)
    (d / "tests").mkdir(parents=True, exist_ok=True)
    (d / "solution").mkdir(parents=True, exist_ok=True)

    (d / "environment" / "Dockerfile").write_text(T.DOCKERFILE)
    (d / "task.toml").write_text(T.TASK_TOML)
    (d / "instruction.md").write_text(
        T.INSTRUCTION_PREAMBLE_TMPL.format(hdr=art["hdr"]) + instr
    )
    # metadata: carry source + mark v2
    try:
        meta = json.loads(meta_json)
    except Exception:
        meta = {}
    meta.update(
        {
            "dataset_version": "v2",
            "header": art["hdr"],
            "verifier": "agent-linked-gtest",
        }
    )
    (d / "metadata.json").write_text(json.dumps(meta, indent=2))

    (d / "tests" / "test_solution.cpp").write_text(art["new_test"])
    (d / "tests" / "test.sh").write_text(T.TEST_SH)
    (d / "tests" / "test_state.py").write_text(T.TEST_STATE_PY)
    (d / "tests" / "config.json").write_text(T.CONFIG_JSON)

    (d / "solution" / "solve.sh").write_text(
        T.render_solve_sh(art["hdr"], art["header_src"])
    )


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0, help="0 = all 5000")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--docker-image", default="nemo-cpp-gtest:v2")
    ap.add_argument("--target-repo", default="laion/exp_rpt_nemotron-cpp-v2")
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument(
        "--report", type=Path, default=None, help="write a JSON validation report here"
    )
    args = ap.parse_args()

    df = load_source()
    n = len(df) if args.limit <= 0 else min(args.limit, len(df))
    print(f"source rows: {len(df)}  processing: {n}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # transform all (cheap, in-process)
    jobs = []  # (task_id, instr, meta, art)
    skip_reasons: dict[str, int] = {}
    for i in range(n):
        instr, test, meta = extract_task(df.iloc[i]["task_binary"])
        art, why = transform(instr, test)
        if art is None:
            key = why.split(":")[0]
            skip_reasons[key] = skip_reasons.get(key, 0) + 1
            continue
        jobs.append((f"{PREFIX}-{i:06d}", instr, meta, art))
    print(
        f"transformed (structurally usable): {len(jobs)}  skipped: {dict(skip_reasons)}"
    )

    # validate in parallel under Docker (the oracle gate)
    kept = []
    fail_reasons: dict[str, int] = {}
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {
            ex.submit(validate_task, args.docker_image, art): (tid, instr, meta, art)
            for (tid, instr, meta, art) in jobs
        }
        for fut in as_completed(futs):
            tid, instr, meta, art = futs[fut]
            ok, why = fut.result()
            done += 1
            if ok:
                kept.append((tid, instr, meta, art))
            else:
                fail_reasons[why] = fail_reasons.get(why, 0) + 1
            if done % 100 == 0:
                print(f"  validated {done}/{len(jobs)}  kept={len(kept)}")

    print(
        f"\nKEPT (gold->1 AND empty->0): {len(kept)}/{len(jobs)}  "
        f"fail_reasons={dict(fail_reasons)}"
    )

    # assemble kept task dirs
    for tid, instr, meta, art in kept:
        write_task_dir(args.out_dir, tid, instr, meta, art)
    print(f"wrote {len(kept)} task dirs to {args.out_dir}")

    report = {
        "source_repo": SRC_REPO,
        "processed": n,
        "transformed": len(jobs),
        "skip_reasons": skip_reasons,
        "kept": len(kept),
        "fail_reasons": fail_reasons,
        "target_repo": args.target_repo,
    }
    if args.report:
        args.report.write_text(json.dumps(report, indent=2))

    # convert + upload
    if not args.no_upload and kept:
        from scripts.harbor import tasks_parquet_converter as tpc
        from huggingface_hub import HfApi

        tasks = tpc.find_tasks(args.out_dir, recursive=True)
        pq = args.out_dir.parent / "nemotron_cpp_v2.parquet"
        tpc.to_parquet(args.out_dir, pq, tasks, compression="gz")
        print(f"parquet: {pq} ({pq.stat().st_size / 1e6:.1f} MB, {len(tasks)} tasks)")
        api = HfApi()
        api.create_repo(args.target_repo, repo_type="dataset", exist_ok=True)
        api.upload_file(
            path_or_fileobj=str(pq),
            path_in_repo="tasks.parquet",
            repo_id=args.target_repo,
            repo_type="dataset",
        )
        print(f"uploaded -> https://huggingface.co/datasets/{args.target_repo}")

    print("\nDONE.", json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
