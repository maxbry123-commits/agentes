#!/usr/bin/env python3
"""Build codenet-python **v3**: repopulate the test I/O dropped by the v1/v2
parquet -> tasks extraction.

Root cause
----------
``laion/exp_rpt_codenet-python-v2`` (and its predecessor
``DCAgent/exp_rpt_codenet-python``) ships every task with **zero-byte**
``tests/inputs/input_0.txt`` and ``tests/outputs/output_0.txt``.  The verifier
``tests/test.sh`` is correct -- it feeds ``/tests/inputs/input_*.txt`` to
``python3 /app/solution.py`` on stdin and diffs stdout against
``/tests/outputs/output_*.txt`` (whitespace-normalised) -- but with empty test
files the solution hits EOFError and never matches, so reward is always 0.

The genuine I/O still lives **inside each task's own ``instruction.md``**: the
CodeNet sample Input/Output example(s) were embedded verbatim when the
instruction was generated (CodeNet's judge test cases ARE the sample I/O from the
problem statement -- verified against ``windchimeran/codenet_python`` p00001).
The parquet->tasks extraction simply never wrote those bytes into the test files.

This script re-derives the test cases by parsing the embedded examples out of
``instruction.md`` (see ``extract_io.py``) and writes them into
``tests/inputs/input_<i>.txt`` / ``tests/outputs/output_<i>.txt`` for every task,
updating ``metadata.json``'s ``num_tests``.  Everything else in each task tar --
``environment/`` (the Daytona snapshot key), ``task.toml``, ``test.sh``,
``instruction.md`` -- is preserved BYTE-FOR-BYTE.

Output: a new ``tasks.parquet`` with the same ``(path, task_binary)`` schema,
ready to upload to ``laion/exp_rpt_codenet-python-v3``.

Idempotent / snapshot-safe: environment/ is never touched, so the unique-Dockerfile
(snapshot) count is identical to v2.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
import tarfile
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_io import extract_io_pairs  # noqa: E402


def _normalize(text: str) -> str:
    """Match test.sh's comparison: collapse all whitespace runs to single spaces,
    strip ends. We DON'T pre-normalize the stored files (we keep them readable),
    but we use this only for the empty-pair guard."""
    return " ".join(text.split())


def _build_solve_sh(code: str) -> bytes:
    """Oracle solve.sh: write the CodeNet reference solution to /app/solution.py
    (the path the verifier runs). Embedded via base64 so arbitrary code bytes survive
    the heredoc/quoting unscathed."""
    import base64

    b64 = base64.b64encode(code.encode("utf-8")).decode("ascii")
    script = (
        "#!/bin/bash\n"
        "set -e\n"
        "mkdir -p /app\n"
        f"echo {b64} | base64 -d > /app/solution.py\n"
    )
    return script.encode("utf-8")


def rebuild_task(
    path: str,
    task_binary: bytes,
    match: dict | None = None,
) -> tuple[bytes, int]:
    """Return (new_gzipped_tar, num_tests).

    If ``match`` is given (keys: input, output, code), use the authoritative CodeNet
    clean I/O as the single test case and write the reference ``code`` as the oracle
    ``solution/solve.sh``. Otherwise fall back to the instruction.md embedded examples.
    Every other member (environment/, task.toml, test.sh, instruction.md) is preserved
    byte-for-byte.
    """
    raw = gzip.decompress(task_binary)
    src = tarfile.open(fileobj=io.BytesIO(raw))

    members = src.getmembers()
    instr_member = next((m for m in members if m.name == "instruction.md"), None)
    if instr_member is None:
        raise ValueError(f"{path}: no instruction.md")
    instruction = src.extractfile(instr_member).read().decode("utf-8")

    if match is not None:
        pairs = [(match["input"], match["output"])]
        solve_sh = _build_solve_sh(match["code"])
    else:
        pairs = extract_io_pairs(instruction)
        solve_sh = None
    # Drop pairs whose normalized input AND output are both empty (junk).
    pairs = [(i, o) for (i, o) in pairs if (_normalize(i) or _normalize(o))]

    out_buf = io.BytesIO()
    dst = tarfile.open(fileobj=out_buf, mode="w")

    # Copy every member EXCEPT the stale tests/inputs/* and tests/outputs/* files
    # (and the inputs/outputs dirs, which we recreate). Preserve byte-for-byte.
    for m in members:
        name = m.name.lstrip("./")
        if name.startswith("tests/inputs/") and m.isfile():
            continue
        if name.startswith("tests/outputs/") and m.isfile():
            continue
        if name in ("tests/inputs", "tests/outputs"):
            continue  # recreate below
        if m.name in ("tests/inputs", "tests/outputs"):
            continue
        # When writing a fresh oracle, drop any stale solution/ members (recreated below).
        if solve_sh is not None and (
            name == "solution" or name.startswith("solution/")
        ):
            continue
        if m.isdir():
            dst.addfile(m)
            continue
        f = src.extractfile(m)
        data = f.read() if f else b""
        # metadata.json: update num_tests to match the repopulated cases
        if name == "metadata.json":
            try:
                meta = json.loads(data.decode("utf-8"))
                meta["num_tests"] = len(pairs)
                if match is not None and match.get("problem_id"):
                    # Restore the CodeNet problem_id that the v1/v2 extraction dropped.
                    meta["problem_id"] = match["problem_id"]
                data = (json.dumps(meta, indent=2) + "\n").encode("utf-8")
            except Exception:
                pass
        info = tarfile.TarInfo(name=m.name)
        info.size = len(data)
        info.mode = m.mode
        info.mtime = m.mtime
        info.type = m.type
        info.uid, info.gid = m.uid, m.gid
        info.uname, info.gname = m.uname, m.gname
        dst.addfile(info, io.BytesIO(data))

    # (Re)create tests/inputs and tests/outputs dirs + the populated test files.
    for d in ("tests/inputs", "tests/outputs"):
        di = tarfile.TarInfo(name=d)
        di.type = tarfile.DIRTYPE
        di.mode = 0o755
        di.mtime = int(time.time())
        dst.addfile(di)

    for i, (inp, out) in enumerate(pairs):
        # Store a trailing newline (typical of competitive-programming I/O files);
        # test.sh normalises whitespace so this is cosmetic but matches convention.
        in_bytes = (inp if inp.endswith("\n") else inp + "\n").encode("utf-8")
        out_bytes = (out if out.endswith("\n") else out + "\n").encode("utf-8")
        for sub, payload in (("inputs", in_bytes), ("outputs", out_bytes)):
            kind = "input" if sub == "inputs" else "output"
            ti = tarfile.TarInfo(name=f"tests/{sub}/{kind}_{i}.txt")
            ti.size = len(payload)
            ti.mode = 0o644
            ti.mtime = int(time.time())
            dst.addfile(ti, io.BytesIO(payload))

    # Oracle solution (matched-CodeNet mode only).
    if solve_sh is not None:
        sd = tarfile.TarInfo(name="solution")
        sd.type = tarfile.DIRTYPE
        sd.mode = 0o755
        sd.mtime = int(time.time())
        dst.addfile(sd)
        si = tarfile.TarInfo(name="solution/solve.sh")
        si.size = len(solve_sh)
        si.mode = 0o755
        si.mtime = int(time.time())
        dst.addfile(si, io.BytesIO(solve_sh))

    dst.close()
    return gzip.compress(out_buf.getvalue()), len(pairs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_parquet", required=True)
    ap.add_argument("--out_parquet", required=True)
    ap.add_argument("--limit", type=int, default=0, help="process first N (0 = all)")
    ap.add_argument(
        "--drop_empty",
        action="store_true",
        help="drop tasks with no usable test case (recommended with --match_map)",
    )
    ap.add_argument(
        "--match_map",
        default=None,
        help="parquet from match_codenet.py (path, problem_id, sim, input, output, code). "
        "When set, tasks with sim>=--min_sim get authoritative CodeNet clean I/O + a "
        "reference-code oracle; others fall back to embedded-example extraction.",
    )
    ap.add_argument("--min_sim", type=float, default=0.7)
    args = ap.parse_args()

    df = pd.read_parquet(args.in_parquet)
    if args.limit:
        df = df.iloc[: args.limit]

    match_by_path: dict[str, dict] = {}
    if args.match_map:
        mm = pd.read_parquet(args.match_map)
        for _, r in mm.iterrows():
            if float(r["sim"]) >= args.min_sim:
                match_by_path[r["path"]] = {
                    "input": r["input"],
                    "output": r["output"],
                    "code": r["code"],
                    "problem_id": r["problem_id"],
                }
        print(f"loaded {len(match_by_path)} confident matches (sim>={args.min_sim})")

    rows = []
    n_zero = 0
    n_matched = 0
    dist = {}
    for idx in range(len(df)):
        row = df.iloc[idx]
        path = row["path"]
        match = match_by_path.get(path)
        if match is not None:
            n_matched += 1
        new_bin, num_tests = rebuild_task(path, row["task_binary"], match=match)
        dist[num_tests] = dist.get(num_tests, 0) + 1
        if num_tests == 0:
            n_zero += 1
            if args.drop_empty:
                continue
        rows.append({"path": path, "task_binary": new_bin})
        if (idx + 1) % 1000 == 0:
            print(
                f"[{idx + 1}/{len(df)}] kept={len(rows)} matched={n_matched} zero_io={n_zero}",
                flush=True,
            )

    out_df = pd.DataFrame(rows)
    Path(args.out_parquet).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(args.out_parquet, index=False)
    print(
        f"DONE. in={len(df)} out={len(out_df)} matched={n_matched} zero_io={n_zero} "
        f"drop_empty={args.drop_empty}"
    )
    print("num_tests distribution:", dict(sorted(dist.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
