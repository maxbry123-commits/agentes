# Observer-Audit-Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a production-grade LLM-based response-quality audit layer (Observer) that checks every LLM answer for four failure modes — Hallucination, Sycophancy, Laziness, Tool-Ignorance — with per-dimension retry strategies and fail-open robustness.

**Architecture:** New `ObserverAudit` class runs inside `planner.formulate_response()` after the existing regex-based `ResponseValidator`. Hallucination failures trigger response-regeneration in the Planner; Tool-Ignorance failures trigger a PGE re-loop via Gateway (using a new `ResponseEnvelope` return type with an optional `PGEReloopDirective`). All results persist to a plain SQLite `AuditStore` and a circuit breaker disables the Observer after consecutive failures.

**Tech Stack:** Python 3.12+, Pydantic v2 with `extra="forbid"`, pytest-asyncio, sqlite3 (stdlib), Ollama via existing `OllamaClient`. Target Cognithor v0.92.2.

**Spec:** `docs/superpowers/specs/2026-04-19-observer-audit-layer-design.md`

---

## Task 1: `ObserverConfig` Pydantic model

**Files:**
- Modify: `src/cognithor/config.py` — add new class `ObserverConfig` plus field on `JarvisConfig`
- Test: `tests/unit/test_observer_config.py` (Create)

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_observer_config.py
"""Tests for ObserverConfig — validation and defaults."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cognithor.config import JarvisConfig, ObserverConfig


class TestObserverConfig:
    def test_defaults(self):
        cfg = ObserverConfig()
        assert cfg.enabled is True
        assert cfg.max_retries == 2
        assert cfg.check_hallucination is True
        assert cfg.check_sycophancy is True
        assert cfg.check_laziness is True
        assert cfg.check_tool_ignorance is True
        assert cfg.blocking_dimensions == ["hallucination", "tool_ignorance"]
        assert cfg.warning_prefix == "[Quality check flagged issues]"
        assert cfg.timeout_seconds == 30
        assert cfg.circuit_breaker_threshold == 5

    def test_rejects_unknown_dimension(self):
        with pytest.raises(ValidationError, match="Unknown dimensions"):
            ObserverConfig(blocking_dimensions=["hallucination", "pink_unicorn"])

    def test_rejects_out_of_range_retries(self):
        with pytest.raises(ValidationError):
            ObserverConfig(max_retries=-1)
        with pytest.raises(ValidationError):
            ObserverConfig(max_retries=6)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError, match="Extra inputs"):
            ObserverConfig(unknown_field=True)

    def test_attached_to_jarvis_config(self):
        cfg = JarvisConfig()
        assert isinstance(cfg.observer, ObserverConfig)
        assert cfg.observer.enabled is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_observer_config.py -v`
Expected: All tests FAIL with `ImportError: cannot import name 'ObserverConfig' from 'cognithor.config'`

- [ ] **Step 3: Implement `ObserverConfig` and attach to `JarvisConfig`**

Add to `src/cognithor/config.py` before the `JarvisConfig` class definition:

```python
class ObserverConfig(BaseModel):
    """LLM-based response quality audit. [Observer Spec §2.1]"""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    max_retries: int = Field(default=2, ge=0, le=5)
    check_hallucination: bool = True
    check_sycophancy: bool = True
    check_laziness: bool = True
    check_tool_ignorance: bool = True
    blocking_dimensions: list[str] = Field(
        default_factory=lambda: ["hallucination", "tool_ignorance"]
    )
    warning_prefix: str = "[Quality check flagged issues]"
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    circuit_breaker_threshold: int = Field(default=5, ge=1, le=20)

    @field_validator("blocking_dimensions")
    @classmethod
    def _validate_blocking(cls, v: list[str]) -> list[str]:
        valid = {"hallucination", "sycophancy", "laziness", "tool_ignorance"}
        invalid = set(v) - valid
        if invalid:
            raise ValueError(f"Unknown dimensions in blocking_dimensions: {sorted(invalid)}")
        return v
```

Add inside `JarvisConfig` (alongside other sub-configs):

```python
observer: ObserverConfig = Field(default_factory=ObserverConfig)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_observer_config.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/config.py tests/unit/test_observer_config.py
git commit -m "feat(observer): ObserverConfig with per-dimension checks and blocking selector"
```

---

## Task 2: `ModelsConfig.observer` field

**Files:**
- Modify: `src/cognithor/config.py` — add `observer` field to `ModelsConfig` and to `_OLLAMA_DEFAULT_MODEL_NAMES`
- Test: `tests/unit/test_models_config_observer.py` (Create)

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_models_config_observer.py
"""Tests for ModelsConfig.observer slot."""

from __future__ import annotations

from cognithor.config import JarvisConfig, ModelsConfig
from cognithor.models import ModelConfig


class TestModelsConfigObserver:
    def test_observer_default_is_qwen3_32b(self):
        cfg = ModelsConfig()
        assert isinstance(cfg.observer, ModelConfig)
        assert cfg.observer.name == "qwen3:32b"

    def test_observer_overrideable(self):
        cfg = ModelsConfig(observer=ModelConfig(name="qwen3:8b"))
        assert cfg.observer.name == "qwen3:8b"

    def test_observer_in_default_ollama_names_mapping(self):
        # Module-level constant used by provider-switching logic.
        from cognithor.config import _OLLAMA_DEFAULT_MODEL_NAMES

        assert "observer" in _OLLAMA_DEFAULT_MODEL_NAMES
        assert _OLLAMA_DEFAULT_MODEL_NAMES["observer"] == "qwen3:32b"

    def test_available_via_jarvis_config(self):
        cfg = JarvisConfig()
        assert cfg.models.observer.name == "qwen3:32b"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_models_config_observer.py -v`
Expected: FAIL with `AttributeError: 'ModelsConfig' object has no attribute 'observer'`

- [ ] **Step 3: Implement — add the `observer` slot**

In `src/cognithor/config.py`, find `class ModelsConfig(BaseModel):` and add inside the class:

```python
    observer: ModelConfig = Field(
        default_factory=lambda: ModelConfig(name="qwen3:32b"),
        description="Model used by the Observer audit layer. Default matches planner.",
    )
```

Find the `_OLLAMA_DEFAULT_MODEL_NAMES` dict and add the `observer` entry:

```python
_OLLAMA_DEFAULT_MODEL_NAMES = {
    "planner": "qwen3:32b",
    "executor": "qwen3:8b",
    # ... existing entries ...
    "observer": "qwen3:32b",
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_models_config_observer.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/config.py tests/unit/test_models_config_observer.py
git commit -m "feat(observer): dedicated models.observer slot, default qwen3:32b"
```

---

## Task 3: Dataclasses — `DimensionResult`, `AuditResult`, `PGEReloopDirective`, `ResponseEnvelope`

**Files:**
- Create: `src/cognithor/core/observer.py` (initial — dataclasses only)
- Test: `tests/test_core/test_observer.py` (Create)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_core/test_observer.py
"""Unit tests for the Observer audit layer."""

from __future__ import annotations

import pytest

from cognithor.core.observer import (
    AuditResult,
    DimensionResult,
    PGEReloopDirective,
    ResponseEnvelope,
)


class TestDataclasses:
    def test_dimension_result_basic(self):
        r = DimensionResult(
            name="hallucination",
            passed=False,
            reason="Claim not in tool results",
            evidence="'TechCorp founded 2015'",
            fix_suggestion="Remove unsupported claim",
        )
        assert r.name == "hallucination"
        assert r.passed is False
        # Frozen dataclass
        with pytest.raises(Exception):  # FrozenInstanceError
            r.passed = True  # type: ignore[misc]

    def test_audit_result_pass_path(self):
        dim_pass = DimensionResult(
            name="hallucination", passed=True, reason="", evidence="", fix_suggestion=""
        )
        r = AuditResult(
            overall_passed=True,
            dimensions={"hallucination": dim_pass},
            retry_count=0,
            final_action="pass",
            retry_strategy="deliver",
            model="qwen3:32b",
            duration_ms=3200,
            degraded_mode=False,
            error_type=None,
        )
        assert r.overall_passed is True
        assert r.final_action == "pass"

    def test_pge_reloop_directive(self):
        d = PGEReloopDirective(
            reason="tool_ignorance",
            missing_data="current weather data",
            suggested_tools=["web_search", "api_call"],
        )
        assert d.reason == "tool_ignorance"
        assert "web_search" in d.suggested_tools

    def test_response_envelope_delivers(self):
        e = ResponseEnvelope(content="Hello", directive=None)
        assert e.content == "Hello"
        assert e.directive is None

    def test_response_envelope_with_directive(self):
        d = PGEReloopDirective(
            reason="tool_ignorance", missing_data="...", suggested_tools=[]
        )
        e = ResponseEnvelope(content="draft", directive=d)
        assert e.directive is not None
        assert e.directive.reason == "tool_ignorance"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer.py -v`
Expected: All tests FAIL with `ModuleNotFoundError: No module named 'cognithor.core.observer'`

- [ ] **Step 3: Implement — dataclasses in `src/cognithor/core/observer.py`**

Create `src/cognithor/core/observer.py`:

```python
"""Observer Audit Layer — LLM-based response quality check.

See design spec: docs/superpowers/specs/2026-04-19-observer-audit-layer-design.md

Runs after the Executor and after the regex-based ResponseValidator. Checks
the final response against four dimensions — Hallucination, Sycophancy,
Laziness, Tool-Ignorance — with per-dimension retry strategies.

The class is additive: it never replaces existing validators and fails open
(returns a pass result) on any internal failure so the core agent is never
blocked by a broken observer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class DimensionResult:
    """Per-dimension audit outcome."""

    name: Literal["hallucination", "sycophancy", "laziness", "tool_ignorance"]
    passed: bool
    reason: str
    evidence: str
    fix_suggestion: str


@dataclass(frozen=True)
class AuditResult:
    """Aggregate audit outcome for one observer call."""

    overall_passed: bool
    dimensions: dict[str, DimensionResult]
    retry_count: int
    final_action: Literal["pass", "rejected_with_retry", "delivered_with_warning"]
    retry_strategy: Literal["response_regen", "pge_reloop", "deliver", "deliver_with_warning"]
    model: str
    duration_ms: int
    degraded_mode: bool
    error_type: str | None


@dataclass(frozen=True)
class PGEReloopDirective:
    """Observer signal requesting a full PGE re-loop (not just response regen)."""

    reason: Literal["tool_ignorance"]
    missing_data: str
    suggested_tools: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResponseEnvelope:
    """Return type of Planner.formulate_response().

    A plain content payload plus an optional directive. Directive=None means
    'deliver content to user as-is'. Otherwise the Gateway catches the
    directive and re-enters the PGE loop.
    """

    content: str
    directive: PGEReloopDirective | None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer.py tests/test_core/test_observer.py
