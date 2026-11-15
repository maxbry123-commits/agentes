"""Shared utilities for analysis scripts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Sequence,
    Union,
    cast,
)

try:
    import tiktoken
except ImportError:  # pragma: no cover - optional dependency
    tiktoken = None  # type: ignore[assignment]

_EPISODE_PATTERN = re.compile(r"(\d+)")


# ---------------------------------------------------------------------------
# Behavioral pattern detectors
# ---------------------------------------------------------------------------
#
# Regexes that detect agent-trace behavioral features used by behavioral_delta
# and temporal_trace_analysis.

# OpenAI/Anthropic-style structured tool_calls live on the message dict itself
# (msg["tool_calls"]). The OT-Agent trace format embeds them as
# ``<tool_call>{json}</tool_call>`` inside assistant content.
_TOOL_CALL_XML_RE = re.compile(
    r"<tool_call>(.*?)</tool_call>", re.DOTALL | re.IGNORECASE
)

# Tool-result messages come back as ``role=user`` with ``New Terminal Output:``
# in the OT-Agent format, or as ``role=tool`` in OpenAI/Anthropic.
_TOOL_OUTPUT_MARKER = "New Terminal Output:"

# Error patterns that appear in tool/terminal output and indicate the model's
# previous action failed. Matches Python tracebacks, shell errors, common
# error strings. We intentionally avoid matching "error" as a substring of
# longer words (e.g. "errorhandler"), use word boundaries.
_TOOL_ERROR_RE = re.compile(
    r"(?:\bTraceback\s*\(most recent call last\)|"
    r"\bSyntaxError\b|\bNameError\b|\bTypeError\b|\bValueError\b|"
    r"\bAttributeError\b|\bKeyError\b|\bIndexError\b|\bImportError\b|"
    r"\bModuleNotFoundError\b|\bFileNotFoundError\b|"
    r"\bcommand not found\b|\bNo such file or directory\b|"
    r"\bPermission denied\b|\bsegmentation fault\b|"
    r"\bbash: .*?: command not found\b|"
    r"^\s*Error[:\s]|^E\s+|"
    r"\bFAILED\b|\bfailed\s+with\b)",
    re.IGNORECASE | re.MULTILINE,
)

# Thinking-block detector (two common conventions).
_THINK_BLOCK_RE = re.compile(
    r"<think(?:ing)?\s*>(.*?)</think(?:ing)?\s*>", re.DOTALL | re.IGNORECASE
)
_THINK_OPEN_RE = re.compile(r"<think(?:ing)?\s*>", re.IGNORECASE)

# Fenced code block density (we count triple-backtick OPEN markers; a fully
# paired block counts as one).
_CODE_FENCE_RE = re.compile(r"```")

# Self-correction phrasing. Order matters only for documentation; we OR all of
# them and count occurrences.
_SELF_CORRECTION_PATTERNS: list[str] = [
    r"\blet me reconsider\b",
    r"\bactually,?\b",
    r"\bwait,?\b",
    r"\bon second thought\b",
    r"\bI was wrong\b",
    r"\bI'm wrong\b",
    r"\blet me try again\b",
    r"\blet me retry\b",
    r"\blet me re-?try\b",
    r"\blet me re-?examine\b",
    r"\bhmm,?\b",
    r"\bnever mind\b",
    r"\bmy mistake\b",
    r"\bI made an error\b",
    r"\bthat (?:didn't|won't|did not) work\b",
    r"\bnot quite right\b",
]
_SELF_CORRECTION_RE = re.compile("|".join(_SELF_CORRECTION_PATTERNS), re.IGNORECASE)

# Names of tools we surface separately when present. Extracted as the value
# of "name" in a parsed tool_call JSON payload, or matched as
# ``"name": "<tool>"`` directly if the JSON is malformed.
_TOOL_NAME_FROM_JSON_RE = re.compile(r'"name"\s*:\s*"([^"]+)"')


def _safe_str_content(content: Any) -> str:
    """Coerce a message ``content`` field (str / list-of-dicts / other) to str."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                t = item.get("text") or item.get("content") or ""
                if isinstance(t, str):
                    parts.append(t)
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    if isinstance(content, dict):
        t = content.get("text") or content.get("content") or ""
        return t if isinstance(t, str) else ""
    return ""


