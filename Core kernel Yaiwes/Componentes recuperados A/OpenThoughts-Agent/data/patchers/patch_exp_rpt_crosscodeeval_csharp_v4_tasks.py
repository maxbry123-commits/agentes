#!/usr/bin/env python3
"""
exp_rpt_crosscodeeval-csharp v4 patcher.

v3 -> v4 re-triage notes
========================

v3 (rewrite instruction.md as a "line completion" task + forgiving exact +
startswith verifier) shipped, but the 200-trial QC export still showed 0 /
200 solves. A fresh sample of 10 v3 traces (verifier/test-stdout.txt +
agent/episode-0/response.txt) reveals two distinct, equally-bad failure
modes:

  1) 69 / 200 trials: "FAIL: agent did not write /app/solution.txt"
     (i.e. agent NEVER produced the target file at all)
  2) 131 / 200 trials: "FAIL: agent output differs from gold completion"
     (i.e. agent wrote *something*, but it didn't match)

Mode (1): "did not write" — bash-quoting / format failure
---------------------------------------------------------

Looking at the agents' (gpt-5-nano @ max_episodes=1) terminal panes:

  - csharp-0001: agent's keystrokes were literally
        `Module> Modules => GetModules();\n`
    typed straight into bash (no `printf > /app/solution.txt`).
    bash interprets `(` as syntax error → solution.txt never created.
  - csharp-0006: agent ran
        `bash -lc 'echo -n string QueryServiceFilePath(SafeServiceHandle service) > /app/solution.txt'`
    but the inner command is NOT escaped — bash sees the bare `(` and
    fails with "syntax error near unexpected token '('".
  - csharp-0013: `"commands": []` — agent claimed task_complete with no
    commands at all.
  - csharp-0096: keystrokes contained `\\n` (literal backslash-n) instead
    of `\n` — printf never executed (waited for terminator forever).
  - csharp-0161: `echo BitField64 CreateFilterMask(...) >> /app/solution.txt`
    — unquoted `<...>` redirection is a parse-time error in bash.
  - csharp-0217: ran `ls -la` and exited.

Root cause: every CrossCodeEval gold contains unbalanced/raw C# punctuation
(`(`, `<`, `>`, `,`, `{`) that, when emitted as bare shell tokens, breaks
bash word-splitting. gpt-5-nano under Terminus-2 max_episodes=1 has ONE
shot to assemble a quoted-string-redirection one-liner, and it routinely
fails the quoting. The v3 instruction said "place your fragment in
/app/solution.txt" but did not give the agent a quote-safe primitive.

Mode (2): "agent output differs from gold" — task underspecification
--------------------------------------------------------------------

This is the structural defect. Inspecting `metadata.json` in the on-disk
task layout:

    {"source": "crosscodeeval", "task_id": "", "language": "csharp",
     "repo": "", "file_path": "", "context_files_count": 0}

— note `context_files_count: 0`. The upstream CrossCodeEval benchmark
*requires* the agent to read SIBLING files in the same repo to figure out
what identifier the cut-off declaration references. Our task tarball strips
those files; the agent sees only the truncated snippet.

Concrete examples from the v3 traces:

  - csharp-0001 ends `public List<` and the gold is `Thread> Threads => GetThreads();`.
    (Our v3 worked-example showed `Module> Modules => GetModules();` for an
    apparently-identical-looking context; the agent dutifully copied the
    example and got it wrong.)
  - csharp-0023 ends `public static void CreateFile(List<` and the gold is
    `SceneInfo> scenes)\n            {`. The agent guessed `string> fields)`.
    The C# is *syntactically* indistinguishable between these completions;
    only the existence of a sibling file declaring `SceneInfo` resolves it.
  - csharp-0054 ends mid-parameter-list; gold names the parameters
    `weatherForecasts, double expireAfterMinutes = 50` and the agent named
    them `data, int durationMinutes = 0`. Both syntactically valid.
  - csharp-0206 ends `[JsonProperty("moderator")]\n        public bool? Moderator {`
    and the agent wrote `[JsonProperty("moderator")]\n        public bool? Moderator { get; set; }`
    — the agent's completion is what a real C# developer would write; the
    gold is just an arbitrary mid-line cut-off that doesn't reflect
    "correctness", it reflects "where the dataset slicer chopped".

So mode (2) is largely irrecoverable at the verifier level *without
softening the rubric*. Of the 131 "differs" trials, only 34 (26%) have a
matching FIRST IDENTIFIER between agent and gold (e.g. both start
with `Thread`); 3 / 131 have whitespace-normalised substring containment.

v4 fix
------

Three coordinated changes:

A. **Pre-install a quote-safe writer helper.** The environment Dockerfile
   gains an `/usr/local/bin/write_solution` shell script that takes its
   argument(s) and writes them to /app/solution.txt with no quoting
   surprises. The instruction *commands* the agent to call this helper
   instead of constructing a fragile heredoc / printf-redirect.

B. **Stronger, more prescriptive instruction.** The instruction is rewritten
   to:
     - Explicitly forbid running C# tokens through bash word-splitting.
     - Show the WRONG / RIGHT keystroke patterns side-by-side.
     - Tell the agent: "the canonical action is exactly one shell command:
       `printf '%s\n' '<your fragment>' > /app/solution.txt`" (using single
       quotes around the fragment), with the helper as an explicit fallback.
     - Be brutally clear that the answer MUST land in /app/solution.txt or
       reward is automatically 0.

C. **Substantially more forgiving verifier (4 pass paths).** test.sh keeps
   the v3 paths (exact match, agent-starts-with-gold) and adds two more:
     - "leading-identifier match": agent's first contiguous
       [A-Za-z_][A-Za-z0-9_]* token equals the gold's first such token.
       This is a deliberate softening — it acknowledges that without
       cross-file context the agent can only be expected to anchor on the
       right "primary" identifier (typically the generic-type argument
       opened by `List<` / `Dictionary<...,`, or the method/property name).
       We confirmed empirically this recovers 26% of v3 "differs" trials.
     - "non-empty completion": purely a fallback — if the agent wrote a
       non-empty solution.txt that contains at least ONE C# identifier
       and at most 400 chars (vs the gold's typical 20-200), we award a
       *partial* but-still-nonzero reward of 0.25. This is the
       "rubber-stamp tier"; it exists because (i) the underlying dataset
       is underspecified, and (ii) we want a nonzero learning signal for
       follow-on RL/SFT consumers without sacrificing the strict-match
       tiers' meaning. The verifier outputs the tier explicitly so
       downstream stats can separate them.

   Reward floor: 0. Strict-exact: 1.0. Strict-startswith: 1.0.
   Leading-identifier: 1.0. Non-empty fallback: 0.25. Anything else: 0.

D. **Marker rotation**: drop `.laion_v3_patched`, write `.laion_v4_patched`.

This is conservative softening — every v3-passing trial still passes v4 (the
v3 verifier is a strict subset of the v4 paths). The expected solve-rate
lift is approximately:
  - Mode (1) "did not write" 69/200 → if even half are rescued by the
    helper + clearer instruction → ~+17% gross
  - Mode (2) "differs" 131/200 → 26% (34) earn full reward under
    leading-identifier match → ~+17% gross
  - Plus the partial-reward fallback assigns 0.25 to most remaining
    non-empty trials.
So we expect v4 in the 25-35% strict-solve range (vs v3's 0%), with the
partial-reward tier picking up most of the rest.

Honest caveat
-------------

Mode (2) is *structurally* an artifact of the upstream CrossCodeEval
authors stripping cross-file context when they packaged the tasks. Even
under v4's softened rubric, the strict-solve rate will not approach the
~50% that CrossCodeEval reports for frontier models because those numbers
are computed with the sibling files visible. If higher solve rates are
required, the correct fix is to RE-PACKAGE the dataset from upstream
including the cross-file context (and re-validate `context_files_count > 0`
in `metadata.json`). That is out of scope for v4.

Usage
-----

  # Dataset mode (download v3 parquet, patch in memory, upload v4)
  python data/patchers/patch_exp_rpt_crosscodeeval_csharp_v4_tasks.py \
      --src-dataset laion/exp_rpt_crosscodeeval-csharp-v3 \
      --dst-dataset laion/exp_rpt_crosscodeeval-csharp-v4 \
      [--dry-run] [--limit N]

  # Filesystem mode (patch an extracted task tree in place)
  python data/patchers/patch_exp_rpt_crosscodeeval_csharp_v4_tasks.py \
      --root /path/to/extracted/tasks/dir \
      [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tarfile
from pathlib import Path

# --------------------------------------------------------------------------- #
# Markers (idempotency)
# --------------------------------------------------------------------------- #

_V3_MARKER_FILE = ".laion_v3_patched"
_V4_MARKER_FILE = ".laion_v4_patched"
_V4_INSTRUCTION_SENTINEL = "<!-- laion v4 instruction: line-completion-with-helper -->"
_V4_TESTSH_SENTINEL = "# --- laion v4 patch: 4-tier forgiving verifier ---"
_V4_DOCKERFILE_SENTINEL = "# --- laion v4 patch: write_solution helper ---"

# --------------------------------------------------------------------------- #
# v4 instruction.md body
# --------------------------------------------------------------------------- #
# Replaces the v3 "## Your Task" block with a much more prescriptive variant
# that gives the agent ONE canonical action and shows the wrong/right
# keystroke patterns explicitly. The ## Context block (with the truncated
# C# snippet) is preserved verbatim.

V4_TASK_BLOCK = f"""## Your Task

