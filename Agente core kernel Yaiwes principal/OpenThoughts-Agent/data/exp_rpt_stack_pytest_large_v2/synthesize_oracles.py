#!/usr/bin/env python3
"""Generate non-leaky oracle scripts for a selected Stack-Pytest cohort."""

from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI


SYSTEM_PROMPT = """You write a correct private reference /solution/solve.sh for
a Python task. Return only a bash script beginning with #!/bin/bash. The script
must create the implementation under /app described by the task. Do not access,
modify, copy, or infer anything from /tests at runtime. Do not copy
/setup_files: it is not mounted for these Harbor tasks. Do not install a package
unless it is explicitly listed in the captured runtime dependencies. Prefer a
self-contained implementation with the Python standard library. Make every
directory and package __init__.py required by the specified import path. Cover
the stated contract and its edge cases rather than hard-coding examples. The
verifier will run after this script exits.
"""


def clean_script(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return raw if raw.startswith("#!") else f"#!/bin/bash\n{raw}"


def prompt_for(task: Path) -> str:
    requirements = (
        (task / "tests" / "requirements.txt").read_text(encoding="utf-8").strip()
    )
    requirement_text = requirements or "None beyond pytest."
    instruction = (task / "instruction.md").read_text(encoding="utf-8")
    return f"""Create the private reference solve.sh for this task.\n\nCaptured runtime dependencies:\n{requirement_text}\n\nTask instruction:\n{instruction}"""


def generate_one(
    task: Path,
    model: str,
    client: OpenAI,
    overwrite: bool,
    attempts: int,
    max_completion_tokens: int,
) -> str:
    output = task / "solution" / "solve.sh"
    if output.exists() and not overwrite:
        return "skipped"
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_for(task)},
                ],
                max_completion_tokens=max_completion_tokens,
            )
            break
        except Exception as exc:
            last_error = exc
            if attempt + 1 == attempts:
                raise
            time.sleep(2**attempt)
    else:  # pragma: no cover - loop either breaks or raises
        raise RuntimeError(
            "teacher generation exhausted without a response"
        ) from last_error
    output.parent.mkdir(exist_ok=True)
    output.write_text(
        clean_script(response.choices[0].message.content or ""), encoding="utf-8"
    )
    output.chmod(0o755)
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--model", default="gpt-5")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--max-completion-tokens", type=int, default=8_192)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--task-names", nargs="+", help="Explicit task directories to regenerate"
    )
    args = parser.parse_args()
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is required")
    available = {
        task.name: task
        for task in args.tasks_dir.iterdir()
        if (task / "instruction.md").is_file()
    }
    if args.task_names:
        missing = sorted(set(args.task_names) - available.keys())
        if missing:
            raise ValueError(f"unknown tasks: {', '.join(missing)}")
        tasks = [available[name] for name in args.task_names]
    else:
        tasks = [available[name] for name in sorted(available)[: args.limit]]
    if not args.task_names and len(tasks) != args.limit:
        raise ValueError(f"requested {args.limit} tasks, found {len(tasks)}")
    client = OpenAI()
    counts: dict[str, int] = {"ok": 0, "skipped": 0, "error": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                generate_one,
                task,
                args.model,
                client,
                args.overwrite,
                args.attempts,
                args.max_completion_tokens,
            ): task
            for task in tasks
        }
        for future in as_completed(futures):
            try:
                counts[future.result()] += 1
            except Exception as exc:
                counts["error"] += 1
                print(
                    f"{futures[future].name}: {type(exc).__name__}: {exc}", flush=True
                )
    print(
        f"generated={counts['ok']} skipped={counts['skipped']} errors={counts['error']}"
    )
    return 0 if not counts["error"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
