# Video Input via vLLM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let Cognithor users attach a local video file or paste a video URL in the chat and have it analyzed end-to-end by Qwen3.6-27B (or any vLLM-served VLM with video support), with adaptive frame-sampling based on duration, session-lifetime cleanup, and hard-error fail-flow (no Ollama fallback — Ollama has no vision).

**Architecture:** Single-video-per-turn payload adapter on top of the existing `VLLMBackend` from PR #137. Three new modules: `MediaUploadServer` (local HTTP file-server that vLLM fetches from via `host.docker.internal`), `VideoSamplingResolver` (ffprobe + adaptive bucket table), `VideoCleanupWorker` (in-memory session registry + filesystem mtime-based TTL). Existing `VLLMBackend.chat()` gets a new `video: dict | None` kwarg; `WorkingMemory` gets a `video_attachment: dict | None` field; Flutter paperclip becomes a `PopupMenuButton`.

**Tech Stack:** Python 3.12, Pydantic v2, pytest-asyncio, FastAPI (existing), httpx, Flutter 3.41.4, Docker Desktop + vLLM from PR #137, ffmpeg/ffprobe (LGPL build bundled on Windows, expected in `$PATH` elsewhere).

**Spec:** `docs/superpowers/specs/2026-04-23-video-input-vllm-design.md` — read it before starting. Seven decisions are locked, three Day-1 spikes are gated.

---

## ⚠ CRITICAL: Day-1 Spike Gate

**Task 1 is a dedicated spike to verify three risks before any other code is written.** If the spike finding invalidates a spec assumption (especially the `extra_body.mm_processor_kwargs.video` wire shape or the vLLM fetch-allowlist policy), STOP and return to the design table — do not continue with Tasks 2+ on top of a broken premise.

---

## File Structure

**New Python files:**
- `src/cognithor/core/video_sampling.py` — ~80 LOC — `VideoSampling` dataclass + `resolve_sampling()` + bucket rules
- `src/cognithor/channels/media_server.py` — ~120 LOC — `MediaUploadServer` (FastAPI static on 127.0.0.1:<ephemeral>)
- `src/cognithor/gateway/video_cleanup.py` — ~80 LOC — `VideoCleanupWorker` with in-memory session map + filesystem TTL sweep
- `tests/test_core/test_video_sampling.py`
- `tests/test_channels/test_media_server.py`
- `tests/test_gateway/test_video_cleanup.py`
- `tests/test_core/test_vllm_backend_video.py` — `VLLMBackend.chat(video=...)` payload shape
- `tests/test_integration/test_vllm_video_fake_server.py` — end-to-end vs. fake OpenAI server
- `flutter_app/test/widgets/chat_input_video_menu_test.dart`
- `flutter_app/test/widgets/chat_bubble_video_test.dart`
- `docs/vllm-video-spike-notes.md` — spike output, ground truth for all later tasks

**Modified Python files:**
- `src/cognithor/core/llm_backend.py` — `MediaUploadError` + 3 subclasses, added to `CircuitBreaker.excluded_exceptions` wiring in `UnifiedLLMClient`
- `src/cognithor/core/vllm_backend.py` — `chat(video=...)` kwarg, `_attach_video_to_last_user()` helper
- `src/cognithor/core/vllm_orchestrator.py` — `docker run` adds `--media-io-kwargs` + `--add-host host.docker.internal:host-gateway` + `-e COGNITHOR_MEDIA_URL`
- `src/cognithor/core/unified_llm.py` — video+DEGRADED = hard error (no Ollama fallback)
- `src/cognithor/config.py` — `VLLMConfig` gains 6 video fields
- `src/cognithor/models.py` — `WorkingMemory.video_attachment: dict | None`
- `src/cognithor/core/planner.py` — route to `vision_model_detail` when `video_attachment is not None`
- `src/cognithor/gateway/gateway.py` — extract video attachment per turn, register with cleanup worker
- `src/cognithor/channels/api.py` — `POST /api/media/upload` + `GET /api/media/thumb/<uuid>.jpg`

**Modified Flutter files:**
- `flutter_app/lib/widgets/chat_input.dart` — `IconButton` → `PopupMenuButton`
- `flutter_app/lib/widgets/chat_bubble.dart` — render video-kind metadata with thumbnail
- `flutter_app/lib/providers/chat_provider.dart` — `sendVideo()`, URL-paste detection

**Modified build/docs:**
- `installer/build_installer.py` — bundle LGPL ffmpeg under `%LOCALAPPDATA%\Cognithor\ffmpeg\`
- `.github/workflows/build-windows-installer.yml` — LGPL-vs-GPL verification step
- `docs/vllm-user-guide.md` — video section
- `docs/vllm-manual-test.md` — video smoke-test matrix
- `CHANGELOG.md` — `[Unreleased]` entry

---

## TDD Contract

Same as PR #137: each task follows write failing test → red → implement → green → commit. Ruff check + format --check on every file touched.

**Before EVERY commit** (except Task 1 which has no code):
```bash
python -m ruff check <files>
python -m ruff format --check <files>
```

---

## Task 1: Day-1 Spike — ✅ COMPLETE 2026-04-23

**Findings:** [`docs/superpowers/spikes/2026-04-23-video-input-vllm-spike-findings.md`](../spikes/2026-04-23-video-input-vllm-spike-findings.md)

**Gate:** 🟢 APPROVED — proceed to Task 2.

**Key outcomes that propagate into later tasks:**

1. **Base image must be `vllm/vllm-openai:cu130-nightly`** (not `:v0.19.1`). v0.19.1 crashes Qwen3.6-27B-NVFP4 at warmup; the fix is shipped in `cu130-nightly` only. See Task 10 for the full `docker run` line.
2. **Wire shape** `extra_body.mm_processor_kwargs.video.{fps | num_frames}` is accepted as specced. No change to Task 9.
3. **Fetch policy** — vLLM has no allowlist; any HTTPS URL works. `--allowed-media-domains` NOT needed. Task 10 keeps `--add-host host.docker.internal:host-gateway`.
4. **Fetch resilience** — some public CDNs (observed: GCS) return 403 to the container's HTTP client. Spec's local-HTTP-upload path is empirically validated as the safer common case. Task 13's user-facing fail message should include a "try uploading instead" hint when a URL fetch returns 4xx.
5. **VRAM ceiling on 32 GB GPUs** — the launcher default profile **must** use `--max-model-len 16384 --max-num-seqs 2 --max-num-batched-tokens 2048 --gpu-memory-utilization 0.94 --cpu-offload-gb 4 --enforce-eager`. Larger GPUs relax these — see Task 5 for the config fields and Task 10 for the flag generation.
6. **ffprobe HTTP timing** — not empirically measured in the spike. Task 3's unit tests + `resolve_sampling()` integration test are the new gate for the 30 s default.

No production code committed in this task.

---

## Task 2: VideoSampling Dataclass + Bucket Rules

**Files:**
- Create: `src/cognithor/core/video_sampling.py`
- Create: `tests/test_core/test_video_sampling.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_core/test_video_sampling.py
from __future__ import annotations

import pytest

from cognithor.core.video_sampling import VideoSampling, _bucket_for_duration


class TestVideoSamplingDataclass:
    def test_fps_only(self):
        s = VideoSampling(fps=2.0, duration_sec=25.0)
        assert s.fps == 2.0
        assert s.num_frames is None
        assert s.duration_sec == 25.0

    def test_num_frames_only(self):
        s = VideoSampling(num_frames=32, duration_sec=900.0)
        assert s.num_frames == 32
        assert s.fps is None

    def test_as_mm_kwargs_fps(self):
        s = VideoSampling(fps=3.0)
        assert s.as_mm_kwargs() == {"fps": 3.0}

    def test_as_mm_kwargs_num_frames(self):
        s = VideoSampling(num_frames=64)
        assert s.as_mm_kwargs() == {"num_frames": 64}

    def test_as_mm_kwargs_raises_when_neither(self):
        s = VideoSampling()  # both None
        with pytest.raises(ValueError):
            s.as_mm_kwargs()


class TestBucketForDuration:
    # Spec bucket table (see design doc § "Frame Sampling"):
    # <10s → fps=3; 10-30s → fps=2; 30s-2min → fps=1;
    # 2-5min → num_frames=64; 5-15min → num_frames=32; >15min → num_frames=32
    @pytest.mark.parametrize("dur,expected_fps,expected_num", [
        (5.0,   3.0,  None),
        (9.99,  3.0,  None),
        (10.0,  2.0,  None),
        (29.99, 2.0,  None),
        (30.0,  1.0,  None),
        (119.99, 1.0, None),
        (120.0, None, 64),
        (299.99, None, 64),
        (300.0,  None, 32),
        (899.99, None, 32),
        (900.0,  None, 32),  # >15min still 32
        (3600.0, None, 32),
    ])
    def test_buckets(self, dur: float, expected_fps: float | None, expected_num: int | None) -> None:
        s = _bucket_for_duration(dur)
        assert s.fps == expected_fps
        assert s.num_frames == expected_num

    def test_zero_or_negative_duration_falls_back(self):
        # Defensive: upstream feeds us >0 but guard anyway
        s = _bucket_for_duration(0.0)
        assert s.num_frames == 32
        assert s.fps is None
        s = _bucket_for_duration(-5.0)
        assert s.num_frames == 32
```

- [ ] **Step 2: Run — expect `ImportError`**

```bash
python -m pytest tests/test_core/test_video_sampling.py -v
```
Expected: `ModuleNotFoundError: No module named 'cognithor.core.video_sampling'`.

- [ ] **Step 3: Create `src/cognithor/core/video_sampling.py`**

```python
"""Video sampling: pick fps or num_frames for a vLLM `video_url` request.

Uses ffprobe to detect duration, then maps to the bucket table from the
spec (docs/superpowers/specs/2026-04-23-video-input-vllm-design.md).

This module is pure-logic-plus-subprocess. `_bucket_for_duration` is
pure; `resolve_sampling` (added in Task 3) is the I/O entry point.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VideoSampling:
    """Resolved per-video sampling spec.

    Exactly one of `fps` or `num_frames` is set when sampling is active.
    Both None is a default-constructed placeholder and will raise from
    `as_mm_kwargs()`.
    """

    fps: float | None = None
    num_frames: int | None = None
    duration_sec: float | None = None  # for logging/UI, not sent to vLLM

    def as_mm_kwargs(self) -> dict[str, Any]:
        """Return the dict suitable for `extra_body.mm_processor_kwargs.video`.

        Shape confirmed by Task-1 spike.
        """
        if self.fps is not None:
            return {"fps": self.fps}
        if self.num_frames is not None:
            return {"num_frames": self.num_frames}
        raise ValueError("VideoSampling has neither fps nor num_frames set")


# Bucket thresholds in seconds
_BUCKET_LT_10 = 10.0
_BUCKET_LT_30 = 30.0
_BUCKET_LT_2MIN = 120.0
_BUCKET_LT_5MIN = 300.0
_BUCKET_LT_15MIN = 900.0


def _bucket_for_duration(duration_sec: float) -> VideoSampling:
    """Map a duration in seconds to a VideoSampling per the spec's bucket table.

    Defensive default for non-positive durations: `num_frames=32` so callers
    don't have to special-case ffprobe edge-cases.
    """
    if duration_sec <= 0:
        return VideoSampling(num_frames=32, duration_sec=duration_sec)
    if duration_sec < _BUCKET_LT_10:
        return VideoSampling(fps=3.0, duration_sec=duration_sec)
    if duration_sec < _BUCKET_LT_30:
        return VideoSampling(fps=2.0, duration_sec=duration_sec)
    if duration_sec < _BUCKET_LT_2MIN:
        return VideoSampling(fps=1.0, duration_sec=duration_sec)
    if duration_sec < _BUCKET_LT_5MIN:
        return VideoSampling(num_frames=64, duration_sec=duration_sec)
    # 5 min – 15 min AND > 15 min both use num_frames=32; UI banner is
    # a display concern not a sampling one.
    return VideoSampling(num_frames=32, duration_sec=duration_sec)
```

- [ ] **Step 4: Run — expect all pass**

```bash
python -m pytest tests/test_core/test_video_sampling.py -v
```
Expected: `17 passed`.

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/core/video_sampling.py tests/test_core/test_video_sampling.py
python -m ruff format --check src/cognithor/core/video_sampling.py tests/test_core/test_video_sampling.py
git add src/cognithor/core/video_sampling.py tests/test_core/test_video_sampling.py
git commit -m "feat(video): VideoSampling dataclass + duration bucket rules"
```

---

## Task 3: `resolve_sampling()` — ffprobe Wrapper + Fallback Chain

**Files:**
- Modify: `src/cognithor/core/video_sampling.py` (add `resolve_sampling`)
- Modify: `tests/test_core/test_video_sampling.py` (add `TestResolveSampling`)

- [ ] **Step 1: Append to the test file**

```python
from unittest.mock import MagicMock, patch

from cognithor.core.video_sampling import resolve_sampling


class TestResolveSampling:
    def _mk_probe_stdout(self, duration: float) -> str:
        import json as _json
        return _json.dumps({"format": {"duration": str(duration)}})

    def test_adaptive_short_clip(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(5.0))
        with patch("subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.fps == 3.0
        assert s.num_frames is None
        assert s.duration_sec == 5.0

    def test_adaptive_long_clip(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(1800.0))
        with patch("subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32
        assert s.duration_sec == 1800.0

    def test_ffprobe_missing_falls_back_to_num_frames_32(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32
        assert s.fps is None
        assert s.duration_sec is None

    def test_ffprobe_timeout_falls_back(self):
        import subprocess as _sp
        with patch("subprocess.run", side_effect=_sp.TimeoutExpired(cmd="ffprobe", timeout=5)):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32

    def test_ffprobe_nonzero_returncode_falls_back(self):
        mock = MagicMock(returncode=1, stdout="", stderr="file not found")
        with patch("subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32

    def test_ffprobe_unparseable_json_falls_back(self):
        mock = MagicMock(returncode=0, stdout="not json at all")
        with patch("subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32

    def test_ffprobe_negative_duration_falls_back(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(-1.0))
        with patch("subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32

    def test_ffprobe_duration_over_24h_falls_back(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(100_000.0))
        with patch("subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32

    def test_override_fixed_32_skips_ffprobe(self):
        with patch("subprocess.run") as run_mock:
            s = resolve_sampling("/tmp/x.mp4", override="fixed_32")
        assert s.num_frames == 32
        assert s.fps is None
        run_mock.assert_not_called()

    def test_override_fixed_64_skips_ffprobe(self):
        with patch("subprocess.run") as run_mock:
            s = resolve_sampling("/tmp/x.mp4", override="fixed_64")
        assert s.num_frames == 64
        run_mock.assert_not_called()

    def test_override_fps_1_skips_ffprobe(self):
        with patch("subprocess.run") as run_mock:
            s = resolve_sampling("/tmp/x.mp4", override="fps_1")
        assert s.fps == 1.0
        run_mock.assert_not_called()

    def test_http_url_uses_http_timeout(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(45.0))
        with patch("subprocess.run", return_value=mock) as run_mock:
            resolve_sampling("https://example.com/clip.mp4", timeout_seconds=5, http_timeout_seconds=30)
        # Verify the timeout kwarg passed to subprocess.run is the HTTP one (30, not 5)
        assert run_mock.call_args.kwargs["timeout"] == 30

    def test_local_path_uses_local_timeout(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(45.0))
        with patch("subprocess.run", return_value=mock) as run_mock:
            resolve_sampling("/tmp/x.mp4", timeout_seconds=5, http_timeout_seconds=30)
        assert run_mock.call_args.kwargs["timeout"] == 5
```

- [ ] **Step 2: Run — expect `ImportError: cannot import name 'resolve_sampling'`**

```bash
python -m pytest tests/test_core/test_video_sampling.py::TestResolveSampling -v
```

- [ ] **Step 3: Add `resolve_sampling` to `src/cognithor/core/video_sampling.py`**

Imports to add at the top:

```python
import json as _json
import subprocess
from typing import Literal

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

_MAX_PLAUSIBLE_DURATION_SEC = 86400.0  # 24 hours; anything bigger is almost certainly garbage
```

Then add:

```python
SamplingOverride = Literal["adaptive", "fixed_32", "fixed_64", "fps_1"]


def resolve_sampling(
    source: str,
    *,
    ffprobe_path: str = "ffprobe",
    timeout_seconds: int = 5,
    http_timeout_seconds: int = 30,
    override: SamplingOverride = "adaptive",
) -> VideoSampling:
    """Resolve a video source URL or local path to a VideoSampling.

    For `override != "adaptive"`, returns a fixed sampling without touching
    ffprobe. For adaptive, runs ffprobe with the appropriate timeout
    (`timeout_seconds` for local paths, `http_timeout_seconds` for URLs) and
    falls back to `VideoSampling(num_frames=32)` on any failure.
    """
    if override == "fixed_32":
        return VideoSampling(num_frames=32)
    if override == "fixed_64":
        return VideoSampling(num_frames=64)
    if override == "fps_1":
        return VideoSampling(fps=1.0)

    is_http = source.lower().startswith(("http://", "https://"))
    timeout = http_timeout_seconds if is_http else timeout_seconds

    cmd = [
        ffprobe_path, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        source,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        log.warning("video_ffprobe_missing", recovery="fallback to num_frames=32")
        return VideoSampling(num_frames=32)
    except subprocess.TimeoutExpired:
        log.warning("video_duration_detection_timeout", source=_redact_source(source), timeout_seconds=timeout)
        return VideoSampling(num_frames=32)

    if result.returncode != 0:
        log.warning("video_ffprobe_failed", returncode=result.returncode, stderr=result.stderr.strip()[:200])
        return VideoSampling(num_frames=32)

    try:
        data = _json.loads(result.stdout)
        duration = float(data["format"]["duration"])
    except (_json.JSONDecodeError, KeyError, ValueError, TypeError):
        log.warning("video_ffprobe_unparseable", stdout=result.stdout[:200])
        return VideoSampling(num_frames=32)

    if duration <= 0 or duration > _MAX_PLAUSIBLE_DURATION_SEC:
        log.warning("video_duration_implausible", duration=duration)
        return VideoSampling(num_frames=32)

    return _bucket_for_duration(duration)


def _redact_source(source: str) -> str:
    """Strip query strings from URLs so we don't log credentials / tokens."""
    if "?" in source:
        return source.split("?", 1)[0] + "?…"
    return source