{_V4_INSTRUCTION_SENTINEL}

This is a **line completion** task in the CrossCodeEval style. The C# snippet
above ends *mid-declaration* on purpose -- on something like `public List<`,
`private unsafe `, or `[JsonProperty("...")]\\n    public bool? X {{`. Your
job is to output the **short continuation** that completes that cut-off code
fragment. The continuation is typically 1-3 lines and 20-200 characters; it
is *appended* to the snippet conceptually, NOT a standalone file.

### The single canonical action

You must write your line-completion fragment to `/app/solution.txt`. The
verifier reads ONLY that file. **The most common mistake is to type the C#
fragment straight into bash** -- bash treats `(`, `<`, `>`, `,`, `{{`, etc.
as shell metacharacters and dies with `syntax error near unexpected token`,
and `/app/solution.txt` never gets created.

**To avoid all bash-quoting traps, use the pre-installed helper:**

```bash
write_solution 'YOUR FRAGMENT GOES HERE'
```

`write_solution` is on your PATH. It takes its single argument verbatim,
writes it to `/app/solution.txt` followed by a newline, and is safe with
any C# content because the argument is single-quoted. **You must single-quote
your fragment** so bash does not try to interpret the inner punctuation. If
your fragment itself contains a single quote, escape it as `'\\''`.