@dataclass
class BehavioralFeatures:
    """Per-trace behavioral features extracted from the conversation.

    Computed once per trace at load time so downstream binning / aggregation
    is cheap. All counts are integers; ratios are floats in [0, 1] (or None
    when the denominator is zero).
    """

    tool_calls_total: int = 0
    tool_calls_by_name: Dict[str, int] = field(default_factory=dict)
    tool_errors: int = 0  # responses whose text matches typical error patterns
    tool_responses: int = 0  # total tool/terminal-output responses
    tool_error_rate: Optional[float] = None  # tool_errors / tool_responses
    think_blocks: int = 0  # number of <think>...</think> openings (counts both `<think>` and `<thinking>`)
    think_tokens: int = 0  # token count INSIDE <think> blocks
    assistant_msgs: int = 0
    assistant_tokens: int = 0
    think_token_ratio: Optional[float] = None  # think_tokens / assistant_tokens
    mean_assistant_tokens: Optional[float] = None  # assistant_tokens / assistant_msgs
    code_fence_blocks: int = 0  # roughly (number of ``` markers) // 2
    self_correction_hits: int = 0
    premature_stop: bool = False  # last assistant turn was not followed by a tool turn AND reward < threshold
    last_role: Optional[str] = None


def _count_tokens_local(text: str, encoder) -> int:
    """Token count helper that tolerates a missing encoder."""
    if not text:
        return 0
    if encoder is not None:
        try:
            return len(encoder.encode(text, disallowed_special=()))
        except Exception:
            return len(text.split())
    return len(text.split())


def extract_behavioral_features(
    record: Dict[str, Any],
    encoder: Optional[Any] = None,
) -> BehavioralFeatures:
    """Extract per-trace behavioral features from a conversation record.

    Handles both OpenAI/Anthropic-style ``tool_calls`` (set on the message
    object) and the OT-Agent-style ``<tool_call>{json}</tool_call>`` embedded
    in assistant content. Tool responses are detected as ``role=tool`` (OAI)
    or ``role=user`` content containing ``New Terminal Output:`` (OT-Agent).
    """
    features = BehavioralFeatures()
    if not isinstance(record, dict):
        return features

    messages = record.get("messages") or record.get("conversations")
    if not isinstance(messages, list) or not messages:
        return features

    last_role: Optional[str] = None
    by_name: Dict[str, int] = {}

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        if isinstance(role, str):
            last_role = role
        content = _safe_str_content(msg.get("content"))

        if role == "assistant":
            features.assistant_msgs += 1
            tok = _count_tokens_local(content, encoder)
            features.assistant_tokens += tok

            # Structured tool_calls on the message (OpenAI / Anthropic schema).
            structured_calls = msg.get("tool_calls")
            if isinstance(structured_calls, list):
                for call in structured_calls:
                    features.tool_calls_total += 1
                    name = None
                    if isinstance(call, dict):
                        fn = call.get("function")
                        if isinstance(fn, dict):
                            name = fn.get("name")
                        name = name or call.get("name")
                    if isinstance(name, str) and name:
                        by_name[name] = by_name.get(name, 0) + 1

            # Embedded <tool_call>{json}</tool_call> blocks (OT-Agent schema).
            for block in _TOOL_CALL_XML_RE.findall(content):
                features.tool_calls_total += 1
                # Parse the tool name out of the JSON payload.
                try:
                    payload = json.loads(block.strip())
                    name = payload.get("name") if isinstance(payload, dict) else None
                except (json.JSONDecodeError, AttributeError):
                    name = None
                    m = _TOOL_NAME_FROM_JSON_RE.search(block)
                    if m:
                        name = m.group(1)
                if isinstance(name, str) and name:
                    by_name[name] = by_name.get(name, 0) + 1

            # Thinking blocks.
            features.think_blocks += len(_THINK_OPEN_RE.findall(content))
            for inner in _THINK_BLOCK_RE.findall(content):
                features.think_tokens += _count_tokens_local(inner, encoder)

            # Fenced code blocks: count pairs of ```.
            n_fences = len(_CODE_FENCE_RE.findall(content))
            features.code_fence_blocks += n_fences // 2

            # Self-correction phrases.
            features.self_correction_hits += len(_SELF_CORRECTION_RE.findall(content))

        elif role == "tool":
            features.tool_responses += 1
            if _TOOL_ERROR_RE.search(content):
                features.tool_errors += 1

        elif role == "user":
            # OT-Agent loops tool output through a user-role message prefixed
            # with "New Terminal Output:". Count those as tool responses.
            if _TOOL_OUTPUT_MARKER in content:
                features.tool_responses += 1
                if _TOOL_ERROR_RE.search(content):
                    features.tool_errors += 1

    features.tool_calls_by_name = by_name
    features.last_role = last_role

    if features.assistant_msgs:
        features.mean_assistant_tokens = (
            features.assistant_tokens / features.assistant_msgs
        )
    if features.assistant_tokens:
        features.think_token_ratio = features.think_tokens / features.assistant_tokens
    if features.tool_responses:
        features.tool_error_rate = features.tool_errors / features.tool_responses

    # Premature stop: trace ended on an assistant turn rather than a tool
    # response. A weak signal — some legitimate completions DO end on an
    # assistant message.
    features.premature_stop = last_role == "assistant"

    return features


