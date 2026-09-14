# Startup Bug Investigation — v0.88.0 → v0.90.0

**Date:** 2026-04-11
**Investigator:** stabilization task 1
**Severity:** High — affects every PyPI user who installs via `pip install cognithor`

## Summary

PyPI currently serves **v0.88.0** while the local tree is at **v0.90.0**.
The v0.90.0 release introduced a full package rename from `jarvis` to `cognithor`
(source tree, entry points, import paths). This means any user on v0.88.0 may
have stale internal paths that reference the old `jarvis` package name, and the
jump to v0.90.0 will be the first published version under the new name.

## Problem

1. **No post-build smoke test in CI.** The GitHub Actions publish workflow
   (`publish.yml`) builds a wheel and uploads it directly to PyPI without ever
   installing the artifact and running a basic import / entry-point check.

2. **Rename risk.** The `jarvis` → `cognithor` rename touches every import path,
   the `[project.scripts]` entry point, and package discovery config. A single
   missed reference will cause `ModuleNotFoundError` at startup for end users.

3. **Version gap.** There is no published v0.89.x. Users upgrading from v0.88.0
   to v0.90.0 get every change at once with no incremental validation.

## Root Cause

CI does not install and test the built artifact before uploading to PyPI. The
wheel is produced by `python -m build` and then handed straight to
`twine upload` (or the equivalent PyPI action) with zero validation.

## Affected Files

| File | Issue |
|------|-------|
| `.github/workflows/publish.yml` | No install-and-smoke-test step after wheel build |
| `pyproject.toml` | Entry point `cognithor = "cognithor.__main__:main"` — correct locally but never verified in CI |
| `src/cognithor/__init__.py` | `__version__` must match `pyproject.toml` — no automated check |

## Fix Plan

1. **Add release smoke tests** (this task) — `tests/release/test_pypi_startup.py`
   validates version consistency, package data, importability, and wheel build.

2. **Add pre-release validation job to `publish.yml`** (task 4):
   - Build wheel in isolated step.
   - Install it into a fresh venv.
   - Run `cognithor --version` and verify output matches expected version.
   - Run `python -m pytest tests/release/ -v` against the installed package.
   - Only proceed to PyPI upload if all checks pass.

3. **Consider a v0.89.0 bridge release** (optional) — publish under the old
   `jarvis` name with a deprecation warning pointing users to `cognithor`.

## Reproduction

```bash
# Show the version gap
pip install cognithor          # installs 0.88.0 from PyPI
python -c "import cognithor; print(cognithor.__version__)"  # 0.88.0

# Local tree
python -c "import cognithor; print(cognithor.__version__)"  # 0.90.0
```