```

- [ ] **Step 4: Run — expect all pass**

```bash
python -m pytest tests/test_core/test_video_sampling.py -v
```
Expected: `30 passed` (17 from Task 2 + 13 new).

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/core/video_sampling.py tests/test_core/test_video_sampling.py
python -m ruff format --check src/cognithor/core/video_sampling.py tests/test_core/test_video_sampling.py
git add src/cognithor/core/video_sampling.py tests/test_core/test_video_sampling.py
git commit -m "feat(video): ffprobe-based resolve_sampling with adaptive + override modes"
```

---

## Task 4: MediaUploadError Hierarchy

**Files:**
- Modify: `src/cognithor/core/llm_backend.py` (add 3 error classes after `LLMBadRequestError`)
- Modify: `tests/test_core/test_llm_backend_errors.py` (add test class)

- [ ] **Step 1: Append to `tests/test_core/test_llm_backend_errors.py`**

```python
class TestMediaUploadErrors:
    def test_media_upload_error_is_llm_backend_error(self):
        from cognithor.core.llm_backend import LLMBackendError, MediaUploadError
        assert issubclass(MediaUploadError, LLMBackendError)

    def test_too_large_inherits(self):
        from cognithor.core.llm_backend import MediaUploadError, MediaUploadTooLargeError
        assert issubclass(MediaUploadTooLargeError, MediaUploadError)
        err = MediaUploadTooLargeError("file is 600 MB, max is 500 MB", status_code=413)
        assert err.status_code == 413

    def test_unsupported_format_inherits(self):
        from cognithor.core.llm_backend import MediaUploadError, MediaUploadUnsupportedFormatError
        assert issubclass(MediaUploadUnsupportedFormatError, MediaUploadError)

    def test_quota_exceeded_inherits(self):
        from cognithor.core.llm_backend import MediaUploadError, MediaUploadQuotaExceededError
        assert issubclass(MediaUploadQuotaExceededError, MediaUploadError)

    def test_all_carry_recovery_hint(self):
        from cognithor.core.llm_backend import MediaUploadTooLargeError
        err = MediaUploadTooLargeError(
            "too big",
            recovery_hint="Shorten or downscale the clip before uploading.",
        )
        assert err.recovery_hint == "Shorten or downscale the clip before uploading."
```

- [ ] **Step 2: Run — expect `ImportError: cannot import name 'MediaUploadError'`**

```bash
python -m pytest tests/test_core/test_llm_backend_errors.py::TestMediaUploadErrors -v
```

- [ ] **Step 3: Add to `src/cognithor/core/llm_backend.py`** (below the existing `LLMBadRequestError` class)

```python
class MediaUploadError(LLMBackendError):
    """Upload of a media file (video in v1) could not be accepted by the
    local media server. User-side problem, not a vLLM/backend fault —
    excluded from circuit-breaker failure counting in UnifiedLLMClient.
    """


class MediaUploadTooLargeError(MediaUploadError):
    """Upload exceeds ``config.vllm.video_max_upload_mb``."""


class MediaUploadUnsupportedFormatError(MediaUploadError):
    """File extension not in the allow-list (.mp4, .webm, .mov, .mkv, .avi)."""


class MediaUploadQuotaExceededError(MediaUploadError):
    """Would exceed ``config.vllm.video_quota_gb`` even after LRU eviction.

    This can only happen if the single upload is larger than the entire
    quota — otherwise LRU eviction always makes room. Practically means
    the user needs to raise ``video_quota_gb`` or shrink the file.
    """
```

- [ ] **Step 4: Run — expect all pass**