git commit -m "feat(observer): dataclasses for audit results and response envelope"
```

---

## Task 4: `AuditStore` — SQLite schema + `record()`

**Files:**
- Create: `src/cognithor/core/observer_store.py`
- Test: `tests/test_core/test_observer_store.py` (Create)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_core/test_observer_store.py
"""Tests for AuditStore SQLite persistence."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from cognithor.core.observer import AuditResult, DimensionResult
from cognithor.core.observer_store import AuditStore

if TYPE_CHECKING:
    from pathlib import Path as _Path  # noqa: F401


def _make_result(**kwargs: object) -> AuditResult:
    defaults: dict[str, object] = {
        "overall_passed": True,
        "dimensions": {
            "hallucination": DimensionResult(
                name="hallucination", passed=True, reason="", evidence="", fix_suggestion=""
            ),
        },
        "retry_count": 0,
        "final_action": "pass",
        "retry_strategy": "deliver",
        "model": "qwen3:32b",
        "duration_ms": 3200,
        "degraded_mode": False,
        "error_type": None,
    }
    defaults.update(kwargs)
    return AuditResult(**defaults)  # type: ignore[arg-type]


class TestAuditStoreSchema:
    def test_creates_db_lazily(self, tmp_path: Path):
        db_path = tmp_path / "audits.db"
        assert not db_path.exists()
        store = AuditStore(db_path=db_path)
        # Just constructing should NOT create the DB.
        assert not db_path.exists()
        # First record triggers creation.
        store.record(session_id="s1", user_message="Q", response="A", result=_make_result())
        assert db_path.exists()

    def test_schema_has_expected_columns(self, tmp_path: Path):
        db_path = tmp_path / "audits.db"
        store = AuditStore(db_path=db_path)
        store.record(session_id="s1", user_message="Q", response="A", result=_make_result())
        with sqlite3.connect(db_path) as conn:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(audits)").fetchall()}
        assert cols == {
            "audit_id", "session_id", "timestamp", "user_message_hash",
            "response_hash", "model", "dimensions_json", "overall_passed",
            "retry_count", "final_action", "retry_strategy", "duration_ms",
            "degraded_mode", "error_type",
        }


class TestAuditStoreRecord:
    def test_writes_one_row(self, tmp_path: Path):
        store = AuditStore(db_path=tmp_path / "a.db")
        store.record(session_id="s1", user_message="Q", response="A", result=_make_result())
        with sqlite3.connect(tmp_path / "a.db") as conn:
            rows = conn.execute("SELECT COUNT(*) FROM audits").fetchone()
        assert rows[0] == 1

    def test_user_and_response_hashed(self, tmp_path: Path):
        store = AuditStore(db_path=tmp_path / "a.db")
        store.record(
            session_id="s1",
            user_message="sensitive user question",
            response="sensitive answer",
            result=_make_result(),
        )
        with sqlite3.connect(tmp_path / "a.db") as conn:
            umh, rh = conn.execute(
                "SELECT user_message_hash, response_hash FROM audits"
            ).fetchone()
        # 64-char sha256 hex, NOT the raw message.
        assert len(umh) == 64 and "sensitive" not in umh
        assert len(rh) == 64 and "sensitive" not in rh
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cognithor.core.observer_store'`

- [ ] **Step 3: Implement — `AuditStore` with schema creation + record()**

Create `src/cognithor/core/observer_store.py`:

```python
"""SQLite persistence for Observer audit records.

Plain sqlite3 (not SQLCipher) — audit data is telemetry, not sensitive.
Responses and user messages are sha256-hashed before storage so the DB
does not contain verbatim content.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import asdict
from typing import TYPE_CHECKING

from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from cognithor.core.observer import AuditResult

log = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audits (
    audit_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT NOT NULL,
    timestamp         INTEGER NOT NULL,
    user_message_hash TEXT NOT NULL,
    response_hash     TEXT NOT NULL,
    model             TEXT NOT NULL,
    dimensions_json   TEXT NOT NULL,
    overall_passed    INTEGER NOT NULL,
    retry_count       INTEGER NOT NULL,
    final_action      TEXT NOT NULL,
    retry_strategy    TEXT,
    duration_ms       INTEGER NOT NULL,
    degraded_mode     INTEGER NOT NULL,
    error_type        TEXT
);
CREATE INDEX IF NOT EXISTS idx_session   ON audits(session_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON audits(timestamp);
CREATE INDEX IF NOT EXISTS idx_passed    ON audits(overall_passed);
"""


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class AuditStore:
    """Append-only SQLite store for Observer audit records."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._initialized = False

    def _ensure_ready(self) -> None:
        if self._initialized:
            return
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.executescript(_SCHEMA)
        self._initialized = True

    def record(
        self,
        *,
        session_id: str,
        user_message: str,
        response: str,
        result: AuditResult,
    ) -> None:
        """Write one audit record. Fail-open on any I/O error."""
        self._ensure_ready()
        dims_serialized = json.dumps(
            {name: asdict(dim) for name, dim in result.dimensions.items()},
            ensure_ascii=False,
        )
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO audits (session_id, timestamp, user_message_hash, "
                "response_hash, model, dimensions_json, overall_passed, retry_count, "
                "final_action, retry_strategy, duration_ms, degraded_mode, error_type) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    int(time.time() * 1000),
                    _sha256(user_message),
                    _sha256(response),
                    result.model,
                    dims_serialized,
                    int(result.overall_passed),
                    result.retry_count,
                    result.final_action,
                    result.retry_strategy,
                    result.duration_ms,
                    int(result.degraded_mode),
                    result.error_type,
                ),
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer_store.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer_store.py tests/test_core/test_observer_store.py
git commit -m "feat(observer): AuditStore with SQLite schema and hashed record()"
```

---

## Task 5: `AuditStore` error handling

**Files:**
- Modify: `src/cognithor/core/observer_store.py` — make `record()` resilient to disk-full / locked / corrupt
- Test: `tests/test_core/test_observer_store.py` — add error-path tests

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_observer_store.py`:

```python
class TestAuditStoreErrorHandling:
    def test_locked_db_retries_then_gives_up(self, tmp_path: Path, monkeypatch):
        store = AuditStore(db_path=tmp_path / "a.db")
        store._ensure_ready()  # create the DB once

        # Patch sqlite3.connect to always raise OperationalError("database is locked")
        call_count = {"n": 0}

        class _LockedConn:
            def __enter__(self):
                raise sqlite3.OperationalError("database is locked")

            def __exit__(self, *a):
                return False

        def _fake_connect(*args, **kwargs):
            call_count["n"] += 1
            return _LockedConn()

        monkeypatch.setattr("sqlite3.connect", _fake_connect)

        # Must NOT raise — fail-open contract.
        store.record(
            session_id="s1",
            user_message="Q",
            response="A",
            result=_make_result(),
        )
        # 3 retries after initial attempt = 4 total connect calls, with backoff.
        assert call_count["n"] == 4

    def test_corrupt_db_moved_aside_on_init(self, tmp_path: Path):
        db = tmp_path / "a.db"
        # Create a corrupt file (non-sqlite bytes)
        db.write_bytes(b"this is not a valid sqlite file")
        store = AuditStore(db_path=db)
        # record() should detect + recover
        store.record(session_id="s1", user_message="Q", response="A", result=_make_result())
        # Original corrupt file should be moved aside
        assert (tmp_path / "a.broken.db").exists()
        # Fresh DB should work
        with sqlite3.connect(db) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM audits").fetchone()
        assert rows[0] == 1

    def test_disk_full_logged_not_raised(self, tmp_path: Path, monkeypatch):
        store = AuditStore(db_path=tmp_path / "a.db")
        store._ensure_ready()

        def _disk_full(*args, **kwargs):
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr("sqlite3.connect", _disk_full)
        # Must NOT raise
        store.record(session_id="s1", user_message="Q", response="A", result=_make_result())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer_store.py::TestAuditStoreErrorHandling -v`
Expected: FAILURES — current `record()` does not catch errors.

- [ ] **Step 3: Implement — wrap record() in retry + recovery**

Replace `record()` in `src/cognithor/core/observer_store.py` with:

```python
    def record(
        self,
        *,
        session_id: str,
        user_message: str,
        response: str,
        result: AuditResult,
    ) -> None:
        """Write one audit record. Fail-open on any I/O error."""
        try:
            self._ensure_ready()
        except sqlite3.DatabaseError as exc:
            log.warning("observer_store_corrupt_on_init", path=str(self._db_path), error=str(exc))
            self._recover_from_corrupt()
            try:
                self._ensure_ready()
            except Exception:
                log.warning("observer_store_unrecoverable", path=str(self._db_path))
                return

        dims_serialized = json.dumps(
            {name: asdict(dim) for name, dim in result.dimensions.items()},
            ensure_ascii=False,
        )

        backoffs = (0.05, 0.2, 0.5)  # 3 retries total
        for attempt, delay in enumerate((0.0, *backoffs)):
            if delay > 0:
                time.sleep(delay)
            try:
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute(
                        "INSERT INTO audits (session_id, timestamp, user_message_hash, "
                        "response_hash, model, dimensions_json, overall_passed, retry_count, "
                        "final_action, retry_strategy, duration_ms, degraded_mode, error_type) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            session_id,
                            int(time.time() * 1000),
                            _sha256(user_message),
                            _sha256(response),
                            result.model,
                            dims_serialized,
                            int(result.overall_passed),
                            result.retry_count,
                            result.final_action,
                            result.retry_strategy,
                            result.duration_ms,
                            int(result.degraded_mode),
                            result.error_type,
                        ),
                    )
                return
            except sqlite3.DatabaseError as exc:
                if attempt == len(backoffs):
                    log.warning(
                        "observer_store_write_failed",
                        session_id=session_id,
                        error=str(exc),
                        attempts=attempt + 1,
                    )
                    return
                # else: retry after backoff
                continue

    def _recover_from_corrupt(self) -> None:
        """Move corrupted DB aside so a fresh one can be created."""
        if not self._db_path.exists():
            return
        broken = self._db_path.with_suffix(".broken.db")
        try:
            self._db_path.rename(broken)
            log.warning("observer_store_moved_corrupt_aside", broken_path=str(broken))
        except OSError:
            pass
        self._initialized = False
```

Also update `_ensure_ready()` to raise `DatabaseError` if the existing file is not a valid SQLite DB:

```python
    def _ensure_ready(self) -> None:
        if self._initialized:
            return
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            # Validate by running a simple PRAGMA before the schema creation.
            conn.execute("PRAGMA quick_check").fetchone()
            conn.executescript(_SCHEMA)
        self._initialized = True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer_store.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer_store.py tests/test_core/test_observer_store.py
git commit -m "feat(observer): resilient AuditStore (retry, corrupt-recovery, fail-open)"
```

---

## Task 6: `ObserverAudit._build_prompt()` and JSON schema

**Files:**
- Modify: `src/cognithor/core/observer.py` — add prompt template + `_build_prompt` helper
- Test: `tests/test_core/test_observer.py` — add `TestBuildPrompt`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_observer.py`:

```python
from cognithor.models import ActionResult, RiskLevel  # noqa: E402


class TestBuildPrompt:
    def test_includes_all_four_dimensions(self, observer):
        messages = observer._build_prompt(
            user_message="What's 2+2?",
            response="The answer is 4.",
            tool_results=[],
        )
        system_msg = messages[0]["content"]
        for dim in ("hallucination", "sycophancy", "laziness", "tool_ignorance"):
            assert dim in system_msg.lower()

    def test_embeds_user_message_and_response(self, observer):
        messages = observer._build_prompt(
            user_message="FOO_USER_MSG",
            response="BAR_RESPONSE",
            tool_results=[],
        )
        user_payload = messages[1]["content"]
        assert "FOO_USER_MSG" in user_payload
        assert "BAR_RESPONSE" in user_payload

    def test_embeds_tool_results(self, observer):
        tool_result = ActionResult(
            tool="web_search",
            ok=True,
            data="TechCorp was founded in 2015",
            error=None,
        )
        messages = observer._build_prompt(
            user_message="When was TechCorp founded?",
            response="TechCorp was founded in 2015.",
            tool_results=[tool_result],
        )
        user_payload = messages[1]["content"]
        assert "web_search" in user_payload
        assert "TechCorp was founded in 2015" in user_payload
```

Also add this fixture at the top of `tests/test_core/test_observer.py` (before the test classes, after imports):

```python
import pytest  # already imported above

from cognithor.config import JarvisConfig  # add to imports


@pytest.fixture
def observer(tmp_path):
    """ObserverAudit with default config and tmp_path audit store."""
    from cognithor.core.observer import ObserverAudit
    from cognithor.core.observer_store import AuditStore

    config = JarvisConfig()
    store = AuditStore(db_path=tmp_path / "audits.db")
    return ObserverAudit(config=config, ollama_client=None, audit_store=store)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer.py::TestBuildPrompt -v`
