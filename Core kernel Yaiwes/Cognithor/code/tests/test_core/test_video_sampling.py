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
        with pytest.raises(ValueError, match="neither fps nor num_frames"):
            s.as_mm_kwargs()


class TestBucketForDuration:
    # Spec bucket table (see design doc § "Frame Sampling"):
    # <10s → fps=3; 10-30s → fps=2; 30s-2min → fps=1;
    # 2-5min → num_frames=64; 5-15min → num_frames=32; >15min → num_frames=32
    @pytest.mark.parametrize(
        "dur,expected_fps,expected_num",
        [
            (5.0, 3.0, None),
            (9.99, 3.0, None),
            (10.0, 2.0, None),
            (29.99, 2.0, None),
            (30.0, 1.0, None),
            (119.99, 1.0, None),
            (120.0, None, 64),
            (299.99, None, 64),
            (300.0, None, 32),
            (899.99, None, 32),
            (900.0, None, 32),  # >15min still 32
            (3600.0, None, 32),
        ],
    )
    def test_buckets(
        self, dur: float, expected_fps: float | None, expected_num: int | None
    ) -> None:
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


from unittest.mock import MagicMock, patch

from cognithor.core.video_sampling import resolve_sampling


class TestResolveSampling:
    def _mk_probe_stdout(self, duration: float) -> str:
        import json as _json

        return _json.dumps({"format": {"duration": str(duration)}})

    def test_adaptive_short_clip(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(5.0))
        with patch("cognithor.core.video_sampling.subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.fps == 3.0
        assert s.num_frames is None
        assert s.duration_sec == 5.0

    def test_adaptive_long_clip(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(1800.0))
        with patch("cognithor.core.video_sampling.subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32
        assert s.duration_sec == 1800.0

    def test_ffprobe_missing_falls_back_to_num_frames_32(self):
        with patch("cognithor.core.video_sampling.subprocess.run", side_effect=FileNotFoundError):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32
        assert s.fps is None
        assert s.duration_sec is None

    def test_ffprobe_timeout_falls_back(self):
        import subprocess as _sp

        exc = _sp.TimeoutExpired(cmd="ffprobe", timeout=5)
        with patch("cognithor.core.video_sampling.subprocess.run", side_effect=exc):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32

    def test_ffprobe_nonzero_returncode_falls_back(self):
        mock = MagicMock(returncode=1, stdout="", stderr="file not found")
        with patch("cognithor.core.video_sampling.subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32

    def test_ffprobe_unparseable_json_falls_back(self):
        mock = MagicMock(returncode=0, stdout="not json at all")
        with patch("cognithor.core.video_sampling.subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32

    def test_ffprobe_negative_duration_falls_back(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(-1.0))
        with patch("cognithor.core.video_sampling.subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32

    def test_ffprobe_duration_over_24h_falls_back(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(100_000.0))
        with patch("cognithor.core.video_sampling.subprocess.run", return_value=mock):
            s = resolve_sampling("/tmp/x.mp4")
        assert s.num_frames == 32

    def test_override_fixed_32_skips_ffprobe(self):
        with patch("cognithor.core.video_sampling.subprocess.run") as run_mock:
            s = resolve_sampling("/tmp/x.mp4", override="fixed_32")
        assert s.num_frames == 32
        assert s.fps is None
        run_mock.assert_not_called()

    def test_override_fixed_64_skips_ffprobe(self):
        with patch("cognithor.core.video_sampling.subprocess.run") as run_mock:
            s = resolve_sampling("/tmp/x.mp4", override="fixed_64")
        assert s.num_frames == 64
        run_mock.assert_not_called()

    def test_override_fps_1_skips_ffprobe(self):
        with patch("cognithor.core.video_sampling.subprocess.run") as run_mock:
            s = resolve_sampling("/tmp/x.mp4", override="fps_1")
        assert s.fps == 1.0
        run_mock.assert_not_called()

    def test_http_url_uses_http_timeout(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(45.0))
        with patch("cognithor.core.video_sampling.subprocess.run", return_value=mock) as run_mock:
            resolve_sampling(
                "https://example.com/clip.mp4",
                timeout_seconds=5,
                http_timeout_seconds=30,
            )
        assert run_mock.call_args.kwargs["timeout"] == 30

    def test_local_path_uses_local_timeout(self):
        mock = MagicMock(returncode=0, stdout=self._mk_probe_stdout(45.0))
        with patch("cognithor.core.video_sampling.subprocess.run", return_value=mock) as run_mock:
            resolve_sampling("/tmp/x.mp4", timeout_seconds=5, http_timeout_seconds=30)
        assert run_mock.call_args.kwargs["timeout"] == 5