```bash
python -m pytest tests/test_core/test_llm_backend_errors.py -v
```
Expected: all passing (count depends on PR #137 baseline).

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/core/llm_backend.py tests/test_core/test_llm_backend_errors.py
python -m ruff format --check src/cognithor/core/llm_backend.py tests/test_core/test_llm_backend_errors.py
git add src/cognithor/core/llm_backend.py tests/test_core/test_llm_backend_errors.py
git commit -m "feat(llm): MediaUploadError hierarchy for video upload failures"
```

---

## Task 5: VLLMConfig Video Fields

**Files:**
- Modify: `src/cognithor/config.py` (extend existing `VLLMConfig`)
- Modify: `tests/config/test_vllm_config.py` (add test class)

- [ ] **Step 1: Append to the test file**

```python
class TestVLLMConfigVideoFields:
    def test_video_defaults(self):
        c = VLLMConfig()
        assert c.video_sampling_mode == "adaptive"
        assert c.video_ffprobe_path == "ffprobe"
        assert c.video_ffprobe_timeout_seconds == 5
        assert c.video_ffprobe_http_timeout_seconds == 30
        assert c.video_max_upload_mb == 500
        assert c.video_quota_gb == 5
        assert c.video_upload_ttl_hours == 24

    def test_video_sampling_mode_literal_rejects_garbage(self):
        with pytest.raises(ValidationError):
            VLLMConfig(video_sampling_mode="totally_bogus")

    def test_video_sampling_mode_accepts_all_four(self):
        for mode in ("adaptive", "fixed_32", "fixed_64", "fps_1"):
            c = VLLMConfig(video_sampling_mode=mode)
            assert c.video_sampling_mode == mode

    def test_timeout_lower_bound(self):
        with pytest.raises(ValidationError):
            VLLMConfig(video_ffprobe_timeout_seconds=0)

    def test_upload_mb_upper_bound(self):
        with pytest.raises(ValidationError):
            VLLMConfig(video_max_upload_mb=999999)


class TestVLLMConfigLauncherFields:
    """Flags that the spike identified as required for 32 GB-class GPUs.
    Defaults match the spike's working RTX 5090 profile."""

    def test_launcher_defaults_match_spike_profile(self):
        c = VLLMConfig()
        assert c.max_model_len == 16384
        assert c.max_num_seqs == 2
        assert c.max_num_batched_tokens == 2048
        assert c.gpu_memory_utilization == 0.94
        assert c.cpu_offload_gb == 4
        assert c.enforce_eager is True

    def test_gpu_util_must_be_in_open_unit_interval(self):
        with pytest.raises(ValidationError):
            VLLMConfig(gpu_memory_utilization=0.0)
        with pytest.raises(ValidationError):
            VLLMConfig(gpu_memory_utilization=1.01)

    def test_larger_gpu_profile(self):
        """User with an A100 loosens the defaults."""
        c = VLLMConfig(
            max_model_len=65536,
            max_num_seqs=8,
            gpu_memory_utilization=0.90,
            cpu_offload_gb=0,
            enforce_eager=False,
        )
        assert c.max_model_len == 65536
        assert c.cpu_offload_gb == 0
        assert c.enforce_eager is False
```

- [ ] **Step 2: Run — expect `AttributeError` on `video_sampling_mode`**

```bash
python -m pytest tests/config/test_vllm_config.py::TestVLLMConfigVideoFields -v
```

- [ ] **Step 3: Add fields to `VLLMConfig` in `src/cognithor/config.py`**

At the top of the file (or inside appropriate import block):

```python
from typing import Literal
```
(if not already imported)

Inside `VLLMConfig`, after the existing `request_timeout_seconds` field:

```python
    # Video-input (from video-input-vllm spec 2026-04-23)
    video_sampling_mode: Literal["adaptive", "fixed_32", "fixed_64", "fps_1"] = Field(default="adaptive")
    video_ffprobe_path: str = Field(default="ffprobe")
    video_ffprobe_timeout_seconds: int = Field(default=5, ge=1, le=30)
    video_ffprobe_http_timeout_seconds: int = Field(default=30, ge=5, le=120)
    video_max_upload_mb: int = Field(default=500, ge=1, le=5000)
    video_quota_gb: int = Field(default=5, ge=1, le=100)
    video_upload_ttl_hours: int = Field(default=24, ge=1, le=168)

    # Launcher flags for the vLLM `docker run` command (see Day-1 spike findings).
    # Defaults target a 32 GB-class consumer GPU (RTX 5090) — loosen on larger cards.
    max_model_len: int = Field(default=16384, ge=2048, le=1_010_000)
    max_num_seqs: int = Field(default=2, ge=1, le=256)
    max_num_batched_tokens: int = Field(default=2048, ge=512, le=131072)
    gpu_memory_utilization: float = Field(default=0.94, gt=0.0, le=1.0)
    cpu_offload_gb: int = Field(default=4, ge=0, le=128)
    enforce_eager: bool = Field(default=True)
```

**Rationale for the defaults (documented in the field descriptions / user guide):** the spike verified that a 32 GB RTX 5090 running Qwen3.6-27B-NVFP4 stabilizes at exactly these values. On A100/H100 (80 GB), users override `gpu_memory_utilization=0.90`, `cpu_offload_gb=0`, `enforce_eager=False`, `max_model_len=65536+` via the CognithorConfig cascade (config.yaml or `COGNITHOR_VLLM__*` env vars). The installer wizard (Task 21) writes the right profile based on the auto-detected VRAM bucket.

- [ ] **Step 4: Run — expect all pass**

```bash
python -m pytest tests/config/test_vllm_config.py -v
```
Expected: all previous + 5 new tests pass.

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/config.py tests/config/test_vllm_config.py
python -m ruff format --check src/cognithor/config.py tests/config/test_vllm_config.py
git add src/cognithor/config.py tests/config/test_vllm_config.py
git commit -m "feat(config): video-related fields on VLLMConfig (sampling mode, quotas, TTL)"
```

---

## Task 6: MediaUploadServer — save_upload + LRU Eviction

**Files:**
- Create: `src/cognithor/channels/media_server.py`
- Create: `tests/test_channels/test_media_server.py`

This task covers only the `save_upload` / `delete` / `public_url` / quota logic. The FastAPI HTTP app is added in Task 7.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_channels/test_media_server.py
from __future__ import annotations

from pathlib import Path

import pytest

from cognithor.channels.media_server import MediaUploadServer
from cognithor.config import CognithorConfig, VLLMConfig
from cognithor.core.llm_backend import (
    MediaUploadQuotaExceededError,
    MediaUploadTooLargeError,
    MediaUploadUnsupportedFormatError,
)


@pytest.fixture
def server(tmp_path: Path) -> MediaUploadServer:
    cfg = CognithorConfig(
        cognithor_home=tmp_path,
        vllm=VLLMConfig(
            enabled=True,
            video_max_upload_mb=10,   # small cap for fast tests
            video_quota_gb=1,
        ),
    )
    srv = MediaUploadServer(cfg)
    # Pretend we've bound to port 4711 (real start() is tested in Task 7)
    srv._port = 4711
    return srv


class TestSaveUpload:
    def test_saves_bytes_returns_uuid(self, server: MediaUploadServer):
        data = b"\x00" * 1024  # 1 KB
        uuid = server.save_upload(data, "mp4")
        assert uuid
        path = server._media_dir / f"{uuid}.mp4"
        assert path.is_file()
        assert path.read_bytes() == data

    def test_rejects_file_over_per_file_cap(self, server: MediaUploadServer):
        too_big = b"\x00" * (11 * 1024 * 1024)  # 11 MB > 10 MB cap
        with pytest.raises(MediaUploadTooLargeError):
            server.save_upload(too_big, "mp4")

    def test_rejects_unsupported_extension(self, server: MediaUploadServer):
        with pytest.raises(MediaUploadUnsupportedFormatError):
            server.save_upload(b"\x00" * 1024, "exe")

    def test_case_insensitive_extension(self, server: MediaUploadServer):
        uuid = server.save_upload(b"\x00" * 1024, "MP4")
        assert uuid  # accepts "MP4" / "Mp4"

    def test_public_url_shape(self, server: MediaUploadServer):
        uuid = server.save_upload(b"\x00" * 1024, "mp4")
        url = server.public_url(uuid, "mp4")
        assert url == f"http://host.docker.internal:4711/media/{uuid}.mp4"

    def test_lru_eviction_when_quota_exceeded(self, server: MediaUploadServer, tmp_path: Path):
        # Quota is 1 GB. Fill up with 3 files of 5 MB each (< cap, close to quota)
        # Then add a file that would push total over 1 GB if nothing is evicted.
        # The actual sizes don't need to exceed 1 GB — we monkey-patch the quota to
        # something small to exercise the eviction path deterministically.
        server._quota_bytes = 12 * 1024 * 1024  # override quota to 12 MB for this test

        # Save 3 files totaling 9 MB
        import time
        u1 = server.save_upload(b"\x00" * (3 * 1024 * 1024), "mp4")
        time.sleep(0.01)  # ensure distinct mtimes
        u2 = server.save_upload(b"\x00" * (3 * 1024 * 1024), "mp4")
        time.sleep(0.01)
        u3 = server.save_upload(b"\x00" * (3 * 1024 * 1024), "mp4")

        # Now save a 5 MB file — total would be 14 MB > 12 MB quota.
        # Expected: u1 (oldest) gets evicted.
        u4 = server.save_upload(b"\x00" * (5 * 1024 * 1024), "mp4")
        assert not (server._media_dir / f"{u1}.mp4").exists()
        assert (server._media_dir / f"{u2}.mp4").exists()
        assert (server._media_dir / f"{u4}.mp4").exists()


class TestDelete:
    def test_delete_removes_file(self, server: MediaUploadServer):
        uuid = server.save_upload(b"\x00" * 1024, "mp4")
        path = server._media_dir / f"{uuid}.mp4"
        assert path.exists()
        server.delete(uuid, "mp4")
        assert not path.exists()

    def test_delete_of_missing_is_noop(self, server: MediaUploadServer):
        server.delete("nonexistent-uuid-abc", "mp4")  # must not raise
```

- [ ] **Step 2: Run — expect `ModuleNotFoundError`**

```bash
python -m pytest tests/test_channels/test_media_server.py -v
```

- [ ] **Step 3: Create `src/cognithor/channels/media_server.py`**

```python
"""MediaUploadServer — local HTTP file-server for vLLM to fetch user uploads.

vLLM inside the Cognithor-managed Docker container reaches this server via
``http://host.docker.internal:<port>/media/<uuid>.<ext>``. The server binds
only on ``127.0.0.1``, so only processes on the host machine can reach it.

This file contains the storage + quota logic. The FastAPI app + port binding
live in companion methods `start()` / `stop()` added in Task 7.
"""

from __future__ import annotations

import uuid as _uuid
from pathlib import Path
from typing import TYPE_CHECKING

from cognithor.core.llm_backend import (
    MediaUploadQuotaExceededError,
    MediaUploadTooLargeError,
    MediaUploadUnsupportedFormatError,
)
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.config import CognithorConfig

log = get_logger(__name__)

_ALLOWED_EXTS = frozenset({"mp4", "webm", "mov", "mkv", "avi"})


class MediaUploadServer:
    """Local-loopback static file server for vLLM media fetches.

    Lifecycle: instantiate with the live CognithorConfig, call `await start()`
    to bind the ephemeral port (returns the port number), `await stop()` at
    shutdown. In between, call `save_upload(data, ext) -> uuid` to store
    bytes and `public_url(uuid, ext) -> str` to get the URL vLLM should fetch.
    """

    def __init__(self, config: "CognithorConfig") -> None:
        self._config = config
        self._media_dir = config.cognithor_home / "media" / "vllm-uploads"
        self._media_dir.mkdir(parents=True, exist_ok=True)
        self._max_per_file_bytes = config.vllm.video_max_upload_mb * 1024 * 1024
        self._quota_bytes = config.vllm.video_quota_gb * 1024 * 1024 * 1024
        self._port: int | None = None
        self._server = None  # filled by start() in Task 7

    def save_upload(self, data: bytes, ext: str) -> str:
        """Store `data` under `<uuid>.<ext>` in the media dir, return uuid.

        Raises MediaUploadTooLargeError / MediaUploadUnsupportedFormatError /
        MediaUploadQuotaExceededError on the respective failure modes. LRU-
        evicts older files if the new upload would push total size over quota.
        """
        ext_lower = ext.lower().lstrip(".")
        if ext_lower not in _ALLOWED_EXTS:
            raise MediaUploadUnsupportedFormatError(
                f"Unsupported extension: {ext!r}. Allowed: {sorted(_ALLOWED_EXTS)}",
                status_code=400,
            )
        if len(data) > self._max_per_file_bytes:
            mb = len(data) / 1024 / 1024
            cap = self._max_per_file_bytes / 1024 / 1024
            raise MediaUploadTooLargeError(
                f"Upload is {mb:.1f} MB, max per file is {cap:.0f} MB",
                status_code=413,
                recovery_hint="Shorten or downscale the clip before uploading.",
            )
        if len(data) > self._quota_bytes:
            raise MediaUploadQuotaExceededError(
                f"Upload alone ({len(data)/1024/1024:.1f} MB) exceeds the full quota"
                f" ({self._quota_bytes/1024/1024/1024:.1f} GB)",
                status_code=413,
                recovery_hint="Raise config.vllm.video_quota_gb or shrink the file.",
            )

        # LRU eviction until the new file fits
        self._evict_until_fits(len(data))

        uuid_str = _uuid.uuid4().hex
        path = self._media_dir / f"{uuid_str}.{ext_lower}"
        path.write_bytes(data)
        log.info(
            "video_upload_saved",
            uuid=uuid_str,
            ext=ext_lower,
            bytes=len(data),
        )
        return uuid_str

    def _evict_until_fits(self, incoming_bytes: int) -> None:
        """Delete oldest files (by mtime) until adding `incoming_bytes` fits under quota."""
        files = list(self._media_dir.iterdir())
        current = sum(f.stat().st_size for f in files if f.is_file())
        if current + incoming_bytes <= self._quota_bytes:
            return
        # Sort by mtime ascending (oldest first)
        files.sort(key=lambda f: f.stat().st_mtime)
        for f in files:
            if not f.is_file():
                continue
            if current + incoming_bytes <= self._quota_bytes:
                break
            size = f.stat().st_size
            try:
                f.unlink()
            except OSError as exc:
                log.warning("video_evict_failed", file=str(f), error=str(exc))
                continue
            # Also drop sidecar thumbnail if present
            thumb = f.with_suffix(".jpg")
            if thumb.exists():
                try:
                    thumb.unlink()
                except OSError:
                    pass
            current -= size
            log.info("video_evicted_lru", file=f.name, freed_bytes=size)

    def delete(self, uuid: str, ext: str) -> None:
        """Remove a specific upload (and its thumbnail). Noop if missing."""
        ext_lower = ext.lower().lstrip(".")
        path = self._media_dir / f"{uuid}.{ext_lower}"
        if path.exists():
            try:
                path.unlink()
            except OSError as exc:
                log.warning("video_delete_failed", uuid=uuid, error=str(exc))
        thumb = self._media_dir / f"{uuid}.jpg"
        if thumb.exists():
            try:
                thumb.unlink()
            except OSError:
                pass

    def public_url(self, uuid: str, ext: str) -> str:
        """Return the URL vLLM should fetch: ``http://host.docker.internal:<port>/media/<uuid>.<ext>``.

        Requires `start()` to have been called (or `_port` manually set in tests).
        """
        if self._port is None:
            raise RuntimeError("MediaUploadServer not started; call await start() first")
        ext_lower = ext.lower().lstrip(".")
        return f"http://host.docker.internal:{self._port}/media/{uuid}.{ext_lower}"

    # start() / stop() added in Task 7
```

- [ ] **Step 4: Run — expect all pass**

```bash
python -m pytest tests/test_channels/test_media_server.py -v
```

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/channels/media_server.py tests/test_channels/test_media_server.py
python -m ruff format --check src/cognithor/channels/media_server.py tests/test_channels/test_media_server.py
git add src/cognithor/channels/media_server.py tests/test_channels/test_media_server.py
git commit -m "feat(media): MediaUploadServer save_upload with quota + LRU eviction"
```

---

## Task 7: MediaUploadServer — FastAPI App + Port Binding

**Files:**
- Modify: `src/cognithor/channels/media_server.py` (add `start()` / `stop()` / the FastAPI sub-app)
- Modify: `tests/test_channels/test_media_server.py` (add `TestLifecycle`)

- [ ] **Step 1: Append test class**

```python
class TestLifecycle:
    @pytest.mark.asyncio
    async def test_start_binds_ephemeral_port_serves_media(self, tmp_path: Path):
        from cognithor.config import CognithorConfig, VLLMConfig
        import httpx

        cfg = CognithorConfig(
            cognithor_home=tmp_path,
            vllm=VLLMConfig(enabled=True, video_max_upload_mb=10, video_quota_gb=1),
        )
        srv = MediaUploadServer(cfg)
        port = await srv.start()
        try:
            assert port > 0
            uuid = srv.save_upload(b"hello video world", "mp4")
            url = f"http://127.0.0.1:{port}/media/{uuid}.mp4"
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=5.0)
            assert r.status_code == 200
            assert r.content == b"hello video world"
        finally:
            await srv.stop()

    @pytest.mark.asyncio
    async def test_start_stop_is_idempotent(self, tmp_path: Path):
        from cognithor.config import CognithorConfig, VLLMConfig
        cfg = CognithorConfig(
            cognithor_home=tmp_path,
            vllm=VLLMConfig(enabled=True),
        )
        srv = MediaUploadServer(cfg)
        port = await srv.start()
        await srv.stop()
        await srv.stop()  # second stop must not raise
        # Restart on a fresh instance
        srv2 = MediaUploadServer(cfg)
        port2 = await srv2.start()
        assert port2 > 0
        await srv2.stop()
```

- [ ] **Step 2: Run — expect `AttributeError: 'MediaUploadServer' object has no attribute 'start'`**

```bash
python -m pytest tests/test_channels/test_media_server.py::TestLifecycle -v
```

- [ ] **Step 3: Extend `src/cognithor/channels/media_server.py` with the lifecycle**

Add imports at the top (keeping existing ones):

```python
import asyncio
import socket

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
```

Add the methods inside the class, after `public_url`:

```python
    async def start(self) -> int:
        """Bind to 127.0.0.1:<ephemeral>, serve /media/<uuid>.<ext> as static files.

        Returns the bound port. Call `await stop()` at shutdown.
        """
        # Pick an ephemeral port ourselves so we can tell the orchestrator before
        # uvicorn actually binds (uvicorn accepts 0 but only reports after start).
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            self._port = probe.getsockname()[1]

        app = FastAPI(title="Cognithor MediaUploadServer", openapi_url=None, docs_url=None)

        @app.get("/media/{filename}")
        async def serve(filename: str) -> FileResponse:
            # Very strict: no paths, only flat <uuid>.<ext> names
            if "/" in filename or ".." in filename:
                raise HTTPException(status_code=400, detail="invalid filename")
            path = self._media_dir / filename
            if not path.is_file():
                raise HTTPException(status_code=404, detail="not found")
            return FileResponse(path)

        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=self._port,
            log_level="warning",
            access_log=False,
        )
        self._server = uvicorn.Server(config)
        self._serve_task = asyncio.create_task(self._server.serve())
        # Wait for startup (server.started flips true when uvicorn is ready)
        for _ in range(50):
            if self._server.started:
                break
            await asyncio.sleep(0.05)
        log.info("media_server_started", port=self._port)
        return self._port

    async def stop(self) -> None:
        """Shut down the uvicorn serving loop. Idempotent."""
        if self._server is None:
            return
        self._server.should_exit = True
        try:
            await self._serve_task
        except Exception as exc:
            log.warning("media_server_stop_error", error=str(exc))
        self._server = None
        self._serve_task = None
        log.info("media_server_stopped")
```

Also add `_server` and `_serve_task` to the init defaults alongside `_server = None`:

```python
        self._serve_task: asyncio.Task | None = None
```

- [ ] **Step 4: Run — expect `2 passed`**

```bash
python -m pytest tests/test_channels/test_media_server.py::TestLifecycle -v
```

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/channels/media_server.py tests/test_channels/test_media_server.py
python -m ruff format --check src/cognithor/channels/media_server.py tests/test_channels/test_media_server.py
git add src/cognithor/channels/media_server.py tests/test_channels/test_media_server.py
git commit -m "feat(media): MediaUploadServer FastAPI app + ephemeral-port lifecycle"
```

---

## Task 8: VideoCleanupWorker — Session Registry + TTL Sweep

**Files:**
- Create: `src/cognithor/gateway/video_cleanup.py`
- Create: `tests/test_gateway/test_video_cleanup.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gateway/test_video_cleanup.py
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

import pytest

from cognithor.gateway.video_cleanup import VideoCleanupWorker


def _touch(path: Path, size: int = 64, mtime_age_sec: float = 0.0) -> None:
    """Create a file with optional artificially-old mtime."""
    path.write_bytes(b"x" * size)
    if mtime_age_sec > 0:
        t = time.time() - mtime_age_sec
        os.utime(path, (t, t))


class TestRegisterAndSessionClose:
    @pytest.mark.asyncio
    async def test_register_upload_is_tracked_by_session(self, tmp_path: Path):
        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        worker.register_upload("abc123", "session-1")
        worker.register_upload("def456", "session-1")
        worker.register_upload("ghi789", "session-2")
        assert set(worker._by_session["session-1"]) == {"abc123", "def456"}
        assert worker._by_session["session-2"] == ["ghi789"]

    @pytest.mark.asyncio
    async def test_on_session_close_deletes_only_that_sessions_files(self, tmp_path: Path):
        _touch(tmp_path / "abc123.mp4")
        _touch(tmp_path / "abc123.jpg")  # thumbnail sidecar
        _touch(tmp_path / "def456.mp4")
        _touch(tmp_path / "ghi789.mp4")

        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        worker.register_upload("abc123", "session-1")
        worker.register_upload("def456", "session-1")
        worker.register_upload("ghi789", "session-2")

        await worker.on_session_close("session-1")

        assert not (tmp_path / "abc123.mp4").exists()
        assert not (tmp_path / "abc123.jpg").exists()
        assert not (tmp_path / "def456.mp4").exists()
        assert (tmp_path / "ghi789.mp4").exists()
        assert "session-1" not in worker._by_session

    @pytest.mark.asyncio
    async def test_on_session_close_for_unknown_session_is_noop(self, tmp_path: Path):
        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        await worker.on_session_close("ghost-session")


class TestTTLSweep:
    @pytest.mark.asyncio
    async def test_sweep_deletes_files_older_than_ttl(self, tmp_path: Path):
        old = tmp_path / "old-uuid.mp4"
        fresh = tmp_path / "fresh-uuid.mp4"
        _touch(old, mtime_age_sec=25 * 3600)      # 25 h old
        _touch(fresh, mtime_age_sec=1 * 3600)     # 1 h old

        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        await worker._sweep_once()

        assert not old.exists()
        assert fresh.exists()

    @pytest.mark.asyncio
    async def test_sweep_deletes_thumbnails_too(self, tmp_path: Path):
        old_video = tmp_path / "old.mp4"
        old_thumb = tmp_path / "old.jpg"
        _touch(old_video, mtime_age_sec=25 * 3600)
        _touch(old_thumb, mtime_age_sec=25 * 3600)

        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        await worker._sweep_once()

        assert not old_video.exists()
        assert not old_thumb.exists()

    @pytest.mark.asyncio
    async def test_sweep_ignores_missing_dir(self, tmp_path: Path):
        missing = tmp_path / "does-not-exist"
        worker = VideoCleanupWorker(media_dir=missing, ttl_hours=24)
        # Must not raise
        await worker._sweep_once()


class TestStartStop:
    @pytest.mark.asyncio
    async def test_start_runs_initial_sweep(self, tmp_path: Path):
        old = tmp_path / "old.mp4"
        _touch(old, mtime_age_sec=25 * 3600)

        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24, sweep_interval_sec=0.05)
        await worker.start()
        await asyncio.sleep(0.02)  # give the initial sweep a moment
        await worker.stop()

        assert not old.exists()

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(self, tmp_path: Path):
        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        await worker.start()
        await worker.stop()
        await worker.stop()  # second stop must not raise
