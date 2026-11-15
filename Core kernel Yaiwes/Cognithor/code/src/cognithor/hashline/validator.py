# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Hash-Validierung vor Edit-Operationen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from cognithor.hashline.cache import HashlineCache
    from cognithor.hashline.config import HashlineConfig
    from cognithor.hashline.hasher import LineHasher
    from cognithor.hashline.models import EditIntent, HashlinedFile

log = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of validating an edit intent against the current file state.

    Attributes:
        valid: Whether the edit intent's hash matches the current disk content.
        reason: Human-readable explanation of the validation outcome.
        current_content: The current content of the target line on disk.
        current_hash: The current hash tag of the target line on disk.
        stale: Whether the cached data was stale and had to be refreshed.
    """

    valid: bool
    reason: str
    current_content: str | None
    current_hash: str | None
    stale: bool = False


class HashlineValidator:
    """Validates edit intents by comparing hashes against disk state.

    Args:
        hasher: LineHasher for computing line hashes.
        cache: HashlineCache for looking up cached file data.
        config: HashlineConfig for thresholds.
    """

    def __init__(
        self,
        hasher: LineHasher,
        cache: HashlineCache,
        config: HashlineConfig,
    ) -> None:
        self._hasher = hasher
        self._cache = cache
        self._config = config

    def validate_edit(self, intent: EditIntent) -> ValidationResult:
        """Validate an edit intent against the current file on disk.

        Looks up the target file in cache. If not cached, reads the file
        fresh and caches it (does not reject uncached files). Then recomputes
        the hash of the target line from disk and compares it to the intent's
        expected hash.

        Args:
            intent: The edit operation to validate.

        Returns:
            ValidationResult indicating whether the edit is safe.
        """
        resolved = intent.file_path.resolve()
        stale = False

        # Cache lookup
        cached = self._cache.get(resolved)
        if cached is None or self._cache.is_stale(resolved):
            stale = cached is not None
            cached = self._load_and_cache(resolved)

        # Read the actual line content from disk for freshest check
        disk_content = self._read_line_from_disk(resolved, intent.target_line)
        if disk_content is None:
            return ValidationResult(
                valid=False,
                reason=f"Line {intent.target_line} does not exist in {resolved} "
                f"(file has fewer lines)",
                current_content=None,
                current_hash=None,
                stale=stale,
            )

        # Compute hash of the line as it currently exists on disk
        current_tag, _full = self._hasher.hash_line(disk_content)

        if current_tag != intent.target_hash:
            # Also check if the cache hash differs from disk (concurrent change)
            cache_tag = None
            if cached and intent.target_line <= len(cached.lines):
                cache_tag = cached.lines[intent.target_line - 1].hash_tag

            reason_parts = [
                f"Hash mismatch on line {intent.target_line}: "
                f"intent={intent.target_hash!r}, disk={current_tag!r}"
            ]
            if cache_tag and cache_tag != current_tag:
                reason_parts.append(f", cache={cache_tag!r} (stale)")

            return ValidationResult(
                valid=False,
                reason="".join(reason_parts),
                current_content=disk_content,
                current_hash=current_tag,
                stale=stale,
            )

        return ValidationResult(
            valid=True,
            reason="Hash verified",
            current_content=disk_content,
            current_hash=current_tag,
            stale=stale,
        )

    def validate_batch(self, intents: list[EditIntent]) -> list[ValidationResult]:
        """Validate multiple edit intents, sorted by line number descending.

        Processing highest line numbers first ensures line numbers remain
        stable during batch edits.

        Args:
            intents: List of edit intents to validate.

        Returns:
            List of ValidationResult in the same descending-line order.
        """
        sorted_intents = sorted(intents, key=lambda i: i.target_line, reverse=True)
        return [self.validate_edit(intent) for intent in sorted_intents]

    def _read_line_from_disk(self, path: Path, line_number: int) -> str | None:
        """Read a single line from disk by its 1-based line number.

        Args:
            path: Path to the file.
            line_number: 1-based line number.

        Returns:
            The line content (without newline), or None if out of range.
        """
        try:
            with open(path, encoding="utf-8") as f:
                for i, line in enumerate(f, start=1):
                    if i == line_number:
                        return line.rstrip("\n").rstrip("\r")
        except UnicodeDecodeError:
            try:
                with open(path, encoding="latin-1") as f:
                    for i, line in enumerate(f, start=1):
                        if i == line_number:
                            return line.rstrip("\n").rstrip("\r")
            except Exception:
                log.debug("hashline_latin1_fallback_read_failed", exc_info=True)
        except Exception:
            log.debug("hashline_line_read_failed", exc_info=True)
        return None

    def _load_and_cache(self, path: Path) -> HashlinedFile | None:
        """Read a file, build HashlinedFile, and store in cache.

        Args:
            path: Resolved path to the file.

        Returns:
            The cached HashlinedFile, or None on error.
        """
        try:
            # Delayed import to avoid circular dependency
            from cognithor.hashline.tagger import HashlineTagger

            tagger = HashlineTagger(self._hasher, self._cache, self._config)
            return tagger.read_and_tag(path)
        except Exception:
            log.debug("validator_cache_load_failed", path=str(path), exc_info=True)
            return None