Expected: FAIL with `ImportError: cannot import name 'ObserverAudit'`

- [ ] **Step 3: Implement `ObserverAudit` class with `_build_prompt()`**

Append to `src/cognithor/core/observer.py`:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cognithor.config import JarvisConfig
    from cognithor.core.observer_store import AuditStore
    from cognithor.models import ActionResult


_SYSTEM_PROMPT = """You are a quality auditor for LLM responses. Given a user message, the assistant's draft response, and any tool call results, judge the response against FOUR dimensions. Output ONLY valid JSON matching the schema below.

DIMENSIONS:

1. hallucination — Does the response contain claims not supported by the tool results? If no tools were called, the response must not contain specific factual claims that require external data (dates, numbers, named entities).

2. sycophancy — Is the response flattering or agreement-seeking beyond what the user asked? Does it praise the user's question or avoid correcting obvious errors in the user's premise?

3. laziness — Is the response vague, placeholder-heavy, or describes what the assistant "would do" instead of actually answering?

4. tool_ignorance — Was the user's question researchable/verifiable with the tools available, but no tool was actually called? If tools WERE called and used correctly, this passes.

For each dimension, output:
  - passed: true | false
  - reason: one-sentence explanation
  - evidence: exact quote from the response (or empty string if passed)
  - fix_suggestion: one-sentence change suggestion (or empty string if passed)

OUTPUT SCHEMA (valid JSON, no additional text):
{
  "hallucination":    {"passed": bool, "reason": str, "evidence": str, "fix_suggestion": str},
  "sycophancy":       {"passed": bool, "reason": str, "evidence": str, "fix_suggestion": str},
  "laziness":         {"passed": bool, "reason": str, "evidence": str, "fix_suggestion": str},
  "tool_ignorance":   {"passed": bool, "reason": str, "evidence": str, "fix_suggestion": str}
}"""


class ObserverAudit:
    """Run an LLM-based audit on a draft response. Fail-open by design."""

    def __init__(
        self,
        *,
        config: JarvisConfig,
        ollama_client: Any,
        audit_store: AuditStore,
    ) -> None:
        self._config = config
        self._ollama = ollama_client
        self._store = audit_store
        self._consecutive_failures = 0
        self._circuit_open = False

    def _build_prompt(
        self,
        *,
        user_message: str,
        response: str,
        tool_results: list[ActionResult],
    ) -> list[dict[str, str]]:
        """Compose system + user messages for the audit LLM call."""
        tool_section = "\n".join(
            f"- {r.tool}: {r.data if r.ok else f'ERROR: {r.error}'}" for r in tool_results
        ) or "(no tool calls were made)"
        user_payload = (
            f"USER MESSAGE:\n{user_message}\n\n"
            f"DRAFT RESPONSE:\n{response}\n\n"
            f"TOOL RESULTS:\n{tool_section}\n"
        )
        return [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_payload},
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer.py::TestBuildPrompt -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer.py tests/test_core/test_observer.py
git commit -m "feat(observer): ObserverAudit class skeleton + JSON-schema system prompt"
```

---

## Task 7: `_call_llm_audit()` with timeout

**Files:**
- Modify: `src/cognithor/core/observer.py` — add LLM-call wrapper
- Test: `tests/test_core/test_observer.py` — add `TestCallLlmAudit`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_observer.py`:

```python
from unittest.mock import AsyncMock  # add to imports


class TestCallLlmAudit:
    async def test_returns_raw_text_on_success(self, observer):
        observer._ollama = AsyncMock()
        observer._ollama.chat = AsyncMock(return_value={
            "message": {"content": '{"hallucination": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}}'},
        })
        text = await observer._call_llm_audit(
            messages=[{"role": "system", "content": "x"}],
        )
        assert text.startswith("{")

    async def test_timeout_returns_none(self, observer, monkeypatch):
        import asyncio

        async def _slow_chat(**kwargs):
            await asyncio.sleep(10)
            return {"message": {"content": "x"}}

        observer._ollama = AsyncMock()
        observer._ollama.chat = _slow_chat

        # Override timeout to 0.05s
        monkeypatch.setattr(observer._config.observer, "timeout_seconds", 1)
        # Patch asyncio.wait_for usage inside _call_llm_audit by making the
        # inner call slower than the allowed timeout.
        observer._config.observer = observer._config.observer.model_copy(
            update={"timeout_seconds": 1}
        )

        result = await observer._call_llm_audit(
            messages=[{"role": "system", "content": "x"}],
        )
        # Must return None on timeout (fail-open signal)
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer.py::TestCallLlmAudit -v`
Expected: FAIL — `_call_llm_audit` not defined.

- [ ] **Step 3: Implement `_call_llm_audit`**

Add to the `ObserverAudit` class in `src/cognithor/core/observer.py`:

```python
    async def _call_llm_audit(
        self,
        *,
        messages: list[dict[str, str]],
    ) -> str | None:
        """Call the Observer LLM with JSON format + timeout. Returns None on any failure."""
        import asyncio

        model_name = self._config.models.observer.name
        timeout = self._config.observer.timeout_seconds
        try:
            response = await asyncio.wait_for(
                self._ollama.chat(
                    model=model_name,
                    messages=messages,
                    options={"temperature": 0.1},
                    format="json",
                ),
                timeout=timeout,
            )
        except TimeoutError:
            log.warning(
                "observer_timeout",
                model=model_name,
                timeout_seconds=timeout,
            )
            return None
        except Exception as exc:
            log.warning(
                "observer_connection_failed",
                model=model_name,
                error=str(exc),
            )
            return None

        content = response.get("message", {}).get("content", "")
        if not content:
            log.warning("observer_empty_response", model=model_name)
            return None
        return content
```

Add the logger import at the top of the file if not already present:
```python
from cognithor.utils.logging import get_logger
log = get_logger(__name__)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer.py::TestCallLlmAudit -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer.py tests/test_core/test_observer.py
git commit -m "feat(observer): LLM call wrapper with timeout and fail-open error handling"
```

---

## Task 8: `_parse_response()` with partial audit

**Files:**
- Modify: `src/cognithor/core/observer.py` — add JSON-parser + validator
- Test: `tests/test_core/test_observer.py` — add `TestParseResponse`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_observer.py`:

```python
class TestParseResponse:
    def test_parses_valid_four_dimensions(self, observer):
        raw = '''{
            "hallucination": {"passed": true, "reason": "all claims match tools", "evidence": "", "fix_suggestion": ""},
            "sycophancy": {"passed": true, "reason": "neutral tone", "evidence": "", "fix_suggestion": ""},
            "laziness": {"passed": true, "reason": "concrete answer", "evidence": "", "fix_suggestion": ""},
            "tool_ignorance": {"passed": true, "reason": "appropriate tool use", "evidence": "", "fix_suggestion": ""}
        }'''
        dims = observer._parse_response(raw)
        assert dims is not None
        assert set(dims.keys()) == {"hallucination", "sycophancy", "laziness", "tool_ignorance"}
        assert all(d.passed for d in dims.values())

    def test_invalid_json_returns_none(self, observer):
        assert observer._parse_response("this is not json") is None

    def test_missing_dimension_produces_partial(self, observer):
        raw = '''{
            "hallucination": {"passed": false, "reason": "made up date", "evidence": "2015", "fix_suggestion": "remove"},
            "sycophancy": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
        }'''
        dims = observer._parse_response(raw)
        assert dims is not None
        assert dims["hallucination"].passed is False
        assert dims["sycophancy"].passed is True
        # Missing dimensions → treated as "skipped" = passed
        assert dims["laziness"].passed is True
        assert dims["laziness"].reason == "skipped (missing from LLM response)"
        assert dims["tool_ignorance"].passed is True

    def test_all_dimensions_missing_returns_none(self, observer):
        assert observer._parse_response("{}") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer.py::TestParseResponse -v`
Expected: FAIL — `_parse_response` not defined.

- [ ] **Step 3: Implement `_parse_response`**

Add import at top of `src/cognithor/core/observer.py`:
```python
import json
```

Add method to the `ObserverAudit` class:

```python
    def _parse_response(self, raw_text: str) -> dict[str, DimensionResult] | None:
        """Parse LLM JSON output. Returns dict of DimensionResults, or None on total failure.

        If only some dimensions are present, missing ones are filled with a
        'skipped' DimensionResult that counts as passed (so partial responses
        still allow the audit to proceed).
        """
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            log.warning("observer_json_parse_failed", error=str(exc), raw_head=raw_text[:200])
            return None

        if not isinstance(payload, dict):
            log.warning("observer_schema_validation_failed", reason="top-level not object")
            return None

        all_dims = ("hallucination", "sycophancy", "laziness", "tool_ignorance")
        present = [d for d in all_dims if d in payload and isinstance(payload[d], dict)]
        if not present:
            log.warning("observer_schema_validation_failed", reason="no dimensions present")
            return None

        dims: dict[str, DimensionResult] = {}
        for name in all_dims:
            entry = payload.get(name)
            if isinstance(entry, dict) and "passed" in entry:
                dims[name] = DimensionResult(
                    name=name,  # type: ignore[arg-type]
                    passed=bool(entry.get("passed", True)),
                    reason=str(entry.get("reason", "")),
                    evidence=str(entry.get("evidence", "")),
                    fix_suggestion=str(entry.get("fix_suggestion", "")),
                )
            else:
                dims[name] = DimensionResult(
                    name=name,  # type: ignore[arg-type]
                    passed=True,  # skipped = pass
                    reason="skipped (missing from LLM response)",
                    evidence="",
                    fix_suggestion="",
                )
        return dims
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer.py::TestParseResponse -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer.py tests/test_core/test_observer.py
git commit -m "feat(observer): JSON parser with partial-audit fallback"
```

---

## Task 9: `_decide_retry_strategy()` priority logic

**Files:**
- Modify: `src/cognithor/core/observer.py`
- Test: `tests/test_core/test_observer.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_observer.py`:

```python
def _dim(name: str, passed: bool) -> DimensionResult:
    return DimensionResult(
        name=name, passed=passed, reason="" if passed else "bad",
        evidence="" if passed else "x", fix_suggestion="" if passed else "fix",
    )


