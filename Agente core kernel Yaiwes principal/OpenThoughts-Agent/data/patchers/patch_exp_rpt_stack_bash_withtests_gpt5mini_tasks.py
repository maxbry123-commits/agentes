#!/usr/bin/env python3
"""
exp_rpt_stack-bash-withtests-gpt5mini v2 patcher.

Same failure mode as `DCAgent/exp_rpt_stack-bash-withtests` (gpt4o variant):
QC of 200 trials showed 151/200 (75.5%) infra-failed with
`VerifierRuntimeError: No reward file found`. Sampled 8/10 from the
`failures/` partition + 2 from `traces/` and all 8 failures share the
same pattern as the sibling stack-bash-withtests v1 dataset:

  * Every `tests/test.sh` wraps the real verifier in a `run_verifier()`
    shell function and dispatches via `if run_verifier; then echo 1 >
    /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi`.
  * Inside `run_verifier()` the script `exit`s directly (e.g. on
    missing `$1` -> `Usage:` print, missing files, missing tools like
    `git`/`module`, etc.). Because the inner `exit` exits the WHOLE
    script (not a subshell return), control never reaches the if/else,
    and `/logs/verifier/reward.txt` is never written.
  * Harbor's verifier polls for `reward.txt`, doesn't find it, and
    raises `RewardFileNotFoundError` -> `VerifierRuntimeError`.

Real verifier stdout from the corpus:

    Usage: /tests/test.sh <filename> <srcroot>
    Usage: /tests/test.sh <commit>...
    Usage: /tests/test.sh <day>
    /tests/test.sh: line 24: git: command not found
    /tests/test.sh: line 50: git: command not found
    /tests/test.sh: line 69: fstrmsymbols: command not found    # passes!
    ERROR: input /root/.../finish.txt missing for this experiment

(The fst* line above is the trace from a SUCCESSFUL trial -- those
scripts don't need the missing tool to write reward; they finish their
own way.)

Fix is identical to `patch_stack_bash_withtests_tasks.py`:

  1. **Reward floor + EXIT trap.** Inserted right after the shebang.
     Guarantees `/logs/verifier/reward.txt` is "0" by the time the
     script exits, even if every later step fails. This alone takes
     ~151 unrecoverable infra-fails -> 151 legitimate reward=0 trials,
     restoring the infra-ok rate from 24.5% to ~99%.
  2. **Default positional args.** If the script has a parseable
     `Usage:` / `usage:` / `USAGE:` line documenting expected args,
     extract placeholder values and rewrite `if run_verifier; then`
     to `if run_verifier "arg1" "arg2" ...; then`. Lets the agent's
     setup reach further into the verifier before failing.
  3. **Idempotent** via marker comment.

We do NOT attempt to fix bugs in the test.sh body itself (missing
binaries, hard syntax errors, etc.); those tasks will still legitimately
score reward=0, which is the correct outcome -- infra-ok with a real
verifier signal is the success criterion, not solve rate.

CLI: --root <dir> [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Idempotency marker -- DIFFERENT name from the gpt4o sibling patcher so
# `bash -n` failures show which patcher touched the file.
PATCH_MARKER = (
    "# --- laion v2 patch: stack-bash-withtests-gpt5mini args + reward floor ---"
)
PATCH_END_MARKER = "# --- end laion v2 patch (gpt5mini) ---"

# Reward floor + EXIT trap. Unconditional, always inserted right after the
# shebang.
REWARD_FLOOR = f"""{PATCH_MARKER}
mkdir -p /logs/verifier 2>/dev/null || true
echo 0 > /logs/verifier/reward.txt 2>/dev/null || true
trap '[ -s /logs/verifier/reward.txt ] || echo 0 > /logs/verifier/reward.txt' EXIT
{PATCH_END_MARKER}
"""

USAGE_LINE_RE = re.compile(
    r"""(?ix)
    (?:^|[\s"'#])
    (?:Usage|usage|USAGE)
    \s*(?:[:]|\s+is\s+)\s*
    (?P<rest>[^\n"]*?)
    (?:["]|$)
    """,
    flags=re.VERBOSE,
)

SHEBANG_RE = re.compile(r"^(#![^\n]*\n)")

DISPATCH_RE = re.compile(
    r"^(?P<indent>[ \t]*)if[ \t]+run_verifier[ \t]*;[ \t]*then[ \t]*$",
    flags=re.MULTILINE,
)

USAGE_NOISE = {
    "$0",
    "\\$0",
    "$@",
    "\\$@",
    "[options]",
    "[OPTIONS]",
    "[flags]",
    "[FLAGS]",
    "[args]",
    "[ARGS]",
    "[--help]",
    "[-h]",
    "-h",
    "--help",
    "[options...]",
    "[arguments...]",
}


def _looks_like_script_name(token: str) -> bool:
    t = token.strip().strip("`").strip("'").strip('"')
    if not t:
        return True
    if t.endswith(".sh") or t.endswith(".bash"):
        return True
    if t.startswith("./") or t.startswith("/"):
        return True
    if t in ("test.sh", "$0", "\\$0"):
        return True
    if re.fullmatch(r"[a-zA-Z_][\w.+-]*", t) and len(t) <= 30:
        return True
    return False


def _extract_default_for_token(token: str) -> str | None:
    t = token.strip()
    if not t:
        return None
    if t in USAGE_NOISE:
        return None

    inner = t
    if (
        (inner.startswith("<") and inner.endswith(">"))
        or (inner.startswith("{") and inner.endswith("}"))
        or (inner.startswith("[") and inner.endswith("]"))
    ):
        inner = inner[1:-1].strip()

    if not inner:
        return None
    if inner.startswith("-"):
        return None

    if "|" in inner:
        first = inner.split("|", 1)[0].strip()
        first = re.sub(r"[<>{}\[\]]", "", first).strip()
        if first and not first.startswith("-"):
            return first
        return None

    cleaned = re.sub(r"[<>{}\[\]]", "", inner).strip()
    if not cleaned:
        return None
    return "default"


def parse_usage_args(usage_rest: str) -> list[str] | None:
    text = usage_rest.strip()

    def _strip_trailing_redir(s: str) -> str:
        depth_a = depth_c = depth_s = 0
        for i, ch in enumerate(s):
            if ch == "<":
                depth_a += 1
            elif ch == ">":
                if depth_a > 0:
                    depth_a -= 1
                else:
                    return s[:i].rstrip()
            elif ch == "{":
                depth_c += 1
            elif ch == "}":
                depth_c -= 1
            elif ch == "[":
                depth_s += 1
            elif ch == "]":
                depth_s -= 1
            elif ch in "&;" and depth_a == 0 and depth_c == 0 and depth_s == 0:
                return s[:i].rstrip()
        return s

    text = _strip_trailing_redir(text)
    text = text.strip().strip(":").strip()
    if not text:
        return None

    tokens: list[str] = []
    buf = ""
    depth_angle = depth_curly = depth_square = 0
    for ch in text:
        if ch in "<{[":
            depth_angle += ch == "<"
            depth_curly += ch == "{"
            depth_square += ch == "["
            buf += ch
            continue
        if ch in ">}]":
            depth_angle -= ch == ">"
            depth_curly -= ch == "}"
            depth_square -= ch == "]"
            buf += ch
            continue
        if ch.isspace() and depth_angle == 0 and depth_curly == 0 and depth_square == 0:
            if buf:
                tokens.append(buf)
                buf = ""
            continue
        buf += ch
    if buf:
        tokens.append(buf)

    if not tokens:
        return None

    if _looks_like_script_name(tokens[0]):
        tokens = tokens[1:]

    if not tokens:
        return None

    defaults: list[str] = []
    for tok in tokens:
        d = _extract_default_for_token(tok)
        if d is None:
            if len(defaults) >= 8:
                break
            continue
        defaults.append(d)
        if len(defaults) >= 8:
            break

    if not defaults:
        return None
    return defaults


def find_first_usage(text: str) -> tuple[str, list[str]] | None:
    for m in USAGE_LINE_RE.finditer(text):
        rest = m.group("rest")
        defaults = parse_usage_args(rest)
        if defaults:
            return rest, defaults
    return None


def patch_test_sh(text: str) -> tuple[str, bool, bool]:
    """Apply the reward floor (always) + arg injection (if usage line
    parseable). Returns (new_text, changed, args_injected).
    """
    if PATCH_MARKER in text:
        return text, False, False

    args_injected = False
    new_text = text

    detected = find_first_usage(text)
    if detected is not None:
        _raw, defaults = detected
        quoted = " ".join(f'"{d}"' for d in defaults)

        def _rewrite(match: re.Match[str]) -> str:
            indent = match.group("indent")
            return (
                f"{indent}# laion v2 (gpt5mini): inject default positional args parsed\n"
                f"{indent}# from the script's Usage: line so run_verifier doesn't abort\n"
                f'{indent}# on `[ -z "$1" ]` before reward.txt is written.\n'
                f"{indent}if run_verifier {quoted}; then"
            )

        new_text2, n_subs = DISPATCH_RE.subn(_rewrite, new_text, count=1)
        if n_subs > 0:
            new_text = new_text2
            args_injected = True

    m = SHEBANG_RE.match(new_text)
    if m:
        new_text = m.group(1) + REWARD_FLOOR + new_text[m.end() :]
    else:
        new_text = "#!/bin/bash\n" + REWARD_FLOOR + new_text

    return new_text, new_text != text, args_injected


def syntax_check(path: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["bash", "-n", str(path)],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return False, "bash -n timed out"
    except FileNotFoundError:
        return False, "bash not found"
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout).strip()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process at most N task dirs (0 = all)",
    )
    p.add_argument(
        "--drop-log",
        type=str,
        default=None,
        help="Optional path to write dropped-task report (TSV: task_id\\tstderr)",
    )
    args = p.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    test_paths = sorted(root.glob("*/tests/test.sh"))
    if not test_paths:
        print(f"No tests/test.sh files under {root}", file=sys.stderr)
        return 2

    if args.limit:
        test_paths = test_paths[: args.limit]

    n_total = len(test_paths)
    n_with_args = 0
    n_floor_only = 0
    n_already = 0
    n_dropped = 0
    drop_log_lines: list[str] = []
    dropped_examples: list[tuple[str, str]] = []

    for i, p in enumerate(test_paths, 1):
        task_dir = p.parent.parent
        task_id = task_dir.name
        original = p.read_text()

        if PATCH_MARKER in original:
            n_already += 1
            continue

        patched, changed, args_injected = patch_test_sh(original)
        if not changed:
            continue

        if args.dry_run:
            with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as tf:
                tf.write(patched)
                tmp_path = Path(tf.name)
            try:
                ok, stderr = syntax_check(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
        else:
            p.write_text(patched)
            ok, stderr = syntax_check(p)

        if not ok:
            first_line = stderr.splitlines()[0] if stderr else "(no stderr)"
            drop_log_lines.append(f"{task_id}\t{first_line}")
            if len(dropped_examples) < 5:
                dropped_examples.append((task_id, first_line))
            n_dropped += 1
            if not args.dry_run:
                shutil.rmtree(task_dir, ignore_errors=True)
            if i % 1000 == 0 or i == n_total:
                print(
                    f"[{i}/{n_total}] with_args={n_with_args} "
                    f"floor_only={n_floor_only} dropped={n_dropped} "
                    f"already={n_already}",
                    flush=True,
                )
            continue

        if args_injected:
            n_with_args += 1
        else:
            n_floor_only += 1

        if i % 1000 == 0 or i == n_total:
            print(
                f"[{i}/{n_total}] with_args={n_with_args} "
                f"floor_only={n_floor_only} dropped={n_dropped} "
                f"already={n_already}",
                flush=True,
            )

    pct_dropped = (100.0 * n_dropped / n_total) if n_total else 0.0
    pct_with_args = (100.0 * n_with_args / n_total) if n_total else 0.0
    print()
    print("=" * 60)
    print(f"Total tasks scanned:           {n_total}")
    print(f"Patched with args injection:   {n_with_args} ({pct_with_args:.1f}%)")
    print(f"Patched floor+trap only:       {n_floor_only}")
    print(f"Already patched (skipped):     {n_already}")
    print(f"Dropped (bash -n failed):      {n_dropped} ({pct_dropped:.1f}%)")
    print(f"Dry run:                       {args.dry_run}")
    print("=" * 60)

    if dropped_examples:
        print("\nFirst dropped tasks (id, bash -n stderr):")
        for tid, msg in dropped_examples:
            print(f"  {tid}: {msg}")

    if args.drop_log and drop_log_lines:
        Path(args.drop_log).write_text("\n".join(drop_log_lines) + "\n")
        print(f"\nFull drop log written to: {args.drop_log}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