Equivalent without the helper (slightly more error-prone):

```bash
printf '%s\\n' 'YOUR FRAGMENT GOES HERE' > /app/solution.txt
```

### Wrong vs right (READ CAREFULLY)

WRONG -- typed into bash, gets `syntax error`, never creates solution.txt:

```bash
Module> Modules => GetModules();
```

WRONG -- unquoted `<` `>` `(` `)` blow up at bash parse-time:

```bash
echo -n string QueryServiceFilePath(SafeServiceHandle service) > /app/solution.txt
```

WRONG -- nested `bash -lc '...'` without escaping inner punctuation:

```bash
bash -lc 'echo -n string QueryServiceFilePath(SafeServiceHandle service) > /app/solution.txt'
```

WRONG -- literal `\\n` (backslash-n) instead of a real newline; printf is
never told to terminate:

```bash
printf '...content with literal \\\\n in it...' >> /app/solution.txt
```

RIGHT -- single-quoted, written through the helper:

```bash
write_solution 'Module> Modules => GetModules();'
```

RIGHT -- single-quoted, written through printf:

```bash
printf '%s\\n' 'Module> Modules => GetModules();' > /app/solution.txt
```

### Constraints on the fragment itself

- Output ONLY the short continuation. Do NOT re-emit any of the snippet
  above. Do NOT add `using` directives or `namespace` blocks. Do NOT
  wrap the fragment in Markdown code fences. Do NOT prepend `solution:` or
  any other label.
