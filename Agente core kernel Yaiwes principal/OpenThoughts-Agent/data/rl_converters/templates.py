"""Parameterized verifier templates for RL conversion.

Every template follows the nemotron-cpp-v2 contract:
1. echo 0 > reward.txt (default-fail)
2. Compile/run agent code without pipe masking (capture real exit code)
3. Require tests > 0 AND failures == 0
4. python3 -m pytest /tests/test_state.py for pass_ratio-parseable output

Select by language: get_test_sh("python"), get_dockerfile("python"), etc.
"""

TEST_STATE_PY = '''\
"""Harbor state assertion: reward.txt must be "1" (verifier passed)."""
from pathlib import Path

REWARD = Path("/logs/verifier/reward.txt")


def test_reward_is_pass():
    assert REWARD.exists(), f"Reward file {REWARD} not written by the verifier"
    val = REWARD.read_text().strip()
    assert val == "1", f"Task not solved (reward.txt={val!r})"
'''

CONFIG_JSON = """\
{
  "tests": {
    "test_reward_is_pass": {
      "weight": 1.0
    }
  }
}
"""

TASK_TOML = """\
version = "1.0"

[agent]
timeout_sec = 900.0

[metadata]
author_name = "Sandboxes"
author_email = "sandboxes@sandboxes.com"
difficulty = "medium"
category = "sandbox"
tags = ["sandbox"]

[verifier]
restart_environment = false
timeout_sec = 720.0
"""

# ---------------------------------------------------------------------------
# Dockerfiles by language
# ---------------------------------------------------------------------------

DOCKERFILES = {
    "python": """\
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y python3-pytest && rm -rf /var/lib/apt/lists/*
""",
    "java": """\
FROM eclipse-temurin:17-jdk

WORKDIR /app

RUN apt-get update && apt-get install -y maven bash python3 python3-pytest && rm -rf /var/lib/apt/lists/*
""",
    "cpp": """\
FROM gcc:13

WORKDIR /app

RUN apt-get update && apt-get install -y cmake libgtest-dev bash python3 python3-pytest && \\
    rm -rf /var/lib/apt/lists/*
RUN cd /usr/src/gtest && cmake . && make && cp lib/*.a /usr/lib/
""",
    "rust": """\
FROM rust:1.75

WORKDIR /app

RUN apt-get update && apt-get install -y python3 python3-pytest && rm -rf /var/lib/apt/lists/*
""",
    "csharp": """\
FROM mcr.microsoft.com/dotnet/sdk:8.0

WORKDIR /app

RUN apt-get update && apt-get install -y python3 python3-pytest && rm -rf /var/lib/apt/lists/*
""",
    "bash": """\
FROM ubuntu:24.04

WORKDIR /app

RUN apt-get update && apt-get install -y python3 python3-pytest && rm -rf /var/lib/apt/lists/*
""",
    "ruby": """\
FROM ruby:3.2

WORKDIR /app

RUN apt-get update && apt-get install -y python3 python3-pytest && rm -rf /var/lib/apt/lists/*
""",
}

# ---------------------------------------------------------------------------
# test.sh by language
# ---------------------------------------------------------------------------