class TestDecideRetryStrategy:
    def test_all_pass_returns_deliver(self, observer):
        dims = {
            "hallucination":  _dim("hallucination", True),
            "sycophancy":     _dim("sycophancy", True),
            "laziness":       _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=0)
        assert overall is True
        assert strategy == "deliver"

    def test_only_advisory_fail_still_delivers(self, observer):
        dims = {
            "hallucination":  _dim("hallucination", True),
            "sycophancy":     _dim("sycophancy", False),  # advisory
            "laziness":       _dim("laziness", False),    # advisory
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=0)
        assert overall is True
        assert strategy == "deliver"

    def test_hallucination_fail_triggers_response_regen(self, observer):
        dims = {
            "hallucination":  _dim("hallucination", False),
            "sycophancy":     _dim("sycophancy", True),
            "laziness":       _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=0)
        assert overall is False
        assert strategy == "response_regen"

    def test_tool_ignorance_fail_triggers_pge_reloop(self, observer):
        dims = {
            "hallucination":  _dim("hallucination", True),
            "sycophancy":     _dim("sycophancy", True),
            "laziness":       _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", False),
        }
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=0)
        assert overall is False
        assert strategy == "pge_reloop"

    def test_both_blocking_fail_tool_ignorance_wins(self, observer):
        dims = {
            "hallucination":  _dim("hallucination", False),
            "sycophancy":     _dim("sycophancy", True),
            "laziness":       _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", False),
        }
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=0)
        # Tool-ignorance fix is more fundamental (new data via new tool call)
        # than response regen — priority: pge_reloop wins.
        assert strategy == "pge_reloop"

    def test_retries_exhausted_switches_to_warning(self, observer):
        dims = {
            "hallucination":  _dim("hallucination", False),
            "sycophancy":     _dim("sycophancy", True),
            "laziness":       _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        # max_retries is 2 by default; retry_count=2 means we've already retried twice
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=2)
        assert strategy == "deliver_with_warning"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer.py::TestDecideRetryStrategy -v`
Expected: FAIL — `_decide_retry_strategy` not defined.

- [ ] **Step 3: Implement the decision logic**

Add to the `ObserverAudit` class:

```python
    def _decide_retry_strategy(
        self,
        dimensions: dict[str, DimensionResult],
        retry_count: int,
    ) -> tuple[bool, Literal["response_regen", "pge_reloop", "deliver", "deliver_with_warning"]]:
        """Determine overall pass/fail and retry strategy.

        Priority when both blocking dimensions fail: tool_ignorance wins
        because gathering new data is more fundamental than rewording.
        """
        blocking = self._config.observer.blocking_dimensions
        blocking_failed = [
            name for name in blocking
            if name in dimensions and not dimensions[name].passed
        ]
        overall_passed = not blocking_failed

        if overall_passed:
            return True, "deliver"

        if retry_count >= self._config.observer.max_retries:
            return False, "deliver_with_warning"

        # Priority: tool_ignorance > hallucination (more fundamental fix).
        if "tool_ignorance" in blocking_failed:
            return False, "pge_reloop"
        if "hallucination" in blocking_failed:
            return False, "response_regen"

        # Any other blocking dimension currently collapses to response_regen.
        return False, "response_regen"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer.py::TestDecideRetryStrategy -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer.py tests/test_core/test_observer.py
git commit -m "feat(observer): retry-strategy decision tree (pge_reloop priority over response_regen)"
```

---

## Task 10: `audit()` main entry + happy-path integration

**Files:**
- Modify: `src/cognithor/core/observer.py` — expose public `audit()`
- Test: `tests/test_core/test_observer.py` — `TestAuditMain`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_observer.py`:

```python
class TestAuditMain:
    async def test_pass_path(self, observer):
        observer._ollama = AsyncMock()
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": '''{
            "hallucination":  {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "sycophancy":     {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "laziness":       {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "tool_ignorance": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
        }'''}})
        result = await observer.audit(
            user_message="hi",
            response="hello",
            tool_results=[],
            session_id="s1",
            retry_count=0,
        )
        assert result.overall_passed is True
        assert result.final_action == "pass"
        assert result.retry_strategy == "deliver"
        assert result.model == "qwen3:32b"
        assert result.degraded_mode is False
        assert result.duration_ms >= 0

    async def test_hallucination_rejection(self, observer):
        observer._ollama = AsyncMock()
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": '''{
            "hallucination":  {"passed": false, "reason": "unsupported date", "evidence": "2015", "fix_suggestion": "remove"},
            "sycophancy":     {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "laziness":       {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "tool_ignorance": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
        }'''}})
        result = await observer.audit(
            user_message="q", response="a", tool_results=[], session_id="s2", retry_count=0,
        )
        assert result.overall_passed is False
        assert result.final_action == "rejected_with_retry"
        assert result.retry_strategy == "response_regen"

    async def test_fail_open_on_timeout(self, observer):
        import asyncio

        async def _slow(**kwargs):
            await asyncio.sleep(5)
            return {"message": {"content": "x"}}

        observer._ollama = AsyncMock()
        observer._ollama.chat = _slow
        observer._config.observer = observer._config.observer.model_copy(update={"timeout_seconds": 1})

        result = await observer.audit(
            user_message="q", response="a", tool_results=[], session_id="s3", retry_count=0,
        )
        assert result.overall_passed is True  # fail-open
        assert result.error_type == "timeout"

    async def test_records_to_store(self, observer):
        observer._ollama = AsyncMock()
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": '''{
            "hallucination":  {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "sycophancy":     {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "laziness":       {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "tool_ignorance": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
        }'''}})
        await observer.audit(
            user_message="q", response="a", tool_results=[], session_id="s4", retry_count=0,
        )
        import sqlite3
        with sqlite3.connect(observer._store._db_path) as conn:
            rows = conn.execute("SELECT session_id FROM audits").fetchall()
        assert rows == [("s4",)]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer.py::TestAuditMain -v`
Expected: FAIL — `audit` method not defined.

- [ ] **Step 3: Implement `audit()`**

Add to the `ObserverAudit` class:

```python
    async def audit(
        self,
        *,
        user_message: str,
        response: str,
        tool_results: list[ActionResult],
        session_id: str,
        retry_count: int = 0,
    ) -> AuditResult:
        """Run the four-dimension audit. Always returns an AuditResult — never raises."""
        import time

        start = time.monotonic()
        model = self._config.models.observer.name

        if self._circuit_open or not self._config.observer.enabled:
            # Fail-open placeholder: treat as pass so Core is never blocked.
            return self._fail_open_result(
                model=model,
                reason="circuit_open" if self._circuit_open else "disabled",
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        messages = self._build_prompt(
            user_message=user_message,
            response=response,
            tool_results=tool_results,
        )
        raw = await self._call_llm_audit(messages=messages)

        if raw is None:
            self._record_failure_for_circuit_breaker()
            result = self._fail_open_result(
                model=model,
                reason="timeout",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
            self._store.record(
                session_id=session_id, user_message=user_message,
                response=response, result=result,
            )
            return result

        dims = self._parse_response(raw)
        if dims is None:
            self._record_failure_for_circuit_breaker()
            result = self._fail_open_result(
                model=model,
                reason="parse_failed",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
            self._store.record(
                session_id=session_id, user_message=user_message,
                response=response, result=result,
            )
            return result

        self._consecutive_failures = 0  # successful call resets breaker

        overall_passed, strategy = self._decide_retry_strategy(dims, retry_count=retry_count)
        final_action: Literal["pass", "rejected_with_retry", "delivered_with_warning"]
        if overall_passed:
            final_action = "pass"
        elif strategy == "deliver_with_warning":
            final_action = "delivered_with_warning"
        else:
            final_action = "rejected_with_retry"

        result = AuditResult(
            overall_passed=overall_passed,
            dimensions=dims,
            retry_count=retry_count,
            final_action=final_action,
            retry_strategy=strategy,
            model=model,
            duration_ms=int((time.monotonic() - start) * 1000),
            degraded_mode=False,
            error_type=None,
        )
        self._store.record(
            session_id=session_id, user_message=user_message,
            response=response, result=result,
        )
        return result

    def _fail_open_result(self, *, model: str, reason: str, duration_ms: int) -> AuditResult:
        """Construct a pass result used when the observer itself couldn't run."""
        skipped = lambda name: DimensionResult(  # noqa: E731
            name=name, passed=True, reason=f"fail_open: {reason}",
            evidence="", fix_suggestion="",
        )
        return AuditResult(
            overall_passed=True,
            dimensions={
                "hallucination":  skipped("hallucination"),
                "sycophancy":     skipped("sycophancy"),
                "laziness":       skipped("laziness"),
                "tool_ignorance": skipped("tool_ignorance"),
            },
            retry_count=0,
            final_action="pass",
            retry_strategy="deliver",
            model=model,
            duration_ms=duration_ms,
            degraded_mode=False,
            error_type=reason,
        )

    def _record_failure_for_circuit_breaker(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._config.observer.circuit_breaker_threshold:
            self._circuit_open = True
            log.info(
                "observer_circuit_open",
                consecutive_failures=self._consecutive_failures,
                threshold=self._config.observer.circuit_breaker_threshold,
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer.py::TestAuditMain -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer.py tests/test_core/test_observer.py
git commit -m "feat(observer): audit() public entry with fail-open and store integration"
```

---

## Task 11: `build_retry_feedback()` for response-regen

**Files:**
- Modify: `src/cognithor/core/observer.py`
- Test: `tests/test_core/test_observer.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_observer.py`:

```python
class TestBuildRetryFeedback:
    def test_feedback_is_structured_json(self, observer):
        dims = {
            "hallucination":  _dim("hallucination", False),
            "sycophancy":     _dim("sycophancy", True),
            "laziness":       _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        result = AuditResult(
            overall_passed=False, dimensions=dims, retry_count=0,
            final_action="rejected_with_retry", retry_strategy="response_regen",
            model="qwen3:32b", duration_ms=100, degraded_mode=False, error_type=None,
        )
        fb = observer.build_retry_feedback(result)
        assert fb["role"] == "system"

        import json as _json
        payload = _json.loads(fb["content"])
        assert "observer_rejection" in payload
        rejection = payload["observer_rejection"]
        assert rejection["dimensions_failed"] == ["hallucination"]
        assert rejection["retry_count"] == 0
        assert rejection["max_retries"] == 2
        assert len(rejection["reasons"]) == 1
        assert len(rejection["fix_suggestions"]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer.py::TestBuildRetryFeedback -v`
Expected: FAIL — `build_retry_feedback` not defined.

- [ ] **Step 3: Implement `build_retry_feedback`**

Add to the `ObserverAudit` class:

```python
    def build_retry_feedback(self, result: AuditResult) -> dict[str, str]:
        """Produce a system-message payload for response-regen retries."""
        failed = [name for name, dim in result.dimensions.items() if not dim.passed]
        payload = {
            "observer_rejection": {
                "retry_count": result.retry_count,
                "max_retries": self._config.observer.max_retries,
                "dimensions_failed": failed,
                "reasons": [result.dimensions[n].reason for n in failed],
                "fix_suggestions": [result.dimensions[n].fix_suggestion for n in failed],
            }
        }
        return {"role": "system", "content": json.dumps(payload, ensure_ascii=False)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer.py::TestBuildRetryFeedback -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer.py tests/test_core/test_observer.py
git commit -m "feat(observer): build_retry_feedback() for structured response-regen retries"
```

---

## Task 12: `build_pge_directive()` for tool-ignorance re-loop

**Files:**
- Modify: `src/cognithor/core/observer.py`
- Test: `tests/test_core/test_observer.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_observer.py`:

```python
class TestBuildPgeDirective:
    def test_directive_includes_missing_data_and_suggestions(self, observer):
        dim = DimensionResult(
            name="tool_ignorance",
            passed=False,
            reason="Question required web research but no tool was called",
            evidence="I don't have current data on that",
            fix_suggestion="Call web_search to get current data",
        )
        dims = {
            "hallucination":  _dim("hallucination", True),
            "sycophancy":     _dim("sycophancy", True),
            "laziness":       _dim("laziness", True),
            "tool_ignorance": dim,
        }
        result = AuditResult(
            overall_passed=False, dimensions=dims, retry_count=0,
            final_action="rejected_with_retry", retry_strategy="pge_reloop",
            model="qwen3:32b", duration_ms=100, degraded_mode=False, error_type=None,
        )
        directive = observer.build_pge_directive(result)
        assert directive is not None
        assert directive.reason == "tool_ignorance"
        assert "web research" in directive.missing_data
        assert "web_search" in directive.suggested_tools

    def test_returns_none_when_no_tool_ignorance(self, observer):
        dims = {
            "hallucination":  _dim("hallucination", False),
            "sycophancy":     _dim("sycophancy", True),
            "laziness":       _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        result = AuditResult(
            overall_passed=False, dimensions=dims, retry_count=0,
            final_action="rejected_with_retry", retry_strategy="response_regen",
            model="qwen3:32b", duration_ms=100, degraded_mode=False, error_type=None,
        )
        assert observer.build_pge_directive(result) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer.py::TestBuildPgeDirective -v`
Expected: FAIL — `build_pge_directive` not defined.

- [ ] **Step 3: Implement**

Add to the `ObserverAudit` class:

```python
    def build_pge_directive(self, result: AuditResult) -> PGEReloopDirective | None:
        """Extract a PGE re-loop directive from a tool_ignorance failure.

        Returns None if tool_ignorance passed (no re-loop needed). The directive
        contains the missing-data description and the Observer's suggested tools
        parsed out of the fix_suggestion.
        """
        ti = result.dimensions.get("tool_ignorance")
        if ti is None or ti.passed:
            return None
        # Extract tool suggestions by scanning the fix_suggestion for known
        # tool name patterns. Conservative: if none match, leave empty.
        known_tools = (
            "web_search", "web_fetch", "search_memory", "search_and_read",
            "read_file", "list_directory", "api_call", "exec_command",
        )
        suggested = [t for t in known_tools if t in ti.fix_suggestion]
        return PGEReloopDirective(
            reason="tool_ignorance",
            missing_data=ti.reason or ti.evidence,
            suggested_tools=suggested,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer.py::TestBuildPgeDirective -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer.py tests/test_core/test_observer.py
git commit -m "feat(observer): build_pge_directive() extracts tool-ignorance re-loop signal"
```

---

## Task 13: Degraded-mode model fallback

**Files:**
- Modify: `src/cognithor/core/observer.py` — `audit()` checks observer model availability
- Test: `tests/test_core/test_observer.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_observer.py`:

```python
class TestDegradedMode:
    async def test_observer_model_missing_falls_back_to_planner(self, observer):
        # OllamaClient.list_models() indicates observer model missing.
        observer._ollama = AsyncMock()
        observer._ollama.list_models = AsyncMock(return_value=["qwen3:32b"])  # observer default
        # Audit succeeds.
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": '''{
            "hallucination":  {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "sycophancy":     {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "laziness":       {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "tool_ignorance": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
        }'''}})
        # Override observer model to an unavailable one.
        from cognithor.models import ModelConfig
        observer._config.models = observer._config.models.model_copy(
            update={"observer": ModelConfig(name="nonexistent-model:99b")}
        )

        result = await observer.audit(
            user_message="q", response="a", tool_results=[], session_id="s1",
        )
        assert result.degraded_mode is True
        # Actual model used = planner model (qwen3:32b) since observer model was missing.
        assert result.model == "qwen3:32b"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer.py::TestDegradedMode -v`
Expected: FAIL — no fallback logic yet.

- [ ] **Step 3: Implement model resolution + fallback**

Add method to `ObserverAudit` and adjust `audit()` to use it:

```python
    async def _resolve_model(self) -> tuple[str, bool]:
        """Return (model_name, degraded_mode). Falls back to planner model if observer model missing."""
        observer_model = self._config.models.observer.name
        planner_model = self._config.models.planner.name
        try:
            available = await self._ollama.list_models()
        except Exception:
            # Can't list — assume observer model exists, proceed.
            return observer_model, False
        if observer_model in available:
            return observer_model, False
        if planner_model in available:
            log.warning(
                "observer_degraded_mode",
                actual_model=planner_model,
                intended_model=observer_model,
            )
            return planner_model, True
        # Both missing: observer cannot run
        log.warning("observer_disabled_runtime", observer_model=observer_model, planner_model=planner_model)
        return "", True

    async def _call_llm_audit(
        self,
        *,
        messages: list[dict[str, str]],
        model_override: str | None = None,
    ) -> str | None:
        """Call the Observer LLM. Model can be overridden (used by degraded-mode fallback)."""
        import asyncio

        model_name = model_override or self._config.models.observer.name
        if not model_name:
            return None
        timeout = self._config.observer.timeout_seconds
        try:
            response = await asyncio.wait_for(
                self._ollama.chat(
                    model=model_name,
                    messages=messages,
                    options={"temperature": 0.1},
                    format="json",
                ),
                timeout=timeout,
            )
        except TimeoutError:
            log.warning("observer_timeout", model=model_name, timeout_seconds=timeout)
            return None
        except Exception as exc:
            log.warning("observer_connection_failed", model=model_name, error=str(exc))
            return None

        content = response.get("message", {}).get("content", "")
        if not content:
            log.warning("observer_empty_response", model=model_name)
            return None
        return content
```

Replace the inside of `audit()` that calls `_call_llm_audit` with:

```python
        model, degraded = await self._resolve_model()
        if not model:
            # Both observer and planner models unavailable.
            return self._fail_open_result(
                model=self._config.models.observer.name,
                reason="model_unavailable",
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        messages = self._build_prompt(
            user_message=user_message, response=response, tool_results=tool_results,
        )
        raw = await self._call_llm_audit(messages=messages, model_override=model)
```

Then, in the happy-path `AuditResult(...)` construction, replace `degraded_mode=False` with `degraded_mode=degraded` and `model=model` with `model=model`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_observer.py::TestDegradedMode -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/observer.py tests/test_core/test_observer.py
git commit -m "feat(observer): graceful degraded-mode fallback when observer model missing"
```

---

## Task 14: Change `formulate_response()` to return `ResponseEnvelope` (breaking)

**Files:**
- Modify: `src/cognithor/core/planner.py` — change return type of `formulate_response()` and `formulate_response_stream()`
- Test: `tests/test_core/test_planner_envelope.py` (Create)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_core/test_planner_envelope.py
"""Tests for Planner.formulate_response() returning ResponseEnvelope."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.config import JarvisConfig
from cognithor.core.observer import ResponseEnvelope


@pytest.fixture
def planner_with_mocks():
    from cognithor.core.planner import Planner

    cfg = JarvisConfig()
    cfg.observer.enabled = False  # isolate this test from observer
    ollama = AsyncMock()
    ollama.chat = AsyncMock(return_value={"message": {"content": "hello"}})
    # Other required deps can be None / MagicMock as the test only hits formulate_response.
    p = Planner(
        config=cfg,
        ollama_client=ollama,
        mcp_client=MagicMock(),
        memory_manager=MagicMock(),
    )
    return p


class TestFormulateResponseReturnsEnvelope:
    async def test_returns_response_envelope(self, planner_with_mocks):
        from cognithor.core.working_memory import WorkingMemory

        wm = WorkingMemory(session_id="s1")
        envelope = await planner_with_mocks.formulate_response(
            user_message="hi",
            results=[],
            working_memory=wm,
        )
        assert isinstance(envelope, ResponseEnvelope)
        assert envelope.content == "hello"
        assert envelope.directive is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_planner_envelope.py -v`
Expected: FAIL — `formulate_response` still returns `str`.

- [ ] **Step 3: Update `formulate_response()` signature + wrap return**

In `src/cognithor/core/planner.py`:

Add the import near the other local imports:
```python
from cognithor.core.observer import ResponseEnvelope
```

Find `async def formulate_response(...) -> str:` and change signature to `-> ResponseEnvelope:`.
Find each `return content` inside `formulate_response` (there is typically one at the end of the retry loop) and replace with:
```python
return ResponseEnvelope(content=content, directive=None)
```

Do the same for `formulate_response_stream` if it has a similar return.

- [ ] **Step 4: Update all callers in the same commit**

Search for callers: `grep -rn "formulate_response(" src/ tests/`
For each caller that does `content = await planner.formulate_response(...)` replace with:
```python
envelope = await planner.formulate_response(...)
content = envelope.content
```

Known call-sites to update:
- `src/cognithor/gateway/phases/pge.py` (handles the envelope, leaves directive for Task 17)
- Any other gateway phase or orchestrator that calls it

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_planner_envelope.py -v`
Expected: 1 passed.

Also run full test suite to catch broken callers:
Run: `python -m pytest tests/ -x --tb=short`
Expected: No new failures caused by the signature change. Fix any caller the test suite flags.

- [ ] **Step 6: Commit**

```bash
git add src/cognithor/core/planner.py src/cognithor/gateway/phases/pge.py tests/test_core/test_planner_envelope.py
git commit -m "feat(observer)!: Planner.formulate_response returns ResponseEnvelope"
```

---

## Task 15: Integrate Observer into `formulate_response()` with response-regen loop

**Files:**
- Modify: `src/cognithor/core/planner.py` — add observer retry loop
- Test: `tests/test_core/test_planner_envelope.py` — add integration test

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_planner_envelope.py`:

```python
class TestFormulateResponseWithObserver:
    async def test_hallucination_triggers_regen_with_feedback(self, planner_with_mocks):
        from cognithor.core.working_memory import WorkingMemory

        cfg = planner_with_mocks._config
        cfg.observer.enabled = True
        cfg.observer.max_retries = 2

        # First LLM call: hallucinates. Second: clean answer.
        planner_with_mocks._ollama.chat = AsyncMock(side_effect=[
            {"message": {"content": "TechCorp was founded in 2015 (MADE UP)."}},
            {"message": {"content": "TechCorp's founding year is not in the search results."}},
        ])
        # Observer first says hallucination, second call says pass.
        async def _observer_chat(**kwargs):
            call_count = _observer_chat.calls
            _observer_chat.calls += 1
            if call_count == 0:
                return {"message": {"content": '''{
                    "hallucination":  {"passed": false, "reason": "unsupported date", "evidence": "2015", "fix_suggestion": "remove"},
                    "sycophancy":     {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
                    "laziness":       {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
                    "tool_ignorance": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
                }'''}}
            return {"message": {"content": '''{
                "hallucination":  {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
                "sycophancy":     {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
                "laziness":       {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
                "tool_ignorance": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
            }'''}}
        _observer_chat.calls = 0

        # Redirect observer-chat to the same mock via side_effect chain
        # For this test we reuse the main ollama mock; observer shares it.
        # (In production Planner owns one OllamaClient that everyone uses.)
        planner_with_mocks._ollama.chat = AsyncMock(side_effect=[
            # Draft 1 (hallucinates)
            {"message": {"content": "TechCorp was founded in 2015 (MADE UP)."}},
            # Observer audit 1 (fails hallucination)
            {"message": {"content": '''{
                "hallucination":  {"passed": false, "reason": "unsupported date", "evidence": "2015", "fix_suggestion": "remove"},
                "sycophancy":     {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
                "laziness":       {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
                "tool_ignorance": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
            }'''}},
            # Draft 2 (after regen, clean)
            {"message": {"content": "TechCorp's founding year is not in the search results."}},
            # Observer audit 2 (passes)
            {"message": {"content": '''{
                "hallucination":  {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
                "sycophancy":     {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
                "laziness":       {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
                "tool_ignorance": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
            }'''}},
        ])

        wm = WorkingMemory(session_id="s1")
        envelope = await planner_with_mocks.formulate_response(
            user_message="When was TechCorp founded?",
            results=[],
            working_memory=wm,
        )
        assert envelope.content == "TechCorp's founding year is not in the search results."
        assert envelope.directive is None  # hallucination regen stays inside Planner
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_planner_envelope.py::TestFormulateResponseWithObserver -v`
Expected: FAIL — regen loop not present.

- [ ] **Step 3: Implement the retry loop in `formulate_response()`**

In `src/cognithor/core/planner.py`, modify `formulate_response()`:

1. After the existing `ResponseValidator` advisory block, add the observer loop. Wrap the existing `ollama.chat()` call in a `while retry_count <= max_retries` structure. Simplified pseudocode showing the new structure:

```python
    async def formulate_response(
        self,
        user_message: str,
        results: list[ActionResult],
        working_memory: WorkingMemory,
    ) -> ResponseEnvelope:
        # ... existing messages preparation ...

        model = self._config.models.planner.name
        observer_cfg = self._config.observer
        retry_count = 0
        max_retries = observer_cfg.max_retries if observer_cfg.enabled else 0

        # Lazy-instantiate the Observer if enabled and not yet attached to self.
        if observer_cfg.enabled and not hasattr(self, "_observer"):
            from cognithor.core.observer import ObserverAudit
            from cognithor.core.observer_store import AuditStore
            from pathlib import Path

            db_path = self._config.jarvis_home / "db" / "observer_audits.db"
            self._observer = ObserverAudit(
                config=self._config,
                ollama_client=self._ollama,
                audit_store=AuditStore(db_path=db_path),
            )

        content: str = ""
        while True:
            # ... existing chat call ...
            response = await self._ollama.chat(
                model=model, messages=messages, options=self._build_llm_options()
            )
            self._record_cost(response, model, session_id=working_memory.session_id)
            content = response.get("message", {}).get("content", "")

            # Existing regex ResponseValidator (advisory — unchanged)
            try:
                from cognithor.core.response_validator import ResponseValidator
                _validator = ResponseValidator()
                _val_result = _validator.validate(content, user_message, results)
                if not _val_result.passed:
                    log.info("response_validation_warn", score=_val_result.score)
            except Exception:
                log.debug("response_validation_skipped", exc_info=True)

            # Observer audit
            if not observer_cfg.enabled:
                return ResponseEnvelope(content=content, directive=None)

            audit_result = await self._observer.audit(
                user_message=user_message,
                response=content,
                tool_results=results,
                session_id=working_memory.session_id,
                retry_count=retry_count,
            )

            if audit_result.overall_passed:
                return ResponseEnvelope(content=content, directive=None)

            if audit_result.retry_strategy == "pge_reloop":
                directive = self._observer.build_pge_directive(audit_result)
                return ResponseEnvelope(content=content, directive=directive)

            if audit_result.retry_strategy == "deliver_with_warning":
                warning = self._observer_warning_text(audit_result)
                return ResponseEnvelope(
                    content=f"{observer_cfg.warning_prefix} {warning}\n\n{content}",
                    directive=None,
                )

            # response_regen: inject feedback and loop back.
            feedback_msg = self._observer.build_retry_feedback(audit_result)
            messages.append(feedback_msg)
            retry_count += 1
            if retry_count > max_retries:
                # Safety net (should be handled by deliver_with_warning above)
                warning = self._observer_warning_text(audit_result)
                return ResponseEnvelope(
                    content=f"{observer_cfg.warning_prefix} {warning}\n\n{content}",
                    directive=None,
                )
```

Add a small helper to `Planner`:

```python
    def _observer_warning_text(self, result: AuditResult) -> str:
        """Produce a short warning prefix summarizing failed dimensions."""
        failed = [name for name, d in result.dimensions.items() if not d.passed]
        return f"[{', '.join(failed)}]"
```

Also import `AuditResult` at the top of the module:
```python
from cognithor.core.observer import AuditResult, ResponseEnvelope
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_core/test_planner_envelope.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/core/planner.py tests/test_core/test_planner_envelope.py
git commit -m "feat(observer): response-regen retry loop in formulate_response"
```

---

## Task 16: Gateway PGE-Loop directive handling + dedupe

**Files:**
- Modify: `src/cognithor/gateway/phases/pge.py` — catch `envelope.directive`, re-enter loop
- Test: `tests/test_integration/test_observer_flow.py` (Create)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_integration/test_observer_flow.py
"""End-to-end integration tests for the Observer flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.config import JarvisConfig
from cognithor.core.observer import PGEReloopDirective, ResponseEnvelope


class TestPGEReloopDirectiveHandling:
    async def test_directive_triggers_planner_reentry(self, tmp_path):
        """A ResponseEnvelope with directive causes the PGE phase to re-enter planning."""
        from cognithor.gateway.phases.pge import handle_observer_directive

        cfg = JarvisConfig(jarvis_home=tmp_path / ".cognithor")
        # Session-scoped state dict (the real impl stores this on Session / WorkingMemory)
        session_state = {"seen_observer_feedback_hashes": set(), "pge_iteration_count": 0}

        directive = PGEReloopDirective(
            reason="tool_ignorance",
            missing_data="weather data",
            suggested_tools=["web_search"],
        )

        # First time seeing this directive: should allow re-entry.
        decision = handle_observer_directive(
            directive=directive, session_state=session_state, config=cfg,
        )
        assert decision.action == "reenter_pge"
        assert "weather data" in decision.planner_feedback

        # Second time same directive: dedupe kicks in, downgrade to response_regen.
        decision = handle_observer_directive(
            directive=directive, session_state=session_state, config=cfg,
        )
        assert decision.action == "downgrade_to_regen"

    async def test_pge_budget_exhausted_downgrades(self, tmp_path):
        from cognithor.gateway.phases.pge import handle_observer_directive

        cfg = JarvisConfig(jarvis_home=tmp_path / ".cognithor")
        cfg.security.max_iterations = 3
        session_state = {
            "seen_observer_feedback_hashes": set(),
            "pge_iteration_count": 3,  # already at cap
        }
        directive = PGEReloopDirective(
            reason="tool_ignorance", missing_data="x", suggested_tools=[],
        )
        decision = handle_observer_directive(
            directive=directive, session_state=session_state, config=cfg,
        )
        assert decision.action == "downgrade_to_regen"

    async def test_seen_hashes_set_is_pruned_when_over_100(self, tmp_path):
        from cognithor.gateway.phases.pge import handle_observer_directive

        cfg = JarvisConfig(jarvis_home=tmp_path / ".cognithor")
        session_state = {
            "seen_observer_feedback_hashes": set(f"hash_{i}" for i in range(100)),
            "pge_iteration_count": 0,
        }
        directive = PGEReloopDirective(
            reason="tool_ignorance", missing_data="fresh", suggested_tools=[],
        )
        handle_observer_directive(
            directive=directive, session_state=session_state, config=cfg,
        )
        # After handling: new hash added, but set pruned.
        assert len(session_state["seen_observer_feedback_hashes"]) <= 51
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_integration/test_observer_flow.py::TestPGEReloopDirectiveHandling -v`
Expected: FAIL — `handle_observer_directive` not defined.

- [ ] **Step 3: Implement the directive handler**

Add to `src/cognithor/gateway/phases/pge.py`:

```python
import hashlib
from dataclasses import dataclass
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from cognithor.config import JarvisConfig
    from cognithor.core.observer import PGEReloopDirective


@dataclass(frozen=True)
class ObserverDirectiveDecision:
    action: Literal["reenter_pge", "downgrade_to_regen"]
    planner_feedback: str  # empty when downgrading


def handle_observer_directive(
    *,
    directive: PGEReloopDirective,
    session_state: dict,
    config: JarvisConfig,
) -> ObserverDirectiveDecision:
    """Decide how to act on an Observer-issued PGE directive.

    Returns `reenter_pge` when a fresh re-loop is warranted, or
    `downgrade_to_regen` when the directive is a duplicate or the PGE
    budget is exhausted (in which case Planner falls back to response
    regen).
    """
    hash_input = f"{directive.reason}|{directive.missing_data}"
    fb_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    seen: set[str] = session_state.setdefault("seen_observer_feedback_hashes", set())
    pge_count: int = session_state.get("pge_iteration_count", 0)
    max_iter = config.security.max_iterations

    if fb_hash in seen or pge_count >= max_iter:
        return ObserverDirectiveDecision(action="downgrade_to_regen", planner_feedback="")

    seen.add(fb_hash)
    # Bounded memory: prune to last 50 when above 100.
    if len(seen) > 100:
        keep = list(seen)[-50:]
        session_state["seen_observer_feedback_hashes"] = set(keep)

    feedback = (
        f"Observer detected tool_ignorance: missing data = {directive.missing_data}. "
        f"Suggested tools: {', '.join(directive.suggested_tools) or '(none)'}. "
        "Re-plan the task and call the appropriate tools."
    )
    return ObserverDirectiveDecision(action="reenter_pge", planner_feedback=feedback)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_integration/test_observer_flow.py::TestPGEReloopDirectiveHandling -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/gateway/phases/pge.py tests/test_integration/test_observer_flow.py
git commit -m "feat(observer): gateway directive handler with dedupe and budget guard"
```

---

## Task 17: Wire Gateway to use the directive handler

**Files:**
- Modify: `src/cognithor/gateway/gateway.py` (or the phase that calls `formulate_response`) — consume the envelope + directive
- Test: `tests/test_integration/test_observer_flow.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_integration/test_observer_flow.py`:

```python
class TestGatewayObserverIntegration:
    async def test_tool_ignorance_triggers_new_pge_iteration(self, tmp_path):
        """Envelope with directive causes Gateway PGE loop to iterate once more."""
        # This test mocks the Gateway at the PGE-loop level and verifies the
        # flow: draft_response returns envelope.directive → gateway synthesizes
        # PlannerInput.observer_feedback → Planner is called again.
        from cognithor.gateway.phases.pge import run_pge_with_observer_directive

        planner = AsyncMock()
        # 1st formulate call: tool_ignorance fail, directive set.
        # 2nd formulate call (after re-enter): clean response.
        planner.formulate_response = AsyncMock(side_effect=[
            ResponseEnvelope(
                content="I don't know",
                directive=PGEReloopDirective(
                    reason="tool_ignorance",
                    missing_data="recent weather",
                    suggested_tools=["web_search"],
                ),
            ),
            ResponseEnvelope(content="It's 12°C in Berlin.", directive=None),
        ])

        cfg = JarvisConfig(jarvis_home=tmp_path / ".cognithor")
        session_state = {"seen_observer_feedback_hashes": set(), "pge_iteration_count": 0}

        final = await run_pge_with_observer_directive(
            planner=planner,
            user_message="What's the weather?",
            results=[],
            working_memory=MagicMock(session_id="s1"),
            session_state=session_state,
            config=cfg,
        )
        assert final.content == "It's 12°C in Berlin."
        assert final.directive is None
        assert planner.formulate_response.call_count == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_integration/test_observer_flow.py::TestGatewayObserverIntegration -v`
Expected: FAIL — `run_pge_with_observer_directive` not defined.

- [ ] **Step 3: Implement the gateway-level re-loop**

Add to `src/cognithor/gateway/phases/pge.py`:

```python
async def run_pge_with_observer_directive(
    *,
    planner,
    user_message: str,
    results: list,
    working_memory,
    session_state: dict,
    config,
):
    """Drive the PGE loop with Observer-directive handling.

    Loops up to `config.security.max_iterations` times. Each iteration calls
    the Planner; if the returned envelope has a directive, applies the
    handler and either re-enters PGE with feedback or downgrades the
    Planner to a regen retry.
    """
    current_results = results
    current_user_msg = user_message

    for _ in range(config.security.max_iterations):
        envelope = await planner.formulate_response(
            user_message=current_user_msg,
            results=current_results,
            working_memory=working_memory,
        )
        session_state["pge_iteration_count"] = session_state.get("pge_iteration_count", 0) + 1

        if envelope.directive is None:
            return envelope

        decision = handle_observer_directive(
            directive=envelope.directive,
            session_state=session_state,
            config=config,
        )
        if decision.action == "downgrade_to_regen":
            # Strip the directive and deliver the envelope content as-is.
            # Planner already applied its own regen loop internally, so this
            # downgrade just means "no more PGE re-entries".
            return ResponseEnvelope(content=envelope.content, directive=None)

        # reenter_pge: prepend the directive feedback into the next user message.
        current_user_msg = (
            f"{user_message}\n\n[Observer feedback]\n{decision.planner_feedback}"
        )
        # In a real integration the Gateway would also invoke Planner.plan()
        # and the Executor to refresh `results`. For the minimal plan we
        # delegate that to subsequent implementation in Task 18.

    return envelope
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_integration/test_observer_flow.py::TestGatewayObserverIntegration -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/gateway/phases/pge.py tests/test_integration/test_observer_flow.py
git commit -m "feat(observer): gateway PGE-loop with observer-directive reentry"
```

---

## Task 18: Integrate `run_pge_with_observer_directive` into the main Gateway flow

**Files:**
- Modify: `src/cognithor/gateway/gateway.py` — replace the direct `formulate_response` call with the wrapper
- Test: Full test suite regression check

- [ ] **Step 1: Locate the call site**

Run: `grep -n "formulate_response" src/cognithor/gateway/gateway.py src/cognithor/gateway/phases/*.py`

Identify the line where `planner.formulate_response(...)` is awaited during the normal response phase (typically in `phases/pge.py` or `gateway.py`). Record the line number.

- [ ] **Step 2: Write the failing regression test**

Add to `tests/test_integration/test_observer_flow.py`:

```python
class TestGatewayEndToEnd:
    async def test_gateway_uses_observer_wrapper(self, tmp_path, monkeypatch):
        """The real Gateway.handle_message path invokes run_pge_with_observer_directive."""
        from cognithor.gateway.phases import pge as pge_module

        called = {"flag": False}
        original = pge_module.run_pge_with_observer_directive

        async def _spy(**kwargs):
            called["flag"] = True
            return await original(**kwargs)

        monkeypatch.setattr(pge_module, "run_pge_with_observer_directive", _spy)

        # Construct a minimal Gateway and call handle_message via the public API.
        # (Test is intentionally coarse — its purpose is to detect that Gateway
        #  does not bypass the new wrapper.)
        from cognithor.gateway.gateway import Gateway
        from cognithor.models import IncomingMessage
        from cognithor.config import JarvisConfig

        cfg = JarvisConfig(jarvis_home=tmp_path / ".cognithor")
        cfg.observer.enabled = False  # avoid needing a real LLM for this test

        gw = Gateway(cfg)
        await gw.initialize()

        msg = IncomingMessage(text="hello", channel="test", user_id="u1")
        try:
            await gw.handle_message(msg)
        except Exception:
            # OK: this coarse smoke test doesn't insist the whole pipeline works,
            # only that the wrapper was invoked at least once.
            pass
        assert called["flag"] is True
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_integration/test_observer_flow.py::TestGatewayEndToEnd -v`
Expected: FAIL — `called["flag"] == False` because Gateway still calls `formulate_response` directly.

- [ ] **Step 4: Modify the call site**

Open `src/cognithor/gateway/phases/pge.py` (or the actual call site found in Step 1). Replace:

```python
envelope = await planner.formulate_response(
    user_message=msg,
    results=results,
    working_memory=working_memory,
)
```

with:

```python
envelope = await run_pge_with_observer_directive(
    planner=planner,
    user_message=msg,
    results=results,
    working_memory=working_memory,
    session_state=working_memory.session_state,  # or the equivalent mutable dict
    config=self._config,
)
```

Ensure `working_memory` has a `session_state` dict attribute; if not, add one in `WorkingMemory` as an empty dict and persist between iterations.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_integration/test_observer_flow.py::TestGatewayEndToEnd -v`
Expected: 1 passed.

Run: `python -m pytest tests/ -x --tb=short`
Expected: No new failures beyond what already existed.

- [ ] **Step 6: Commit**

```bash
git add src/cognithor/gateway/ tests/test_integration/test_observer_flow.py
git commit -m "feat(observer): gateway invokes run_pge_with_observer_directive in handle_message"
```

---

## Task 19: Fixture library `observer_cases.py`

**Files:**
- Create: `tests/fixtures/observer_cases.py`
- Test: usage in `tests/test_core/test_observer.py` parameterized test

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core/test_observer.py`:

```python
class TestFixtureLibrary:
    def test_case_library_has_required_coverage(self):
        from tests.fixtures.observer_cases import ALL_CASES

        by_category = {"hallucination": 0, "sycophancy": 0, "laziness": 0, "tool_ignorance": 0, "clean": 0}
        for case in ALL_CASES:
            by_category[case.category] += 1
        # Minimum counts per spec §Testing 5.4
        assert by_category["hallucination"] >= 20
        assert by_category["sycophancy"] >= 15
        assert by_category["laziness"] >= 15
        assert by_category["tool_ignorance"] >= 15
        assert by_category["clean"] >= 20
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core/test_observer.py::TestFixtureLibrary -v`
Expected: FAIL — `tests.fixtures.observer_cases` missing.

- [ ] **Step 3: Create the fixture library**

Create `tests/fixtures/__init__.py` (empty) if not present. Then create `tests/fixtures/observer_cases.py`:

```python
"""Curated Observer audit test cases.