```

- [ ] **Step 2: Run — expect `ModuleNotFoundError`**

```bash
python -m pytest tests/test_gateway/test_video_cleanup.py -v
```

- [ ] **Step 3: Create `src/cognithor/gateway/video_cleanup.py`**

```python
"""VideoCleanupWorker — deletes uploaded videos on session close + TTL expiry.

No persistent state — the 24 h filesystem-mtime-based TTL sweep is authoritative.
Session tracking is an optimization: users who close a session before the TTL
window get their videos deleted sooner. If Cognithor crashes mid-session and
never fires `on_session_close`, the TTL sweep picks up the orphans on the next
run or within the hour.

See spec: docs/superpowers/specs/2026-04-23-video-input-vllm-design.md
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


class VideoCleanupWorker:
    """Manages per-session cleanup and a periodic TTL sweep."""

    def __init__(
        self,
        media_dir: Path,
        *,
        ttl_hours: int = 24,
        sweep_interval_sec: float = 60.0,
    ) -> None:
        self._media_dir = media_dir
        self._ttl_hours = ttl_hours
        self._sweep_interval = sweep_interval_sec
        self._by_session: dict[str, list[str]] = {}
        self._sweep_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """Run TTL sweep once at start, then kick off the periodic sweep loop."""
        await self._sweep_once()
        self._stop_event.clear()
        self._sweep_task = asyncio.create_task(self._run_periodic())
        log.info("video_cleanup_started", media_dir=str(self._media_dir), ttl_hours=self._ttl_hours)

    async def stop(self) -> None:
        """Cancel the periodic sweep. Idempotent."""
        if self._sweep_task is None:
            return
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._sweep_task, timeout=2.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            self._sweep_task.cancel()
        self._sweep_task = None
        log.info("video_cleanup_stopped")

    def register_upload(self, uuid: str, session_id: str) -> None:
        """Track this upload so it's deleted when the session closes."""
        self._by_session.setdefault(session_id, []).append(uuid)

    async def on_session_close(self, session_id: str) -> None:
        """Delete all uploads (and thumbnails) registered under this session."""
        uuids = self._by_session.pop(session_id, [])
        for uuid in uuids:
            self._delete_upload(uuid)

    def _delete_upload(self, uuid: str) -> None:
        """Remove any file starting with ``<uuid>.`` in the media dir."""
        if not self._media_dir.is_dir():
            return
        for path in self._media_dir.glob(f"{uuid}.*"):
            try:
                path.unlink()
            except OSError as exc:
                log.warning("video_cleanup_delete_failed", uuid=uuid, path=str(path), error=str(exc))

    async def _run_periodic(self) -> None:
        """Loop: wait `_sweep_interval` seconds, sweep, repeat until stopped."""
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._sweep_interval)
                return  # stop signal arrived
            except asyncio.TimeoutError:
                pass
            await self._sweep_once()

    async def _sweep_once(self) -> None:
        """Delete every file in `media_dir` whose mtime is older than ttl_hours."""
        if not self._media_dir.is_dir():
            return
        cutoff = time.time() - self._ttl_hours * 3600
        deleted = 0
        for path in self._media_dir.iterdir():
            if not path.is_file():
                continue
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    deleted += 1
            except OSError as exc:
                log.warning("video_ttl_sweep_failed", path=str(path), error=str(exc))
        if deleted:
            log.info("video_ttl_sweep_completed", deleted=deleted)
```

- [ ] **Step 4: Run — expect all pass**

```bash
python -m pytest tests/test_gateway/test_video_cleanup.py -v
```

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/gateway/video_cleanup.py tests/test_gateway/test_video_cleanup.py
python -m ruff format --check src/cognithor/gateway/video_cleanup.py tests/test_gateway/test_video_cleanup.py
git add src/cognithor/gateway/video_cleanup.py tests/test_gateway/test_video_cleanup.py
git commit -m "feat(video): VideoCleanupWorker with session registry + mtime TTL sweep"
```

---

## Task 9: VLLMBackend.chat(video=...) — Payload Adapter

**Files:**
- Modify: `src/cognithor/core/vllm_backend.py` (add `_attach_video_to_last_user` helper + `video` kwarg)
- Create: `tests/test_core/test_vllm_backend_video.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_core/test_vllm_backend_video.py
from __future__ import annotations

import json as _json

import pytest
from pytest_httpx import HTTPXMock

from cognithor.core.vllm_backend import VLLMBackend, _attach_video_to_last_user


BASE_URL = "http://localhost:8000/v1"


@pytest.fixture
def backend() -> VLLMBackend:
    return VLLMBackend(base_url=BASE_URL, timeout=5)


class TestAttachVideoHelper:
    def test_prepends_video_url_content_item_to_last_user(self):
        messages = [
            {"role": "system", "content": "you are helpful"},
            {"role": "user", "content": "What is in this?"},
        ]
        video = {"url": "http://x/a.mp4", "sampling": {"fps": 2.0}}
        new_messages, mm_kwargs = _attach_video_to_last_user(messages, video)

        # System message untouched
        assert new_messages[0] == messages[0]
        # Last user message converted to content-item list
        last = new_messages[-1]
        assert last["role"] == "user"
        assert isinstance(last["content"], list)
        assert last["content"][0] == {"type": "video_url", "video_url": {"url": "http://x/a.mp4"}}
        assert last["content"][1] == {"type": "text", "text": "What is in this?"}
        # mm kwargs shape
        assert mm_kwargs == {"mm_processor_kwargs": {"video": {"fps": 2.0}}}

    def test_num_frames_sampling(self):
        video = {"url": "http://x/a.mp4", "sampling": {"num_frames": 32}}
        _, mm_kwargs = _attach_video_to_last_user(
            [{"role": "user", "content": "hi"}], video
        )
        assert mm_kwargs == {"mm_processor_kwargs": {"video": {"num_frames": 32}}}

    def test_empty_text_part_not_added(self):
        """If the user message content is already an empty string, don't
        inject a zero-length text part (spec Open Question: vLLM might or
        might not accept this — simplest: keep text absent)."""
        messages = [{"role": "user", "content": ""}]
        video = {"url": "http://x/a.mp4", "sampling": {"fps": 1.0}}
        new_messages, _ = _attach_video_to_last_user(messages, video)
        content_items = new_messages[-1]["content"]
        assert len(content_items) == 1  # only the video, no text
        assert content_items[0]["type"] == "video_url"

    def test_caller_messages_not_mutated(self):
        messages = [{"role": "user", "content": "orig"}]
        video = {"url": "http://x/a.mp4", "sampling": {"fps": 1.0}}
        _attach_video_to_last_user(messages, video)
        assert messages[0]["content"] == "orig"
        assert isinstance(messages[0]["content"], str)


class TestChatWithVideo:
    @pytest.mark.asyncio
    async def test_chat_with_video_sends_video_url_and_mm_kwargs(
        self, backend: VLLMBackend, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions",
            status_code=200,
            json={
                "choices": [{"message": {"content": "A drone flying over a field."}}],
                "model": "mmangkad/Qwen3.6-27B-NVFP4",
                "usage": {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110},
            },
        )
        resp = await backend.chat(
            model="mmangkad/Qwen3.6-27B-NVFP4",
            messages=[{"role": "user", "content": "What's in this clip?"}],
            video={"url": "http://host.docker.internal:4711/media/abc.mp4", "sampling": {"fps": 2.0}},
        )
        assert resp.content == "A drone flying over a field."

        request = httpx_mock.get_requests()[0]
        body = _json.loads(request.content)

        # The video_url content item landed in the last user message
        last_msg = body["messages"][-1]
        assert last_msg["role"] == "user"
        assert isinstance(last_msg["content"], list)
        assert any(
            c.get("type") == "video_url"
            and c["video_url"]["url"] == "http://host.docker.internal:4711/media/abc.mp4"
            for c in last_msg["content"]
        )

        # extra_body.mm_processor_kwargs.video is present
        assert body["extra_body"]["mm_processor_kwargs"]["video"] == {"fps": 2.0}

    @pytest.mark.asyncio
    async def test_chat_without_video_does_not_set_extra_body(
        self, backend: VLLMBackend, httpx_mock: HTTPXMock
    ):
        """Regression: image-only or text-only requests must not grow an
        extra_body.mm_processor_kwargs key they don't need."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions",
            status_code=200,
            json={"choices": [{"message": {"content": "ok"}}], "model": "x"},
        )
        await backend.chat(
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            messages=[{"role": "user", "content": "hi"}],
        )
        body = _json.loads(httpx_mock.get_requests()[0].content)
        assert "extra_body" not in body or "mm_processor_kwargs" not in body.get("extra_body", {})
```

- [ ] **Step 2: Run — expect various failures**

```bash
python -m pytest tests/test_core/test_vllm_backend_video.py -v
```

- [ ] **Step 3: Add the helper to `src/cognithor/core/vllm_backend.py`**

Near the top of the file, next to `_attach_images_to_last_user`:

```python
def _attach_video_to_last_user(
    messages: list[dict[str, Any]],
    video: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Attach a single video to the last user message and build the
    mm_processor_kwargs payload for vLLM's extra_body.

    Args:
        messages: Ollama-shaped chat messages. Not mutated.
        video: {"url": str, "sampling": {"fps": float} | {"num_frames": int}}

    Returns:
        (new_messages, extra_body_update) where
        - new_messages: a fresh list with the last user message's content
          replaced by a list of content items: [video_url, (optional) text]
        - extra_body_update: {"mm_processor_kwargs": {"video": <sampling>}}
          ready to merge into the outgoing chat-completion body.
    """
    new_messages = [dict(m) for m in messages]

    # Find last user message (create one if none exists)
    for i in range(len(new_messages) - 1, -1, -1):
        if new_messages[i].get("role") == "user":
            last = new_messages[i]
            break
    else:
        last = {"role": "user", "content": ""}
        new_messages.append(last)

    existing = last.get("content", "")
    text_part = existing if isinstance(existing, str) else ""
    content_items: list[dict[str, Any]] = [
        {"type": "video_url", "video_url": {"url": video["url"]}},
    ]
    if text_part:
        content_items.append({"type": "text", "text": text_part})

    last["content"] = content_items
    # Put the modified copy back (we're iterating new_messages but `last` is a ref into it)

    extra_body = {"mm_processor_kwargs": {"video": video["sampling"]}}
    return new_messages, extra_body
```

Extend `chat()` to accept `video` and merge the `extra_body`:

```python
async def chat(
    self,
    model: str,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.7,
    top_p: float = 0.9,
    format_json: bool = False,
    images: list[str] | None = None,
    video: dict[str, Any] | None = None,
) -> ChatResponse:
    """... existing docstring, add: `video` is a dict {url, sampling} per the
    video-input spec (2026-04-23). Exactly zero or one video per turn."""
    if images:
        messages = _attach_images_to_last_user(messages, images)

    extra_body: dict[str, Any] = {}
    if video is not None:
        messages, video_extra = _attach_video_to_last_user(messages, video)
        extra_body.update(video_extra)

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
    }
    if tools:
        payload["tools"] = tools
    if format_json:
        payload["response_format"] = {"type": "json_object"}
    if extra_body:
        payload["extra_body"] = extra_body

    # ... rest of existing chat() body (HTTP POST + error handling) ...
```

(Preserve the existing HTTP post and error-handling tail — just thread `extra_body` into the payload.)

- [ ] **Step 4: Run — expect all pass**

