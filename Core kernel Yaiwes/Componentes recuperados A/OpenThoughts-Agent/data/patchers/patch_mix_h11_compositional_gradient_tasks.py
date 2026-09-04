#!/usr/bin/env python3
"""
Patch ``DCAgent/mix_h11_compositional_gradient`` for a corpus-wide verifier
defect that masks the model's true solve rate.

Triage findings (200-trial QC pass, 2026-05-14 → 2026-05-15)
============================================================

Reported headline: 200 trials, 100% infra-ok (Docker build succeeds for every
task), but only 11.0% solved — by far the lowest solve in this batch. The
"100% infra-ok" number is misleading because the breakage moved one layer
downstream: every task builds, the agent runs, but **the verifier itself is
broken for ~64% of the corpus** so the reward is forced to 0 regardless of
what the agent did.

Categorised verifier outcomes across the 200 sampled trials:

    75   verifier ran but `pytest /tests/test_solution.py` returned
         ``file or directory not found`` — the test file in the tar is named
         ``tests/test_2skill.py`` or ``tests/test_3skill.py`` (matches the
         ``n_skills`` field in metadata) yet ``tests/test.sh`` hard-codes
         the ``test_solution.py`` filename.
    52   verifier ran a stdin/stdout test loop over ``/tests/inputs/input_*.txt``
         and reported ``Results: 0/0 passed`` because no ``inputs/`` directory
         exists in the tar at all. Source family is exclusively
         ``codenet-python``.
    22   PASSED (true solves, mostly stack-pytest / pymethods2test layouts).
    14   ``ImportError while importing test module ... ModuleNotFoundError: No
         module named '<X>'`` where ``<X>`` is the upstream library name
         (e.g. ``bottle_song``). The pytest test imports a non-``solution``
         module but the instruction.md told the agent to "place your solution
         in /app/" with no library-naming hint. These are an instruction
         issue we do NOT fix in v2.
    13   Some tests pass, some fail (real algo bugs — agent's fault).
    10   ``ModuleNotFoundError: No module named 'solution'`` — agent did not
         create a ``solution.py``. Real agent failures.
    5    Real assertion failures.
    4    CrossCodeEval ``test_solution_imports``/``test_solution_not_empty``
         both fail (often because the upstream snippet needs a system lib
         missing from the python:3.10-slim base, e.g. ``libtk8.6.so``).
    3    Other / SyntaxError in the test fixture (e.g. a stray ``` fence
         inside test_solution.py from upstream).

Full-corpus structural defect inventory (3873 rows total, layout pivot on
``tests/{test_solution.py, test_2skill.py, test_3skill.py, inputs/}`` × what
``tests/test.sh`` actually invokes):

    1409  test_solution.py + sh runs pytest /tests/test_solution.py  ── CORRECT
     893  test_2skill.py   + sh runs pytest /tests/test_solution.py  ── BROKEN A
     571  test_3skill.py   + sh runs pytest /tests/test_solution.py  ── BROKEN A
     537  (no test file)   + sh runs stdin/stdout loop over inputs/   ── BROKEN B
     258  test_2skill.py   + sh runs stdin/stdout loop over inputs/   ── BROKEN C
     205  test_3skill.py   + sh runs stdin/stdout loop over inputs/   ── BROKEN C

Total broken: 2464 / 3873 = 63.6% of the corpus. The 11% solve rate the
model achieved is on the 1409 healthy tasks plus a handful of true solves
that snuck through (e.g. when a stdin/stdout task happens to also pass an
empty inputs loop — exits 0 → reward 1 in some sh variants).

Why we don't / can't fix BROKEN B
----------------------------------

The 537 "no test file" cases are all ``codenet-python`` rows that ship a
``tests/test.sh`` whose body is a ``for input_file in /tests/inputs/input_*.txt``
loop. The ``inputs/`` and ``outputs/`` dirs are absent from the
mix_h11 tar. The plausible upstream
(``DCAgent/exp_rpt_codenet-python``) does ship the directory structure but
**every file inside is 0 bytes** — the dataset itself has empty inputs/outputs
fixtures. We cannot reconstruct test data from upstream. These 537 tasks are
fundamentally unverifiable in the current dataset state and are reported but
NOT modified by this patcher. The right long-term fix is to drop them from
the mix or re-curate them from a different source. We leave them alone in v2
so the snapshot identity stays stable; their reward will remain 0 (or 1 by
accident — the original sh exits 0 if TOTAL==0, but reads PASSED=0/TOTAL=0
and writes ``0`` to reward.txt — so they reliably score 0 already).

What this patcher fixes
-----------------------

**BROKEN A** (1464 tasks): ``tests/test.sh`` runs ``pytest /tests/test_solution.py``
but the actual test file in the tar is ``tests/test_2skill.py`` or
``tests/test_3skill.py``. We rewrite the pytest target in test.sh to point
at the actual test file present.

**BROKEN C** (463 tasks): ``tests/test.sh`` is a stdin/stdout test loop but the
tar also contains ``tests/test_2skill.py`` or ``tests/test_3skill.py``. The
stdin/stdout loop will trivially report ``0/0 passed`` because no inputs
exist. We overwrite test.sh with a pytest-invoking variant that runs the
present test file. The ``inputs/`` loop is replaced; we lose nothing because
that loop was structurally non-functional.

Both fixes are local to ``tests/test.sh`` only. ``environment/Dockerfile``,
``instruction.md``, ``metadata.json``, ``task.toml``, and the test fixture
files themselves are untouched.

Snapshot accounting (Daytona caps: max_new_snapshots=10, max_org_snapshots=60)
-----------------------------------------------------------------------------

The source corpus has 4 distinct ``environment/Dockerfile`` byte-images
(3 minimal variants + 1 CrossCodeEval variant with apt-get git). We do NOT
modify any Dockerfile, so the Daytona env-hash set for this dataset stays
at exactly 4 snapshots — well under both caps. The patch is entirely
out-of-band of the build context.

Idempotency
-----------

Each rewritten ``tests/test.sh`` carries the marker
``# --- laion v2 patch: mix_h11 sh-pytest-target ---``
on its first non-shebang line. ``patch_task_files`` skips tasks whose
test.sh already contains this marker (re-runs are safe).

Usage
-----

    # Dataset mode (download v2 parquet, patch in memory, upload as v2 to
    # laion/mix_h11_compositional_gradient-v2):
    python data/patchers/patch_mix_h11_compositional_gradient_tasks.py \\
        --src-dataset DCAgent/mix_h11_compositional_gradient \\
        --dst-dataset laion/mix_h11_compositional_gradient-v2

    # Dry run (no writes, no upload):
    python data/patchers/patch_mix_h11_compositional_gradient_tasks.py \\
        --src-dataset DCAgent/mix_h11_compositional_gradient \\
        --dry-run

    # Local parquet round-trip (skip upload):
    python data/patchers/patch_mix_h11_compositional_gradient_tasks.py \\
        --src-parquet /tmp/in.parquet \\
        --dst-parquet /tmp/out.parquet \\
        --no-upload
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tarfile
from pathlib import Path


# --------------------------------------------------------------------------- #
# Marker (idempotency)
# --------------------------------------------------------------------------- #

PATCH_MARKER = "# --- laion v2 patch: mix_h11 sh-pytest-target ---"


# --------------------------------------------------------------------------- #
# New test.sh body. We mirror the structure of the upstream pytest test.sh
# (whitelist deps install, mkdir /logs/verifier, trap-based reward.txt write,
# pytest invocation) but parameterise the test-file basename so the same sh
# works for test_solution.py / test_2skill.py / test_3skill.py.
#
# Generated at patch time with the chosen basename substituted into
# {TEST_FILE} (no f-string interpolation at runtime so the literal $()
# bash substitutions survive).
# --------------------------------------------------------------------------- #

NEW_TEST_SH_TEMPLATE = """#!/bin/bash
{MARKER}
# v2 verifier: pytest runner targeting {TEST_FILE} (the test file that
# actually ships in this task's tar). Mirrors the upstream pytest-runner
# layout but with the correct filename.
set -e

