"""make_repos.py -- create 5 tiny local git repos, each with a simple bug + issue.

Each repo gets:
  * a single small Python module with an obvious bug,
  * a test file that fails because of the bug,
  * an ISSUE.md describing the problem in plain language,
  * an initialized git repo with one commit (swe-agent expects a git repo).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from config import REPOS_DIR

# (name, issue title, issue body, source filename, buggy source, test source)
TASKS = [
    (
        "offbyone",
        "Off-by-one in sum_range",
        "`sum_range(n)` should return the sum of integers from 1 to n inclusive, "
        "but it stops one short. Fix the off-by-one so `sum_range(5) == 15`.",
        "calc.py",
        "def sum_range(n):\n    total = 0\n    for i in range(1, n):  # BUG: excludes n\n        total += i\n    return total\n",
        "from calc import sum_range\n\ndef test_sum_range():\n    assert sum_range(5) == 15\n",
    ),
    (
        "returnsnone",
        "add() returns None instead of the sum",
        "The `add(a, b)` function computes the sum but forgets to return it, so it "
        "returns None. Make it return the sum.",
        "math_ops.py",
        "def add(a, b):\n    result = a + b\n    # BUG: missing return\n",
        "from math_ops import add\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    ),
    (
        "wrongop",
        "multiply() uses + instead of *",
        "`multiply(a, b)` is supposed to multiply its two arguments but it adds "
        "them. Fix the operator.",
        "arith.py",
        "def multiply(a, b):\n    return a + b  # BUG: should be *\n",
        "from arith import multiply\n\ndef test_multiply():\n    assert multiply(4, 5) == 20\n",
    ),
    (
        "reversed",
        "reverse_string returns the original string",
        "`reverse_string(s)` should return the reversed string but currently "
        "returns the input unchanged. Fix it so `reverse_string('abc') == 'cba'`.",
        "strutil.py",
        "def reverse_string(s):\n    return s  # BUG: not reversed\n",
        "from strutil import reverse_string\n\ndef test_reverse():\n    assert reverse_string('abc') == 'cba'\n",
    ),
    (
        "emptylist",
        "max_of returns 0 for non-empty lists",
        "`max_of(nums)` should return the maximum element of a non-empty list but "
        "always returns 0. Fix it so `max_of([3, 7, 2]) == 7`.",
        "listutil.py",
        "def max_of(nums):\n    return 0  # BUG: ignores nums\n",
        "from listutil import max_of\n\ndef test_max_of():\n    assert max_of([3, 7, 2]) == 7\n",
    ),
]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def make_all() -> list[Path]:
    created = []
    for name, title, body, fname, src, test in TASKS:
        repo = REPOS_DIR / name
        repo.mkdir(parents=True, exist_ok=True)
        (repo / fname).write_text(src, encoding="utf-8")
        (repo / f"test_{fname}").write_text(test, encoding="utf-8")
        (repo / "ISSUE.md").write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
        if not (repo / ".git").exists():
            _git(repo, "init", "-q")
            _git(repo, "config", "user.email", "tokviz@example.com")
            _git(repo, "config", "user.name", "tokviz")
        _git(repo, "add", "-A")
        try:
            _git(repo, "commit", "-q", "-m", f"initial: {name} with bug")
        except subprocess.CalledProcessError:
            pass  # nothing to commit (re-run)
        created.append(repo)
        print("repo:", repo)
    return created


if __name__ == "__main__":
    make_all()