```bash
python -m pytest tests/test_core/test_vllm_backend_video.py -v
```

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/core/vllm_backend.py tests/test_core/test_vllm_backend_video.py
python -m ruff format --check src/cognithor/core/vllm_backend.py tests/test_core/test_vllm_backend_video.py
git add src/cognithor/core/vllm_backend.py tests/test_core/test_vllm_backend_video.py
git commit -m "feat(vllm): VLLMBackend.chat(video=...) with mm_processor_kwargs shape"
```

**Note:** the exact `extra_body.mm_processor_kwargs.video` shape here matches the spec's assumption. If Task 1 spike revealed a different shape, adjust `_attach_video_to_last_user`'s return accordingly AND re-run the tests.

---

## Task 10: VLLMOrchestrator — docker run Flags for Video

**Files:**
- Modify: `src/cognithor/core/vllm_orchestrator.py` (extend `start_container()` with all spike-required flags)
- Modify: `tests/test_core/test_vllm_orchestrator.py` (add `TestStartContainerVideoFlags`)

Per the Day-1 spike findings, the `docker run` command must now include the full set of flags that made Qwen3.6-27B-NVFP4 stable on RTX 5090 (32 GB). The image default changes from `v0.19.1` to `cu130-nightly` and the config fields from Task 5 feed most of the values.

- [ ] **Step 1: Append test class**

```python
class TestStartContainerVideoFlags:
    def _run_start(self, **orch_kwargs):
        from unittest.mock import MagicMock, patch
        from cognithor.core.vllm_orchestrator import VLLMOrchestrator
        with patch.object(VLLMOrchestrator, "_port_available", return_value=True), \
             patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="cid")) as run_mock, \
             patch.object(VLLMOrchestrator, "_wait_for_health", return_value=True):
            orch = VLLMOrchestrator(**orch_kwargs)
            orch.start_container("mmangkad/Qwen3.6-27B-NVFP4")
        return run_mock.call_args[0][0]

    def test_default_image_is_cu130_nightly(self):
        args = self._run_start(port=8000)
        assert "vllm/vllm-openai:cu130-nightly" in args

    def test_docker_run_includes_media_io_kwargs(self):
        args = self._run_start(port=8000)
        idx = args.index("--media-io-kwargs")
        assert '"video"' in args[idx + 1]
        assert '"num_frames": -1' in args[idx + 1]

    def test_docker_run_includes_add_host(self):
        args = self._run_start(port=8000)
        assert "--add-host" in args
        idx = args.index("--add-host")
        assert args[idx + 1] == "host.docker.internal:host-gateway"

    def test_docker_run_includes_spike_stability_flags(self):
        args = self._run_start(port=8000)
        assert "--max-model-len" in args and args[args.index("--max-model-len") + 1] == "16384"
        assert "--max-num-seqs" in args and args[args.index("--max-num-seqs") + 1] == "2"
        assert "--max-num-batched-tokens" in args and args[args.index("--max-num-batched-tokens") + 1] == "2048"
        assert "--gpu-memory-utilization" in args and args[args.index("--gpu-memory-utilization") + 1] == "0.94"
        assert "--cpu-offload-gb" in args and args[args.index("--cpu-offload-gb") + 1] == "4"
        assert "--enforce-eager" in args
        assert "--reasoning-parser" in args and args[args.index("--reasoning-parser") + 1] == "qwen3"
        assert "--trust-remote-code" in args

    def test_docker_run_includes_media_url_env_when_port_given(self):
        from unittest.mock import MagicMock, patch
        from cognithor.core.vllm_orchestrator import VLLMOrchestrator
        with patch.object(VLLMOrchestrator, "_port_available", return_value=True), \
             patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="cid")) as run_mock, \
             patch.object(VLLMOrchestrator, "_wait_for_health", return_value=True):
            orch = VLLMOrchestrator(port=8000)
            orch.media_url = "http://host.docker.internal:4711"
            orch.start_container("mmangkad/Qwen3.6-27B-NVFP4")
        args = run_mock.call_args[0][0]
        assert any("COGNITHOR_MEDIA_URL=http://host.docker.internal:4711" in a for a in args)

    def test_overrides_from_vllm_config(self):
        """A 40 GB-class GPU loosens the defaults — orchestrator reads from VLLMConfig."""
        from cognithor.config import VLLMConfig
        cfg = VLLMConfig(
            max_model_len=65536,
            max_num_seqs=8,
            max_num_batched_tokens=8192,
            gpu_memory_utilization=0.90,
            cpu_offload_gb=0,
            enforce_eager=False,
        )
        args = self._run_start(port=8000, config=cfg)
        assert args[args.index("--max-model-len") + 1] == "65536"
        assert args[args.index("--gpu-memory-utilization") + 1] == "0.9"
        # --cpu-offload-gb must be OMITTED when 0 (vLLM complains if 0 is passed)
        assert "--cpu-offload-gb" not in args
        # --enforce-eager must be OMITTED when disabled
        assert "--enforce-eager" not in args
```

- [ ] **Step 2: Run — expect failures**

```bash
python -m pytest tests/test_core/test_vllm_orchestrator.py::TestStartContainerVideoFlags -v
```

- [ ] **Step 3: Extend `VLLMOrchestrator.start_container()` in `src/cognithor/core/vllm_orchestrator.py`**

Update the `__init__` default image to `vllm/vllm-openai:cu130-nightly`. Add `self.media_url: str | None = None`. Accept a `config: VLLMConfig | None = None` parameter with the defaults carried from the config (see Task 5). Build the command:

```python
def start_container(self, model: str, *, health_timeout: int | None = None) -> ContainerInfo:
    # ... existing port-resolve logic ...

    cfg = self._config  # VLLMConfig, see Task 5
    cmd = [
        "docker", "run", "-d",
        "--gpus", "all",
        "--add-host", "host.docker.internal:host-gateway",
        "-v", "cognithor-hf-cache:/root/.cache/huggingface",
        "-e", f"HF_TOKEN={self._hf_token}",
        "-p", f"{port}:8000",
        "--label", "cognithor.managed=true",
    ]
    if self.media_url:
        cmd.extend(["-e", f"COGNITHOR_MEDIA_URL={self.media_url}"])
    cmd.extend([
        self.docker_image,  # defaults to "vllm/vllm-openai:cu130-nightly"
        "--model", model,
        "--max-model-len", str(cfg.max_model_len),
        "--max-num-seqs", str(cfg.max_num_seqs),
        "--max-num-batched-tokens", str(cfg.max_num_batched_tokens),
        "--gpu-memory-utilization", f"{cfg.gpu_memory_utilization:g}",
        "--reasoning-parser", "qwen3",
        "--trust-remote-code",
        "--media-io-kwargs", '{"video": {"num_frames": -1}}',
    ])
    if cfg.cpu_offload_gb > 0:
        cmd.extend(["--cpu-offload-gb", str(cfg.cpu_offload_gb)])
    if cfg.enforce_eager:
        cmd.append("--enforce-eager")
    # ... rest of existing body (subprocess.run + health wait) ...
```

- [ ] **Step 4: Run — expect all pass + all existing orchestrator tests still green**

```bash
python -m pytest tests/test_core/test_vllm_orchestrator.py -v
```

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/core/vllm_orchestrator.py tests/test_core/test_vllm_orchestrator.py
python -m ruff format --check src/cognithor/core/vllm_orchestrator.py tests/test_core/test_vllm_orchestrator.py
git add src/cognithor/core/vllm_orchestrator.py tests/test_core/test_vllm_orchestrator.py
git commit -m "feat(vllm): orchestrator switches to cu130-nightly + spike stability flags"
```

---

## Task 11: WorkingMemory.video_attachment Field

**Files:**
- Modify: `src/cognithor/models.py` (add `video_attachment: dict | None = None` field to `WorkingMemory`)
- Modify: appropriate existing test file for `WorkingMemory` (usually `tests/test_models/test_working_memory.py`)

- [ ] **Step 1: Write the failing test**

```python
# Append to whatever test file already tests WorkingMemory — find with:
# grep -l "class.*WorkingMemory\|from cognithor.models import WorkingMemory" tests/

def test_working_memory_has_video_attachment_default_none(self):
    from cognithor.models import WorkingMemory
    wm = WorkingMemory(session_id="s1")
    assert wm.video_attachment is None

def test_working_memory_video_attachment_accepts_dict(self):
    from cognithor.models import WorkingMemory
    wm = WorkingMemory(session_id="s1")
    wm.video_attachment = {"url": "http://x/a.mp4", "sampling": {"fps": 2.0}}
    assert wm.video_attachment["url"] == "http://x/a.mp4"

def test_working_memory_clear_for_new_request_resets_video(self):
    from cognithor.models import WorkingMemory
    wm = WorkingMemory(session_id="s1")
    wm.video_attachment = {"url": "http://x/a.mp4", "sampling": {"fps": 1.0}}
    wm.clear_for_new_request()
    assert wm.video_attachment is None
```

- [ ] **Step 2: Run — expect `AttributeError: 'WorkingMemory' object has no attribute 'video_attachment'`**

- [ ] **Step 3: Add the field and clear-on-new-request logic**

In `src/cognithor/models.py`, find the `WorkingMemory` class. Add the field (near `image_attachments`):

```python
    video_attachment: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Per-turn video attachment: {'url': str, 'sampling': {'fps': float} | {'num_frames': int}}. "
            "At most one video per chat turn (see video-input spec 2026-04-23)."
        ),
    )
```

In `clear_for_new_request()`, add:

```python
        self.video_attachment = None
```

- [ ] **Step 4: Run — expect all pass**

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/models.py tests/test_models/test_working_memory.py
python -m ruff format --check src/cognithor/models.py tests/test_models/test_working_memory.py
git add src/cognithor/models.py tests/test_models/test_working_memory.py
git commit -m "feat(models): WorkingMemory.video_attachment per-turn field"
```

---

## Task 12: Planner — Route to vision_model_detail on Video

**Files:**
- Modify: `src/cognithor/core/planner.py` (`formulate_response`: route to `vision_model_detail` when video is present)
- Modify: `tests/test_core/test_planner_envelope.py` (add test to existing `TestVisionRouting` class or similar)

- [ ] **Step 1: Write the failing test**

Find the existing vision-routing test class in `tests/test_core/test_planner_envelope.py` (added in PR #132 for image-attachments). Append:

```python
async def test_video_attachment_also_routes_to_vision_model(
    self, planner_with_mocks
):
    from cognithor.models import WorkingMemory
    planner_with_mocks._config.vision_model_detail = "mmangkad/Qwen3.6-27B-NVFP4"
    wm = WorkingMemory(session_id="s1")
    wm.video_attachment = {
        "url": "http://host.docker.internal:4711/media/abc.mp4",
        "sampling": {"fps": 1.0},
    }

    await planner_with_mocks.formulate_response(
        user_message="Describe the video",
        results=[],
        working_memory=wm,
    )

    call = planner_with_mocks._ollama.chat.call_args
    assert call.kwargs.get("model") == "mmangkad/Qwen3.6-27B-NVFP4"
    assert call.kwargs.get("video") is not None
    assert call.kwargs["video"]["url"].endswith("abc.mp4")
```

- [ ] **Step 2: Run — expect failure (video kwarg not passed through)**

- [ ] **Step 3: Modify `Planner.formulate_response()` in `src/cognithor/core/planner.py`**

Find the block that already handles image routing:

```python
        image_paths = list(working_memory.image_attachments or [])
        if image_paths and getattr(self._config, "vision_model_detail", None):
            model = self._config.vision_model_detail
        else:
            model = self._router.select_model("summarization", "medium")
```

Change to:

```python
        image_paths = list(working_memory.image_attachments or [])
        video_attach = working_memory.video_attachment
        if (image_paths or video_attach is not None) and getattr(self._config, "vision_model_detail", None):
            model = self._config.vision_model_detail
        else:
            model = self._router.select_model("summarization", "medium")
```

Further down, when calling `_generate_draft_with_retry`, pass `video`:

```python
        response = await self._generate_draft_with_retry(
            model=model,
            messages=messages,
            options=options,
            images=image_paths or None,
            video=video_attach,  # NEW
        )
```

Update `_generate_draft_with_retry` signature to accept `video: dict | None = None` and forward to `self._ollama.chat(..., video=video)`.

- [ ] **Step 4: Run — expect all pass**

```bash
python -m pytest tests/test_core/test_planner_envelope.py -v
```

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/core/planner.py tests/test_core/test_planner_envelope.py
python -m ruff format --check src/cognithor/core/planner.py tests/test_core/test_planner_envelope.py
git add src/cognithor/core/planner.py tests/test_core/test_planner_envelope.py
git commit -m "feat(planner): route to vision_model_detail on video_attachment + pass video kwarg"
```

---

## Task 13: UnifiedLLMClient — Hard-Error on Video + DEGRADED vLLM

**Files:**
- Modify: `src/cognithor/core/unified_llm.py` (extend `chat()` hard-error branch to also cover video)
- Modify: `tests/test_core/test_unified_llm_circuit_breaker.py`

From PR #137, `UnifiedLLMClient.chat()` already hard-errors for image requests when vLLM is DEGRADED. Extend that to also hard-error when `video` is passed.

- [ ] **Step 1: Append to the existing `TestFailFlowDispatch` class**

```python
    @pytest.mark.asyncio
    async def test_video_request_hard_errors_when_vllm_degraded(
        self, mock_vllm_backend, mock_ollama_client
    ):
        mock_vllm_backend.chat.side_effect = VLLMNotReadyError("down")
        client = UnifiedLLMClient(
            ollama_client=mock_ollama_client,
            backend=mock_vllm_backend,
            _breaker_recovery_timeout=60.0,
        )
        # Trip the breaker
        for _ in range(3):
            try:
                await client.chat(model="x", messages=[{"role": "user", "content": "hi"}])
            except Exception:
                pass

        # Now a video request — no silent fallback
        with pytest.raises(VLLMNotReadyError):
            await client.chat(
                model="x",
                messages=[{"role": "user", "content": "what is this?"}],
                video={"url": "http://x/a.mp4", "sampling": {"fps": 1.0}},
            )
```

- [ ] **Step 2: Run — expect failure (video not handled)**

- [ ] **Step 3: Modify `UnifiedLLMClient.chat()` in `src/cognithor/core/unified_llm.py`**

Find the existing `chat()` method that already branches on `is_image_request`. Add a `is_video_request` sibling:

```python
async def chat(self, *args, images=None, video=None, **kwargs):
    is_image_request = bool(images)
    is_video_request = video is not None
    # "vision request" = anything that the fallback path can't do
    is_vision_request = is_image_request or is_video_request

    breaker = self._breaker_for(self._backend_type)
    try:
        if self._backend is not None:
            # Forward images and video to the backend
            backend_kwargs = dict(kwargs)
            if images is not None:
                backend_kwargs["images"] = images
            if video is not None:
                backend_kwargs["video"] = video
            result = await breaker.call(self._backend.chat(*args, **backend_kwargs))
        else:
            result = await breaker.call(self._ollama.chat(*args, **kwargs))
        self._refresh_status()
        return result
    except (VLLMNotReadyError, CircuitBreakerOpen) as exc:
        self._refresh_status()
        if is_vision_request:
            # No fallback — Ollama can't do images or video
            if isinstance(exc, CircuitBreakerOpen):
                raise VLLMNotReadyError(
                    "vLLM offline — vision/video request cannot be processed",
                    recovery_hint="Start vLLM from LLM Backends settings.",
                ) from exc
            raise
        if self._backend_type == "vllm" and self._ollama is not None:
            log.warning("vllm_fallback_to_ollama")
            return await self._ollama.chat(*args, **kwargs)
        raise
```