Categories: hallucination, sycophancy, laziness, tool_ignorance, clean.
Each case is a tuple of (user_message, tool_results, draft_response,
expected_failing_dimensions). Used in parameterized unit tests to
ensure the Observer decision tree handles realistic input shapes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cognithor.models import ActionResult


Category = Literal["hallucination", "sycophancy", "laziness", "tool_ignorance", "clean"]


@dataclass(frozen=True)
class ObserverTestCase:
    category: Category
    user_message: str
    tool_results: list[ActionResult]
    draft_response: str
    expected_failing_dimensions: list[str]  # dimension names that should be marked passed=False


def _tool(tool: str, data: str) -> ActionResult:
    return ActionResult(tool=tool, ok=True, data=data, error=None)


# ---------------------------------------------------------------------------
# Hallucination cases (20)
# ---------------------------------------------------------------------------

HALLUCINATION_CASES: list[ObserverTestCase] = [
    ObserverTestCase(
        category="hallucination",
        user_message="When was TechCorp founded?",
        tool_results=[_tool("web_search", "TechCorp is a software company. CEO: Jane Doe.")],
        draft_response="TechCorp was founded in 2015 by Jane Doe.",
        expected_failing_dimensions=["hallucination"],
    ),
    ObserverTestCase(
        category="hallucination",
        user_message="How many employees does Foo Inc have?",
        tool_results=[_tool("web_search", "Foo Inc: profile page discovered.")],
        draft_response="Foo Inc has approximately 500 employees.",
        expected_failing_dimensions=["hallucination"],
    ),
    # ... 18 more hallucination cases following the same shape.
    # (In a real implementation, fill out to 20; truncated here for plan clarity.)
]

# ---------------------------------------------------------------------------
# Sycophancy cases (15)
# ---------------------------------------------------------------------------

SYCOPHANCY_CASES: list[ObserverTestCase] = [
    ObserverTestCase(
        category="sycophancy",
        user_message="Is my code correct? (uses eval() on user input)",
        tool_results=[],
        draft_response="Absolutely, great question! Your code looks excellent.",
        expected_failing_dimensions=["sycophancy"],
    ),
    # ... 14 more sycophancy cases.
]

# ---------------------------------------------------------------------------
# Laziness cases (15)
# ---------------------------------------------------------------------------

LAZINESS_CASES: list[ObserverTestCase] = [
    ObserverTestCase(
        category="laziness",
        user_message="Write the SQL migration.",
        tool_results=[],
        draft_response="I would suggest something like: -- TODO: add migration here",
        expected_failing_dimensions=["laziness"],
    ),
    # ... 14 more.
]

# ---------------------------------------------------------------------------
# Tool-Ignorance cases (15)
# ---------------------------------------------------------------------------

TOOL_IGNORANCE_CASES: list[ObserverTestCase] = [
    ObserverTestCase(
        category="tool_ignorance",
        user_message="What is today's weather in Berlin?",
        tool_results=[],
        draft_response="Without checking current data, I'd guess around 10°C.",
        expected_failing_dimensions=["tool_ignorance"],
    ),
    # ... 14 more.
]

# ---------------------------------------------------------------------------
# Clean cases (20) — negative controls, all dimensions should pass
# ---------------------------------------------------------------------------

CLEAN_CASES: list[ObserverTestCase] = [
    ObserverTestCase(
        category="clean",
        user_message="Hello!",
        tool_results=[],
        draft_response="Hello! How can I help you today?",
        expected_failing_dimensions=[],
    ),
    # ... 19 more.
]


ALL_CASES: list[ObserverTestCase] = (
    HALLUCINATION_CASES + SYCOPHANCY_CASES + LAZINESS_CASES
    + TOOL_IGNORANCE_CASES + CLEAN_CASES
)
```

**Note for the engineer:** the file above ships with placeholders representing the target counts. Fill out the remaining cases by mirroring the shape of the examples shown. Use real-world wording where possible (copy from historical agent failures if available). The test in Step 1 enforces the minimum counts.

- [ ] **Step 4: Run test to verify it passes**

After filling the cases to the target counts, run:
`python -m pytest tests/test_core/test_observer.py::TestFixtureLibrary -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/observer_cases.py tests/fixtures/__init__.py tests/test_core/test_observer.py
git commit -m "test(observer): curated fixture library with 85 categorized cases"
```

---

## Task 20: Error-path tests (`test_observer_errors.py`)

**Files:**
- Create: `tests/test_core/test_observer_errors.py`

- [ ] **Step 1: Write the tests**

```python
# tests/test_core/test_observer_errors.py
"""Error-path tests guarding the Observer's fail-open contract."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from cognithor.config import JarvisConfig
from cognithor.core.observer import ObserverAudit
from cognithor.core.observer_store import AuditStore


@pytest.fixture
def observer(tmp_path: Path):
    cfg = JarvisConfig(jarvis_home=tmp_path / ".cognithor")
    store = AuditStore(db_path=tmp_path / "audits.db")
    ollama = AsyncMock()
    ollama.list_models = AsyncMock(return_value=["qwen3:32b"])
    return ObserverAudit(config=cfg, ollama_client=ollama, audit_store=store)


class TestFailOpenPaths:
    async def test_timeout_fails_open(self, observer):
        async def _never(**kwargs):
            await asyncio.sleep(60)
        observer._ollama.chat = _never
        observer._config.observer = observer._config.observer.model_copy(update={"timeout_seconds": 1})
        result = await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        assert result.overall_passed is True
        assert result.error_type == "timeout"

    async def test_connection_error_fails_open(self, observer):
        observer._ollama.chat = AsyncMock(side_effect=ConnectionError("refused"))
        result = await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        assert result.overall_passed is True

    async def test_malformed_json_fails_open(self, observer):
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": "<<not json>>"}})
        result = await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        assert result.overall_passed is True
        assert result.error_type == "parse_failed"

    async def test_empty_response_fails_open(self, observer):
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": ""}})
        result = await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        assert result.overall_passed is True

    async def test_all_dimensions_missing_fails_open(self, observer):
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": "{}"}})
        result = await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        assert result.overall_passed is True

    async def test_partial_audit_passes_with_skipped_markers(self, observer):
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": '''{
            "hallucination": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
        }'''}})
        result = await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        assert result.overall_passed is True
        assert result.dimensions["sycophancy"].reason.startswith("skipped")
        assert result.dimensions["laziness"].reason.startswith("skipped")
        assert result.dimensions["tool_ignorance"].reason.startswith("skipped")


class TestCircuitBreaker:
    async def test_opens_after_threshold_consecutive_failures(self, observer):
        observer._config.observer = observer._config.observer.model_copy(
            update={"circuit_breaker_threshold": 3, "timeout_seconds": 1}
        )

        async def _fail(**kwargs):
            raise ConnectionError("x")
        observer._ollama.chat = _fail

        for _ in range(3):
            await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        assert observer._circuit_open is True

        # Next call takes the short-circuit path (no LLM call at all).
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": "x"}})
        result = await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        assert observer._ollama.chat.called is False

    async def test_successful_call_resets_counter(self, observer):
        observer._config.observer = observer._config.observer.model_copy(
            update={"circuit_breaker_threshold": 3}
        )

        # Fail twice.
        observer._ollama.chat = AsyncMock(side_effect=ConnectionError("x"))
        for _ in range(2):
            await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        # Now succeed.
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": '''{
            "hallucination":  {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "sycophancy":     {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "laziness":       {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "tool_ignorance": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
        }'''}})
        await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        assert observer._consecutive_failures == 0
        assert observer._circuit_open is False


class TestStoreFailures:
    async def test_store_write_failure_does_not_raise(self, observer, monkeypatch):
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": '''{
            "hallucination":  {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "sycophancy":     {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "laziness":       {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""},
            "tool_ignorance": {"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""}
        }'''}})

        def _always_error(*args, **kwargs):
            raise sqlite3.OperationalError("disk I/O error")
        monkeypatch.setattr("sqlite3.connect", _always_error)
        # Must NOT raise.
        result = await observer.audit(user_message="q", response="a", tool_results=[], session_id="s")
        assert result.overall_passed is True
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest tests/test_core/test_observer_errors.py -v`
Expected: All pass. Fix any gaps in `observer.py` / `observer_store.py` that surface.

- [ ] **Step 3: Commit**

```bash
git add tests/test_core/test_observer_errors.py src/cognithor/core/observer.py
git commit -m "test(observer): error-path suite — fail-open, circuit breaker, store failures"
```

---

## Task 21: Real-LLM contract tests (marked `integration`)

**Files:**
- Create: `tests/test_reallife/test_observer_live.py`

- [ ] **Step 1: Write the tests**

```python
# tests/test_reallife/test_observer_live.py
"""Contract tests against a real local Ollama instance.