TEST_SHS = {
    "python": """\
#!/bin/bash
set -u
REWARD=/logs/verifier/reward.txt
mkdir -p /logs/verifier
echo 0 > "$REWARD"

cd /app

if [ -f pom.xml ]; then
    mkdir -p /app/src/test/java
    cp /tests/TestSolution.java /app/src/test/java/ 2>/dev/null
    timeout 300 mvn test > /logs/verifier/test_output.txt 2>&1
    MVN_EXIT=$?
    if [ "$MVN_EXIT" -eq 0 ] && grep -qE "Tests run:[[:space:]]*[1-9]" /logs/verifier/test_output.txt; then
        echo 1 > "$REWARD"
    fi
else
    cp /tests/test_solution.py /app/ 2>/dev/null
    timeout 300 python3 -m pytest /app/test_solution.py --tb=short > /logs/verifier/test_output.txt 2>&1
    PYTEST_EXIT=$?
    if [ "$PYTEST_EXIT" -eq 0 ]; then
        echo 1 > "$REWARD"
    fi
fi

python3 -m pytest /tests/test_state.py --tb=short 2>/dev/null
exit 0
""",
    "java": """\
#!/bin/bash
set -u
REWARD=/logs/verifier/reward.txt
mkdir -p /logs/verifier
echo 0 > "$REWARD"

cd /app

if [ ! -f pom.xml ]; then
    echo "No pom.xml -> reward 0"
else
    mkdir -p /app/src/test/java
    cp /tests/TestSolution.java /app/src/test/java/
    timeout 300 mvn test > /logs/verifier/test_output.txt 2>&1
    MVN_EXIT=$?
    if [ "$MVN_EXIT" -eq 0 ] && grep -qE "Tests run:[[:space:]]*[1-9]" /logs/verifier/test_output.txt; then
        echo 1 > "$REWARD"
    fi
fi

python3 -m pytest /tests/test_state.py --tb=short 2>/dev/null
exit 0
""",
    "cpp": """\
#!/bin/bash
set -u
REWARD=/logs/verifier/reward.txt
mkdir -p /logs/verifier
echo 0 > "$REWARD"

cd /app
rm -f /tmp/test_runner /logs/verifier/gtest.json

g++ -std=c++17 -I/app -o /tmp/test_runner /tests/test_solution.cpp \\
    -lgtest -lgtest_main -pthread > /logs/verifier/compile_output.txt 2>&1
CC=$?
if [ "$CC" -ne 0 ] || [ ! -x /tmp/test_runner ]; then
    echo "COMPILE FAILED -> reward 0"
    python3 -m pytest /tests/test_state.py --tb=short 2>/dev/null
    exit 0
fi

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

python3 -m pytest /tests/test_state.py --tb=short 2>/dev/null
exit 0
""",
    "rust": """\
#!/bin/bash
set -u
REWARD=/logs/verifier/reward.txt
mkdir -p /logs/verifier
echo 0 > "$REWARD"

cd /app

if [ ! -f Cargo.toml ]; then
    echo "No Cargo.toml -> reward 0"
else
    mkdir -p /app/tests
    cp /tests/test_solution.rs /app/tests/ 2>/dev/null
    timeout 300 cargo test > /logs/verifier/test_output.txt 2>&1
    CARGO_EXIT=$?
    if [ "$CARGO_EXIT" -eq 0 ]; then
        echo 1 > "$REWARD"
    fi
fi

python3 -m pytest /tests/test_state.py --tb=short 2>/dev/null
exit 0
""",
    "csharp": """\
#!/bin/bash
set -u
REWARD=/logs/verifier/reward.txt
mkdir -p /logs/verifier
echo 0 > "$REWARD"

cd /app

if [ ! -f *.csproj ] && [ ! -f *.sln ]; then
    echo "No .csproj/.sln -> reward 0"
else
    mkdir -p /app/tests
    cp /tests/TestSolution.cs /app/tests/ 2>/dev/null
    timeout 300 dotnet test > /logs/verifier/test_output.txt 2>&1
    DOTNET_EXIT=$?
    if [ "$DOTNET_EXIT" -eq 0 ]; then
        echo 1 > "$REWARD"
    fi
fi

python3 -m pytest /tests/test_state.py --tb=short 2>/dev/null
exit 0
""",
    "bash": """\
#!/bin/bash
set -u
REWARD=/logs/verifier/reward.txt
mkdir -p /logs/verifier
echo 0 > "$REWARD"

cd /app
timeout 300 bash /tests/test_solution.sh > /logs/verifier/test_output.txt 2>&1
SCRIPT_EXIT=$?
if [ "$SCRIPT_EXIT" -eq 0 ]; then
    echo 1 > "$REWARD"
fi

python3 -m pytest /tests/test_state.py --tb=short 2>/dev/null
exit 0
""",
    "ruby": """\
#!/bin/bash
set -u
REWARD=/logs/verifier/reward.txt
mkdir -p /logs/verifier
echo 0 > "$REWARD"

cd /app
cp /tests/test_spec.rb /app/ 2>/dev/null
timeout 300 rspec /app/test_spec.rb --format documentation > /logs/verifier/test_output.txt 2>&1
RSPEC_EXIT=$?
if [ "$RSPEC_EXIT" -eq 0 ]; then
    echo 1 > "$REWARD"
fi

python3 -m pytest /tests/test_state.py --tb=short 2>/dev/null
exit 0
""",
}


def get_test_sh(language: str) -> str:
    return TEST_SHS[language]


def get_dockerfile(language: str) -> str:
    return DOCKERFILES[language]


def get_test_state_py() -> str:
    return TEST_STATE_PY


def get_config_json() -> str:
    return CONFIG_JSON


def get_task_toml(tags: list[str] | None = None) -> str:
    if tags:
        tag_str = ", ".join(f'"{t}"' for t in tags)
        return TASK_TOML.replace('tags = ["sandbox"]', f"tags = [{tag_str}]")
    return TASK_TOML


SUPPORTED_LANGUAGES = list(TEST_SHS.keys())