# Convenience list of feature names that downstream code aggregates as
# scalar deltas. Tool-call-by-name is handled separately.
SCALAR_BEHAVIORAL_FIELDS: tuple[str, ...] = (
    "tool_calls_total",
    "tool_errors",
    "tool_responses",
    "tool_error_rate",
    "think_blocks",
    "think_tokens",
    "think_token_ratio",
    "assistant_msgs",
    "assistant_tokens",
    "mean_assistant_tokens",
    "code_fence_blocks",
    "self_correction_hits",
)


# ---------------------------------------------------------------------------
# JSONL iteration
# ---------------------------------------------------------------------------


def iter_jsonl(path: Path) -> Iterator[Dict]:
    """Yield parsed dicts from a JSONL file, raising on malformed lines."""
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Failed to parse JSON on line {line_number}: {exc}"
                ) from exc


# ---------------------------------------------------------------------------
# Conversation text extraction
# ---------------------------------------------------------------------------

TokenRepresentation = Literal["serialized", "conversation_text", "chat_template"]
"""The source representation used before a tokenizer counts a conversation."""

TOKEN_REPRESENTATIONS: tuple[TokenRepresentation, ...] = (
    "serialized",
    "conversation_text",
    "chat_template",
)


def validate_token_representation(representation: str) -> TokenRepresentation:
    """Validate and return an explicitly requested token-count representation."""
    if representation not in TOKEN_REPRESENTATIONS:
        choices = ", ".join(TOKEN_REPRESENTATIONS)
        raise ValueError(
            f"Unknown token representation {representation!r}; choose one of: {choices}."
        )
    return cast(TokenRepresentation, representation)


