"""Smoke tests for wheel / PyPI release readiness.

These tests verify that the built package is consistent and functional
before it ever reaches PyPI.
"""

from __future__ import annotations

import importlib
import importlib.util
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_pyproject_version() -> str:
    """Return the version string from pyproject.toml."""
    pp = PROJECT_ROOT / "pyproject.toml"
    with pp.open("rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def _read_init_version() -> str:
    """Return __version__ from src/cognithor/__init__.py."""
    init = PROJECT_ROOT / "src" / "cognithor" / "__init__.py"
    text = init.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    assert match, "Could not find __version__ in __init__.py"
    return match.group(1)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPyPIStartup:
    """Validate that the package is release-ready."""

    def test_version_consistency(self) -> None:
        """pyproject.toml and __init__.py must declare the same version."""
        pyproject_ver = _read_pyproject_version()
        init_ver = _read_init_version()
        assert pyproject_ver == init_ver, (
            f"Version mismatch: pyproject.toml={pyproject_ver!r}, __init__.py={init_ver!r}"
        )

    def test_package_data_included(self) -> None:
        """Critical non-Python data files must exist in the source tree."""
        src = PROJECT_ROOT / "src" / "cognithor"
        required = [
            src / "i18n" / "locales" / "de.json",
            src / "i18n" / "locales" / "en.json",
            src / "cli" / "model_registry.json",
        ]
        missing = [str(p) for p in required if not p.exists()]
        assert not missing, f"Missing package data files: {missing}"

    @pytest.mark.release
    @pytest.mark.skipif(
        not importlib.util.find_spec("build"),
        reason="'build' package not installed — skipped in CI",
    )
    def test_wheel_builds_cleanly(self, tmp_path: Path) -> None:
        """A wheel can be built from the current tree without errors."""
        result = subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(tmp_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Wheel build failed (rc={result.returncode}):\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        wheels = list(tmp_path.glob("*.whl"))
        assert len(wheels) == 1, f"Expected 1 .whl, found {len(wheels)}: {wheels}"

    def test_entry_point_importable(self) -> None:
        """The declared entry point module must be importable."""
        mod = importlib.import_module("cognithor.__main__")
        assert callable(getattr(mod, "main", None)), "cognithor.__main__.main is not callable"
