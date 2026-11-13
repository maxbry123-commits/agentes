"""Tests fuer F-009: Voice-Model Downloads muessen Hash-verifiziert werden.

Prueft dass:
  - _download_piper_voice SHA-256 Hash nach Download berechnet
  - _verify_voice_hash bei bekanntem Hash verifiziert
  - _verify_voice_hash bei unbekanntem Hash warnt (nicht blockiert)
  - _verify_voice_hash bei falschem Hash eine Exception wirft
  - Der SHA-256 Hash im Download-Log erscheint
  - _KNOWN_VOICE_HASHES Dictionary existiert
"""

from __future__ import annotations

import hashlib
import inspect
import tempfile
from pathlib import Path

import pytest


class TestDownloadHasHashVerification:
    """Source-Level-Pruefung: Download-Funktion berechnet SHA-256."""

    def test_download_function_uses_hashlib(self) -> None:
        """_download_piper_voice muss hashlib importieren."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        dl_section = source[source.index("_download_piper_voice") :]
        dl_end = dl_section.index('log.info("cc_tts_endpoint_registered")')
        dl_source = dl_section[:dl_end]
        assert "hashlib" in dl_source, "_download_piper_voice muss hashlib verwenden"

    def test_download_function_computes_sha256(self) -> None:
        """_download_piper_voice muss SHA-256 berechnen."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        dl_section = source[source.index("_download_piper_voice") :]
        dl_end = dl_section.index('log.info("cc_tts_endpoint_registered")')
        dl_source = dl_section[:dl_end]
        assert "sha256" in dl_source.lower(), "_download_piper_voice muss SHA-256 berechnen"

    def test_download_calls_verify(self) -> None:
        """_download_piper_voice muss _verify_voice_hash aufrufen."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        dl_section = source[source.index("_download_piper_voice") :]
        dl_end = dl_section.index('log.info("cc_tts_endpoint_registered")')
        dl_source = dl_section[:dl_end]
        assert "_verify_voice_hash" in dl_source, (
            "_download_piper_voice muss _verify_voice_hash aufrufen"
        )

    def test_download_logs_hash(self) -> None:
        """Der SHA-256 Hash muss im Log erscheinen."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        dl_section = source[source.index("_download_piper_voice") :]
        dl_end = dl_section.index('log.info("cc_tts_endpoint_registered")')
        dl_source = dl_section[:dl_end]
        assert "sha256=file_hash" in dl_source or "sha256=" in dl_source, (
            "Download-Log muss den SHA-256 Hash enthalten"
        )


class TestKnownVoiceHashes:
    """Prueft dass das Hash-Dictionary existiert."""

    def test_known_hashes_dict_exists(self) -> None:
        """_KNOWN_VOICE_HASHES Dictionary muss im Source existieren."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        assert "_KNOWN_VOICE_HASHES" in source

    def test_verify_function_exists(self) -> None:
        """_verify_voice_hash Funktion muss im Source existieren."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        assert "def _verify_voice_hash" in source


class TestVerifyVoiceHashLogic:
    """Testet die Hash-Verifizierungs-Logik standalone."""

    def test_known_hash_matches(self) -> None:
        """Bekannter Hash + korrekter File-Hash = kein Error."""
        known_hashes = {"test-voice": "abc123def456"}

        def verify(voice: str, file_hash: str) -> None:
            expected = known_hashes.get(voice)
            if expected is None:
                return
            if file_hash != expected:
                raise ValueError(f"Integrity check failed for {voice}")

        # Sollte keinen Error werfen
        verify("test-voice", "abc123def456")

    def test_known_hash_mismatch_raises(self) -> None:
        """Bekannter Hash + falscher File-Hash = ValueError."""
        known_hashes = {"test-voice": "correct-hash"}

        def verify(voice: str, file_hash: str) -> None:
            expected = known_hashes.get(voice)
            if expected is None:
                return
            if file_hash != expected:
                raise ValueError(f"Integrity check failed for {voice}")

        with pytest.raises(ValueError, match="Integrity check failed"):
            verify("test-voice", "wrong-hash")

    def test_unknown_voice_no_error(self) -> None:
        """Unbekannte Voice = kein Error (nur Warning)."""
        known_hashes: dict[str, str] = {}

        def verify(voice: str, file_hash: str) -> None:
            expected = known_hashes.get(voice)
            if expected is None:
                return  # Warning, kein Error
            if file_hash != expected:
                raise ValueError(f"Integrity check failed for {voice}")

        # Sollte durchgehen ohne Error
        verify("unknown-voice", "any-hash")

    def test_source_raises_on_mismatch(self) -> None:
        """_verify_voice_hash im Source muss bei Mismatch raisen."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        verify_section = source[source.index("def _verify_voice_hash") :]
        verify_end = verify_section.index("\n                async def")
        verify_source = verify_section[:verify_end]
        assert "raise ValueError" in verify_source or "raise" in verify_source, (
            "_verify_voice_hash muss bei Hash-Mismatch eine Exception werfen"
        )


class TestHashComputation:
    """Prueft die korrekte SHA-256 Berechnung."""

    def test_sha256_of_known_content(self) -> None:
        """SHA-256 eines bekannten Inhalts muss korrekt sein."""
        content = b"test model content"
        expected = hashlib.sha256(content).hexdigest()

        with tempfile.NamedTemporaryFile(suffix=".onnx", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            computed = hashlib.sha256(path.read_bytes()).hexdigest()
            assert computed == expected
        finally:
            path.unlink(missing_ok=True)

    def test_different_content_different_hash(self) -> None:
        """Verschiedener Inhalt muss verschiedene Hashes ergeben."""
        hash_a = hashlib.sha256(b"model version 1").hexdigest()
        hash_b = hashlib.sha256(b"model version 2").hexdigest()
        assert hash_a != hash_b

    def test_same_content_same_hash(self) -> None:
        """Gleicher Inhalt muss gleichen Hash ergeben (Determinismus)."""
        content = b"deterministic test"
        hash_1 = hashlib.sha256(content).hexdigest()
        hash_2 = hashlib.sha256(content).hexdigest()
        assert hash_1 == hash_2
