"""Tests fuer F-022: Silero VAD via torch.hub.load ohne Integrity-Check.

Prueft dass:
  - SILERO_REPO einen gepinnten Tag enthaelt (nicht nur Repo-Name)
  - torch.hub.load mit dem gepinnten SILERO_REPO aufgerufen wird
  - SILERO_MODEL_HASH Feld existiert (fuer optionalen Integrity-Check)
  - Bei Hash-Mismatch das Modell nicht verwendet wird
  - Bei Hash-Match das Modell geladen wird
  - Fallback auf Energie-VAD bei Fehler weiterhin funktioniert
  - Source-Code die Fixes enthaelt
"""

from __future__ import annotations

import inspect

# torch ist moeglicherweise nicht installiert — nur Source-Level-Checks
# und Mocked-Tests
import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock torch falls nicht installiert
_mock_torch = MagicMock()
sys.modules.setdefault("torch", _mock_torch)

from cognithor.channels.voice import VADDetector


class TestPinnedRepo:
    """Prueft dass das Repository gepinnt ist."""

    def test_silero_repo_has_tag(self) -> None:
        """SILERO_REPO muss einen Tag/Commit enthalten (Format repo:tag)."""
        assert ":" in VADDetector.SILERO_REPO

    def test_silero_repo_not_bare(self) -> None:
        """SILERO_REPO darf nicht nur 'snakers4/silero-vad' sein."""
        assert VADDetector.SILERO_REPO != "snakers4/silero-vad"

    def test_silero_repo_contains_version(self) -> None:
        """SILERO_REPO enthaelt eine Version (v-Praefix)."""
        _, tag = VADDetector.SILERO_REPO.split(":", 1)
        assert tag.startswith("v"), f"Tag '{tag}' hat kein v-Praefix"

    def test_silero_model_hash_field_exists(self) -> None:
        """SILERO_MODEL_HASH Feld existiert."""
        assert hasattr(VADDetector, "SILERO_MODEL_HASH")


class TestIntegrityCheck:
    """Prueft Integrity-Verifikation bei Hash-Mismatch."""

    @pytest.mark.asyncio
    async def test_hash_mismatch_rejects_model(self) -> None:
        """Bei Hash-Mismatch: Modell wird nicht verwendet."""
        config = MagicMock()
        config.sample_rate = 16000
        config.vad_threshold = 0.5
        vad = VADDetector(config)

        # Setze bekannten Hash
        original_hash = VADDetector.SILERO_MODEL_HASH
        try:
            VADDetector.SILERO_MODEL_HASH = "expected_hash_that_wont_match"

            mock_model = MagicMock()
            # state_dict() liefert Parameter
            mock_param = MagicMock()
            mock_param.cpu.return_value.numpy.return_value.tobytes.return_value = b"data"
            mock_model.state_dict.return_value = {"layer.weight": mock_param}

            with patch("torch.hub.load", return_value=(mock_model, None)):
                await vad.load()

            assert vad._use_silero is False
            assert vad._model is None
        finally:
            VADDetector.SILERO_MODEL_HASH = original_hash

    @pytest.mark.asyncio
    async def test_hash_match_accepts_model(self) -> None:
        """Bei Hash-Match: Modell wird geladen."""
        import hashlib

        config = MagicMock()
        vad = VADDetector(config)

        mock_param = MagicMock()
        mock_param.cpu.return_value.numpy.return_value.tobytes.return_value = b"data"
        mock_model = MagicMock()
        mock_model.state_dict.return_value = {"layer.weight": mock_param}

        # Berechne den erwarteten Hash
        state_bytes = str(sorted(["layer.weight"])).encode()
        state_bytes += b"data"
        expected_hash = hashlib.sha256(state_bytes).hexdigest()

        original_hash = VADDetector.SILERO_MODEL_HASH
        try:
            VADDetector.SILERO_MODEL_HASH = expected_hash

            with patch("torch.hub.load", return_value=(mock_model, None)):
                await vad.load()

            assert vad._use_silero is True
            assert vad._model is mock_model
        finally:
            VADDetector.SILERO_MODEL_HASH = original_hash

    @pytest.mark.asyncio
    async def test_empty_hash_skips_check(self) -> None:
        """Bei leerem SILERO_MODEL_HASH wird kein Check durchgefuehrt."""
        config = MagicMock()
        vad = VADDetector(config)

        mock_model = MagicMock()

        original_hash = VADDetector.SILERO_MODEL_HASH
        try:
            VADDetector.SILERO_MODEL_HASH = ""

            with patch("torch.hub.load", return_value=(mock_model, None)):
                await vad.load()

            assert vad._use_silero is True
            # state_dict() sollte nicht aufgerufen worden sein (kein Hash-Check)
            mock_model.state_dict.assert_not_called()
        finally:
            VADDetector.SILERO_MODEL_HASH = original_hash


class TestFallback:
    """Prueft dass Fehler zum Energie-VAD-Fallback fuehren."""

    @pytest.mark.asyncio
    async def test_torch_import_error_fallback(self) -> None:
        """Wenn torch.hub.load fehlschlaegt: Energie-VAD."""
        config = MagicMock()
        vad = VADDetector(config)

        with patch("torch.hub.load", side_effect=RuntimeError("no torch")):
            await vad.load()

        assert vad._use_silero is False

    @pytest.mark.asyncio
    async def test_uses_pinned_repo_in_call(self) -> None:
        """torch.hub.load wird mit SILERO_REPO aufgerufen."""
        config = MagicMock()
        vad = VADDetector(config)

        original_hash = VADDetector.SILERO_MODEL_HASH
        try:
            VADDetector.SILERO_MODEL_HASH = ""
            mock_model = MagicMock()

            with patch("torch.hub.load", return_value=(mock_model, None)) as mock_load:
                await vad.load()

            mock_load.assert_called_once()
            call_kwargs = mock_load.call_args
            assert (
                call_kwargs[1].get("repo_or_dir") == VADDetector.SILERO_REPO
                or call_kwargs[0][0] == VADDetector.SILERO_REPO
            )
        finally:
            VADDetector.SILERO_MODEL_HASH = original_hash


class TestSourceLevelChecks:
    """Prueft den Source-Code auf die Fixes."""

    def test_load_uses_pinned_repo(self) -> None:
        source = inspect.getsource(VADDetector.load)
        assert "SILERO_REPO" in source

    def test_load_has_integrity_check(self) -> None:
        source = inspect.getsource(VADDetector.load)
        assert "SILERO_MODEL_HASH" in source

    def test_load_uses_sha256(self) -> None:
        source = inspect.getsource(VADDetector.load)
        assert "sha256" in source

    def test_load_rejects_on_mismatch(self) -> None:
        source = inspect.getsource(VADDetector.load)
        assert "integrity_check_failed" in source

    def test_class_has_pinned_repo_constant(self) -> None:
        source = inspect.getsource(VADDetector)
        assert "SILERO_REPO" in source
        assert ":v" in source  # Gepinnter Tag

    def test_no_bare_repo_reference(self) -> None:
        """Kein ungepinnter Repo-Name im torch.hub.load Aufruf."""
        source = inspect.getsource(VADDetector.load)
        # Darf nicht "snakers4/silero-vad" ohne Tag enthalten
        assert 'repo_or_dir="snakers4/silero-vad"' not in source
