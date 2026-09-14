"""Tests für den UserPreferenceStore.

Testet:
  - CRUD-Operationen (get_or_create, update)
  - Auto-Learning (Nachrichtenlänge → Verbosity)
  - record_interaction mit exponential moving average
  - Verbosity-Hint-Generierung
  - SQLite-Persistenz
"""

from __future__ import annotations

import pytest

from cognithor.core.user_preferences import UserPreference, UserPreferenceStore


@pytest.fixture()
def store(tmp_path) -> UserPreferenceStore:
    """Erstellt einen temporären UserPreferenceStore."""
    db_path = tmp_path / "test_sessions.db"
    return UserPreferenceStore(db_path=db_path)


class TestUserPreference:
    """Tests für das UserPreference-Modell."""

    def test_default_values(self) -> None:
        pref = UserPreference(user_id="test-user")
        assert pref.verbosity == "normal"
        assert pref.greeting_name == ""
        assert pref.formality == "informal"
        assert pref.avg_message_length == 0.0
        assert pref.interaction_count == 0

    def test_verbosity_hint_normal(self) -> None:
        pref = UserPreference(user_id="test", verbosity="normal")
        assert pref.verbosity_hint == ""

    def test_verbosity_hint_terse(self) -> None:
        pref = UserPreference(user_id="test", verbosity="terse")
        hint = pref.verbosity_hint
        assert "kurz" in hint.lower() or "knapp" in hint.lower()

    def test_verbosity_hint_verbose(self) -> None:
        pref = UserPreference(user_id="test", verbosity="verbose")
        hint = pref.verbosity_hint
        assert "ausführlich" in hint.lower() or "detail" in hint.lower()


class TestUserPreferenceStore:
    """Tests für den SQLite-basierten Store."""

    def test_get_or_create_new(self, store: UserPreferenceStore) -> None:
        pref = store.get_or_create("user-123")
        assert pref.user_id == "user-123"
        assert pref.verbosity == "normal"
        assert pref.interaction_count == 0

    def test_get_or_create_existing(self, store: UserPreferenceStore) -> None:
        pref1 = store.get_or_create("user-123")
        pref1.greeting_name = "Alex"
        store.update(pref1)

        pref2 = store.get_or_create("user-123")
        assert pref2.greeting_name == "Alex"

    def test_update(self, store: UserPreferenceStore) -> None:
        pref = store.get_or_create("user-456")
        pref.verbosity = "verbose"
        pref.formality = "formal"
        store.update(pref)

        loaded = store.get_or_create("user-456")
        assert loaded.verbosity == "verbose"
        assert loaded.formality == "formal"

    def test_different_users_isolated(self, store: UserPreferenceStore) -> None:
        pref_a = store.get_or_create("user-a")
        pref_a.greeting_name = "Anna"
        store.update(pref_a)

        pref_b = store.get_or_create("user-b")
        pref_b.greeting_name = "Bob"
        store.update(pref_b)

        assert store.get_or_create("user-a").greeting_name == "Anna"
        assert store.get_or_create("user-b").greeting_name == "Bob"


class TestAutoLearning:
    """Tests für Auto-Learning der Verbosity."""

    def test_record_interaction_increments_count(self, store: UserPreferenceStore) -> None:
        pref = store.record_interaction("user-x", 50)
        assert pref.interaction_count == 1

    def test_avg_message_length_initialized(self, store: UserPreferenceStore) -> None:
        pref = store.record_interaction("user-x", 100)
        assert pref.avg_message_length == 100.0

    def test_avg_message_length_ema(self, store: UserPreferenceStore) -> None:
        # First interaction sets the average
        store.record_interaction("user-y", 100)
        # Second interaction uses EMA: 0.1 * 200 + 0.9 * 100 = 110
        pref = store.record_interaction("user-y", 200)
        assert abs(pref.avg_message_length - 110.0) < 1.0

    def test_verbosity_stays_normal_before_5_interactions(
        self,
        store: UserPreferenceStore,
    ) -> None:
        for _ in range(4):
            pref = store.record_interaction("user-z", 10)
        assert pref.verbosity == "normal"  # Not enough interactions

    def test_terse_verbosity_after_5_short_messages(
        self,
        store: UserPreferenceStore,
    ) -> None:
        for _ in range(6):
            pref = store.record_interaction("user-short", 15)
        assert pref.verbosity == "terse"

    def test_verbose_verbosity_after_5_long_messages(
        self,
        store: UserPreferenceStore,
    ) -> None:
        for _ in range(6):
            pref = store.record_interaction("user-long", 500)
        assert pref.verbosity == "verbose"

    def test_normal_verbosity_for_medium_messages(
        self,
        store: UserPreferenceStore,
    ) -> None:
        for _ in range(6):
            pref = store.record_interaction("user-med", 100)
        assert pref.verbosity == "normal"