(Preserve whatever response-normalization logic the current method has — only the input-peeling + vision-request branch changes.)

- [ ] **Step 4: Run — expect all CB tests pass including the new one**

```bash
python -m pytest tests/test_core/test_unified_llm_circuit_breaker.py -v
```

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/core/unified_llm.py tests/test_core/test_unified_llm_circuit_breaker.py
python -m ruff format --check src/cognithor/core/unified_llm.py tests/test_core/test_unified_llm_circuit_breaker.py
git add src/cognithor/core/unified_llm.py tests/test_core/test_unified_llm_circuit_breaker.py
git commit -m "feat(unified-llm): hard-error on video request when vLLM is DEGRADED"
```

---

## Task 14: FastAPI /api/media/upload Endpoint

**Files:**
- Modify: `src/cognithor/channels/api.py` (add `/api/media/upload` handler) — or add to a new `media_api.py` router if the file is already large
- Create: `tests/test_channels/test_media_api.py`

The upload endpoint runs ffprobe + (best-effort) ffmpeg thumbnail and returns the shape the Flutter client expects.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_channels/test_media_api.py
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cognithor.channels.media_api import build_media_app  # new helper, added in this task
from cognithor.channels.media_server import MediaUploadServer
from cognithor.config import CognithorConfig, VLLMConfig


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    cfg = CognithorConfig(
        cognithor_home=tmp_path,
        vllm=VLLMConfig(enabled=True, video_max_upload_mb=10, video_quota_gb=1),
    )
    media_server = MediaUploadServer(cfg)
    media_server._port = 4711  # not running, but public_url needs a port
    app = build_media_app(config=cfg, media_server=media_server)
    return TestClient(app)


class TestUploadEndpoint:
    def test_upload_valid_video_returns_metadata(self, client: TestClient):
        from cognithor.core.video_sampling import VideoSampling

        with patch(
            "cognithor.channels.media_api.resolve_sampling",
            return_value=VideoSampling(fps=1.0, duration_sec=93.5),
        ), patch(
            "cognithor.channels.media_api._extract_thumbnail",  # sync ffmpeg wrapper
            return_value=True,
        ):
            r = client.post(
                "/api/media/upload",
                files={"file": ("drone.mp4", b"\x00" * 2048, "video/mp4")},
            )
        assert r.status_code == 200
        data = r.json()
        assert "uuid" in data
        assert data["url"].startswith("http://host.docker.internal:4711/media/")
        assert data["duration_sec"] == 93.5
        assert data["sampling"] == {"fps": 1.0}
        assert data["thumb_url"].startswith("/api/media/thumb/")

    def test_upload_too_large_returns_413(self, client: TestClient):
        too_big = b"\x00" * (11 * 1024 * 1024)
        r = client.post(
            "/api/media/upload",
            files={"file": ("big.mp4", too_big, "video/mp4")},
        )
        assert r.status_code == 413
        assert "recovery_hint" in r.json().get("detail", {})

    def test_upload_unsupported_extension_returns_400(self, client: TestClient):
        r = client.post(
            "/api/media/upload",
            files={"file": ("trojan.exe", b"\x00" * 1024, "application/octet-stream")},
        )
        assert r.status_code == 400


class TestThumbEndpoint:
    def test_thumb_returns_jpeg(self, client: TestClient, tmp_path: Path):
        # Pre-plant a thumbnail
        uuid = "test-uuid-1234"
        (tmp_path / "media" / "vllm-uploads").mkdir(parents=True, exist_ok=True)
        thumb = tmp_path / "media" / "vllm-uploads" / f"{uuid}.jpg"
        thumb.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg-bytes")
        r = client.get(f"/api/media/thumb/{uuid}.jpg")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("image/")

    def test_thumb_returns_404_for_missing(self, client: TestClient):
        r = client.get("/api/media/thumb/not-a-real-uuid.jpg")
        assert r.status_code == 404
```

- [ ] **Step 2: Run — expect `ModuleNotFoundError`**

```bash
python -m pytest tests/test_channels/test_media_api.py -v
```

- [ ] **Step 3: Create `src/cognithor/channels/media_api.py`**

```python
"""/api/media/upload + /api/media/thumb FastAPI routes.

Separate from the MediaUploadServer (which only serves vLLM fetches). These
endpoints are invoked by the Flutter client and run on the main Cognithor API
port. They delegate the actual storage to MediaUploadServer.save_upload and
run ffprobe/ffmpeg synchronously in a thread (both complete in <200 ms for
typical videos).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from cognithor.core.llm_backend import (
    MediaUploadError,
    MediaUploadTooLargeError,
    MediaUploadUnsupportedFormatError,
)
from cognithor.core.video_sampling import resolve_sampling
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.channels.media_server import MediaUploadServer
    from cognithor.config import CognithorConfig

log = get_logger(__name__)

media_router = APIRouter(prefix="/api/media", tags=["media"])


@media_router.post("/upload")
async def upload_video(request: Request, file: UploadFile = File(...)) -> dict:
    config: CognithorConfig = request.app.state.config
    media_server: MediaUploadServer = request.app.state.media_server

    data = await file.read()
    filename = file.filename or "video.mp4"
    ext = Path(filename).suffix.lstrip(".")

    try:
        uuid = media_server.save_upload(data, ext)
    except MediaUploadTooLargeError as exc:
        raise HTTPException(
            status_code=413,
            detail={"message": str(exc), "recovery_hint": exc.recovery_hint},
        ) from exc
    except MediaUploadUnsupportedFormatError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except MediaUploadError as exc:
        raise HTTPException(status_code=507, detail={"message": str(exc)}) from exc

    # Path on disk for the just-saved file
    saved_path = media_server._media_dir / f"{uuid}.{ext.lower()}"

    # Best-effort thumbnail (sync call, ~100 ms for typical videos)
    _extract_thumbnail(
        saved_path,
        media_server._media_dir / f"{uuid}.jpg",
        ffmpeg_path="ffmpeg",
    )

    # Resolve sampling via the configured mode
    sampling = resolve_sampling(
        str(saved_path),
        ffprobe_path=config.vllm.video_ffprobe_path,
        timeout_seconds=config.vllm.video_ffprobe_timeout_seconds,
        http_timeout_seconds=config.vllm.video_ffprobe_http_timeout_seconds,
        override=config.vllm.video_sampling_mode,
    )

    return {
        "uuid": uuid,
        "url": media_server.public_url(uuid, ext),
        "duration_sec": sampling.duration_sec,
        "sampling": sampling.as_mm_kwargs(),
        "thumb_url": f"/api/media/thumb/{uuid}.jpg",
    }


@media_router.get("/thumb/{filename}")
async def thumb(request: Request, filename: str) -> FileResponse:
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="invalid filename")
    media_server: MediaUploadServer = request.app.state.media_server
    path = media_server._media_dir / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(path, media_type="image/jpeg")


def _extract_thumbnail(source: Path, dest: Path, *, ffmpeg_path: str = "ffmpeg") -> bool:
    """Best-effort: extract the first frame as JPEG. Returns True on success."""
    if not shutil.which(ffmpeg_path) and not Path(ffmpeg_path).is_file():
        return False
    try:
        subprocess.run(
            [ffmpeg_path, "-y", "-loglevel", "error", "-ss", "0", "-i", str(source),
             "-vframes", "1", "-vf", "scale=192:108", str(dest)],
            capture_output=True, text=True, timeout=10,
        )
    except Exception as exc:
        log.warning("thumbnail_extract_failed", error=str(exc))
        return False
    return dest.is_file()


def build_media_app(*, config: "CognithorConfig", media_server: "MediaUploadServer") -> FastAPI:
    """Standalone FastAPI app for tests. In production the media_router is
    included into the main APIChannel app via app.include_router()."""
    app = FastAPI()
    app.state.config = config
    app.state.media_server = media_server
    app.include_router(media_router)
    return app
```

Wire into production: find `channels/api.py`'s `_create_app` (from PR #137 which added `backends_router`). Add alongside the backends_router include:

```python
try:
    from cognithor.channels.media_api import media_router
    app.include_router(media_router)
    app.state.media_server = self._media_server  # injected by Gateway at start
except Exception as exc:
    log.warning("media_router_include_failed", error=str(exc))
```

- [ ] **Step 4: Run — expect all pass**

```bash
python -m pytest tests/test_channels/test_media_api.py -v
```

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/channels/media_api.py src/cognithor/channels/api.py tests/test_channels/test_media_api.py
python -m ruff format --check src/cognithor/channels/media_api.py src/cognithor/channels/api.py tests/test_channels/test_media_api.py
git add src/cognithor/channels/media_api.py src/cognithor/channels/api.py tests/test_channels/test_media_api.py
git commit -m "feat(api): /api/media/upload + /api/media/thumb endpoints"
```

---

## Task 15: Gateway — MediaUploadServer + VideoCleanupWorker Lifecycle + Per-Turn Extraction

**Files:**
- Modify: `src/cognithor/gateway/gateway.py` (lazy-instantiate + start/stop on lifecycle, extract video from incoming message)
- Modify: `tests/test_gateway/test_gateway_video_wiring.py` (new test file)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gateway/test_gateway_video_wiring.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.config import CognithorConfig, VLLMConfig


class TestGatewayVideoWiring:
    def test_video_attachment_extracted_into_working_memory(self):
        """Given an IncomingMessage whose attachments list holds one video
        URL and one image, the Gateway pulls the video into
        WorkingMemory.video_attachment and leaves the image in image_attachments."""
        from cognithor.gateway.gateway import _classify_attachments

        image_attachments, video_attachment, rejected_extras = _classify_attachments(
            [
                "/tmp/pic.png",
                "/tmp/clip.mp4",
            ]
        )
        assert image_attachments == ["/tmp/pic.png"]
        assert video_attachment is not None
        assert video_attachment == "/tmp/clip.mp4"
        assert rejected_extras == []

    def test_second_video_is_rejected_with_error(self):
        from cognithor.gateway.gateway import _classify_attachments

        image_attachments, video_attachment, rejected_extras = _classify_attachments(
            [
                "/tmp/clip1.mp4",
                "/tmp/clip2.mp4",
                "/tmp/clip3.webm",
            ]
        )
        assert video_attachment == "/tmp/clip1.mp4"  # first wins
        assert rejected_extras == ["/tmp/clip2.mp4", "/tmp/clip3.webm"]

    def test_no_videos_returns_none(self):
        from cognithor.gateway.gateway import _classify_attachments

        _, video_attachment, rejected_extras = _classify_attachments(
            [
                "/tmp/pic.png",
                "/tmp/doc.pdf",
            ]
        )
        assert video_attachment is None
        assert rejected_extras == []
```

- [ ] **Step 2: Run — expect `ImportError: cannot import name '_classify_attachments'`**

- [ ] **Step 3: Add the classifier to `src/cognithor/gateway/gateway.py`**

Near the top of the file (after imports), define the classifier as a pure function for testability:

```python
_IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"})
_VIDEO_EXTS = frozenset({".mp4", ".webm", ".mov", ".mkv", ".avi"})


def _classify_attachments(
    attachments: list[str],
) -> tuple[list[str], str | None, list[str]]:
    """Split an attachment list into images / one video / rejected extra videos.

    Returns:
        (image_attachments, first_video_or_None, rejected_extra_videos)

    Single-video-per-turn policy (spec Decision 7): the first video in the
    list wins; any additional videos go into `rejected_extra_videos` so the
    caller can surface a user-visible validation error.
    """
    images: list[str] = []
    video: str | None = None
    rejected: list[str] = []
    for path in attachments:
        ext = ""
        if "." in path:
            ext = "." + path.rsplit(".", 1)[-1].lower()
        if ext in _IMAGE_EXTS:
            images.append(path)
        elif ext in _VIDEO_EXTS:
            if video is None:
                video = path
            else:
                rejected.append(path)
    return images, video, rejected
```

Then inside the Gateway's per-turn pre-processing (where `image_attachments` is set on `wm` — search for the existing `wm.image_attachments = [a for a in ...]` block added in PR #132), replace with:

```python
        if msg.attachments:
            images, video_path, rejected_videos = _classify_attachments(msg.attachments)
            wm.image_attachments = images
            if video_path is not None:
                # video_path is a local path OR a URL the Flutter client already
                # resolved via /api/media/upload (in which case attachments[N]
                # holds the host.docker.internal URL). Sampling resolution
                # happens here for URLs that skipped the upload endpoint.
                wm.video_attachment = _build_video_attachment(video_path, self._config)
                if self._vllm_orchestrator is not None:
                    # Register upload with cleanup worker (best-effort; only
                    # matters if video_path is a local upload, not an external URL)
                    uuid = _extract_uuid_from_path(video_path)
                    if uuid and self._video_cleanup:
                        self._video_cleanup.register_upload(uuid, wm.session_id)
            if rejected_videos:
                await self._surface_validation_error(
                    wm.session_id,
                    f"Ein Video pro Nachricht. {len(rejected_videos)} weitere Videos wurden ignoriert.",
                )
```

`_build_video_attachment` and `_extract_uuid_from_path` are helpers in gateway.py (or `gateway/video_attach.py` if you prefer a separate file — keep gateway.py from growing too large).

Also in Gateway init, lazy-instantiate MediaUploadServer + VideoCleanupWorker when vllm is enabled:

```python
        if self._config.vllm.enabled:
            from cognithor.channels.media_server import MediaUploadServer
            from cognithor.gateway.video_cleanup import VideoCleanupWorker

            self._media_server = MediaUploadServer(self._config)
            self._video_cleanup = VideoCleanupWorker(
                media_dir=self._media_server._media_dir,
                ttl_hours=self._config.vllm.video_upload_ttl_hours,
            )
            # Start in the existing init phase; stop in `shutdown()`
```

