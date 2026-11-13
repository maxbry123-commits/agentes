"""T22 — scan paths for banned vendor LLM imports/calls.

Does not delete files. Does not flag gateway tests by default.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Sequence

BANNED_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.MULTILINE)
    for p in (
        r"^\s*(?:import|from)\s+openai\b",
        r"^\s*(?:import|from)\s+anthropic\b",
        r"^\s*(?:import|from)\s+groq\b",
        r"^\s*(?:import|from)\s+together\b",
        r"^\s*(?:import|from)\s+mistralai\b",
        r"^\s*(?:import|from)\s+cohere\b",
        r"^\s*(?:import|from)\s+google\.generativeai\b",
        r"^\s*from\s+langchain_openai\b",
        r"^\s*from\s+openai\s+import\b",
    )
)

_SKIP_PARTS = frozenset({".git", "__pycache__", "node_modules", ".venv", "venv"})
_TEST_HINTS = ("/tests/", "\\tests\\", "/test_", "\\test_")


def _as_roots(root: Path | str | Sequence[str | Path] | None, roots: list[str] | None) -> list[Path]:
    items: list[Path] = []
    if roots:
        items.extend(Path(r) for r in roots)
    if root is None:
        pass
    elif isinstance(root, (str, Path)):
        items.append(Path(root))
    else:
        items.extend(Path(r) for r in root)
    if not items:
        raise ValueError("root or roots required")
    return items


def _is_test_path(path: Path) -> bool:
    text = str(path).replace("\\", "/")
    name = path.name
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    return "/tests/" in f"/{text}/"


def _iter_py(root: Path, globs: Iterable[str]) -> Iterable[Path]:
    if root.is_file() and root.suffix == ".py":
        yield root
        return
    if not root.exists():
        return
    for pattern in globs:
        for p in root.rglob(pattern.replace("**/", "") if pattern.startswith("**/") else pattern):
            if not p.is_file() or p.suffix != ".py":
                continue
            if any(part in _SKIP_PARTS for part in p.parts):
                continue
            yield p


def scan_paths_for_llm_ban(
    root: Path | str | Sequence[str | Path] | None = None,
    extra_globs: list[str] | None = None,
    roots: list[str] | None = None,
    *,
    include_tests: bool = False,
) -> list[str]:
    """Return relative paths that import/call banned LLM vendors."""
    globs = extra_globs or ["**/*.py"]
    hits: list[str] = []
    seen: set[str] = set()
    for base in _as_roots(root, roots):
        base = base.resolve()
        for path in _iter_py(base, globs):
            if not include_tests and _is_test_path(path):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not any(pat.search(text) for pat in BANNED_PATTERNS):
                continue
            try:
                rel = str(path.resolve().relative_to(base))
            except ValueError:
                rel = str(path)
            if rel not in seen:
                seen.add(rel)
                hits.append(rel)
    return hits


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bad = root / "vendor_call.py"
        good = root / "clean.py"
        testp = root / "tests" / "test_gateway.py"
        testp.parent.mkdir(parents=True)
        bad.write_text("import openai\n", encoding="utf-8")
        good.write_text("x = 1\n", encoding="utf-8")
        testp.write_text("from openai import OpenAI\n", encoding="utf-8")
        hits = scan_paths_for_llm_ban(root)
        assert hits == ["vendor_call.py"], hits
        hits_all = scan_paths_for_llm_ban(root, include_tests=True)
        assert "vendor_call.py" in hits_all
        assert any("test_gateway.py" in h for h in hits_all)
        print("ok", hits)
