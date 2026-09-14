from __future__ import annotations

from cognithor.memory.cag.content_normalizer import ContentNormalizer


class TestNormalize:
    def test_strip_bom(self):
        assert ContentNormalizer.normalize("\ufeffhello") == "hello"

    def test_normalize_line_endings(self):
        assert ContentNormalizer.normalize("a\r\nb\rc") == "a\nb\nc"

    def test_collapse_blank_lines(self):
        result = ContentNormalizer.normalize("a\n\n\n\nb")
        assert result == "a\n\nb"

    def test_strip_trailing_whitespace(self):
        result = ContentNormalizer.normalize("hello   \nworld\t\n")
        assert result == "hello\nworld"

    def test_deterministic(self):
        text = "  hello \r\n world  "
        assert ContentNormalizer.normalize(text) == ContentNormalizer.normalize(text)


class TestComputeHash:
    def test_deterministic(self):
        h1 = ContentNormalizer.compute_hash("hello")
        h2 = ContentNormalizer.compute_hash("hello")
        assert h1 == h2

    def test_different_input_different_hash(self):
        h1 = ContentNormalizer.compute_hash("hello")
        h2 = ContentNormalizer.compute_hash("world")
        assert h1 != h2


class TestHasChanged:
    def test_has_changed_true(self):
        stored = ContentNormalizer.compute_hash("hello")
        assert ContentNormalizer.has_changed(stored, "goodbye") is True

    def test_has_changed_false(self):
        text = "hello world"
        stored = ContentNormalizer.compute_hash(ContentNormalizer.normalize(text))
        assert ContentNormalizer.has_changed(stored, text) is False

    def test_empty_text(self):
        stored = ContentNormalizer.compute_hash("")
        assert ContentNormalizer.has_changed(stored, "") is False
