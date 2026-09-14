"""
Cognithor · Shared Test-Fixtures.

Alle Tests nutzen ein temporäres Verzeichnis statt ~/.cognithor/.
So sind Tests isoliert und reproduzierbar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cognithor.config import CognithorConfig, ensure_directory_structure
from cognithor.i18n import set_locale

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def _set_test_locale():
    """Ensure all tests run with German locale (backwards compatibility)."""
    set_locale("de")
    yield
    set_locale("de")


@pytest.fixture(autouse=True)
def _disable_file_encryption(monkeypatch):
    """Disable transparent file encryption for all tests.

    Tests write files to tmp_path and read them back as plaintext.
    If a real keyring key is present the EncryptedFileIO singleton would
    encrypt those files, causing assertions like
        assert "# 2026-02-21" in file.read_text()
    to fail because the file contains the COGNITHOR_ENC_V1 ciphertext.

    We patch the singleton's _fernet attribute to None so that
    EncryptedFileIO.write() / read() fall back to plain UTF-8 I/O.
    The singleton is re-initialized lazily, so we also force
    _initialized=True to prevent _ensure_init() from re-enabling it.
    """
    try:
        from cognithor.security.encrypted_file import efile

        monkeypatch.setattr(efile, "_fernet", None)
        monkeypatch.setattr(efile, "_initialized", True)
    except Exception:
        # If the module is unavailable, there is nothing to patch.
        pass


@pytest.fixture
def tmp_jarvis_home(tmp_path: Path) -> Path:
    """Temporäres Jarvis-Home-Verzeichnis."""
    return tmp_path / ".cognithor"


@pytest.fixture
def config(tmp_jarvis_home: Path) -> CognithorConfig:
    """CognithorConfig mit temporärem Home-Verzeichnis."""
    return CognithorConfig(cognithor_home=tmp_jarvis_home)


@pytest.fixture
def initialized_config(config: CognithorConfig) -> CognithorConfig:
    """CognithorConfig mit erstellter Verzeichnisstruktur."""
    ensure_directory_structure(config)
    return config
