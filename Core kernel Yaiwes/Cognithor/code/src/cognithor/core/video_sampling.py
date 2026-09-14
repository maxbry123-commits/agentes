"""Video sampling: map video duration to fps/num_frames for a vLLM request.

Maps duration to the bucket table from
docs/superpowers/specs/2026-04-23-video-input-vllm-design.md.
Pure logic only; I/O entry point ``resolve_sampling`` is added in Task 3.
"""

from __future__ import annotations

import json as _json
import subprocess
from dataclasses import dataclass
from typing import Any, Literal

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

_MAX_PLAUSIBLE_DURATION_SEC = 86400.0  # 24 hours; anything bigger is almost certainly garbage


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
    # 5 min - 15 min AND > 15 min both use num_frames=32; UI banner is
    # a display concern not a sampling one.
    return VideoSampling(num_frames=32, duration_sec=duration_sec)


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

    For ``override != "adaptive"``, returns a fixed sampling without touching
    ffprobe. For adaptive, runs ffprobe with the appropriate timeout
    (``timeout_seconds`` for local paths, ``http_timeout_seconds`` for URLs)
    and falls back to ``VideoSampling(num_frames=32)`` on any failure.
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
        ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        source,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        log.warning("video_ffprobe_missing", recovery="fallback to num_frames=32")
        return VideoSampling(num_frames=32)
    except subprocess.TimeoutExpired:
        log.warning(
            "video_duration_detection_timeout",
            source=_redact_source(source),
            timeout_seconds=timeout,
        )
        return VideoSampling(num_frames=32)

    if result.returncode != 0:
        log.warning(
            "video_ffprobe_failed",
            returncode=result.returncode,
            stderr=result.stderr.strip()[:200],
        )
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
