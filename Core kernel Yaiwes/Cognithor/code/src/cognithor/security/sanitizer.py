"""Input sanitizer: Protection against prompt injection and path traversal.

Checks and sanitizes all external content before it is presented to the
planner (LLM). External content is wrapped in <external_content> tags,
known injection patterns are removed or neutralized.

Additionally: Validation of voice/model names against path traversal
(CWE-22) -- prevents injection of ../../ sequences into filenames
that are used as paths (e.g. Piper TTS models).

Security guarantees:
  - External content is ALWAYS marked
  - Known injection patterns are neutralized
  - Instruction hierarchy is enforced
  - System prompts cannot be overridden
  - Voice/model names are validated against path traversal

Bible reference: §11.3 (Input-Sanitization)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from cognithor.models import SanitizeResult
from cognithor.utils.logging import get_logger

log = get_logger(__name__)


# ============================================================================
# Voice/Model Name Validation (CWE-22 Path Traversal Prevention)
# ============================================================================

# Piper voice names follow pattern: lang_REGION-name-quality
# e.g. "de_DE-thorsten-high", "de_DE-thorsten_emotional-medium", "en_US-lessac-low"
# Allowed: ASCII letters, digits, underscores, hyphens, dots (for version suffixes)
# Blocked: path separators (/ \), parent traversal (..), null bytes, spaces, special chars
_VOICE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_\-\.]*$")

# Maximum length for voice/model names (prevents abuse via extremely long names)
_MAX_VOICE_NAME_LENGTH = 128


def validate_voice_name(voice: str) -> str:
    """Validates a voice/model name against path traversal attacks (CWE-22).

    Ensures the name contains only safe characters and cannot be used
    to construct paths outside the intended directory.

    Args:
        voice: The voice/model name to validate.

    Returns:
        The validated voice name (unchanged if valid).

    Raises:
        ValueError: If the voice name is invalid or potentially malicious.
    """
    if not voice:
        raise ValueError("Voice name must not be empty")

    if len(voice) > _MAX_VOICE_NAME_LENGTH:
        raise ValueError(f"Voice name too long ({len(voice)} chars, max {_MAX_VOICE_NAME_LENGTH})")

    # Null byte injection check (can bypass string checks in C-level path APIs)
    if "\x00" in voice:
        log.warning("voice_name_null_byte_blocked", voice=repr(voice))
        raise ValueError("Voice name contains null byte")

    # Path separator check (explicit, before regex, for clear error message)
    if "/" in voice or "\\" in voice:
        log.warning("voice_name_path_separator_blocked", voice=voice)
        raise ValueError(f"Voice name contains path separator: {voice!r}")

    # Parent directory traversal check
    if ".." in voice:
        log.warning("voice_name_traversal_blocked", voice=voice)
        raise ValueError(f"Voice name contains directory traversal sequence: {voice!r}")

    # Whitelist regex: only safe characters
    if not _VOICE_NAME_PATTERN.match(voice):
        log.warning("voice_name_invalid_chars_blocked", voice=voice)
        raise ValueError(
            f"Voice name contains invalid characters: {voice!r}. "
            f"Allowed: letters, digits, underscores, hyphens, dots."
        )

    return voice


def validate_model_path_containment(
    model_path: Path,
    allowed_dir: Path,
) -> Path:
    """Defense-in-depth: verifies a constructed model path stays within its directory.

    Even after voice name validation, this ensures the resolved path
    is contained within the expected directory. Catches edge cases
    like symlink escapes or OS-specific path normalization quirks.

    Args:
        model_path: The constructed model file path.
        allowed_dir: The directory the path must reside in.

    Returns:
        The resolved, validated path.

    Raises:
        ValueError: If the resolved path escapes the allowed directory.
    """
    import os.path as _osp

    resolved_str = _osp.normpath(_osp.realpath(str(model_path)))
    allowed_str = _osp.normpath(_osp.realpath(str(allowed_dir)))
    if not resolved_str.startswith(allowed_str + _osp.sep) and resolved_str != allowed_str:
        log.warning(
            "model_path_containment_violation",
            model_path=str(model_path),
            allowed_dir=str(allowed_dir),
        )
        raise ValueError("Model path escapes allowed directory")
    return Path(resolved_str)


# ============================================================================
# Injection-Pattern-Definitionen
# ============================================================================


@dataclass(frozen=True)
class InjectionPattern:
    """A recognized prompt injection pattern."""

    name: str
    pattern: re.Pattern[str]
    severity: str = "high"  # high | medium | low


# Known prompt injection patterns
_INJECTION_PATTERNS: list[InjectionPattern] = [
    # Direkte Instruction-Override
    InjectionPattern(
        name="system_override",
        pattern=re.compile(
            r"(?:ignore|forget|disregard)\s+(?:all\s+)?(?:previous|prior|above)\s+"
            r"(?:instructions?|prompts?|rules?|context)",
            re.IGNORECASE,
        ),
        severity="high",
    ),
    InjectionPattern(
        name="new_instructions",
        pattern=re.compile(
            r"(?:new|updated|revised)\s+(?:system\s+)?instructions?:?\s",
            re.IGNORECASE,
        ),
        severity="high",
    ),
    InjectionPattern(
        name="role_switch",
        pattern=re.compile(
            r"you\s+are\s+now\s+(?:a\s+)?(?:different|new|evil|unrestricted)",
            re.IGNORECASE,
        ),
        severity="high",
    ),
    InjectionPattern(
        name="jailbreak_dan",
        pattern=re.compile(
            r"(?:DAN|do\s+anything\s+now|developer\s+mode|DUDE)\s*(?:mode|prompt)?",
            re.IGNORECASE,
        ),
        severity="high",
    ),
    # System-Prompt Extraktion
    InjectionPattern(
        name="prompt_leak",
        pattern=re.compile(
            r"(?:print|show|reveal|repeat|output|display)\s+(?:your\s+)?"
            r"(?:system\s+)?(?:prompt|instructions?|rules?|configuration)",
            re.IGNORECASE,
        ),
        severity="medium",
    ),
    # XML/Tag Injection
    InjectionPattern(
        name="xml_injection",
        pattern=re.compile(
            r"<\s*/?(?:system|assistant|user|instruction|prompt|tool_result)\s*>",
            re.IGNORECASE,
        ),
        severity="high",
    ),
    # Encoding-Umgehung
    InjectionPattern(
        name="base64_injection",
        pattern=re.compile(
            r"(?:decode|eval|execute)\s+(?:this\s+)?base64",
            re.IGNORECASE,
        ),
        severity="medium",
    ),
    # Delimiter-Confusion
    InjectionPattern(
        name="delimiter_escape",
        pattern=re.compile(
            r"```\s*(?:system|end_turn|human_turn|<\|)",
            re.IGNORECASE,
        ),
        severity="high",
    ),
    # Community-Skill-spezifisch: Tool-Override-Versuche
    InjectionPattern(
        name="tools_required_bypass",
        pattern=re.compile(
            r"(?:ignore|bypass|skip|disable)\s+(?:the\s+)?tools?_required",
            re.IGNORECASE,
        ),
        severity="high",
    ),
    InjectionPattern(
        name="gatekeeper_bypass",
        pattern=re.compile(
            r"(?:ignore|bypass|skip|disable)\s+(?:the\s+)?gatekeeper",
            re.IGNORECASE,
        ),
        severity="high",
    ),
]


# ============================================================================
# Sanitizer
# ============================================================================


class InputSanitizer:
    """Sanitizer for external content. [B§11.3]

    Checks text for known prompt injection patterns and
    neutralizes them. External content is wrapped in safe
    tags.
    """

    def __init__(
        self,
        *,
        extra_patterns: list[InjectionPattern] | None = None,
        strict: bool = True,
    ) -> None:
        """Initializes the sanitizer.

        Args:
            extra_patterns: Additional injection patterns.
            strict: Block instead of neutralize on 'high' severity.
        """
        self._patterns = list(_INJECTION_PATTERNS)
        if extra_patterns:
            self._patterns.extend(extra_patterns)
        self._strict = strict
        self._stats = _SanitizerStats()

    def sanitize_external(self, text: str, source: str = "unknown") -> SanitizeResult:
        """Sanitizes external content and wraps it.

        External content (web scraping, tool output, file content)
        is wrapped in <external_content> tags and checked for
        injection patterns.

        Args:
            text: The external text.
            source: Origin of the text (e.g. 'web', 'file', 'tool').

        Returns:
            SanitizeResult with sanitized text.
        """
        if not text:
            return SanitizeResult(
                original_length=0,
                sanitized_length=0,
                was_modified=False,
                sanitized_text="",
            )

        found_patterns: list[str] = []

        # 0. Unicode normalization — prevents bypass via zero-width chars,
        #    homoglyphs, and NFKD decomposition tricks
        import unicodedata

        sanitized = unicodedata.normalize("NFKC", text)
        # Strip zero-width characters that could hide injection payloads
        sanitized = (
            sanitized.replace("\u200b", "")
            .replace("\u200c", "")
            .replace("\u200d", "")
            .replace("\ufeff", "")
            .replace("\u00ad", "")
        )

        # 1. Check injection patterns
        for ip in self._patterns:
            matches = ip.pattern.findall(sanitized)
            if matches:
                found_patterns.append(f"{ip.name}({ip.severity})")
                self._stats.patterns_detected += 1

                if ip.severity == "high" and self._strict:
                    # High severity: remove match completely
                    sanitized = ip.pattern.sub("[BLOCKED_INJECTION]", sanitized)
                else:
                    # Medium/Low: neutralize in comment
                    sanitized = ip.pattern.sub(
                        lambda m, _ip=ip: f"[NEUTRALIZED: {_ip.name}]",  # type: ignore[misc]
                        sanitized,
                    )

        # 2. Neutralize XML tags (except allowed ones)
        sanitized = self._neutralize_xml_tags(sanitized)

        # 3. In external_content-Tag wrappen
        safe_source = source.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
        wrapped = f'<external_content source="{safe_source}">\n{sanitized}\n</external_content>'

        was_modified = sanitized != text
        if found_patterns:
            self._stats.texts_modified += 1
            log.warning(
                "injection_patterns_detected",
                source=source,
                patterns=found_patterns,
                strict=self._strict,
            )

        self._stats.texts_processed += 1

        return SanitizeResult(
            original_length=len(text),
            sanitized_length=len(wrapped),
            patterns_found=found_patterns,
            was_modified=was_modified,
            sanitized_text=wrapped,
        )

    def sanitize_user_input(self, text: str) -> SanitizeResult:
        """Sanitizes user input (less strict).

        User input is NOT wrapped (it is trusted),
        but checked for XML tag injection that could
        break the instruction hierarchy.

        Args:
            text: The user input.

        Returns:
            SanitizeResult.
        """
        if not text:
            return SanitizeResult(
                original_length=0,
                sanitized_length=0,
                was_modified=False,
                sanitized_text="",
            )

        found_patterns: list[str] = []
        sanitized = text

        # Only check for XML tag injection (user is allowed everything else)
        xml_pattern = next((p for p in self._patterns if p.name == "xml_injection"), None)
        if xml_pattern and xml_pattern.pattern.search(sanitized):
            found_patterns.append("xml_injection(high)")
            sanitized = xml_pattern.pattern.sub("[TAG_REMOVED]", sanitized)

        self._stats.texts_processed += 1
        was_modified = sanitized != text
        if was_modified:
            self._stats.texts_modified += 1

        return SanitizeResult(
            original_length=len(text),
            sanitized_length=len(sanitized),
            patterns_found=found_patterns,
            was_modified=was_modified,
            sanitized_text=sanitized,
        )

    def scan_only(self, text: str) -> list[str]:
        """Scans text for injection patterns without modification.

        Args:
            text: Text to scan.

        Returns:
            List of found pattern names.
        """
        if not text:
            return []
        found: list[str] = []
        for ip in self._patterns:
            if ip.pattern.search(text):
                found.append(f"{ip.name}({ip.severity})")
        return found

    @property
    def stats(self) -> dict[str, int]:
        """Statistics of the sanitizer."""
        return {
            "texts_processed": self._stats.texts_processed,
            "texts_modified": self._stats.texts_modified,
            "patterns_detected": self._stats.patterns_detected,
        }

    def _neutralize_xml_tags(self, text: str) -> str:
        """Neutralizes dangerous XML tags.

        Allowed: <b>, <i>, <code>, <pre>, <br>, <p>, <ul>, <li>, <ol>
        Blocked: <system>, <assistant>, <user>, <instruction>,
                 <tool_result>, <prompt>
        """
        dangerous = re.compile(
            r"<\s*/?(?:system|assistant|user|instruction|prompt|"
            r"tool_result|tool_use|function_call|human_turn|ai_turn)\s*"
            r"(?:\s+[^>]*)?>",
            re.IGNORECASE,
        )
        return dangerous.sub(
            lambda m: m.group(0).replace("<", "&lt;").replace(">", "&gt;"),
            text,
        )


@dataclass
class _SanitizerStats:
    """Internal statistics."""

    texts_processed: int = 0
    texts_modified: int = 0
    patterns_detected: int = 0
