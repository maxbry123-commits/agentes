# Cognithor Stabilization Report

**Date:** 2026-04-12
**Branch:** stabilization/pre-v1-hardening
**Scope:** Bug fixes, release pipeline hardening, test coverage, documentation honesty

## Executive Summary

The release pipeline lacked post-build smoke testing, environment variable overrides were silently broken for backward-compatible JARVIS_* prefixes and multi-word keys, and README numeric claims were stale. All issues have been fixed with 17 new regression tests, a hardened publish workflow, and an automated claims verification script. Remaining risks are limited to the already-published PyPI v0.88.0 (pre-rename, possibly broken) and the lack of mypy --strict and Docker-based E2E tests in CI.

## Reproduced Bugs

### Bug 1: PyPI Startup Risk
- **Root Cause:** No post-build smoke test in publish workflow; built wheel goes to PyPI untested
- **Fix:** Added pre-release validation job with wheel install + smoke test on 2 OS
- **Test:** tests/release/test_pypi_startup.py (4 tests)

### Bug 2: Environment Variable Override Broken
- **Root Cause:** CONFIG_REFERENCE.md documented JARVIS_* prefix, but code only scanned COGNITHOR_*. Also, multi-word top-level keys (owner_name, llm_backend_type) were incorrectly split into nested dicts
- **Fix:** _apply_env_overrides now processes both JARVIS_* and COGNITHOR_* (COGNITHOR wins). Top-level key fallback added. Docs updated.
- **Test:** tests/config/test_env_overrides.py (11 tests)

### Bug 3: Bootstrap Endpoint (Not a Bug — Security Design)
- **Status:** Documented as known limitation, regression test added
- **Test:** tests/test_security/test_bootstrap_binding.py (2 tests)
- **Ticket:** docs/open_issues/networked_bootstrap.md

### Bug 4: Installer Pipeline
- **Root Cause:** Makefile VENV path still used .jarvis (pre-rename), no pre-release validation script
- **Fix:** Makefile updated to .cognithor, prepare_release.py created
- **Script:** scripts/prepare_release.py

## New Test Suites

| Suite | Tests | Purpose |
|-------|-------|---------|
| tests/release/test_pypi_startup.py | 4 | Wheel build, version sync, package data, entry point |
| tests/config/test_env_overrides.py | 11 | All documented env var overrides |
| tests/test_security/test_bootstrap_binding.py | 2 | Bootstrap token security |
| **Total new** | **17** | |

## Release Pipeline Changes

- ci.yml: Version consistency check (pyproject.toml vs __init__.py)
- publish.yml: Pre-release validation job (build wheel -> install in clean env -> smoke test) on ubuntu + windows, gating publish

## README Audit

- Added pre-v1.0 Beta disclaimer
- Fixed: LLM providers 18->19, MCP tools 130+->145+
- Created scripts/verify_readme_claims.py for ongoing validation

## Known Open Points

1. PyPI v0.88.0 may still be broken (pre-rename version) — cannot be fixed retroactively
2. Networked bootstrap for LAN/container deployments — documented, not implemented (docs/open_issues/networked_bootstrap.md)
3. No mypy --strict validation in CI yet
4. Installer E2E tests (Docker-based) not implemented — would require container infrastructure

## Recommended Next Steps for v1.0.0

1. Publish v0.90.0 to PyPI using the hardened pipeline
2. Add mypy --strict to CI
3. Implement Ed25519 capability token for networked bootstrap
4. Add Docker-based installer E2E tests
5. Consider yanking broken PyPI versions (v0.88.0 and earlier if affected)
