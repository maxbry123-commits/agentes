#!/usr/bin/env python3
"""File templates for nemotron-cpp-v2 Harbor tasks.

Snapshot safety: every task uses the SAME environment/Dockerfile (one unique
content hash -> exactly 1 Daytona snapshot).  Nothing task-specific is baked
into the image; the gold header is materialized at trial time by solve.sh and
the test compiles against the agent's /app at trial time.
"""

# --- single shared environment (1 snapshot) -------------------------------
# Matches the original tasks' build env (gcc:13 + libgtest-dev) so the embedded
# reference impls compile exactly as they did when validated.
DOCKERFILE = """\
FROM gcc:13

WORKDIR /app

# Build tools + gtest + python3 (test.sh parses gtest JSON with python3)
RUN apt-get update && apt-get install -y cmake libgtest-dev bash python3 && \\
    rm -rf /var/lib/apt/lists/*

# Build and install gtest static libs
RUN cd /usr/src/gtest && cmake . && make && cp lib/*.a /usr/lib/
"""

# --- task.toml ------------------------------------------------------------
TASK_TOML = """\
version = "1.0"

[agent]
timeout_sec = 900.0

[metadata]
author_name = "Sandboxes"
author_email = "sandboxes@sandboxes.com"
difficulty = "medium"
category = "sandbox"
tags = ["sandbox", "cpp", "gtest"]

[verifier]
restart_environment = false
timeout_sec = 720.0
"""

# --- tests/test.sh --------------------------------------------------------
# Sound verifier:
#   * default reward 0 (written up-front), no EXIT-trap that defaults to 1
#   * compile-fail -> reward 0
#   * runs the gtest binary with --gtest_output=json and requires
#     tests_run > 0 AND failures == 0 AND errors == 0
#   * the binary LINKS the agent's /app/<hdr> via -I/app (no embedded impl).
TEST_SH = """\
#!/bin/bash
# Agent-linked C++/gtest verifier. reward=1 ONLY if the test binary compiles
# against the agent's /app solution, runs >0 tests, and all pass.
set -u
REWARD=/logs/verifier/reward.txt
mkdir -p /logs/verifier
echo 0 > "$REWARD"   # default fail; only an explicit pass overwrites this

cd /app

# Start from a clean slate: remove any stale binary / report so we never
# pass on leftovers from a previous run (compile must (re)create the binary).
rm -f /tmp/test_runner /logs/verifier/gtest.json

echo "Compiling tests against agent solution in /app ..."
# NOTE: do NOT pipe g++ through tee (a pipe would mask g++'s exit status and
# could let us run a stale binary). Capture g++'s real return code.
g++ -std=c++17 -I/app -o /tmp/test_runner /tests/test_solution.cpp \\
    -lgtest -lgtest_main -pthread > /logs/verifier/compile_output.txt 2>&1
CC=$?
if [ "$CC" -ne 0 ] || [ ! -x /tmp/test_runner ]; then
    echo "COMPILE FAILED -> reward 0"
    cat /logs/verifier/compile_output.txt
    exit 0
fi

echo "Running tests ..."
timeout 300 /tmp/test_runner --gtest_output=json:/logs/verifier/gtest.json \\
    > /logs/verifier/test_output.txt 2>&1

python3 - <<'PY'
import json, sys
try:
    d = json.load(open("/logs/verifier/gtest.json"))
except Exception as e:
    print("Could not parse gtest json:", e); sys.exit(0)
tests = int(d.get("tests", 0))
fails = int(d.get("failures", 0)) + int(d.get("errors", 0))
print(f"tests={tests} failures+errors={fails}")
if tests > 0 and fails == 0:
    open("/logs/verifier/reward.txt", "w").write("1")
    print("PASS -> reward 1")
else:
    print("FAIL/empty -> reward 0")
PY

exit 0
"""

# --- tests/test_state.py --------------------------------------------------
TEST_STATE_PY = '''\
"""Harbor state assertion: the in-container verifier (tests/test.sh) must have
written reward.txt == "1" (test binary compiled against the agent's /app
solution, discovered >0 tests, and all passed)."""
from pathlib import Path

REWARD = Path("/logs/verifier/reward.txt")


def test_reward_is_pass():
    assert REWARD.exists(), f"Reward file {REWARD} not written by the verifier"
    val = REWARD.read_text().strip()
    assert val == "1", f"Task not solved (reward.txt={val!r})"
'''

# --- tests/config.json ----------------------------------------------------
CONFIG_JSON = """\
{
  "tests": {
    "test_reward_is_pass": {
      "weight": 1.0
    }
  }
}
"""

# --- instruction.md preamble (prepended to the original spec) -------------
INSTRUCTION_PREAMBLE_TMPL = """\
# C++ implementation task

Implement a header-only C++ solution at **`/app/{hdr}`**. A gtest test suite at
`/tests/test_solution.cpp` will be compiled against your header (with `-I/app`)
and must compile and pass. Your header must provide every type, function, class,
and constant the tests reference, with the exact names, signatures, and behavior
described below. Do not edit the tests.

---

"""


def render_solve_sh(hdr: str, header_src: str) -> str:
    """Gold solution: write the reference header to /app/<hdr> verbatim."""
    # Use a randomized heredoc sentinel-free approach: base64 to avoid any
    # delimiter collision with C++ source content.
    import base64

    b64 = base64.b64encode(header_src.encode("utf-8")).decode("ascii")
    # chunk to keep lines reasonable
    chunks = "\n".join(b64[i : i + 100] for i in range(0, len(b64), 100))
    return (
        "#!/bin/bash\n"
        "set -e\n"
        "mkdir -p /app\n"
        f"base64 -d > '/app/{hdr}' <<'B64EOF'\n"
        f"{chunks}\n"
        "B64EOF\n"
        f'echo "wrote /app/{hdr}"\n'
    )
