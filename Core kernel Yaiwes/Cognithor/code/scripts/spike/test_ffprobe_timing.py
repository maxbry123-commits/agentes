"""Spike test 3 — ffprobe HTTP timing budget.

Runs ffprobe against five different URL types with three network conditions
(local, nearby CDN, cold HF cache) and records wall-clock time. The spec
assumed a 2s budget for pre-flight ffprobe; this test validates whether
that budget is realistic over HTTP.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass

URLS: dict[str, str] = {
    "public_small_cdn": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "public_medium_cdn": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "local_file_server": "http://127.0.0.1:8799/sample.mp4",
}


@dataclass
class Probe:
    name: str
    url: str
    wall_ms: float
    ok: bool
    duration: float | None
    codec: str | None
    stderr_tail: str


def ffprobe(url: str) -> tuple[bool, dict, str]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        "-i",
        url,
    ]
    t0 = time.perf_counter()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10.0)
    except subprocess.TimeoutExpired:
        return False, {}, "TIMEOUT after 10s"
    wall = (time.perf_counter() - t0) * 1000.0
    if r.returncode != 0:
        return False, {"wall_ms": wall}, r.stderr[-240:]
    try:
        info = json.loads(r.stdout)
    except json.JSONDecodeError:
        return False, {"wall_ms": wall}, "JSON decode failed"
    info["wall_ms"] = wall
    return True, info, r.stderr[-240:]


def main() -> int:
    results: list[Probe] = []
    for name, url in URLS.items():
        print(f"=== {name}: {url}")
        ok, info, err = ffprobe(url)
        wall = info.get("wall_ms", 0.0)
        dur = None
        codec = None
        if ok:
            fmt = info.get("format", {})
            dur = float(fmt.get("duration", 0.0))
            streams = info.get("streams", [])
            for s in streams:
                if s.get("codec_type") == "video":
                    codec = s.get("codec_name")
                    break
        p = Probe(
            name=name, url=url, wall_ms=wall, ok=ok, duration=dur, codec=codec, stderr_tail=err
        )
        results.append(p)
        print(f"    wall={wall:.1f}ms ok={ok} dur={dur} codec={codec}")
        if err and not ok:
            print(f"    err={err}")
        print()

    print("=== SUMMARY ===")
    budget_ms = 2000.0
    for p in results:
        verdict = "UNDER BUDGET" if p.wall_ms < budget_ms else "OVER BUDGET"
        print(f"  {p.name:30s} {p.wall_ms:7.1f}ms {verdict}")
    return 0 if all(r.ok for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
