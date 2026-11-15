# vLLM Backend — Manual Smoke Test

The Python + Flutter unit tests and the fake-server integration test cover
everything except the real-hardware path. Before cutting a release that
touches the vLLM backend, run this recipe once on a dev machine with a real
NVIDIA GPU and Docker Desktop.

**Time:** ~30 minutes end-to-end.

## Test Matrix

Pick the row matching your dev hardware and run those steps:

| GPU | VRAM | Expected recommended model | Test sections |
|-----|------|----------------------------|---------------|
| RTX 5090 | 32 GB | `mmangkad/Qwen3.6-27B-NVFP4` | All |
| RTX 4090 | 24 GB | `cyankiwi/Qwen3.6-27B-AWQ-INT4` or fallback | 1–5 |
| RTX 4080 / 4070 Ti Super | 16 GB | `Qwen/Qwen2.5-VL-7B-Instruct` (tested fallback) | 1–4 |

## 1. Fresh install

- Uninstall any previous Cognithor.
- Wipe `~/.cognithor/config.yaml` (or rename it as backup).
- Run the new installer.
- Launch Cognithor. Expect: Flutter UI reaches the main screen. No version-
  mismatch overlay, no config crash.

## 2. Hardware + Docker detection

- Settings → LLM Backends → tap **vLLM**.
- Expect: Cards 1 and 2 turn green within 2 seconds (the polling interval).
  Card 1 shows the correct GPU name, VRAM, and compute capability string.
- If Docker Desktop is not running, start it and wait — Card 2 turns green
  when ready.

## 3. Image pull

- Tap **Pull image**.
- Expect: progress bar advances steadily. Total download ~10 GB.
- Expect: after completion, Card 3 turns green; Card 4 enables.

## 4. Model picker + start (quick path — Qwen2.5-VL-7B)

- Card 4: expect the model dropdown to populate. Qwen2.5-VL-7B is always
  marked "tested" and should show the star badge for any non-Blackwell GPU.
- Select it. Tap **Start vLLM**.
- Expect: within 120 seconds, Card 4 turns green with "Running: Qwen/
  Qwen2.5-VL-7B-Instruct".
- Back in the list view, tap vLLM, tap **Make active**.

## 5. End-to-end chat with vision

- Open the chat screen.
- Attach an image (any PNG) via the paperclip button.
- Ask: "What do you see in this image?"
- Expect: answer comes back within 5–10 seconds, describing the image.
- Close the chat screen and reopen — state persists.

## 6. Fail-flow verification

- In a terminal: `docker stop $(docker ps -q --filter label=cognithor.managed=true)`
- In Cognithor chat, send a text-only message: "hello"
  - Expect: within 2–3 requests, the "⚠ vLLM offline — fallback to Ollama
    active" banner appears. Reply comes from Ollama.
- Send an image request.
  - Expect: red error bubble "vLLM offline — cannot process image".
- In terminal: `docker start <container-id>`
  - Expect: within ~60 seconds (the CircuitBreaker `recovery_timeout`), the
    next text request goes through vLLM again; banner dismisses.

## 7. Lifecycle toggles

- Settings → LLM Backends → vLLM → enable "Keep vLLM running after app close"
- Close Cognithor entirely.
- Verify: `docker ps | grep cognithor.managed` — container still running.
- Reopen Cognithor → status shows "Running" immediately (no restart).
- Disable the toggle. Close Cognithor.
- Verify: `docker ps | grep cognithor.managed` — no result (container was
  stopped on shutdown).

## 8. Blackwell-specific (RTX 5090 only)

- Edit `~/.cognithor/config.yaml` → set `vllm.docker_image: "vllm/vllm-openai:nightly"`.
- Back in the setup screen, pull the nightly image (replaces the old one).
- Pick `mmangkad/Qwen3.6-27B-NVFP4` (star-badged on Blackwell).
- Start. Expect: model loads in ~30–60 seconds.
- Chat with vision. Expect: tokens stream noticeably faster than FP8 on the
  same hardware (NVFP4 uses native tensor cores).

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

## Reporting

If any step fails, capture:
- Contents of `~/.cognithor/log/cognithor.log` (last 200 lines)
- Output of `docker logs <container-id>`
- Screenshot of the relevant Flutter screen

File bugs against the `vllm-backend` label on GitHub.