def serialize_conversation_value(raw_value: Any) -> str:
    """Serialize a raw field exactly as the legacy datagen token counter did.

    This is deliberately distinct from :func:`extract_conversation_text`: JSON
    punctuation, field names, roles, and metadata within the raw value all count.
    """
    if raw_value is None:
        return ""
    if isinstance(raw_value, str):
        return raw_value
    try:
        return json.dumps(raw_value, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        return str(raw_value)


def _extract_from_message_content(content: Any) -> str:
    parts: list[str] = []
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            parts.append(text)
    elif isinstance(content, list):
        for item in content:
            parts.append(_extract_from_message_content(item))
    return "\n".join(p for p in parts if p)


def extract_conversation_text(record: Any) -> str:
    """Extract the full concatenated text from a conversation record.

    Handles ``messages``, ``conversations``, and various fallback fields.
    """
    if isinstance(record, dict):
        messages = record.get("messages") or record.get("conversations")
        if isinstance(messages, list):
            collected: list[str] = []
            for message in messages:
                if isinstance(message, dict):
                    if "content" in message:
                        collected.append(
                            _extract_from_message_content(message["content"])
                        )
                    for key in ("value", "text"):
                        value = message.get(key)
                        if isinstance(value, str):
                            collected.append(value)
                elif isinstance(message, str):
                    collected.append(message)
            combined = "\n".join(chunk for chunk in collected if chunk)
            if combined:
                return combined
        for field in ("conversation", "text", "prompt", "content"):
            value = record.get(field)
            if isinstance(value, str) and value.strip():
                return value
    return json.dumps(record, ensure_ascii=False)


def extract_chat_template_messages(record: Any) -> list[dict[str, Any]]:
    """Normalize a record's message list for ``tokenizer.apply_chat_template``.

    Only message-shaped records are accepted.  Unlike plain conversation text,
    this representation must preserve roles and therefore never falls back to a
    JSON rendering of arbitrary row metadata.
    """
    if isinstance(record, dict):
        messages = record.get("messages") or record.get("conversations")
    else:
        messages = record
    if not isinstance(messages, list) or not messages:
        raise ValueError(
            "chat_template requires a non-empty `messages` or `conversations` list"
        )

    role_aliases = {"human": "user", "gpt": "assistant"}
    normalized: list[dict[str, Any]] = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"chat_template message {index} is not a mapping")
        raw_role = message.get("role") or message.get("from")
        if not isinstance(raw_role, str) or not raw_role:
            raise ValueError(f"chat_template message {index} has no role or from field")
        if "content" in message:
            content = message["content"]
        elif "value" in message:
            content = message["value"]
        elif "text" in message:
            content = message["text"]
        else:
            raise ValueError(
                f"chat_template message {index} has no content, value, or text field"
            )
        normalized.append(
            {"role": role_aliases.get(raw_role, raw_role), "content": content}
        )
    return normalized


def render_token_representation(
    record: Any,
    representation: TokenRepresentation,
    *,
    tokenizer: Any | None = None,
) -> str:
    """Render one record into one explicit, non-interchangeable token input.

    ``serialized`` preserves the legacy raw-JSON measurement, preferring a row's
    ``conversations`` field. ``conversation_text`` concatenates message text.
    ``chat_template`` asks the supplied tokenizer to format normalized messages.
    """
    representation = validate_token_representation(representation)
    if representation == "serialized":
        raw_value = record
        if isinstance(record, dict):
            for field in ("conversations", "messages"):
                if field in record:
                    raw_value = record[field]
                    break
        return serialize_conversation_value(raw_value)
    if representation == "conversation_text":
        return extract_conversation_text(record)
    if tokenizer is None:
        raise ValueError("chat_template representation requires a tokenizer")
    return tokenizer.apply_chat_template(
        extract_chat_template_messages(record),
        tokenize=False,
        add_generation_prompt=False,
    )


def count_conversation_tokens(
    record: Any,
    tokenizer: Any,
    representation: TokenRepresentation,
) -> int:
    """Count one record with an explicit token representation.

    Chat-template tokenization is intentionally delegated directly to the
    tokenizer so template-added tokens use the tokenizer's native semantics.
    All other representations are encoded without added special tokens.
    """
    representation = validate_token_representation(representation)
    if representation == "chat_template":
        token_ids = tokenizer.apply_chat_template(
            extract_chat_template_messages(record),
            tokenize=True,
            add_generation_prompt=False,
        )
        return len(token_ids)
    return len(
        tokenizer.encode(
            render_token_representation(record, representation),
            add_special_tokens=False,
        )
    )


def count_turns(record) -> int:
    """Estimate the number of turns (messages) in a record."""
    if isinstance(record, dict):
        messages = record.get("messages") or record.get("conversations")
        if isinstance(messages, list):
            return len(messages)
        turn_count = record.get("turn_count")
        if isinstance(turn_count, int):
            return turn_count
    return 0


# ---------------------------------------------------------------------------
# Episode number extraction
# ---------------------------------------------------------------------------


def extract_episode_numbers(values: Iterable) -> List[int]:
    """Parse integer episode indices from various formats (str, int, dict)."""
    episodes: List[int] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, (int, float)):
            episodes.append(int(value))
            continue
        if isinstance(value, str):
            cleaned = value.replace("-", " ").replace("_", " ")
            match = _EPISODE_PATTERN.search(cleaned)
            if match:
                episodes.append(int(match.group(1)))
            continue
        if isinstance(value, dict):
            inner = value.get("episode")
            if isinstance(inner, (int, float)):
                episodes.append(int(inner))
            elif isinstance(inner, str):
                cleaned_inner = inner.replace("-", " ").replace("_", " ")
                match = _EPISODE_PATTERN.search(cleaned_inner)
                if match:
                    episodes.append(int(match.group(1)))
    return episodes