mkdir -p /logs/verifier

cleanup() {{
    if [ $? -eq 0 ]; then
        echo "1" > /logs/verifier/reward.txt
    else
        echo "0" > /logs/verifier/reward.txt
    fi
}}
trap cleanup EXIT

cd /app
export PYTHONPATH="/app:${{PYTHONPATH:-}}"

# Setup
pip3 install --quiet pytest 2>/dev/null || true

echo "Running tests..."
# Install whitelisted test dependencies (not agent-created packages).
WHITELIST="requests numpy pandas scipy scikit-learn sklearn torch tensorflow keras httpx aiohttp ddtrace django flask fastapi matplotlib seaborn pillow pydantic pytest-mock requests-mock faker pyyaml pytz cryptography bcrypt hypothesis"
for pkg in $WHITELIST; do
    python3 -c "import ${{pkg//-/_}}" 2>/dev/null || pip install --quiet "$pkg" 2>/dev/null || true
done

pytest /tests/{TEST_FILE} -v --tb=short --timeout=120 2>&1 | tee /logs/verifier/test_output.txt

exit ${{PIPESTATUS[0]}}
"""


def _build_test_sh(test_file_basename: str) -> str:
    """Render the v2 test.sh for a given pytest test-file basename."""
    return NEW_TEST_SH_TEMPLATE.format(
        MARKER=PATCH_MARKER, TEST_FILE=test_file_basename
    )


# --------------------------------------------------------------------------- #
# Per-task patch (operates on a dict of {filename: bytes})
# --------------------------------------------------------------------------- #


def _pick_pytest_target(files: dict[str, bytes]) -> str | None:
    """Return the test-file basename to point pytest at, or None.

    Preference order:
        tests/test_solution.py  ── prefer if present
        tests/test_2skill.py
        tests/test_3skill.py

    None means no pytest test file is present (and we can't construct a
    pytest sh that would do anything useful — handled separately).
    """
    for candidate in ("test_solution.py", "test_2skill.py", "test_3skill.py"):
        if f"tests/{candidate}" in files:
            return candidate
    return None


_PYTEST_SOL_RE = re.compile(
    r"pytest\s+/tests/test_solution\.py",
)


def patch_task_files(files: dict[str, bytes]) -> tuple[dict[str, bytes], str]:
    """Apply the v2 mutation to a dict of {arcname: bytes}.

    Returns (new_files_dict, reason). The reason classifies the task so the
    main loop can summarise.
    """
    out = dict(files)

    sh_key = "tests/test.sh"
    if sh_key not in out:
        return out, "skipped_no_test_sh"

    existing_sh = out[sh_key].decode("utf-8", errors="replace")
    if PATCH_MARKER in existing_sh:
        return out, "skipped_already_patched"

    target = _pick_pytest_target(out)

    if target is None:
        # No pytest test file at all (the codenet-python n_skills=1 stdin/stdout
        # case). We cannot construct a meaningful pytest verifier without
        # inputs/outputs, and the upstream codenet dataset has them empty too.
        # Leave the task alone — its existing sh will still report 0/0 passed
        # → reward 0, same as before.
        return out, "skipped_no_pytest_file_unrecoverable"

    # Decide whether the existing sh is the type we want to rewrite. It is
    # broken if either:
    #   (a) it runs `pytest /tests/test_solution.py` but the actual test file
    #       in the tar is test_2skill.py or test_3skill.py, OR
    #   (b) it runs a stdin/stdout inputs/ loop but a pytest test file is
    #       present (n_skills>=2 codenet-python where the curator added a
    #       pytest test file but forgot to swap the sh).
    if target == "test_solution.py":
        # Test file matches what the sh already targets. Only rewrite if the
        # sh doesn't actually run pytest test_solution.py — i.e. inputs/ loop
        # type. (Stack-pytest etc. already correctly run pytest test_solution.py.)
        if "pytest /tests/test_solution.py" in existing_sh:
            return out, "skipped_already_correct"
        # Else: the sh is the inputs-loop variant and we should swap to pytest.
        new_sh = _build_test_sh("test_solution.py")
        out[sh_key] = new_sh.encode("utf-8")
        return out, "patched_inputs_loop_to_pytest_solution"

    # target is test_2skill.py or test_3skill.py.
    if _PYTEST_SOL_RE.search(existing_sh):
        # BROKEN A: sh runs pytest test_solution.py but we have test_Nskill.py.
        new_sh = _build_test_sh(target)
        out[sh_key] = new_sh.encode("utf-8")
        return out, f"patched_pytest_target_to_{target}"

    if "/tests/inputs/input_" in existing_sh:
        # BROKEN C: sh runs inputs loop but we have a pytest n_skill file.
        new_sh = _build_test_sh(target)
        out[sh_key] = new_sh.encode("utf-8")
        return out, f"patched_inputs_loop_to_{target}"

    # Some other layout we didn't anticipate. Leave untouched.
    return out, "skipped_unexpected_sh_shape"


# --------------------------------------------------------------------------- #
# Tar I/O helpers (mirrors patch_exp_rpt_crosscodeeval_csharp_v3_tasks.py)
# --------------------------------------------------------------------------- #


def _tar_to_dict(archive_bytes: bytes) -> dict[str, bytes]:
    """Unpack a (gzipped) tar archive to {name: file_bytes}. Skips dirs."""
    buf = io.BytesIO(archive_bytes)
    out: dict[str, bytes] = {}
    with tarfile.open(fileobj=buf, mode="r:*") as tf:
        for m in tf.getmembers():
            if m.isfile():
                f = tf.extractfile(m)
                if f is None:
                    continue
                out[m.name] = f.read()
    return out


def _dict_to_tar_gz(files: dict[str, bytes]) -> bytes:
    """Pack a {name: bytes} dict into a gzipped tar archive.

    Emits explicit DIRTYPE entries for parent dirs (matches the v1 layout
    which the Harbor task loader relies on for its `environment/` and
    `tests/` directory discovery).
    """
    dirs: set[str] = set()
    for name in files:
        parts = name.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]))

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for d in sorted(dirs):
            info = tarfile.TarInfo(name=d)
            info.type = tarfile.DIRTYPE
            info.size = 0
            info.mode = 0o755
            tf.addfile(info)
        for name in sorted(files.keys()):
            data = files[name]
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            info.mode = 0o755 if name.endswith(".sh") else 0o644
            info.type = tarfile.REGTYPE
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Dataset-mode (HF parquet round-trip)
# --------------------------------------------------------------------------- #


def patch_parquet(
    src_path: Path,
    dst_path: Path,
    limit: int = 0,
    dry_run: bool = False,
) -> dict[str, int]:
    """Read the v1 parquet, patch each task in memory, write the v2 parquet."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as e:
        raise RuntimeError(
            "pyarrow required for parquet mode: pip install pyarrow"
        ) from e

    src_path = Path(src_path)
    dst_path = Path(dst_path)
    table = pq.read_table(src_path)
    rows = table.to_pylist()
    if limit:
        rows = rows[:limit]

    reasons: dict[str, int] = {}
    new_paths: list[str] = []
    new_binaries: list[bytes] = []

    for i, row in enumerate(rows):
        path = row["path"]
        archive = row["task_binary"]
        files = _tar_to_dict(archive)
        new_files, reason = patch_task_files(files)
        reasons[reason] = reasons.get(reason, 0) + 1
        if dry_run:
            continue
        # Always re-emit the row (patched or not) so the v2 parquet is a
        # superset/exact-replacement of v1. We re-tar even when unchanged
        # so the output is uniform; downstream consumers don't have to
        # special-case partial coverage.
        new_archive = _dict_to_tar_gz(new_files)
        new_paths.append(path)
        new_binaries.append(new_archive)
        if (i + 1) % 200 == 0 or i + 1 == len(rows):
            print(f"[{i + 1}/{len(rows)}] last_reason={reason}", flush=True)

    if not dry_run:
        new_table = pa.table(
            {
                "path": pa.array(new_paths, type=pa.string()),
                "task_binary": pa.array(new_binaries, type=pa.binary()),
            }
        )
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(new_table, str(dst_path))

    return reasons


