#!/usr/bin/env python3
"""
Synthesize oracle solvers (solution/solve.sh) for the TMax-15K -> Harbor tasks.

TMax-15K ships NO gold agent solution. Each task DOES ship a `truth` field (kept in
metadata.json as `truth_hint`) describing the env-setup + EXPECTED RESULTS. We feed
BOTH instruction.md and that truth_hint to a capable teacher so the generated
solve.sh reliably reproduces the expected final state, then the oracle gate
(validate_and_upload_from_hf.py --stages oracle) filters out any that don't verify.

We never show the teacher the test files (tests/test_state.py) — only the
agent-facing instruction + the truth_hint — so it solves the task rather than
hard-coding the assertions.

Usage:
    PY=/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python
    $PY -m data.tmax15k.synthesize_oracle_solvers /tmp/tmax15k_raw --model gpt-5 --workers 32
    # then validate: scripts/daytona/validate_and_upload_from_hf.py --stages oracle ...
"""

from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

SYSTEM_PROMPT = """\
You are an expert Linux terminal engineer. Your job is to write a bash script \
that correctly completes a given task inside a Docker container running Ubuntu.

Rules:
- Output ONLY a bash script (starting with #!/bin/bash), no markdown fences, \
no explanation.
- The script must actually solve the task by producing the required final state \
(files, outputs) — do NOT hardcode expected values blindly; compute them.
- FIRST materialize the task environment by running: bash /solution/setup.sh \
(it is idempotent). The graders run it too; running it makes the input data and \
any ground-truth fixtures exist. ALWAYS start your script with this line.
- Use standard Unix tools, Python 3, or whatever is appropriate. Python 3 with \
numpy/pandas/scipy/networkx/scikit-learn is available; gcc/g++/go/cargo/rustc too.
- Honor every path, filename, numeric format, rounding, and sort order the task \
specifies EXACTLY — graders compare the produced files byte/value-for-value. \
When the task names an exact numeric tolerance or decimal precision, match it.
- A REFERENCE describing how the environment is built and what the expected \
results are is provided to help you produce the correct final state. Use it to \
get the ALGORITHM and the exact OUTPUT FORMAT/VALUES right; do not copy \
ground-truth file paths as a shortcut to bypass actually computing the answer.
- Always create EVERY output file/artifact the task requires (missing-file \
assertions are a common failure). Verify your script actually wrote them.
- For C: when using fseeko/ftello/off_t, compile with \
`-D_FILE_OFFSET_BITS=64 -D_GNU_SOURCE` (or include the right headers) so off_t \
is defined. For C/C++/Rust/Go: COMPILE CLEANLY — a build error means zero output.
- For git operations: the repo may be owned by another user; run \
`git config --global --add safe.directory '*'` first.
- If the task expects a computed value matching a reference, re-derive it with \
the SAME method the reference uses (e.g. networkx pagerank alpha=0.85, the \
specified rolling-window definition) — do not approximate.
- Keep the script self-contained and correct. Prefer Python for numeric/data \
tasks (it is pre-installed with numpy/pandas/scipy/networkx).
"""

USER_PROMPT_TEMPLATE = """\
Complete the following task by writing a bash script (solve.sh).

--- TASK (agent-facing instruction) ---
{instruction}
--- END TASK ---

--- REFERENCE (how the environment is set up + the expected results; for your \
understanding only, do NOT just echo it) ---
{truth_hint}
--- END REFERENCE ---

Output ONLY the bash script, starting with #!/bin/bash.
"""

MAX_HINT_CHARS = 24000


def _call_llm(instruction: str, truth_hint: str, model: str, client) -> str:
    hint = (truth_hint or "(no reference provided)")[:MAX_HINT_CHARS]
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    instruction=instruction, truth_hint=hint
                ),
            },
        ],
        max_completion_tokens=16000,
        timeout=180,
    )
    return (response.choices[0].message.content or "").strip()


SETUP_PREAMBLE = "# [tmax oracle] materialize task fixtures + ground truth (idempotent)\nif [ -f /solution/setup.sh ]; then bash /solution/setup.sh; fi\n"


