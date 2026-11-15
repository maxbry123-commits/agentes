"""Tests for CorrectionMemory — stores and retrieves user corrections."""

import pytest


class TestCorrectionMemory:
    @pytest.fixture
    def mem(self, tmp_path):
        from cognithor.core.correction_memory import CorrectionMemory

        return CorrectionMemory(db_path=tmp_path / "corrections.db")

    def test_store_correction(self, mem):
        cid = mem.store(
            user_message="Analysiere den Vertrag",
            correction_text="Nein, fasse nur zusammen",
            original_plan="analyze_document + write_file",
        )
        assert cid.startswith("corr_")

    def test_find_similar(self, mem):
        mem.store(
            user_message="Analysiere den Vertrag",
            correction_text="Nur zusammenfassen, keine Risiken",
            original_plan="full_analysis",
        )
        matches = mem.find_similar("Pruefe diesen Vertrag")
        assert len(matches) >= 1
        assert "zusammenfassen" in matches[0]["correction_text"]

    def test_no_match_for_unrelated(self, mem):
        mem.store(
            user_message="Schreibe einen Schachbot",
            correction_text="Benutze kein Stockfish",
            original_plan="exec_command stockfish",
        )
        matches = mem.find_similar("Was ist das Wetter?")
        assert len(matches) == 0

    def test_increment_times_triggered(self, mem):
        mem.store(
            user_message="Recherchiere X",
            correction_text="Nutze nur deutsche Quellen",
            original_plan="web_search",
        )
        mem.store(
            user_message="Suche nach Y",
            correction_text="Nur deutsche Quellen bitte",
            original_plan="web_search",
        )
        # Similar corrections should be merged or both found
        matches = mem.find_similar("Recherchiere deutsche Quellen zu Z")
        assert len(matches) >= 1

    def test_should_ask_proactively(self, mem):
        for i in range(3):
            mem.store(
                user_message=f"Recherche {i}",
                correction_text="Nur deutsche Quellen",
                original_plan="web_search",
                keywords=["recherche", "quellen", "deutsch"],
            )
        assert mem.should_ask_proactively("recherche", ["quellen"]) is True

    def test_not_proactive_under_threshold(self, mem):
        mem.store(
            user_message="Recherche",
            correction_text="Nur deutsch",
            original_plan="web_search",
            keywords=["recherche"],
        )
        assert mem.should_ask_proactively("recherche", ["quellen"]) is False

    def test_get_reminder_text(self, mem):
        mem.store(
            user_message="Schreib eine E-Mail",
            correction_text="Immer in Du-Form, nie Sie",
            original_plan="email_send",
            keywords=["email", "schreib"],
        )
        reminder = mem.get_reminder("Verfasse eine E-Mail an Max")
        assert reminder is not None
        assert "Du-Form" in reminder