Add to the async startup sequence (whatever phase the existing PR #137 VLLMOrchestrator lives in):

```python
        if self._media_server is not None:
            port = await self._media_server.start()
            if self._vllm_orchestrator is not None:
                self._vllm_orchestrator.media_url = f"http://host.docker.internal:{port}"
        if self._video_cleanup is not None:
            await self._video_cleanup.start()
```

And to `shutdown()`:

```python
        if self._video_cleanup is not None:
            await self._video_cleanup.stop()
        if self._media_server is not None:
            await self._media_server.stop()
```

- [ ] **Step 4: Run — expect all pass**

```bash
python -m pytest tests/test_gateway/test_gateway_video_wiring.py -v
python -m pytest tests/test_gateway/ -q  # regression
```

- [ ] **Step 5: Ruff + commit**

```bash
python -m ruff check src/cognithor/gateway/gateway.py tests/test_gateway/test_gateway_video_wiring.py
python -m ruff format --check src/cognithor/gateway/gateway.py tests/test_gateway/test_gateway_video_wiring.py
git add src/cognithor/gateway/gateway.py tests/test_gateway/test_gateway_video_wiring.py
git commit -m "feat(gateway): video attachment extraction + MediaServer/Cleanup lifecycle"
```

---

## Task 16: Integration — fake vLLM Server Echoes Video Response

**Files:**
- Modify: `tests/test_integration/test_vllm_fake_server.py` (extend fake server to handle video_url content-item + return stubbed response)

- [ ] **Step 1: Extend the fake server setup to inspect video content-items**

In `tests/test_integration/test_vllm_fake_server.py` (created in PR #137), add a handler branch in the fake `/v1/chat/completions` endpoint:

```python
    @app.post("/v1/chat/completions")
    async def chat(body: dict):
        # ... existing text+image branches ...

        # Detect video
        last_msg = body["messages"][-1]
        content = last_msg.get("content")
        if isinstance(content, list):
            has_video = any(c.get("type") == "video_url" for c in content)
            if has_video:
                video_url = next(c["video_url"]["url"] for c in content if c.get("type") == "video_url")
                extra = body.get("extra_body", {})
                mm_video = extra.get("mm_processor_kwargs", {}).get("video", {})
                return {
                    "choices": [{
                        "message": {"content": f"Saw video {video_url} with sampling {mm_video}"}
                    }],
                    "model": body["model"],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }
        # ... fall through to existing text branch ...
```

Add a new test class:

```python
class TestVLLMBackendVideoEndToEnd:
    @pytest.mark.asyncio
    async def test_video_roundtrip_preserves_url_and_sampling(self, fake_server):
        from cognithor.core.vllm_backend import VLLMBackend

        backend = VLLMBackend(base_url=f"http://127.0.0.1:{fake_server}/v1")
        try:
            resp = await backend.chat(
                model="fake-model",
                messages=[{"role": "user", "content": "describe"}],
                video={"url": "http://example.com/clip.mp4", "sampling": {"fps": 2.0}},
            )
            assert "http://example.com/clip.mp4" in resp.content
            assert "'fps': 2.0" in resp.content or "fps" in resp.content
        finally:
            await backend.close()
```

- [ ] **Step 2: Run — expect 1 new pass**

```bash
python -m pytest tests/test_integration/test_vllm_fake_server.py -v
```

- [ ] **Step 3: Ruff + commit**

```bash
python -m ruff check tests/test_integration/test_vllm_fake_server.py
python -m ruff format --check tests/test_integration/test_vllm_fake_server.py
git add tests/test_integration/test_vllm_fake_server.py
git commit -m "test(vllm): fake server round-trip for video_url + mm_processor_kwargs"
```

---

## Task 17: Flutter — chat_input.dart PopupMenuButton

**Files:**
- Modify: `flutter_app/lib/widgets/chat_input.dart` (replace paperclip `IconButton` with `PopupMenuButton`)
- Create: `flutter_app/test/widgets/chat_input_video_menu_test.dart`

- [ ] **Step 1: Write the failing widget test**

```dart
// flutter_app/test/widgets/chat_input_video_menu_test.dart
import 'package:cognithor_ui/providers/chat_provider.dart';
import 'package:cognithor_ui/providers/llm_backend_provider.dart';
import 'package:cognithor_ui/widgets/chat_input.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

LlmBackendProvider _mkBackendProvider(String active) {
  final p = LlmBackendProvider(apiBaseUrl: 'http://test');
  p.active = active;
  return p;
}

ChatProvider _mkChatProvider() {
  return ChatProvider();  // assume default constructor exists
}

Widget _wrap(Widget child, LlmBackendProvider bp, ChatProvider cp) {
  return MaterialApp(
    home: Scaffold(
      body: MultiProvider(
        providers: [
          ChangeNotifierProvider<LlmBackendProvider>.value(value: bp),
          ChangeNotifierProvider<ChatProvider>.value(value: cp),
        ],
        child: child,
      ),
    ),
  );
}

void main() {
  testWidgets('paperclip opens popup menu with 4 entries', (tester) async {
    final bp = _mkBackendProvider('vllm');
    final cp = _mkChatProvider();
    await tester.pumpWidget(_wrap(const ChatInput(), bp, cp));

    await tester.tap(find.byKey(const ValueKey('chat-input-paperclip')));
    await tester.pumpAndSettle();

    expect(find.text('Bild hochladen'), findsOneWidget);
    expect(find.text('Video hochladen'), findsOneWidget);
    expect(find.text('Datei hochladen'), findsOneWidget);
    expect(find.text('URL einfügen'), findsOneWidget);
  });

  testWidgets('Video entry disabled when active backend != vllm', (tester) async {
    final bp = _mkBackendProvider('ollama');
    final cp = _mkChatProvider();
    await tester.pumpWidget(_wrap(const ChatInput(), bp, cp));

    await tester.tap(find.byKey(const ValueKey('chat-input-paperclip')));
    await tester.pumpAndSettle();

    // Find the PopupMenuItem that holds "Video hochladen" and verify it is disabled
    final videoItem = tester.widget<PopupMenuItem<String>>(
      find.ancestor(
        of: find.text('Video hochladen'),
        matching: find.byType(PopupMenuItem<String>),
      ),
    );
    expect(videoItem.enabled, isFalse);
  });
}
```

- [ ] **Step 2: Run — expect test failures (widget not extended yet)**

```bash
cd flutter_app && flutter test test/widgets/chat_input_video_menu_test.dart
```

- [ ] **Step 3: Modify `flutter_app/lib/widgets/chat_input.dart`**

Find the existing paperclip `IconButton`. Replace with:

```dart
PopupMenuButton<String>(
  key: const ValueKey('chat-input-paperclip'),
  icon: const Icon(Icons.attach_file),
  tooltip: 'Anhang hinzufügen',
  onSelected: (value) async {
    switch (value) {
      case 'image':
        await _pickImage();
        break;
      case 'video':
        await _pickVideo();
        break;
      case 'file':
        await _pickFile();
        break;
      case 'url':
        _showUrlDialog();
        break;
    }
  },
  itemBuilder: (context) {
    final activeBackend = context.read<LlmBackendProvider>().active;
    final vllmActive = activeBackend == 'vllm';
    return [
      const PopupMenuItem(value: 'image', child: Text('Bild hochladen')),
      PopupMenuItem(
        value: 'video',
        enabled: vllmActive,
        child: Tooltip(
          message: vllmActive
              ? 'Video hochladen (nur mit vLLM-Backend)'
              : 'Video-Analyse erfordert vLLM — unter Settings → LLM Backends wechseln.',
          child: Row(
            children: [
              const Text('Video hochladen'),
              if (!vllmActive)
                const Padding(
                  padding: EdgeInsets.only(left: 6),
                  child: Icon(Icons.lock, size: 14, color: Colors.grey),
                ),
            ],
          ),
        ),
      ),
      const PopupMenuItem(value: 'file', child: Text('Datei hochladen')),
      const PopupMenuItem(value: 'url', child: Text('URL einfügen')),
    ];
  },
),
```

Add `_pickVideo()` stub (real implementation in Task 18):

```dart
Future<void> _pickVideo() async {
  // Implemented in Task 18 — connect ChatProvider.sendVideo
  // For now, the button is wired but does nothing on tap.
}
```

- [ ] **Step 4: Run — expect all pass**

```bash
cd flutter_app && flutter test test/widgets/chat_input_video_menu_test.dart && flutter analyze
```

- [ ] **Step 5: Commit**

```bash
cd flutter_app && flutter analyze lib/widgets/chat_input.dart test/widgets/chat_input_video_menu_test.dart
cd ..
git add flutter_app/lib/widgets/chat_input.dart flutter_app/test/widgets/chat_input_video_menu_test.dart
git commit -m "feat(flutter): chat-input paperclip becomes PopupMenuButton with Video entry"
```

---

## Task 18: Flutter — ChatProvider.sendVideo + URL-Paste Detection

**Files:**
- Modify: `flutter_app/lib/providers/chat_provider.dart` (add `sendVideo`, add regex-based URL paste detection)
- Modify: `flutter_app/lib/widgets/chat_input.dart` (wire `_pickVideo` to `sendVideo`)

- [ ] **Step 1: Extend `ChatProvider` with `sendVideo`**

In `flutter_app/lib/providers/chat_provider.dart`, add:

```dart
Future<void> sendVideo(String localPath, String filename) async {
  final bytes = await File(localPath).readAsBytes();
  final uri = Uri.parse('$apiBaseUrl/api/media/upload');
  final request = http.MultipartRequest('POST', uri)
    ..files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));

  final streamed = await request.send();
  final body = await streamed.stream.bytesToString();
  if (streamed.statusCode != 200) {
    throw Exception('Upload failed: HTTP ${streamed.statusCode} — $body');
  }
  final resp = jsonDecode(body) as Map<String, dynamic>;

  // Attach to the next outgoing message metadata
  _pendingVideoAttachment = {
    'kind': 'video',
    'uuid': resp['uuid'],
    'url': resp['url'],
    'filename': filename,
    'duration_sec': resp['duration_sec'],
    'sampling': resp['sampling'],
    'thumb_url': resp['thumb_url'],
  };
  notifyListeners();
}

/// URL-paste detection — call from TextField onChanged.
/// Returns true if the pasted text was consumed as a video URL attachment.
bool handlePastedTextForVideoUrl(String text) {
  final pattern = RegExp(
    r'^\s*(https?://\S+\.(?:mp4|webm|mov|mkv|avi))\s*$',
    caseSensitive: false,
  );
  final m = pattern.firstMatch(text);
  if (m == null) return false;
  _pendingVideoAttachment = {
    'kind': 'video',
    'url': m.group(1),
    'filename': m.group(1)!.split('/').last,
    // duration_sec + sampling filled in by backend on chat-send
    'thumb_url': null,
  };
  notifyListeners();
  return true;
}
```

Add `_pendingVideoAttachment` field + corresponding message-shipping logic (whatever existing `sendMessage` does, prepend the pending video into `message.attachments` then clear it).

- [ ] **Step 2: Wire `_pickVideo()` in `chat_input.dart`**

```dart
Future<void> _pickVideo() async {
  final result = await FilePicker.platform.pickFiles(
    type: FileType.custom,
    allowedExtensions: ['mp4', 'webm', 'mov', 'mkv', 'avi'],
    withData: false,
  );
  if (result == null || result.files.isEmpty) return;
  final file = result.files.first;
  if (file.path == null) return;
  try {
    await context.read<ChatProvider>().sendVideo(file.path!, file.name);
  } catch (e) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Video upload fehlgeschlagen: $e')),
      );
    }
  }
}
```

- [ ] **Step 3: Full Flutter regression**

```bash
cd flutter_app && flutter test && flutter analyze
```

- [ ] **Step 4: Commit**

```bash
cd flutter_app && flutter analyze lib/providers/chat_provider.dart lib/widgets/chat_input.dart
cd ..
git add flutter_app/lib/providers/chat_provider.dart flutter_app/lib/widgets/chat_input.dart
git commit -m "feat(flutter): ChatProvider.sendVideo + URL-paste video detection"
```

---

## Task 19: Flutter — Video Bubble with Thumbnail + Banner for Long Videos

**Files:**
- Modify: `flutter_app/lib/widgets/chat_bubble.dart`
- Create: `flutter_app/test/widgets/chat_bubble_video_test.dart`

- [ ] **Step 1: Write the failing test**

```dart
// flutter_app/test/widgets/chat_bubble_video_test.dart
import 'package:cognithor_ui/widgets/chat_bubble.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('video-kind metadata renders filename + duration + sampling', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: ChatBubble(
          text: 'Was siehst du?',
          isUser: true,
          metadata: {
            'kind': 'video',
            'filename': 'drone.mp4',
            'duration_sec': 42.5,
            'sampling': {'fps': 2.0},
            'thumb_url': null,
          },
        ),
      ),
    ));

    expect(find.text('drone.mp4'), findsOneWidget);
    expect(find.textContaining('0:42'), findsOneWidget);  // duration formatted
    expect(find.textContaining('fps=2'), findsOneWidget);
  });

  testWidgets('long-video banner appears when duration > 15 minutes', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: ChatBubble(
          text: 'Analyze',
          isUser: true,
          metadata: {
            'kind': 'video',
            'filename': 'lecture.mp4',
            'duration_sec': 2400.0,  // 40 min
            'sampling': {'num_frames': 32},
          },
        ),
      ),
    ));
    expect(find.byKey(const ValueKey('video-long-banner')), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run — expect failures**

- [ ] **Step 3: Modify `chat_bubble.dart`** — add a branch for `metadata['kind'] == 'video'`

```dart
Widget _buildVideoPreview(Map<String, dynamic> meta) {
  final filename = meta['filename'] as String? ?? 'video';
  final durationSec = (meta['duration_sec'] as num?)?.toDouble() ?? 0.0;
  final sampling = meta['sampling'] as Map<String, dynamic>? ?? {};
  final thumbUrl = meta['thumb_url'] as String?;

  final samplingLabel = sampling.containsKey('fps')
      ? 'fps=${sampling['fps']}'
      : 'num_frames=${sampling['num_frames'] ?? '?'}';

  final mins = (durationSec / 60).floor();
  final secs = (durationSec % 60).round();
  final durationLabel = '${mins}:${secs.toString().padLeft(2, '0')}';

  return Column(
    crossAxisAlignment: CrossAxisAlignment.end,
    children: [
      Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.15),
          border: Border.all(color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.4)),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 96,
              height: 54,
              color: Colors.grey.shade800,
              child: thumbUrl != null
                  ? Image.network(
                      '${context.read<LlmBackendProvider>().apiBaseUrl}$thumbUrl',
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => const Center(child: Text('🎬', style: TextStyle(fontSize: 22))),
                    )
                  : const Center(child: Text('🎬', style: TextStyle(fontSize: 22))),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(filename, style: const TextStyle(fontWeight: FontWeight.w500)),
                const SizedBox(height: 2),
                Text(
                  '$durationLabel · $samplingLabel',
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade400),
                ),
              ],
            ),
          ],
        ),
      ),
      if (durationSec > 15 * 60)
        Container(
          key: const ValueKey('video-long-banner'),
          margin: const EdgeInsets.only(top: 6),
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.orange.withValues(alpha: 0.15),
            border: Border(left: BorderSide(color: Colors.orange, width: 3)),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            'Video ${(durationSec/60).round()} min — nur 32 Frames werden gesampled. '
            'Zerlege in 5-Min-Clips für mehr Detail.',
            style: const TextStyle(fontSize: 11, color: Colors.orange),
          ),
        ),
    ],
  );
}
```

Call `_buildVideoPreview` from the existing `build()` method when `metadata['kind'] == 'video'`.

- [ ] **Step 4: Run — expect all pass + flutter analyze clean**

```bash
cd flutter_app && flutter test test/widgets/chat_bubble_video_test.dart && flutter analyze lib/widgets/chat_bubble.dart
```

- [ ] **Step 5: Commit**

```bash
git add flutter_app/lib/widgets/chat_bubble.dart flutter_app/test/widgets/chat_bubble_video_test.dart
git commit -m "feat(flutter): chat bubble renders video kind with thumbnail + long-video banner"
```

---

## Task 20: Windows Installer — Bundle LGPL ffmpeg + CI Verification

**Files:**
- Modify: `installer/build_installer.py` (new step `step_ffmpeg()`)
- Modify: `.github/workflows/build-windows-installer.yml` (LGPL-vs-GPL check)

- [ ] **Step 1: Add `step_ffmpeg()` to `installer/build_installer.py`**

```python
FFMPEG_LGPL_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-lgpl-shared.zip"
)