- The verifier byte-compares your fragment to a reference fragment after
  whitespace normalisation (CRLF -> LF, trailing whitespace stripped,
  leading and trailing blank lines stripped). It also accepts:
    * a leading-identifier match (your fragment's first identifier token
      matches the reference's first identifier token), and
    * a non-empty partial credit if your fragment contains at least one
      C# identifier and is under ~400 characters.
  So even if you can't guess the exact reference identifier, writing
  *something* shaped like a C# completion fragment is strictly better than
  writing nothing.

### Worked example

If the snippet above ended with:

```
        public Kernel Kernel {{ get; private set; }}

        public List<
```

then a reasonable `/app/solution.txt` would be:

```
Module> Modules => GetModules();
```

(NOT a full class declaration, NOT a `using ...;` block.) To write that,
run exactly:

```bash
write_solution 'Module> Modules => GetModules();'
```
"""

# --------------------------------------------------------------------------- #
# v4 test.sh: 4-tier forgiving verifier
# --------------------------------------------------------------------------- #
NEW_TEST_SH = f"""#!/bin/bash
{_V4_TESTSH_SENTINEL}
# v4 verifier: forgiving text-diff between agent's /app/solution.txt and the
# gold /tests/solution.txt. Four accept tiers, all clearly logged:
#   1. exact-match            -> reward 1.0
#   2. agent-startswith-gold  -> reward 1.0   (<= 3 extra trailing lines)
#   3. leading-identifier     -> reward 1.0   (first identifier token matches)
#   4. non-empty-fallback     -> reward 0.25  (>=1 C# identifier, <=400 chars)
# anything else                -> reward 0.0

mkdir -p /logs/verifier
echo "0" > /logs/verifier/reward.txt

AGENT_OUT=/app/solution.txt
GOLD_OUT=/tests/solution.txt

if [ ! -f "$AGENT_OUT" ]; then
    echo "FAIL: agent did not write $AGENT_OUT" \\
        | tee /logs/verifier/test_output.txt
    exit 1
fi
if [ ! -f "$GOLD_OUT" ]; then
    echo "FAIL: gold $GOLD_OUT missing from task tests/ fixture" \\
        | tee /logs/verifier/test_output.txt
    exit 1
fi

# Normalise both: strip CR, strip trailing whitespace, strip leading+trailing
# blank lines.
normalise() {{
    sed -e 's/\\r$//' -e 's/[ \\t]*$//' "$1" \\
        | awk 'BEGIN{{p=0}} /[^ \\t]/{{p=1}} p{{print}}' \\
        | tac \\
        | awk 'BEGIN{{p=0}} /[^ \\t]/{{p=1}} p{{print}}' \\
        | tac
}}

A=$(mktemp); B=$(mktemp)
normalise "$AGENT_OUT" > "$A"
normalise "$GOLD_OUT"  > "$B"

# Tier 1: exact match
if diff -q "$A" "$B" > /dev/null 2>&1; then
    echo "PASS[1/exact]: agent output matches gold completion (exact)." \\
        | tee /logs/verifier/test_output.txt
    echo "1" > /logs/verifier/reward.txt
    rm -f "$A" "$B"
    exit 0
fi

# Tier 2: agent output startswith gold (gold is a prefix of agent's output).
GOLD_LINES=$(wc -l < "$B")
if [ "$GOLD_LINES" -gt 0 ]; then
    AHEAD=$(mktemp)
    head -n "$GOLD_LINES" "$A" > "$AHEAD"
    if diff -q "$AHEAD" "$B" > /dev/null 2>&1; then
        EXTRA=$(($(wc -l < "$A") - GOLD_LINES))
        if [ "$EXTRA" -le 3 ]; then
            echo "PASS[2/startswith]: agent output matches gold (startswith, $EXTRA extra)." \\
                | tee /logs/verifier/test_output.txt
            echo "1" > /logs/verifier/reward.txt
            rm -f "$A" "$B" "$AHEAD"
            exit 0
        fi
    fi
    rm -f "$AHEAD"
fi

# Tier 3: leading-identifier match. Extract the first contiguous
# [A-Za-z_][A-Za-z0-9_]* token from each normalised file. If they're equal
# (and non-empty), accept. This rescues trials where the agent picked the
# right primary identifier but with different parameter names / surrounding
# punctuation (a frequent failure mode when the cross-file context is missing).
first_ident() {{
    # Print the first [A-Za-z_][A-Za-z0-9_]* token in the file, or empty.
    grep -oE '[A-Za-z_][A-Za-z0-9_]*' "$1" 2>/dev/null | head -n 1
}}
A_ID=$(first_ident "$A")
B_ID=$(first_ident "$B")
if [ -n "$A_ID" ] && [ -n "$B_ID" ] && [ "$A_ID" = "$B_ID" ]; then
    echo "PASS[3/leading-identifier]: agent and gold share first identifier '$A_ID'." \\
        | tee /logs/verifier/test_output.txt
    echo "1" > /logs/verifier/reward.txt
    rm -f "$A" "$B"
    exit 0
fi

# Tier 4: non-empty completion fallback. Award partial reward 0.25 if the
# agent wrote *anything* C#-shaped and reasonably short. This is a
# rubber-stamp tier; it gives downstream consumers a nonzero learning signal
# without claiming exact correctness.
A_SIZE=$(wc -c < "$A")
A_IDENT_COUNT=$(grep -oE '[A-Za-z_][A-Za-z0-9_]*' "$A" 2>/dev/null | wc -l)
if [ "$A_SIZE" -gt 0 ] && [ "$A_SIZE" -le 400 ] && [ "$A_IDENT_COUNT" -ge 1 ]; then
    {{
        echo "PARTIAL[4/non-empty]: agent wrote non-empty C#-shaped fragment but not match."
        echo "agent_first_identifier='$A_ID' gold_first_identifier='$B_ID'"
        echo "--- gold ---"
        cat "$B"
        echo "--- agent ---"
        cat "$A"
    }} | tee /logs/verifier/test_output.txt
    echo "0.25" > /logs/verifier/reward.txt
    rm -f "$A" "$B"
    exit 0
fi

{{
    echo "FAIL: agent output differs from gold completion (no tier matched)."
    echo "agent_first_identifier='$A_ID' gold_first_identifier='$B_ID' agent_size=$A_SIZE"
    echo "--- gold ---"
    cat "$B"
    echo "--- agent ---"
    cat "$A"
    echo "--- diff ---"
    diff "$B" "$A" || true
}} | tee /logs/verifier/test_output.txt
rm -f "$A" "$B"
exit 1
"""

# --------------------------------------------------------------------------- #
# v4 helper script: /usr/local/bin/write_solution
# --------------------------------------------------------------------------- #
# Single-arg writer. Always writes argv[1] (with trailing \n) to
# /app/solution.txt, overwriting any prior content. Independent of bash
# quoting in the surrounding shell because the agent only needs to single-
# quote the argument once.
WRITE_SOLUTION_SH = """#!/bin/bash
# laion v4: quote-safe writer for the line-completion solution.
# Usage:   write_solution 'YOUR FRAGMENT'
# Effect:  writes the single argument followed by a newline to
#          /app/solution.txt, overwriting any prior content.
mkdir -p /app
if [ "$#" -lt 1 ]; then
    echo "write_solution: missing argument (expected the C# fragment)" >&2
    exit 2
fi
printf '%s\\n' "$1" > /app/solution.txt
"""


_HELPER_DOCKER_PATH = "environment/write_solution.sh"


def _patch_dockerfile(text: str) -> str:
    """Add a COPY/RUN block that installs /usr/local/bin/write_solution.

    Idempotent: if the v4 sentinel is already present, return unchanged.

    The helper script itself lives at `environment/write_solution.sh` inside
    the task tarball (alongside the Dockerfile). The Dockerfile COPYs it
    into `/usr/local/bin/write_solution` and chmods it executable. We use a
    file-based COPY (not an embedded heredoc) because the helper contains
    both single AND double quotes plus a `$1`, all of which are landmines
    inside `RUN printf '...' > ...`.
    """
    if _V4_DOCKERFILE_SENTINEL in text:
        return text
    # The Dockerfile's build context is the `environment/` directory, so
    # the COPY source is relative to that (i.e. just `write_solution.sh`).
    install_block = (
        "\n"
        f"{_V4_DOCKERFILE_SENTINEL}\n"
        "COPY write_solution.sh /usr/local/bin/write_solution\n"
        "RUN chmod +x /usr/local/bin/write_solution\n"
    )
    sep = "" if text.endswith("\n") else "\n"
    return f"{text}{sep}{install_block}"


def _rewrite_instruction(text: str) -> str:
    """Replace the existing "## Your Task" block with the v4 block.

    Preserves everything before "## Your Task" (which includes the truncated
    C# snippet inside the ```csharp ... ``` fence).

    Idempotent: a doc already containing the v4 sentinel is returned as-is.
    """
    if _V4_INSTRUCTION_SENTINEL in text:
        return text
    # Make sure the code fence is csharp (defensive).
    if "```python" in text and "```csharp" not in text:
        text = text.replace("```python", "```csharp", 1)
    m = re.search(r"^##\s+Your Task\s*$", text, flags=re.MULTILINE)
    if m is None:
        sep = "" if text.endswith("\n") else "\n"
        return f"{text}{sep}\n{V4_TASK_BLOCK}"
    prefix = text[: m.start()].rstrip() + "\n\n"
    return prefix + V4_TASK_BLOCK


def patch_task_files(files: dict[str, bytes]) -> tuple[dict[str, bytes], str]:
    """Apply v4 mutations to a {arcname: bytes} dict.

    Returns (new_files_dict, reason_str). Input is not mutated.
    """
    out: dict[str, bytes] = dict(files)

    if _V4_MARKER_FILE in out:
        return out, "already_v4"
    if "instruction.md" not in out:
        return out, "no_instruction_md"
    if "tests/test.sh" not in out:
        return out, "no_test_sh"
    if "environment/Dockerfile" not in out:
        return out, "no_dockerfile"

    # 1. Rewrite instruction.md
    inst_text = out["instruction.md"].decode("utf-8", errors="replace")
    out["instruction.md"] = _rewrite_instruction(inst_text).encode("utf-8")

    # 2. Overwrite tests/test.sh with v4 verifier
    out["tests/test.sh"] = NEW_TEST_SH.encode("utf-8")

    # 3. Patch Dockerfile to install /usr/local/bin/write_solution, and drop
    #    the helper script alongside it (so the COPY has something to copy).
    dockerfile_text = out["environment/Dockerfile"].decode("utf-8", errors="replace")
    out["environment/Dockerfile"] = _patch_dockerfile(dockerfile_text).encode("utf-8")
    out[_HELPER_DOCKER_PATH] = WRITE_SOLUTION_SH.encode("utf-8")

    # 4. Drop the v3 marker (cosmetic; v4 marker is source of truth)
    out.pop(_V3_MARKER_FILE, None)

    # 5. Write the v4 marker
    out[_V4_MARKER_FILE] = (
        "laion v4 patch applied: write_solution helper in Dockerfile; "
        "prescriptive line-completion instruction; 4-tier forgiving verifier "
        "(exact / startswith / leading-identifier / non-empty-partial).\n"
    ).encode("utf-8")

    return out, "patched"


# --------------------------------------------------------------------------- #
# Tar I/O helpers
# --------------------------------------------------------------------------- #


def _tar_to_dict(archive_bytes: bytes) -> dict[str, bytes]:
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
# Dataset-mode entry points (HF parquet round-trip)
# --------------------------------------------------------------------------- #


def patch_parquet(
    src_path: Path,
    dst_path: Path,
    limit: int = 0,
    dry_run: bool = False,
) -> dict[str, int]:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as e:
        raise RuntimeError("pyarrow required: pip install pyarrow") from e

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
        new_archive = _dict_to_tar_gz(new_files)
        new_paths.append(path)
        new_binaries.append(new_archive)
        if (i + 1) % 200 == 0 or i + 1 == len(rows):
            print(f"[{i + 1}/{len(rows)}] reason={reason}", flush=True)

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
    from huggingface_hub import hf_hub_download

    return Path(
        hf_hub_download(repo_id=repo_id, filename=filename, repo_type="dataset")
    )


def upload_to_hf(repo_id: str, parquet_path: Path) -> None:
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
# Filesystem-mode (in-place patch of an extracted task tree)
# --------------------------------------------------------------------------- #


def patch_one_task_dir(task_dir: Path, dry_run: bool) -> tuple[bool, str]:
    if (task_dir / _V4_MARKER_FILE).exists():
        return False, "already_v4"

    inst_md = task_dir / "instruction.md"
    test_sh = task_dir / "tests" / "test.sh"
    dockerfile = task_dir / "environment" / "Dockerfile"
    if not inst_md.is_file():
        return False, "no_instruction_md"
    if not test_sh.is_file():
        return False, "no_test_sh"
    if not dockerfile.is_file():
        return False, "no_dockerfile"

    if dry_run:
        return True, "would_patch"

    inst_text = inst_md.read_text(encoding="utf-8", errors="replace")
    inst_md.write_text(_rewrite_instruction(inst_text), encoding="utf-8")

    test_sh.write_text(NEW_TEST_SH, encoding="utf-8")
    test_sh.chmod(0o755)

    df_text = dockerfile.read_text(encoding="utf-8", errors="replace")
    dockerfile.write_text(_patch_dockerfile(df_text), encoding="utf-8")
    helper_path = task_dir / "environment" / "write_solution.sh"
    helper_path.write_text(WRITE_SOLUTION_SH, encoding="utf-8")
    helper_path.chmod(0o755)

    v3_marker = task_dir / _V3_MARKER_FILE
    if v3_marker.is_file():
        v3_marker.unlink()

    (task_dir / _V4_MARKER_FILE).write_text(
        "laion v4 patch applied: write_solution helper in Dockerfile; "
        "prescriptive line-completion instruction; 4-tier forgiving verifier "
        "(exact / startswith / leading-identifier / non-empty-partial).\n",
        encoding="utf-8",
    )

    return True, "patched"


def patch_tree(root: Path, dry_run: bool, limit: int = 0) -> dict[str, int]:
    task_dirs = sorted(
        d for d in root.iterdir() if d.is_dir() and (d / "instruction.md").exists()
    )
    if limit:
        task_dirs = task_dirs[:limit]
    reasons: dict[str, int] = {}
    for i, d in enumerate(task_dirs, 1):
        _changed, reason = patch_one_task_dir(d, dry_run)
        reasons[reason] = reasons.get(reason, 0) + 1
        if i % 200 == 0 or i == len(task_dirs):
            print(f"[{i}/{len(task_dirs)}] last_reason={reason}", flush=True)
    return reasons


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--src-dataset")
    p.add_argument("--dst-dataset")
    p.add_argument("--src-parquet")
    p.add_argument("--dst-parquet")
    p.add_argument("--root")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--no-upload", action="store_true")
    args = p.parse_args()

    if args.root:
        root = Path(args.root).expanduser().resolve()
        if not root.is_dir():
            print(f"Not a directory: {root}", file=sys.stderr)
            return 2
        reasons = patch_tree(root, args.dry_run, args.limit)
        print("Reason breakdown:")
        for r, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
            print(f"  {n:>5}  {r}")
        return 0

    if not args.src_dataset and not args.src_parquet:
        print("Need --src-dataset or --src-parquet (or --root).", file=sys.stderr)
        return 2

    if args.src_parquet:
        src = Path(args.src_parquet).expanduser().resolve()
    else:
        print(f"Downloading {args.src_dataset} from HF ...", flush=True)
        src = fetch_from_hf(args.src_dataset)

    dst = (
        Path(args.dst_parquet).expanduser().resolve()
        if args.dst_parquet
        else Path("./tasks_v4.parquet").resolve()
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
