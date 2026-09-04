#!/usr/bin/env python3
"""nemotron-cpp-v2 transform: re-wire each DCAgent/exp_rpt_nemotron-cpp task into
an AGENT-LINKED, oracle-verifiable Harbor task.

Root cause of the old dataset (proven in
agent_logs/2026-06-23_nemotron_cpp_verifier_fix.md): each task's
tests/test_solution.cpp EMBEDS a full reference implementation of the class
under test and never #includes the agent's /app header, so the agent's solution
is never linked and the reward is vacuous.

Fix (per task): split test_solution.cpp into
  - the reference prelude  = [includes] + [impl + exception classes + constants +
    fixture classes], with main() and every TEST*/TEST_F block removed.  This is
    the GOLD solution; it is materialized to /app/<hdr> by solution/solve.sh.
  - the test body          = [TEST*/TEST_F blocks] + a fresh main(), prefixed with
    `#include <gtest/gtest.h>` and `#include "<hdr>"`.  The test now LINKS the
    agent's /app/<hdr> (compiled with -I/app); the embedded impl is gone.

A task is KEPT only if its transformed GOLD compiles + all tests pass under the
shared gcc:13 + libgtest-dev image (the oracle gate is the filter); tasks that
reference external libraries (curl, nlohmann/json, selenium, sqlite3, boost, …)
are dropped (they would explode the Daytona snapshot count).
"""

from __future__ import annotations

import re

TEST_BLOCK = re.compile(r"\bTEST(?:_F|_P)?\s*\([^)]*\)\s*\{")
MAIN_BLOCK = re.compile(r"\bint\s+main\s*\([^)]*\)\s*\{")
GTEST_INC = re.compile(r'^[ \t]*#\s*include\s*[<"]gtest/gtest\.h[>"][ \t]*\r?\n', re.M)
EXTERNAL_INC = re.compile(r'#\s*include\s+[<"]([^>"]+)[>"]')


def _extract_braced(s: str, start_brace_idx: int) -> int:
    """Index of the matching close brace for the '{' at start_brace_idx, or -1."""
    depth = 0
    k = start_brace_idx
    n = len(s)
    while k < n:
        c = s[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return k
        k += 1
    return -1


def split_tests(src: str) -> tuple[str, list[str]]:
    """Return (body_without_test_blocks_or_main, [test_blocks])."""
    blocks: list[str] = []
    keep: list[str] = []
    pos = 0
    while True:
        m = TEST_BLOCK.search(src, pos)
        if not m:
            keep.append(src[pos:])
            break
        keep.append(src[pos : m.start()])
        end = _extract_braced(src, m.end() - 1)
        if end < 0:  # unbalanced -> bail, treat remainder as body
            keep.append(src[m.start() :])
            break
        blocks.append(src[m.start() : end + 1])
        pos = end + 1
    body = "".join(keep)
    # strip main()
    mm = MAIN_BLOCK.search(body)
    if mm:
        end = _extract_braced(body, mm.end() - 1)
        if end > 0:
            body = body[: mm.start()] + body[end + 1 :]
    return body, blocks


def has_external_lib(src: str) -> str | None:
    """Return the first external (non-stdlib, non-gtest/gmock) include, or None.

    Heuristic: angle/quote includes that have a path separator or a .h/.hpp
    extension are external project libs (stdlib headers are extension-less,
    e.g. <string>, <vector>)."""
    for inc in EXTERNAL_INC.findall(src):
        if inc.startswith("gtest/"):
            continue  # gtest is in the base image
        if inc.startswith("gmock/"):
            return "gmock"  # gmock not in the base image -> drop
        if "/" in inc or inc.endswith((".h", ".hpp")):
            return inc
    return None


def header_name_from_instruction(instr: str, fallback: str = "solution.hpp") -> str:
    """Best-effort agent-deliverable header name from instruction.md."""
    m = re.findall(r"/app/([A-Za-z0-9_\-]+\.(?:hpp|h))\b", instr)
    if m:
        return m[0]
    m = re.findall(r"\b([A-Za-z0-9_\-]+\.(?:hpp|h))\b", instr)
    if m:
        return m[0]
    return fallback


def transform(instr: str, test_src: str) -> tuple[dict | None, str]:
    """Build the v2 artifacts for one task.

    Returns (artifacts_dict, reason).  artifacts_dict is None if the task is
    structurally unusable (external lib / no test blocks)."""
    ext = has_external_lib(test_src)
    if ext:
        return None, f"external_lib:{ext}"
    body, blocks = split_tests(test_src)
    if not blocks:
        return None, "no_test_blocks"
    hdr = header_name_from_instruction(instr)
    header_src = body.strip() + "\n"
    new_test = (
        "#include <gtest/gtest.h>\n"
        f'#include "{hdr}"\n\n'
        + "\n\n".join(b.strip() for b in blocks)
        + "\n\nint main(int argc, char** argv) {\n"
        "    ::testing::InitGoogleTest(&argc, argv);\n"
        "    return RUN_ALL_TESTS();\n}\n"
    )
    return {"hdr": hdr, "header_src": header_src, "new_test": new_test}, "ok"