def step_ffmpeg() -> Path:
    """Download a LGPL-licensed ffmpeg+ffprobe build and return the bin dir."""
    dest_zip = Path("build/ffmpeg.zip")
    extract_dir = Path("build/ffmpeg")
    if not dest_zip.exists():
        download(FFMPEG_LGPL_URL, dest_zip, desc="ffmpeg LGPL build")
    if not extract_dir.exists():
        import zipfile
        with zipfile.ZipFile(dest_zip) as z:
            z.extractall(extract_dir)
    # BtbN archives have a single top-level folder; find bin/ffmpeg.exe
    for p in extract_dir.rglob("ffmpeg.exe"):
        # Verify the build is actually LGPL (not accidentally GPL)
        result = subprocess.run([str(p), "-version"], capture_output=True, text=True)
        version_lines = (result.stdout + result.stderr).splitlines()
        first_config_line = next((l for l in version_lines if "configuration" in l), "")
        if "--enable-gpl" in first_config_line:
            raise RuntimeError(
                f"Downloaded ffmpeg is a GPL build (configuration: {first_config_line!r}). "
                "GPL would contaminate Cognithor's Apache-2.0 license. Use the LGPL variant."
            )
        return p.parent  # bin/
    raise RuntimeError("ffmpeg.exe not found after extraction")
```

Hook it into `main()` alongside the existing `step_ollama`, `step_python_embed` etc. The Inno Setup script receives the `bin/` path and copies its contents to `%LOCALAPPDATA%\Cognithor\ffmpeg\`.

- [ ] **Step 2: Add CI verification step**

In `.github/workflows/build-windows-installer.yml`, after the "Build installer" step, add:

```yaml
      - name: Verify bundled ffmpeg is LGPL (not GPL)
        shell: pwsh
        run: |
          $ffmpeg = Get-ChildItem -Recurse -Filter ffmpeg.exe | Select-Object -First 1
          if (-not $ffmpeg) { throw "ffmpeg.exe not found in build output" }
          $version = & $ffmpeg.FullName -version 2>&1 | Out-String
          if ($version -match '--enable-gpl') {
            throw "Bundled ffmpeg is a GPL build — Cognithor is Apache-2.0. Use LGPL variant."
          }
          if ($version -notmatch '--enable-version3') {
            Write-Warning "Bundled ffmpeg does not claim LGPL v3 — double-check the build source"
          }
          Write-Host "✓ ffmpeg build is LGPL-compatible"
```

- [ ] **Step 3: Commit**

```bash
python -m ruff check installer/build_installer.py
git add installer/build_installer.py .github/workflows/build-windows-installer.yml
git commit -m "feat(installer): bundle LGPL ffmpeg for Windows + CI verification step"
```

(No unit test here — the check runs in CI as part of the installer build.)

---

## Task 21: User Guide Update — Video Section

**Files:**
- Modify: `docs/vllm-user-guide.md` (append a "Video Input" section)

- [ ] **Step 1: Append this section to `docs/vllm-user-guide.md`**

```markdown
## Video Input

With vLLM active and a video-capable model loaded (Qwen3.6-27B, Qwen2.5-VL-7B-Instruct,
Qwen3.6-35B-A3B, or any VLM vLLM recognizes as video-capable), you can attach a single
video per chat turn.

### Two ways to attach

**Local file**: paperclip → "Video hochladen" → pick a `.mp4` / `.webm` / `.mov` /
`.mkv` / `.avi` (max 500 MB per file, 5 GB total quota).

**URL paste**: paste a direct video URL in the chat input. Cognithor detects URLs
ending in a recognized video extension and treats them as a video attachment. YouTube
links are **not** supported — use a direct `.mp4` link.

### What happens under the hood

1. Local uploads are stored temporarily at `~/.cognithor/media/vllm-uploads/<uuid>.<ext>`,
   served to the vLLM container over a localhost-only HTTP server.
2. `ffprobe` detects video duration and Cognithor picks an adaptive frame sampling rate:
   short clips (< 10 s) get `fps=3`, longer clips get fewer frames spread across the
   full duration.
3. vLLM fetches the video, samples frames internally, and feeds them to the VLM.
4. Uploads are deleted when the chat session closes, or automatically after 24 hours,
   whichever comes first.

### Troubleshooting

**"Video hochladen" entry is greyed out**: the active backend is not vLLM. Settings →
LLM Backends → tap vLLM → "Make active".

**Upload fails with "too big"**: max 500 MB per file. Raise `config.vllm.video_max_upload_mb`
or trim the clip.

**Chat replies "vLLM offline — Video kann nicht verarbeitet werden"**: vLLM is DEGRADED.
Unlike text chat (which falls back to Ollama), videos can't fall back — Ollama has no
vision. Wait ~60 s for the circuit breaker to probe vLLM again, or restart vLLM from
LLM Backends settings.

**Long-video banner appears**: videos longer than 15 min only get 32 frames sampled
(one every ~30 s for a 15-min video, sparser for longer). For detailed temporal
reasoning, trim to 5-min chunks.

**`ffprobe not found` warning in logs**: install ffmpeg on Linux/macOS via
`apt install ffmpeg` / `brew install ffmpeg`. Windows installer bundles it. Without
ffprobe, Cognithor falls back to 32 frames for every video regardless of length.

### Advanced configuration

`~/.cognithor/config.yaml` `vllm:` section:

| Field | Default | Purpose |
|-------|---------|---------|
| `video_sampling_mode` | `adaptive` | `adaptive` / `fixed_32` / `fixed_64` / `fps_1` |
| `video_ffprobe_path` | `ffprobe` | override to absolute path if not in `$PATH` |
| `video_ffprobe_timeout_seconds` | `5` | local-file duration detection timeout |
| `video_ffprobe_http_timeout_seconds` | `30` | URL duration detection timeout |
| `video_max_upload_mb` | `500` | per-file hard cap |
| `video_quota_gb` | `5` | total disk budget; oldest files evicted first |
| `video_upload_ttl_hours` | `24` | automatic cleanup after this many hours |
```

- [ ] **Step 2: Commit**

```bash
git add docs/vllm-user-guide.md
git commit -m "docs(video): user guide video-input section with troubleshooting + config"
```

---

## Task 22: Manual Smoke Test — Video Entries

**Files:**
- Modify: `docs/vllm-manual-test.md`

- [ ] **Step 1: Append new sections to `docs/vllm-manual-test.md`**

```markdown
## 9. Video upload flow (RTX 5090 only — requires video-capable VLM)

Prerequisites: vLLM running with `Qwen/Qwen3.6-27B` (any variant that vLLM has
confirmed video support for).

- Paperclip → "Video hochladen" → pick a ~30 s `.mp4` (e.g., the Qwen OSS sample
  downloaded locally).
- Expect: bubble shows thumbnail + filename + `0:30 · fps=2`.
- Send: "What happens in this video?".
- Expect: answer describes the clip's content within 10–20 s.

## 10. Video URL paste

- Paste `https://qianwen-res.oss-accelerate.aliyuncs.com/Qwen3.5/demo/video/N1cdUjctpG8.mp4`.
- Expect: input field clears, bubble shows a thumbnail-less video card.
- Send: "Describe what you see".
- Expect: answer describes the Qwen demo video.

## 11. Long-video banner + 32-frame sampling

- Upload a > 15-min video.
- Expect: bubble shows the orange `Video N min — nur 32 Frames werden gesampled` banner.
- Send: "Summarize the main topics".
- Expect: answer is coarse but topically correct.

## 12. Video + DEGRADED vLLM

- While chatting: `docker stop $(docker ps -q --filter label=cognithor.managed=true)`.
- Send a video request.
- Expect: red error bubble "vLLM offline — Video kann nicht verarbeitet werden".
- `docker start <container-id>`; wait 60 s; re-send.
- Expect: normal response.

## 13. Cleanup on session close

- Upload a video; note the uuid in `~/.cognithor/media/vllm-uploads/`.
- Close Cognithor.
- Expect: `~/.cognithor/media/vllm-uploads/` is empty, OR contains only files whose
  mtime is < 24 h old from a prior test run (run 14 to verify cleanup actually works).

## 14. Cleanup on TTL expiry (simulated)

- Upload a video.
- `touch -d "2 days ago" ~/.cognithor/media/vllm-uploads/<uuid>.*` (sets mtime into the past).
- Restart Cognithor.
- Expect: the file is gone within 60 s (periodic sweep), or immediately on start
  (start-time sweep).

## 15. Second video in same turn is rejected

- Attach one video (paperclip → video).
- Try to attach a second video (paperclip again — the "Video hochladen" entry
  should still be enabled only if the pending message has no video yet).
- Expect: either the menu entry is disabled with a tooltip "Ein Video pro Nachricht",
  or the second attach attempt produces a snackbar error.
```

- [ ] **Step 2: Commit**

```bash
git add docs/vllm-manual-test.md
git commit -m "docs(video): manual smoke-test recipes 9-15 for video input"
```

---

## Task 23: CHANGELOG + Final Regression + Ruff Sweep

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add `[Unreleased]` entry at top of `CHANGELOG.md`**

```markdown
## [Unreleased]

### Added
- **Video input via vLLM** — attach a local video (.mp4 / .webm / .mov / .mkv /
  .avi) or paste a direct video URL in chat; Qwen3.6-27B (or any vLLM-served
  video-capable VLM) analyzes it end-to-end. Native vLLM `video_url` content
  type — no frame-extraction workarounds. Adaptive frame sampling based on
  duration (fps=3 for clips under 10 s, num_frames=32 for videos over 5 min)
  via `ffprobe`. Single video per chat turn. Local uploads served to vLLM over
  a 127.0.0.1-only HTTP file server. Videos are cleaned up when the chat
  session closes and auto-expire after 24 h. Video requests on a DEGRADED vLLM
  produce a hard error — no silent fallback to Ollama (Ollama has no vision).
  Windows installer now bundles an LGPL-licensed ffmpeg build. See
  `docs/vllm-user-guide.md` and `docs/superpowers/specs/2026-04-23-video-input-vllm-design.md`.

### Changed
- Cognithor now requires Docker Engine ≥ 20.10 when using vLLM on Linux
  (host-gateway flag for `--add-host` was added in 20.10). Docker Desktop
  versions are all fine.
- Flutter paperclip in the chat input is now a popup menu with explicit
  entries for Image / Video / File / URL instead of a single file picker.
```

- [ ] **Step 2: Run full regression**

```bash
python -m pytest tests/ -x -q --ignore=tests/test_integration/test_live_ollama.py 2>&1 | tail -10
```
Expected: all pass. Record the pass count.

- [ ] **Step 3: Flutter full test + analyze**

```bash
cd flutter_app && flutter test 2>&1 | tail -5
cd flutter_app && flutter analyze 2>&1 | tail -5
cd ..
```

- [ ] **Step 4: Ruff final sweep**

```bash
python -m ruff check src/cognithor/ tests/
python -m ruff format --check src/ tests/
```
Expected: `All checks passed!` + `N files already formatted`.

- [ ] **Step 5: Commit CHANGELOG**

```bash
git add CHANGELOG.md
git commit -m "chore(changelog): document video-input via vLLM feature"
```

- [ ] **Step 6: Push and open PR**

```bash
git push -u origin feat/vllm-video-input
```

Open PR with title `feat(vllm-video): native video input via Qwen3.6-27B` and body referencing:
- Spec at `docs/superpowers/specs/2026-04-23-video-input-vllm-design.md`
- Day-1 spike findings at `docs/vllm-video-spike-notes.md`
- The seven locked design decisions
- Known follow-ups (multi-video turn support, YouTube URLs, live-stream input)

After CI green, run the manual smoke tests from Task 22 on real hardware before merging.

---

## Self-Review Checklist

After all 23 tasks are complete:

- [ ] Every new Python module has tests: `video_sampling.py`, `media_server.py`, `video_cleanup.py`, `media_api.py`, video paths in `vllm_backend.py`, video paths in `unified_llm.py`
- [ ] `tests/test_integration/test_vllm_fake_server.py` includes the video roundtrip case
- [ ] Flutter tests cover the paperclip popup menu + video bubble + long-video banner
- [ ] Full regression green (`pytest tests/` excluding `test_live_ollama`)
- [ ] Flutter `flutter test` + `flutter analyze` green
- [ ] Ruff check + format --check clean across `src/` and `tests/`
- [ ] Day-1 spike findings doc exists and matches the code (if the spike revealed different wire shapes, the adjusted code matches)
- [ ] CHANGELOG `[Unreleased]` entry written
- [ ] Backwards compat: users who don't enable vLLM or don't use video see zero behavior change
- [ ] Manual smoke test from Task 22 completed on real NVIDIA hardware with a video-capable VLM
- [ ] vLLM container-log ring buffer from PR #137 still works — video requests don't break it