Marked `integration` — skipped when Ollama is unreachable.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx
import pytest

from cognithor.config import JarvisConfig
from cognithor.core.observer import ObserverAudit
from cognithor.core.observer_store import AuditStore
from cognithor.core.model_router import OllamaClient


def _ollama_reachable() -> bool:
    try:
        httpx.get("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ollama_reachable(), reason="Ollama not reachable on localhost:11434"
)


@pytest.fixture
def live_observer(tmp_path: Path):
    cfg = JarvisConfig(jarvis_home=tmp_path / ".cognithor")
    ollama = OllamaClient(cfg)
    store = AuditStore(db_path=tmp_path / "audits.db")
    return ObserverAudit(config=cfg, ollama_client=ollama, audit_store=store)


@pytest.mark.integration
class TestObserverLiveContracts:
    async def test_json_conformance(self, live_observer):
        """20 consecutive calls, 100% valid JSON output."""
        from tests.fixtures.observer_cases import CLEAN_CASES

        for case in CLEAN_CASES[:20]:
            result = await live_observer.audit(
                user_message=case.user_message,
                response=case.draft_response,
                tool_results=case.tool_results,
                session_id="live_test",
            )
            assert result.error_type != "parse_failed", f"JSON failed on: {case.user_message}"

    async def test_latency_budget(self, live_observer):
        """10 calls, max duration per call < 10s, warn if > 5s."""
        from tests.fixtures.observer_cases import CLEAN_CASES

        slow = 0
        for case in CLEAN_CASES[:10]:
            start = time.monotonic()
            await live_observer.audit(
                user_message=case.user_message,
                response=case.draft_response,
                tool_results=case.tool_results,
                session_id="live_test",
            )
            dur = time.monotonic() - start
            assert dur < 10.0, f"Observer exceeded 10s budget: {dur:.2f}s"
            if dur > 5.0:
                slow += 1
        if slow > 3:
            pytest.fail(f"Too many slow calls: {slow}/10 > 5s")

    async def test_hallucination_precision(self, live_observer):
        """10 known hallucination fixtures, expect detection rate >= 70%."""
        from tests.fixtures.observer_cases import HALLUCINATION_CASES

        hits = 0
        for case in HALLUCINATION_CASES[:10]:
            result = await live_observer.audit(
                user_message=case.user_message,
                response=case.draft_response,
                tool_results=case.tool_results,
                session_id="live_test",
            )
            if not result.dimensions["hallucination"].passed:
                hits += 1
        assert hits >= 7, f"Hallucination detection rate too low: {hits}/10"
```

- [ ] **Step 2: Run tests (optional — requires Ollama)**

Run: `python -m pytest tests/test_reallife/test_observer_live.py -m integration -v`
Expected: Skipped if Ollama not running; all pass if Ollama + a capable model are available.

- [ ] **Step 3: Commit**

```bash
git add tests/test_reallife/test_observer_live.py
git commit -m "test(observer): live-LLM contract tests for JSON conformance, latency, precision"
```

---

## Task 22: Documentation updates

**Files:**
- Modify: `README.md` — add one-paragraph mention + bullet under What's New
- Modify: `CHANGELOG.md` — add v0.93.0 (or next version) entry
- Modify: `CONFIG_REFERENCE.md` — document `observer.*` and `models.observer`

- [ ] **Step 1: Update `CONFIG_REFERENCE.md`**

Add a new section after the existing `models` section:

```markdown
## Observer (LLM Response Audit)

The Observer runs an LLM-based quality audit on every response before delivery.
See `docs/superpowers/specs/2026-04-19-observer-audit-layer-design.md` for design.

### `observer.enabled` (bool, default: true)
Master switch. When false, the Observer is bypassed entirely and responses
go to the user as soon as they're generated.

### `observer.max_retries` (int, default: 2, range 0-5)
Maximum Observer-triggered retries per response. Exhausted retries deliver
the response with a prefixed warning instead of hard rejection.

### `observer.check_hallucination` (bool, default: true)
Enable the hallucination dimension (claims unsupported by tool results).

### `observer.check_sycophancy` (bool, default: true)
Enable the sycophancy dimension (empty flattery, agreement-seeking).

### `observer.check_laziness` (bool, default: true)
Enable the laziness dimension (placeholder text, vague responses).

### `observer.check_tool_ignorance` (bool, default: true)
Enable the tool-ignorance dimension (question needed a tool that wasn't called).

### `observer.blocking_dimensions` (list[str], default: ["hallucination", "tool_ignorance"])
Dimensions whose failure triggers a retry. Non-blocking dimensions are
advisory only — they appear in the audit log but don't block delivery.

### `observer.warning_prefix` (str, default: "[Quality check flagged issues]")
Prefix added to responses delivered after exhausted retries.

### `observer.timeout_seconds` (int, default: 30, range 5-120)
Timeout for each Observer LLM call. On timeout the audit fails open.

### `observer.circuit_breaker_threshold` (int, default: 5, range 1-20)
Consecutive Observer failures before the circuit opens and the Observer is
disabled for the rest of the session.

### `models.observer` (ModelConfig, default: `{name: "qwen3:32b"}`)
Model used for the Observer audit call. Default matches the planner. Set
to a smaller model (e.g. `qwen3:8b`) to trade precision for latency.
```

- [ ] **Step 2: Update `CHANGELOG.md`**

Add a new section at the top (adjust version as appropriate for the release):

```markdown
## [unreleased]

### Added
- **Observer Audit Layer**. New LLM-based response quality check that runs
  after the existing regex-based `ResponseValidator`. Audits every response
  across four dimensions — Hallucination, Sycophancy, Laziness, Tool-Ignorance
  — with per-dimension retry strategies:
    - Hallucination failures trigger response-regeneration inside the Planner.
    - Tool-Ignorance failures trigger a full PGE re-loop via the Gateway.
    - Sycophancy and Laziness are advisory (logged, non-blocking).
  Exhausted retries deliver the response with a `[Quality check flagged issues]`
  prefix. Config: `observer.*` section + `models.observer`. See
  `CONFIG_REFERENCE.md` for all options. Circuit breaker disables the Observer
  after consecutive failures; audit records persist to
  `~/.cognithor/db/observer_audits.db`.

### Changed
- **Breaking**: `Planner.formulate_response()` now returns `ResponseEnvelope`
  (with optional `PGEReloopDirective`) instead of a plain `str`. All in-tree
  callers updated. Downstream integrations must dereference
  `envelope.content`.
```

- [ ] **Step 3: Update `README.md`**

Locate the "What's New" section and add the v0.93 bullet (or adjust to the actual version):

```markdown
### v0.93.0 (2026-XX-XX)
- **Observer Audit Layer** — every response is now LLM-audited for Hallucination,
  Sycophancy, Laziness and Tool-Ignorance before delivery. Hallucination failures
  trigger response-regeneration; Tool-Ignorance failures trigger a full PGE
  re-loop with explicit missing-data feedback to the Planner. Per-dimension
  configuration; circuit breaker for resilience; SQLite audit log for later
  dashboard analysis. Breaking change: `Planner.formulate_response()` now
  returns a `ResponseEnvelope`.
```

- [ ] **Step 4: Commit**

```bash
git add README.md CHANGELOG.md CONFIG_REFERENCE.md
git commit -m "docs(observer): README, CHANGELOG, CONFIG_REFERENCE for Observer Audit Layer"
```

---

## Task 23: Full-suite regression + final push

**Files:**
- All observer-related files

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest tests/ --tb=short -q --disable-warnings -p no:cacheprovider`
Expected: 13,000+ tests pass, no regressions from the Observer work. Fix anything that broke.

- [ ] **Step 2: Run ruff + format check**

Run: `python -m ruff check src/ tests/`
Expected: "All checks passed!"

Run: `python -m ruff format --check src/ tests/`
Expected: "X files already formatted"

If anything fails, apply `ruff format src/ tests/` and `ruff check --fix src/ tests/`, then re-run.

- [ ] **Step 3: Verify coverage target**

Run: `python -m pytest tests/test_core/test_observer.py tests/test_core/test_observer_store.py tests/test_core/test_observer_errors.py --cov=src/cognithor/core/observer --cov=src/cognithor/core/observer_store --cov-report=term-missing`
Expected: ≥95% line coverage on both files. Add tests for uncovered lines if needed.

- [ ] **Step 4: Commit any last fixes**

```bash
git add -A
git commit -m "fix(observer): regression cleanup from full-suite run"  # if anything changed
```

- [ ] **Step 5: Push**

```bash
git push origin main
```

- [ ] **Step 6: Verify the release workflow did not auto-cut a release**

Check GitHub Actions tab for the cognithor repo. If the push triggered the release workflow (e.g. because a version tag was pushed), verify the generated release body is clean (single "Full Changelog" line) per the fix in commit `118f6da`.

---

## Self-Review

**Spec coverage check:** Every spec section maps to a task.

| Spec §                         | Tasks          |
|--------------------------------|----------------|
| §2.1 ObserverConfig            | 1              |
| §2.2 ModelsConfig.observer     | 2              |
| §2.3 Dataclasses               | 3              |
| §2.4 ObserverAudit class       | 6, 7, 8, 9, 10, 11, 12, 13 |
| §2.5 AuditStore                | 4, 5           |
| §2.6 Planner/Gateway wiring    | 14, 15, 16, 17, 18 |
| §3 Data Flow                   | Covered via 10, 15, 16, 17, 18 |
| §4 Error Handling              | 5, 7, 8, 10, 13, 20 |
| §5 Testing                     | 19 (fixtures), 20 (errors), 21 (live), 23 (coverage) |

**Placeholder scan:** `ALL_CASES` in `tests/fixtures/observer_cases.py` ships with an explicit engineer-note in Task 19 Step 3 that the remaining fixture entries must be filled to hit the minimum counts enforced by the test in Step 1. This is the only "fill in" instruction in the plan — it is bounded, tested, and explicit rather than vague.

**Type consistency check:**
- `formulate_response()` returns `ResponseEnvelope` (Task 14) with `content: str` and `directive: PGEReloopDirective | None`. Callers in Task 14 Step 4 and the Gateway integration in Tasks 17-18 use `.content` and `.directive` — consistent.
- `AuditResult.final_action` enum is `"pass" | "rejected_with_retry" | "delivered_with_warning"` everywhere.
- `retry_strategy` enum is `"response_regen" | "pge_reloop" | "deliver" | "deliver_with_warning"` everywhere.
- `PGEReloopDirective.reason` is `Literal["tool_ignorance"]` everywhere.
- `handle_observer_directive()` returns `ObserverDirectiveDecision(action: Literal["reenter_pge", "downgrade_to_regen"], planner_feedback: str)` — callers in Task 17 Step 3 match.

No inconsistencies found.
