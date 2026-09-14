# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Auto-Recovery bei Hash-Mismatches."""

from __future__ import annotations

import difflib
import time
from typing import TYPE_CHECKING

from cognithor.hashline.exceptions import MaxRetriesExceededError
from cognithor.hashline.models import EditIntent, EditResult, HashlinedFile
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.hashline.cache import HashlineCache
    from cognithor.hashline.config import HashlineConfig
    from cognithor.hashline.editor import HashlineEditor
    from cognithor.hashline.tagger import HashlineTagger

log = get_logger(__name__)

_FUZZY_THRESHOLD = 0.8
_SEARCH_RADIUS = 5


class HashlineRecovery:
    """Attempts edits with automatic recovery on hash mismatches.

    When an edit fails due to a hash mismatch, the recovery system re-reads
    the file, uses fuzzy matching to find the intended line at its new
    position, and retries the edit.

    Args:
        tagger: HashlineTagger for re-reading files.
        editor: HashlineEditor for executing edits.
        cache: HashlineCache for cache operations.
        config: HashlineConfig for retry settings.
    """

    def __init__(
        self,
        tagger: HashlineTagger,
        editor: HashlineEditor,
        cache: HashlineCache,
        config: HashlineConfig,
    ) -> None:
        self._tagger = tagger
        self._editor = editor
        self._cache = cache
        self._config = config

    def attempt_with_recovery(self, intent: EditIntent) -> EditResult:
        """Try an edit, recovering from hash mismatches up to max_retries.

        On each mismatch:
            1. Re-read the file from disk.
            2. Fuzzy-match the intended line near its expected position.
            3. Build a new intent with the corrected line number and hash.
            4. Retry.

        Args:
            intent: The original edit intent.

        Returns:
            EditResult from the successful attempt.

        Raises:
            MaxRetriesExceededError: If all retries are exhausted.
        """
        last_error = ""
        current_intent = intent

        for attempt in range(self._config.max_retries + 1):
            result = self._editor.execute_edit(current_intent)
            if result.success:
                result.retry_count = attempt
                return result

            last_error = result.error or "Unknown error"
            log.debug(
                "edit_failed_retrying",
                attempt=attempt,
                line=current_intent.target_line,
                error=last_error,
            )

            if attempt < self._config.max_retries:
                # Sleep before retry
                if self._config.retry_delay_seconds > 0:
                    time.sleep(self._config.retry_delay_seconds)

                # Re-read file
                self._cache.invalidate(current_intent.file_path.resolve())
                try:
                    fresh_data = self._tagger.read_and_tag(current_intent.file_path)
                except Exception as exc:
                    last_error = f"Failed to re-read file: {exc}"
                    continue

                # Try to find the matching line
                new_line = self._find_matching_line(current_intent, fresh_data)
                if new_line is None:
                    last_error = self._build_error_context(current_intent, fresh_data)
                    continue

                # Build corrected intent
                new_tag, _ = self._tagger._hasher.hash_line(fresh_data.lines[new_line - 1].content)
                current_intent = EditIntent(
                    file_path=current_intent.file_path,
                    target_line=new_line,
                    target_hash=new_tag,
                    operation=current_intent.operation,
                    new_content=current_intent.new_content,
                    context_lines=current_intent.context_lines,
                )

        raise MaxRetriesExceededError(
            f"Edit failed after {self._config.max_retries} retries: {last_error}",
            retry_count=self._config.max_retries,
            last_error=last_error,
            file_path=intent.file_path.resolve(),
            line_number=intent.target_line,
        )

    def _find_matching_line(
        self,
        intent: EditIntent,
        fresh_data: HashlinedFile,
    ) -> int | None:
        """Search for the intended line near its expected position using fuzzy match.

        Searches within +/- _SEARCH_RADIUS lines around the original target
        line. Uses difflib.SequenceMatcher with a threshold of 0.8.

        Args:
            intent: The original edit intent (contains expected content context).
            fresh_data: Freshly read file data.

        Returns:
            1-based line number of the best match, or None if no match found.
        """
        # We need to know what the original line content was.
        # Check if there's cached data with the original hash.
        original_content = None

        # Search through the fresh data for a line matching the original hash
        # First, try exact hash match within search radius
        target = intent.target_line
        start = max(1, target - _SEARCH_RADIUS)
        end = min(len(fresh_data.lines), target + _SEARCH_RADIUS)

        for line in fresh_data.lines:
            if start <= line.number <= end and line.hash_tag == intent.target_hash:
                return line.number

        # If we have no original content to fuzzy-match against, we can't recover
        # Try to get it from the validator's last read
        cached = self._cache.get(intent.file_path.resolve())
        if cached and intent.target_line <= len(cached.lines):
            original_content = cached.lines[intent.target_line - 1].content

        if original_content is None:
            return None

        # Fuzzy match within the search radius
        best_ratio = 0.0
        best_line = None

        for line in fresh_data.lines:
            if start <= line.number <= end:
                ratio = difflib.SequenceMatcher(None, original_content, line.content).ratio()
                if ratio >= _FUZZY_THRESHOLD and ratio > best_ratio:
                    best_ratio = ratio
                    best_line = line.number

        return best_line

    def _build_error_context(
        self,
        intent: EditIntent,
        fresh_data: HashlinedFile,
    ) -> str:
        """Build a human-readable error message showing lines around the target.

        Args:
            intent: The failed edit intent.
            fresh_data: Current file data.

        Returns:
            Multi-line string with context around the target line.
        """
        target = intent.target_line
        start = max(1, target - _SEARCH_RADIUS)
        end = min(len(fresh_data.lines), target + _SEARCH_RADIUS)

        lines_text: list[str] = []
        for line in fresh_data.lines:
            if start <= line.number <= end:
                marker = " >> " if line.number == target else "    "
                lines_text.append(f"{marker}{line.number}#{line.hash_tag}| {line.content}")

        context = "\n".join(lines_text)
        return (
            f"Could not find matching line for edit on line {target} "
            f"(expected hash={intent.target_hash!r}).\n"
            f"Current file content around line {target}:\n{context}"
        )
