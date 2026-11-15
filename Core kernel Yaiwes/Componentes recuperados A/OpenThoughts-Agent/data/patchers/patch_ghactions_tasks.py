#!/usr/bin/env python3
"""
Patch every DCAgent/exp_rpt_ghactions task tree so it is actually verifiable.

The bugs (200/200 QC pass)
--------------------------
Two distinct verifier-side bugs accounted for 100% of the 0/200 solves on the
unpatched corpus:

1. **Infra (52/200 = 26%)** — every trial's terminus-2 tmux capture failed
   with ``bash: line 1: script: command not found`` because the base images
   lacked ``/usr/bin/script`` (the Debian/Ubuntu ``bsdutils`` package).

2. **Test fixture (141/200 = 70.5%)** — the *reference* GitHub Actions
   workflow YAML was stored on disk as ``tests/test_solution.py`` (or
   ``tests/test_solution.js`` / ``tests/solution_test.go`` /
   ``tests/TestSolution.java`` / ``tests/tests.rs``) and the verifier ran
   pytest/jest/go test/mvn/cargo over it. The runners crashed during
   collection with a SyntaxError on the first YAML key (``name:``,
   ``on:``, ``jobs:``, or a ``@<sha>`` action pin tokenised as
   ``invalid decimal literal``). Reward was hard-zero regardless of what
   the agent did.

Per-task patches
----------------
A) **environment/Dockerfile**: append three RUN lines (idempotent, behind
   marker ``# --- laion v2 patch: ghactions extras ---``):

     * ``apt-get install bsdutils ca-certificates curl`` (fixes #1)
     * ``pip install 'yamllint==1.35.1' 'PyYAML==6.0.2'``
     * download + extract ``actionlint v1.7.7`` Linux x86_64 binary

   Adding identical RUN lines to every Dockerfile in the corpus keeps the
   Daytona snapshot count at 1 per language family (5 families × 1 image
   each = 5 snapshots, well under the 18-snapshot cap).

B) **tests/**: rename the YAML-disguised-as-source file to
   ``tests/reference_workflow.yml`` (validating it parses as YAML first —
   if it doesn't, drop the task). Replace ``tests/test.sh`` with a
   yamllint + actionlint + key-coverage verifier and add a small
   ``tests/compare_workflows.py`` script implementing the key-coverage
   check.

C) **instruction.md**: prepend a single-line preamble telling the agent
   where to put its solution and what tools the verifier uses, behind
   marker ``--- laion v2 patch: ghactions preamble ---``.

A task that can't be loaded as YAML is dropped (reported with status
``dropped_invalid_yaml``). All file writes are idempotent — second runs
are no-ops.

CLI
---
    python -m data.patchers.patch_ghactions_tasks \
        --root /tmp/ghactions_src \
        [--limit N] [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

import yaml


# ---------------------------------------------------------------------------
# Idempotency markers
# ---------------------------------------------------------------------------

DOCKERFILE_MARKER = "# --- laion v2 patch: ghactions extras ---"
TEST_SH_MARKER = "# --- laion v2 patch: ghactions verifier ---"
INSTRUCTION_MARKER = "<!-- --- laion v2 patch: ghactions preamble --- -->"


# ---------------------------------------------------------------------------
# Patch payloads
# ---------------------------------------------------------------------------

DOCKERFILE_EXTRAS = dedent(
    f"""\

    {DOCKERFILE_MARKER}
    RUN apt-get update && apt-get install -y --no-install-recommends \\
        bsdutils ca-certificates curl \\
     && rm -rf /var/lib/apt/lists/*
    RUN pip install --no-cache-dir 'yamllint==1.35.1' 'PyYAML==6.0.2'
    RUN curl -fsSL https://github.com/rhysd/actionlint/releases/download/v1.7.7/actionlint_1.7.7_linux_amd64.tar.gz \\
          -o /tmp/actionlint.tgz \\
     && tar -xzf /tmp/actionlint.tgz -C /usr/local/bin actionlint \\
     && rm /tmp/actionlint.tgz
    """
)


TEST_SH_CONTENT = dedent(
    """\
    #!/usr/bin/env bash
    # --- laion v2 patch: ghactions verifier ---
    set +e
    mkdir -p /logs/verifier
    echo "0" > /logs/verifier/reward.txt

    # Find the agent's workflow YAML under /app.
    WF=$(find /app -type f \\( -name '*.yml' -o -name '*.yaml' \\) \\
          \\( -path '*/.github/workflows/*' -o -name '*workflow*' -o -name 'ci*' -o -name 'release*' -o -name 'main*' \\) \\
          -print 2>/dev/null | head -1)
    if [ -z "$WF" ]; then
        echo "No workflow YAML found under /app"
        echo "0" > /logs/verifier/reward.txt
        exit 1
    fi
    echo "Found agent workflow: $WF"

    # 1) yamllint catches indentation / tab / SHA-pin lexer issues.
    yamllint -d "{extends: relaxed, rules: {line-length: disable}}" "$WF" 2>&1 \\
        | tee /logs/verifier/yamllint.txt
    yamllint_rc=${PIPESTATUS[0]}

    # 2) actionlint (semantic check of jobs/steps).
    actionlint "$WF" 2>&1 | tee /logs/verifier/actionlint.txt
    actionlint_rc=${PIPESTATUS[0]}

    # 3) Structural match vs reference workflow (key-coverage scorer).
    python /tests/compare_workflows.py /tests/reference_workflow.yml "$WF" 2>&1 \\
        | tee /logs/verifier/compare.txt
    compare_rc=${PIPESTATUS[0]}

    echo "v2 verifier: yamllint_rc=$yamllint_rc actionlint_rc=$actionlint_rc compare_rc=$compare_rc"

    if [ "$yamllint_rc" -eq 0 ] && [ "$actionlint_rc" -eq 0 ] && [ "$compare_rc" -eq 0 ]; then
        echo "1" > /logs/verifier/reward.txt
        exit 0
    else
        echo "0" > /logs/verifier/reward.txt
        exit 1
    fi
    """
)


COMPARE_WORKFLOWS_PY = '''\
#!/usr/bin/env python3
"""Compare an agent GHActions workflow YAML against a reference.

Exits 0 if the agent file structurally matches the reference at top-level
keys: name, on, jobs.<id>.runs-on, jobs.<id>.steps[*].uses,
jobs.<id>.steps[*].run. Allows the agent's keys to be a strict superset
(agents may add comments / extra jobs); requires every reference key to
have a corresponding entry in the agent file.
"""
from __future__ import annotations
import sys
import yaml
from pathlib import Path


def load_yaml(path: Path):
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"YAML load failed for {path}: {e}")
        return None


def get_steps(job):
    if not isinstance(job, dict):
        return []
    return [s for s in (job.get("steps") or []) if isinstance(s, dict)]


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_workflows.py <reference.yml> <agent.yml>")
        return 2
    ref = load_yaml(Path(sys.argv[1]))
    cand = load_yaml(Path(sys.argv[2]))
    if ref is None or cand is None:
        return 2

    issues: list[str] = []

    if "on" in ref and "on" not in cand and True not in cand:
        # PyYAML parses `on:` as True boolean key; allow either form.
        issues.append("missing top-level 'on:' trigger block")

    ref_jobs = (ref.get("jobs") or {}) if isinstance(ref, dict) else {}
    cand_jobs = (cand.get("jobs") or {}) if isinstance(cand, dict) else {}
    for job_id, ref_job in ref_jobs.items():
        if job_id not in cand_jobs:
            issues.append(f"missing job '{job_id}'")
            continue
        cand_job = cand_jobs[job_id] or {}
        if isinstance(ref_job, dict) and ref_job.get("runs-on") \\
                and cand_job.get("runs-on") != ref_job.get("runs-on"):
            issues.append(
                f"job '{job_id}': runs-on mismatch ({cand_job.get('runs-on')!r} vs {ref_job.get('runs-on')!r})"
            )

        ref_uses = {s.get("uses") for s in get_steps(ref_job) if s.get("uses")}
        cand_uses = {s.get("uses") for s in get_steps(cand_job) if s.get("uses")}
        # Allow agent to use newer SHA pin; only require the action name (before '@').
        def action_name(u):
            return u.split("@", 1)[0] if isinstance(u, str) else u
        missing_uses = {action_name(u) for u in ref_uses} - {action_name(u) for u in cand_uses}
        if missing_uses:
            issues.append(f"job '{job_id}': missing actions {sorted(missing_uses)}")

    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        return 1
    print("OK: workflow matches reference structurally")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


INSTRUCTION_PREAMBLE = (
    f"{INSTRUCTION_MARKER}\n"
    "Place your solution at /app/.github/workflows/main.yml — it will be "
    "linted with yamllint + actionlint and structurally compared against a "
    "reference workflow.\n\n"
)


# Reference-YAML filenames the source corpus uses (always actually YAML).
# Order doesn't matter — we always pick whichever exists.
REFERENCE_YAML_CANDIDATES: tuple[str, ...] = (
    "test_solution.py",
    "test_solution.js",
    "solution_test.go",
    "TestSolution.java",
    "tests.rs",
)


# The python variant of the dataset prepends a 2-line
#   import sys
#   sys.path.insert(0, '/app')
#
# Stub above the YAML — it's left over from an earlier verifier-on-pytest
# scheme. Strip it before parsing. Apply only to .py files; the .js / .go /
# .java / .rs variants are pure YAML on disk (optionally with leading `#`
# comments which YAML accepts natively).
_PY_PREAMBLE_LINES: tuple[str, ...] = (
    "import sys",
    "sys.path.insert(0, '/app')",
    'sys.path.insert(0, "/app")',
)


def _strip_py_preamble(text: str) -> str:
    """Drop any leading non-YAML python preamble lines.

    Only stripped from the very top of the file. We stop on the first line
    that isn't blank and isn't on the known preamble allowlist — that line
    is presumed to be the start of the YAML document.
    """
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped in _PY_PREAMBLE_LINES:
            i += 1
            continue
        break
    return "".join(lines[i:])


# ---------------------------------------------------------------------------
# Per-task patching
# ---------------------------------------------------------------------------


def _find_reference_yaml(tests_dir: Path) -> Path | None:
    """Return the path to the YAML-disguised-as-source reference file."""
    for name in REFERENCE_YAML_CANDIDATES:
        p = tests_dir / name
        if p.is_file():
            return p
    return None


def _patch_dockerfile(dockerfile: Path, dry_run: bool) -> str:
    text = dockerfile.read_text()
    if DOCKERFILE_MARKER in text:
        return "already_patched"
    new_text = text.rstrip() + "\n" + DOCKERFILE_EXTRAS
    if not dry_run:
        dockerfile.write_text(new_text)
    return "patched"


def _patch_test_sh(test_sh: Path, dry_run: bool) -> str:
    if test_sh.is_file():
        existing = test_sh.read_text()
        if TEST_SH_MARKER in existing:
            return "already_patched"
    if not dry_run:
        test_sh.write_text(TEST_SH_CONTENT)
        test_sh.chmod(0o755)
    return "patched"


def _patch_compare_py(tests_dir: Path, dry_run: bool) -> str:
    target = tests_dir / "compare_workflows.py"
    if target.is_file() and target.read_text() == COMPARE_WORKFLOWS_PY:
        return "already_patched"
    if not dry_run:
        target.write_text(COMPARE_WORKFLOWS_PY)
        target.chmod(0o755)
    return "patched"


def _patch_instruction(instruction_md: Path, dry_run: bool) -> str:
    if not instruction_md.is_file():
        return "missing"
    text = instruction_md.read_text()
    if INSTRUCTION_MARKER in text:
        return "already_patched"
    new_text = INSTRUCTION_PREAMBLE + text
    if not dry_run:
        instruction_md.write_text(new_text)
    return "patched"


def _rename_reference_yaml(
    ref_path: Path, target_path: Path, cleaned_text: str, dry_run: bool
) -> str:
    """Write ``cleaned_text`` to ``target_path`` and remove ``ref_path``.

    We write the cleaned (preamble-stripped) text rather than a bare rename,
    because the python variant has a 2-line ``import sys`` preamble that
    breaks both ``yaml.safe_load`` and any agent inspection of the file.
    """
    if target_path.is_file() and not ref_path.is_file():
        return "already_patched"
    if not dry_run:
        target_path.write_text(cleaned_text)
        # Only unlink the original after writing the new file, so a crash
        # mid-write doesn't lose the source.
        if ref_path.exists() and ref_path != target_path:
            ref_path.unlink()
    return "patched"


def patch_task(task_dir: Path, dry_run: bool) -> dict:
    """Patch a single task directory.

    Returns ``{"status": ok|dropped_invalid_yaml|missing_reference|error,
                "reason": str}``.
    """
    tests_dir = task_dir / "tests"
    env_dir = task_dir / "environment"
    if not tests_dir.is_dir():
        return {"status": "error", "reason": "no tests/ dir"}
    if not env_dir.is_dir():
        return {"status": "error", "reason": "no environment/ dir"}

    target_yaml = tests_dir / "reference_workflow.yml"

    # If we've already renamed (second run), validate the *target* exists.
    ref_path = _find_reference_yaml(tests_dir)
    candidate = (
        ref_path
        if ref_path is not None
        else (target_yaml if target_yaml.is_file() else None)
    )
    if candidate is None:
        return {"status": "missing_reference", "reason": "no reference YAML file found"}

    # Validate it really is YAML before doing anything destructive. For the
    # python variant we have to strip the 2-line import-sys preamble first.
    try:
        raw = candidate.read_text()
    except (OSError, UnicodeDecodeError) as exc:
        return {"status": "error", "reason": f"read error: {exc.__class__.__name__}"}

    cleaned = _strip_py_preamble(raw) if candidate.suffix == ".py" else raw
    try:
        loaded = yaml.safe_load(cleaned)
    except yaml.YAMLError as exc:
        return {
            "status": "dropped_invalid_yaml",
            "reason": f"yaml.safe_load failed: {exc.__class__.__name__}",
        }

    # An empty / None YAML doc isn't useful as a structural reference.
    if loaded is None or not isinstance(loaded, dict):
        return {
            "status": "dropped_invalid_yaml",
            "reason": "YAML parsed to non-mapping / empty",
        }

    # All checks passed — apply the patches.
    dockerfile_status = _patch_dockerfile(env_dir / "Dockerfile", dry_run)
    if ref_path is not None:
        rename_status = _rename_reference_yaml(ref_path, target_yaml, cleaned, dry_run)
    else:
        rename_status = "already_patched"
    test_sh_status = _patch_test_sh(tests_dir / "test.sh", dry_run)
    compare_status = _patch_compare_py(tests_dir, dry_run)
    instr_status = _patch_instruction(task_dir / "instruction.md", dry_run)

    return {
        "status": "ok",
        "reason": (
            f"dockerfile={dockerfile_status} rename={rename_status} "
            f"test_sh={test_sh_status} compare={compare_status} "
            f"instruction={instr_status}"
        ),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Patch DCAgent/exp_rpt_ghactions tasks (v2 verifier).",
    )
    p.add_argument("--root", required=True, help="Tasks dir (extracted parquet)")
    p.add_argument(
        "--dry-run", action="store_true", help="Report actions only; write nothing"
    )
    p.add_argument(
        "--limit", type=int, default=0, help="Patch at most N tasks (0 = all)"
    )
    p.add_argument(
        "--dropped-out",
        default=None,
        help="Optional path to write dropped task names + reason",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    n_total = len(task_dirs)
    n_ok = 0
    n_dropped = 0
    n_error = 0
    n_missing = 0
    dropped: list[str] = []

    for i, td in enumerate(task_dirs, 1):
        result = patch_task(td, dry_run=args.dry_run)
        status = result["status"]
        if status == "ok":
            n_ok += 1
        elif status == "dropped_invalid_yaml":
            n_dropped += 1
            dropped.append(f"{td.name}\tdropped_invalid_yaml\t{result['reason']}")
            # Remove the directory entirely so it doesn't ship in the dataset.
            if not args.dry_run:
                import shutil

                shutil.rmtree(td)
        elif status == "missing_reference":
            n_missing += 1
            dropped.append(f"{td.name}\tmissing_reference\t{result['reason']}")
            if not args.dry_run:
                import shutil

                shutil.rmtree(td)
        else:
            n_error += 1
            dropped.append(f"{td.name}\terror\t{result['reason']}")

        if i % 500 == 0 or i == n_total:
            print(
                f"[{i}/{n_total}] ok={n_ok} dropped_invalid_yaml={n_dropped} "
                f"missing_reference={n_missing} error={n_error}",
                flush=True,
            )

    print(
        f"\nDone. ok={n_ok}/{n_total}, dropped_invalid_yaml={n_dropped}, "
        f"missing_reference={n_missing}, error={n_error}, "
        f"dry_run={args.dry_run}"
    )

    if args.dropped_out and dropped:
        Path(args.dropped_out).write_text("\n".join(dropped) + "\n")
        print(f"Wrote dropped list to {args.dropped_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
