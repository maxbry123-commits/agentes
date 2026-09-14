"""Spike test 1 — extra_body.mm_processor_kwargs.video wire shape.

Sends a minimal video chat completion against the spike vLLM server with
a known-good public video URL and three candidate wire shapes. Records
which shape(s) vLLM accepts and which it rejects with what error. This
output feeds the Day-1 gate decision in docs/superpowers/spikes/.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import httpx

BASE_URL = "http://127.0.0.1:8765/v1"
# 10 sec, 1 MB BigBuckBunny 360p from test-videos.co.uk (returns HTTP 200 from inside container)
VIDEO_URL = (
    "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"
)
MODEL_ID_ENV_KEY = "SPIKE_MODEL_ID"


def load_model_id() -> str:
    import os

    return os.environ.get(MODEL_ID_ENV_KEY, "mmangkad/Qwen3.6-27B-NVFP4")


def post_chat(payload: dict[str, Any]) -> tuple[int, dict[str, Any] | str]:
    with httpx.Client(timeout=180.0) as client:
        r = client.post(f"{BASE_URL}/chat/completions", json=payload)
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, r.text


def build_base_payload(model_id: str, mm_kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": VIDEO_URL}},
                    {"type": "text", "text": "Beschreibe das Video in einem Satz."},
                ],
            }
        ],
        "max_tokens": 64,
        "temperature": 0.0,
        "extra_body": {"mm_processor_kwargs": mm_kwargs},
    }


CANDIDATES: dict[str, dict[str, Any]] = {
    "A_nested_video_fps": {"video": {"fps": 1}},
    "B_nested_video_num_frames": {"video": {"num_frames": 8}},
    "C_flat_fps": {"fps": 1},
    "D_flat_num_frames": {"num_frames": 8},
    "E_empty": {},
    "F_nested_video_empty": {"video": {}},
}


def main() -> int:
    model_id = load_model_id()
    print(f"[wire-shape] model={model_id}")
    print(f"[wire-shape] video_url={VIDEO_URL}")
    print()

    results: dict[str, dict[str, Any]] = {}
    for name, mm in CANDIDATES.items():
        print(f"=== {name}: mm_processor_kwargs={json.dumps(mm)}")
        try:
            status, body = post_chat(build_base_payload(model_id, mm))
        except Exception as e:
            status, body = 0, f"EXCEPTION: {type(e).__name__}: {e}"
        err_hint = ""
        if isinstance(body, dict) and "error" in body:
            err_hint = str(body["error"])[:240]
        elif isinstance(body, str):
            err_hint = body[:240]
        else:
            err_hint = "(accepted)"
        print(f"    -> status={status} {err_hint}")
        results[name] = {"status": status, "body_hint": err_hint}

    print()
    print("=== SUMMARY ===")
    accepted = [k for k, v in results.items() if v["status"] == 200]
    rejected = [k for k, v in results.items() if v["status"] != 200]
    print(f"accepted: {accepted}")
    print(f"rejected: {rejected}")
    return 0 if accepted else 2


if __name__ == "__main__":
    sys.exit(main())
