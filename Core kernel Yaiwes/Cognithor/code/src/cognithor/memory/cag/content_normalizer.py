from __future__ import annotations

import hashlib
import re


class ContentNormalizer:
    """Deterministic text normalizer for CAG cache entries."""

    @staticmethod
    def normalize(text: str) -> str:
        """Normalize text for deterministic caching.

        Steps: strip BOM, unify line endings, collapse blank lines,
        strip trailing whitespace per line, strip leading/trailing whitespace.
        """
        # Strip BOM
        result = text.lstrip("\ufeff")
        # Unify line endings: \r\n -> \n, then stray \r -> \n
        result = result.replace("\r\n", "\n").replace("\r", "\n")
        # Strip trailing whitespace per line
        result = re.sub(r"[ \t]+$", "", result, flags=re.MULTILINE)
        # Collapse multiple blank lines into a single blank line
        result = re.sub(r"\n{3,}", "\n\n", result)
        # Strip leading/trailing whitespace
        result = result.strip()
        return result

    @staticmethod
    def compute_hash(normalized_text: str) -> str:
        """SHA-256 hex digest of already-normalized text."""
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    @staticmethod
    def has_changed(stored_hash: str, current_text: str) -> bool:
        """Check whether *current_text* (raw) differs from the stored hash."""
        normalized = ContentNormalizer.normalize(current_text)
        return ContentNormalizer.compute_hash(normalized) != stored_hash