def fetch_from_hf(repo_id: str, filename: str = "tasks.parquet") -> Path:
    """Download the parquet from HF and return its local path."""
    from huggingface_hub import hf_hub_download

    local_path = hf_hub_download(
        repo_id=repo_id, filename=filename, repo_type="dataset"
    )
    return Path(local_path)


def upload_to_hf(repo_id: str, parquet_path: Path) -> None:
    """Create (if needed) the dataset repo and upload tasks.parquet."""
    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
    api.upload_file(
        path_or_fileobj=str(parquet_path),
        path_in_repo="tasks.parquet",
        repo_id=repo_id,
        repo_type="dataset",
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--src-dataset",
        help=(
            "HF dataset id with v1 tasks.parquet "
            "(e.g. DCAgent/mix_h11_compositional_gradient)"
        ),
    )
    p.add_argument(
        "--dst-dataset",
        help=(
            "HF dataset id to upload v2 to "
            "(e.g. laion/mix_h11_compositional_gradient-v2)"
        ),
    )
    p.add_argument(
        "--src-parquet",
        help="Local path to v1 tasks.parquet (alternative to --src-dataset)",
    )
    p.add_argument(
        "--dst-parquet",
        help="Local path to write v2 tasks.parquet (default ./tasks_v2.parquet)",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument(
        "--no-upload",
        action="store_true",
        help="Write the local v2 parquet but skip the HF upload step.",
    )
    args = p.parse_args()

    if not args.src_dataset and not args.src_parquet:
        print("Need --src-dataset or --src-parquet.", file=sys.stderr)
        return 2

    if args.src_parquet:
        src = Path(args.src_parquet).expanduser().resolve()
    else:
        print(f"Downloading {args.src_dataset} from HF ...", flush=True)
        src = fetch_from_hf(args.src_dataset)

    dst = (
        Path(args.dst_parquet).expanduser().resolve()
        if args.dst_parquet
        else Path("./tasks_v2.parquet").resolve()
    )

    print(f"Patching {src} -> {dst} ...", flush=True)
    reasons = patch_parquet(src, dst, limit=args.limit, dry_run=args.dry_run)
    print("Reason breakdown:")
    for r, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>5}  {r}")

    if args.dry_run or args.no_upload:
        return 0
    if args.dst_dataset:
        print(f"Uploading {dst} -> {args.dst_dataset} ...", flush=True)
        upload_to_hf(args.dst_dataset, dst)
        print("Upload complete.")
    else:
        print("(No --dst-dataset given; skipping upload.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
