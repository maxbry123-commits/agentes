"""Release test configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "release: Release validation tests (slow)")