# ---------------------------------------------------------------------------
# Token counting (tiktoken)
# ---------------------------------------------------------------------------


def get_tiktoken_encoder():
    """Return a tiktoken encoder, or ``None`` if tiktoken is unavailable."""
    if tiktoken is None:
        return None
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, encoder) -> int:
    """Count tokens in *text* using *encoder*, falling back to whitespace split."""
    if not text:
        return 0
    if encoder is not None:
        return len(encoder.encode(text, disallowed_special=()))
    return len(text.split())


# ---------------------------------------------------------------------------
# HuggingFace dataset loading
# ---------------------------------------------------------------------------


def load_hf_trace_dataset(repo_id: str, split: str = "train"):
    """Load a HuggingFace dataset with a helpful error message on failure."""
    from datasets import load_dataset

    try:
        return load_dataset(repo_id, split=split)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load dataset '{repo_id}' (split={split}): {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Reward / result extraction
# ---------------------------------------------------------------------------


def extract_reward(record) -> Optional[float]:
    """Extract a numeric reward from a record's ``result`` field.

    Returns ``None`` if the value is missing, null-like, or non-numeric.
    """
    if isinstance(record, dict):
        candidate = record.get("result")
    else:
        candidate = record
    if candidate is None:
        return None
    if isinstance(candidate, (int, float)):
        return float(candidate)
    if isinstance(candidate, str):
        stripped = candidate.strip()
        if not stripped or stripped.lower() in ("none", "null", ""):
            return None
        try:
            return float(stripped)
        except (TypeError, ValueError):
            return None
    return None


def mean_reward_per_trial(rows: list) -> Optional[float]:
    """Compute the flat mean reward across all trials (Harbor-style 'accuracy').

    This matches Harbor's Mean metric: every trial contributes equally,
    with errors/missing results counted as 0. No per-task grouping.
    """
    values = []
    for row in rows:
        reward = extract_reward(row)
        values.append(reward if reward is not None else 0.0)
    if not values:
        return None
    return sum(values) / len(values)


# ---------------------------------------------------------------------------
# Infrastructure-error filtering (matches Harbor drop_ei logic)
# ---------------------------------------------------------------------------

DEFAULT_DROP_EXCEPTIONS: frozenset[str] = frozenset(
    [
        "AgentEnvironmentTimeoutError",
        "DaytonaError",
        "DaytonaRateLimitError",
        "DaytonaNotFoundError",
        "EnvironmentStartTimeoutError",
        "SandboxBuildFailedError",
        "PodmanHPCTimeoutError",
        "PodmanHPCCommandError",
        "ApptainerTimeoutError",
        "ApptainerCommandError",
    ]
)


def filter_ei(
    rows: list[dict],
    drop_exceptions: frozenset[str] = DEFAULT_DROP_EXCEPTIONS,
) -> list[dict]:
    """Drop rows whose result is an infrastructure error type."""
    filtered = []
    for row in rows:
        error = extract_error_type(row)
        if error is not None and error in drop_exceptions:
            continue
        filtered.append(row)
    return filtered


def tasks_with_n_attempts(
    rows: list[dict],
    n_attempts: int,
) -> set[str]:
    """Return tasks that have at least *n_attempts* rows after filtering."""
    from collections import Counter

    counts = Counter(row["task"] for row in rows)
    return {task for task, count in counts.items() if count >= n_attempts}


def mean_reward_per_trial_ei(
    rows: list[dict],
    drop_exceptions: frozenset[str] = DEFAULT_DROP_EXCEPTIONS,
    n_attempts: int = 1,
) -> Optional[float]:
    """Mean reward after dropping infra-errored trials and incomplete tasks.

    Mirrors Harbor's MeanDropEI metric.
    """
    clean = filter_ei(rows, drop_exceptions)
    complete_tasks = tasks_with_n_attempts(clean, n_attempts)
    values = []
    for row in clean:
        if row["task"] not in complete_tasks:
            continue
        reward = extract_reward(row)
        values.append(reward if reward is not None else 0.0)
    if not values:
        return None
    return sum(values) / len(values)


def ei_common_tasks(
    all_datasets: dict[str, list[dict]],
    drop_exceptions: frozenset[str] = DEFAULT_DROP_EXCEPTIONS,
    n_attempts: int = 1,
) -> set[str]:
    """Return tasks present and complete (post-EI-filter) in ALL datasets."""
    per_model: list[set[str]] = []
    for rows in all_datasets.values():
        clean = filter_ei(rows, drop_exceptions)
        per_model.append(tasks_with_n_attempts(clean, n_attempts))
    if not per_model:
        return set()
    return set.intersection(*per_model)


def extract_error_type(record) -> Optional[str]:
    """Extract an error type name from a record's ``result`` field.

    Returns the string value when it is not parseable as a number (i.e. it's
    an exception class name like ``"AgentTimeoutError"``).  Returns ``None``
    for numeric results or missing values.
    """
    if isinstance(record, dict):
        candidate = record.get("result")
    else:
        candidate = record
    if candidate is None:
        return None
    if isinstance(candidate, (int, float)):
        return None
    if isinstance(candidate, str):
        stripped = candidate.strip()
        if not stripped or stripped.lower() in ("none", "null"):
            return None
        try:
            float(stripped)
            return None  # it's a number, not an error
        except (TypeError, ValueError):
            return stripped
    return None


# ---------------------------------------------------------------------------
# Date extraction
# ---------------------------------------------------------------------------


def extract_date(record) -> Optional[datetime]:
    """Parse the ``date`` field of a record into a :class:`datetime`.

    Accepts ISO 8601 strings.  Returns ``None`` on failure.
    """
    if isinstance(record, dict):
        candidate = record.get("date")
    else:
        candidate = record
    if candidate is None:
        return None
    if isinstance(candidate, datetime):
        return candidate
    if isinstance(candidate, str):
        try:
            return datetime.fromisoformat(candidate)
        except (TypeError, ValueError):
            return None
    return None


# ---------------------------------------------------------------------------
# Task identity
# ---------------------------------------------------------------------------


def task_id_of(record) -> Optional[str]:
    """Best-effort canonical task identifier for a trace row.

    Trace datasets disagree on which field holds the task identity — some
    use ``task``, others ``task_name``, others bury it inside a nested
    dict. This helper handles the common cases.
    """
    if not isinstance(record, dict):
        return None
    for key in ("task", "task_name", "task_id", "trial_name"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


# ---------------------------------------------------------------------------
# Trace dataclass + unified loader
# ---------------------------------------------------------------------------


@dataclass
class Trace:
    """Normalized view over a single trace row.

    Field-extraction (``extract_reward``, ``extract_error_type``, etc.) is
    eager and cached here so downstream analyses don't repeat the work.
    The ``raw`` dict is kept for one-off field access.
    """

    raw: Dict[str, Any]
    task: Optional[str] = None
    reward: Optional[float] = None
    error_type: Optional[str] = None
    date: Optional[datetime] = None
    turns: int = 0
    conversation: str = ""
    failure_mode: Optional[str] = None
    # Optional cached token count (filled on demand to avoid tokenizer cost).
    tokens: Optional[int] = None
    # Origin tag (e.g. "hf:penfever/dataset", "jsonl:/path/foo.jsonl",
    # "dir:/path/results"). Useful when cross-referencing traces from
    # multiple sources in the same analysis pass.
    source: Optional[str] = None
    # Cached behavioral feature pack. Eagerly extracted at load time so the
    # behavioral-delta / temporal aggregation paths can read fields directly
    # without re-walking the conversation.
    behavioral: BehavioralFeatures = field(default_factory=BehavioralFeatures)

    @classmethod
    def from_row(
        cls,
        row: Dict[str, Any],
        source: Optional[str] = None,
        encoder: Optional[Any] = None,
    ) -> "Trace":
        # update_hf_failure_modes writes to "failure_mode_analysis" by default;
        # accept either the new short name or the legacy long name.
        fm = row.get("failure_mode") or row.get("failure_mode_analysis")
        if isinstance(fm, dict):
            # GPT-5 judge returns a dict; collapse to its 'mode' field if present.
            fm = fm.get("mode") or fm.get("category") or fm.get("summary")
        return cls(
            raw=row,
            task=task_id_of(row),
            reward=extract_reward(row),
            error_type=extract_error_type(row),
            date=extract_date(row),
            turns=count_turns(row),
            conversation=extract_conversation_text(row),
            failure_mode=fm if isinstance(fm, str) else None,
            source=source,
            behavioral=extract_behavioral_features(row, encoder=encoder),
        )


def _iter_results_in_dir(root: Path) -> Iterator[Dict[str, Any]]:
    """Walk a directory of trial folders, yielding their result.json contents.

    Mirrors the eval-trace layout (``<root>/<trial-name>/result.json`` plus
    optional ``agent/``, ``verifier/``). Each yielded row carries the
    trial_name + the conversation pulled from ``agent/conversation.json``
    when present, so downstream code can treat it like an HF row.
    """
    for trial_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        result_path = trial_dir / "result.json"
        if not result_path.exists():
            continue
        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict):
            payload = {"result": payload}
        payload.setdefault("trial_name", trial_dir.name)
        # Pull the conversation if it sits at the conventional path.
        conv_path = trial_dir / "agent" / "conversation.json"
        if conv_path.exists():
            try:
                conv = json.loads(conv_path.read_text(encoding="utf-8"))
                if isinstance(conv, list):
                    payload.setdefault("messages", conv)
            except (json.JSONDecodeError, OSError):
                pass
        yield payload


def load_traces(
    source: Union[str, Path],
    *,
    split: str = "train",
    max_rows: Optional[int] = None,
    encoder: Optional[Any] = None,
) -> List[Trace]:
    """Load traces from any of the supported source types.

    Supported ``source`` formats:
      - HuggingFace dataset id (``"penfever/foo-bar"``)
      - JSONL path (``.jsonl`` or ``.json`` suffix)
      - Local directory of trial folders (each holding ``result.json``)

    Returns a list of :class:`Trace` instances. ``max_rows`` caps the
    number of rows loaded (useful for smoke tests). ``encoder`` (e.g. from
    :func:`get_tiktoken_encoder`) is passed through to the behavioral-feature
    extractor for accurate think-token / assistant-token counts. When
    ``encoder`` is ``None`` we auto-fetch one — pass it explicitly when
    loading many datasets to avoid repeated initialisation.
    """
    # Lazily fetch a shared encoder so behavioral features get accurate
    # tokenization for free.
    if encoder is None:
        encoder = get_tiktoken_encoder()

    if isinstance(source, str) and not Path(source).expanduser().exists():
        # Treat as HF repo id.
        ds = load_hf_trace_dataset(source, split=split)
        traces: List[Trace] = []
        for i, row in enumerate(ds):
            if max_rows is not None and i >= max_rows:
                break
            traces.append(Trace.from_row(row, source=f"hf:{source}", encoder=encoder))
        return traces

    path = Path(source).expanduser().resolve()
    if path.is_file() and path.suffix in (".jsonl", ".json"):
        rows = list(iter_jsonl(path))
        if max_rows is not None:
            rows = rows[:max_rows]
        return [
            Trace.from_row(r, source=f"jsonl:{path}", encoder=encoder) for r in rows
        ]

    if path.is_dir():
        rows: List[Dict[str, Any]] = []
        for row in _iter_results_in_dir(path):
            rows.append(row)
            if max_rows is not None and len(rows) >= max_rows:
                break
        return [Trace.from_row(r, source=f"dir:{path}", encoder=encoder) for r in rows]

    raise ValueError(
        f"Cannot resolve traces source {source!r}: not an existing JSONL, "
        "result.json directory, or HF dataset id."
    )


def group_by_task(traces: Sequence[Trace]) -> Dict[str, List[Trace]]:
    """Bucket traces by their canonical task id; drops rows with no task."""
    out: Dict[str, List[Trace]] = {}
    for t in traces:
        if t.task is None:
            continue
        out.setdefault(t.task, []).append(t)
    return out