def _clean_script(raw: str) -> str:
    if raw.startswith("```"):
        lines = raw.splitlines()
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        raw = "\n".join(inner)
    if not raw.startswith("#!"):
        raw = "#!/bin/bash\n" + raw
    # Guarantee the env-setup runs even if the teacher omitted it: inject the
    # setup invocation right after the shebang (idempotent; harmless if duplicated).
    lines = raw.splitlines()
    shebang = lines[0]
    rest = "\n".join(lines[1:])
    if "/solution/setup.sh" not in rest:
        raw = shebang + "\n" + SETUP_PREAMBLE + rest
    return raw


def _load_truth_hint(task_dir: Path) -> str:
    meta_path = task_dir / "metadata.json"
    if not meta_path.exists():
        return ""
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    # metadata may be flat or nested under "metadata"
    if isinstance(meta.get("metadata"), dict) and "truth_hint" in meta["metadata"]:
        return meta["metadata"].get("truth_hint") or ""
    return meta.get("truth_hint") or ""


def synthesize_one(
    task_dir, *, model, client, overwrite=False, dry_run=False, max_retries=3
):
    result = {"task": task_dir.name}
    instruction_path = task_dir / "instruction.md"
    if not instruction_path.exists():
        result["status"] = "error"
        result["error"] = "no instruction.md"
        return result

    solution_dir = task_dir / "solution"
    solve_path = solution_dir / "solve.sh"

    # We always (re)write when overwrite is set; the converter leaves a placeholder.
    if solve_path.exists() and not overwrite:
        # treat the placeholder as "needs generation": detect the marker.
        try:
            existing = solve_path.read_text(encoding="utf-8")
        except Exception:
            existing = ""
        if "PLACEHOLDER oracle" not in existing:
            result["status"] = "skipped"
            return result

    if dry_run:
        result["status"] = "dry_run"
        return result

    instruction = instruction_path.read_text(encoding="utf-8")
    truth_hint = _load_truth_hint(task_dir)

    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            raw = _call_llm(instruction, truth_hint, model, client)
            if not raw:
                raise RuntimeError("empty completion")
            script = _clean_script(raw)
            solution_dir.mkdir(exist_ok=True)
            solve_path.write_text(script, encoding="utf-8")
            solve_path.chmod(0o755)
            result["status"] = "ok"
            return result
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2**attempt)

    result["status"] = "error"
    result["error"] = str(last_error)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize TMax-15K oracle solvers")
    parser.add_argument("tasks_dir", type=Path)
    parser.add_argument("--model", default="gpt-5")
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--api-key", default=None)
    parser.add_argument(
        "--only-tasks",
        default=None,
        help="Comma-separated task dir names to (re)generate (subset).",
    )
    args = parser.parse_args()

    if not args.tasks_dir.is_dir():
        raise SystemExit(f"Not a directory: {args.tasks_dir}")

    task_dirs = sorted(
        d
        for d in args.tasks_dir.iterdir()
        if d.is_dir() and (d / "instruction.md").exists()
    )
    if args.only_tasks:
        wanted = {t.strip() for t in args.only_tasks.split(",") if t.strip()}
        task_dirs = [d for d in task_dirs if d.name in wanted]
    if not task_dirs:
        raise SystemExit(f"No tasks found in {args.tasks_dir}")
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    print(f"Found {len(task_dirs)} tasks in {args.tasks_dir}")

    if not args.dry_run:
        from openai import OpenAI

        api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit("OPENAI_API_KEY not set")
        client = OpenAI(api_key=api_key)
    else:
        client = None

    counts = {"ok": 0, "skipped": 0, "dry_run": 0, "error": 0}
    errors = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                synthesize_one,
                td,
                model=args.model,
                client=client,
                overwrite=args.overwrite,
                dry_run=args.dry_run,
            ): td
            for td in task_dirs
        }
        completed = 0
        total = len(futures)
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            status = result["status"]
            counts[status] = counts.get(status, 0) + 1
            if status == "error":
                errors.append(f"  {result['task']}: {result.get('error', '?')}")
            if completed % 50 == 0 or completed == total:
                print(
                    f"  [{completed}/{total}] ok={counts['ok']} "
                    f"skipped={counts['skipped']} error={counts['error']}"
                )

    print(
        f"\nDone: generated={counts['ok']} skipped={counts['skipped']} "
        f"dry_run={counts['dry_run']} errors={counts['error']}"
    )
    for e in errors[:20]:
        print(e)


if __name__ == "__main__":
    main()
