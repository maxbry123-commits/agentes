# Enabling the vLLM Backend

Cognithor ships with Ollama as the default local LLM backend — it "just works"
on any Windows/macOS/Linux machine without further setup. vLLM is an **opt-in**
alternative for users with an NVIDIA GPU who want faster inference, native FP4
support (Blackwell / RTX 50xx), or access to models not in the Ollama library.

## Prerequisites

You need:

1. **NVIDIA GPU** with at least 16 GB VRAM. For the best experience:
   - **RTX 5090 (32 GB)** — unlocks NVFP4 quantization, the fastest option
   - **RTX 4090 (24 GB)** — runs FP8 quantization
   - **RTX 4080 / 3090 / 4070 Ti Super (16 GB)** — runs AWQ-INT4 quantization
2. **NVIDIA driver** installed (any modern version from the last 2 years works)
3. **Docker Desktop** installed and running. Download from
   [docker.com](https://www.docker.com/products/docker-desktop). Cognithor will
   not install it for you — the installer needs admin rights and a reboot,
   which Cognithor does not handle.

## Enabling vLLM

1. Start Cognithor normally.
2. Open **Settings → LLM Backends**.
3. Tap **vLLM**. You will see four status cards:
   - **NVIDIA GPU** — detected automatically
   - **Docker Desktop** — detected automatically
   - **vLLM Docker image** — needs a one-time ~10 GB pull
   - **Model** — which model to load
4. If any card is red, fix the underlying issue first (install the missing
   driver, start Docker Desktop, etc.).
5. Tap **Pull image** on Card 3. Progress streams live.
6. Pick a model from Card 4. The star badge (⭐) marks the recommendation for
   your GPU. Models that don't fit your VRAM or require a newer GPU
   architecture are disabled with a tooltip explaining why.
7. Tap **Start vLLM**. First start takes 30–300 seconds depending on model
   size (weights download from HuggingFace).
8. Back in the list view, tap your vLLM row and select **Make active** to
   switch all future chat turns through vLLM.

## Switching Back to Ollama

Settings → LLM Backends → Ollama → **Make active**. The switch is live — no
restart required. vLLM keeps running in the background unless you enable
"Stop vLLM on app close" in settings.

## Troubleshooting

**"Version Mismatch" overlay on launch**: the installer bundled a stale
Flutter build. Install the newer Cognithor release.

**vLLM status card stays red with "No GPU detected"**: run `nvidia-smi` in a
terminal to confirm your driver works. On WSL2 you need the NVIDIA WSL driver
bundle from nvidia.com/drivers — not just the standard Windows driver.

**Docker card stays red**: open Docker Desktop, wait for the whale icon to
stop pulsing (that's the "ready" state).

**Pull fails mid-download**: partial layers are cached. Retry the pull —
Docker will resume from where it stopped.

**Container starts but /health never answers**: the model is probably still
loading. Qwen3.6-27B at FP8 takes ~60 s on an RTX 5090, up to 5 minutes on
slower cards. The setup page shows container logs below the status cards.

**Banner "vLLM offline — fallback to Ollama active"** appears mid-chat: vLLM
has crashed or become unresponsive for 3 consecutive requests. Text chats
transparently route through Ollama; image requests will error out until vLLM
recovers. Check `docker logs <container-id>` for the cause.

**I have a Qwen3.6 model selected but it fails to start**: Ensure
`config.vllm.docker_image` is set to `vllm/vllm-openai:cu130-nightly` (the
default since the Day-1 spike). Earlier stable tags (e.g. v0.19.1) crash
Qwen3.6-27B-NVFP4 at warmup on SM120. Cognithor will adopt a newer tagged
release once `FlashInferCutlassNvFp4LinearKernel` lands upstream.

## Advanced Configuration

`~/.cognithor/config.yaml` section `vllm`:

| Field | Default | Purpose |
|-------|---------|---------|
| `enabled` | `false` | Master on/off |
| `model` | `""` (auto) | HF repo id. Empty → orchestrator picks best per GPU |
| `docker_image` | `vllm/vllm-openai:cu130-nightly` | Override to a specific tag |
| `port` | `8000` | Host port (falls back 8001..8009 if busy) |
| `auto_stop_on_close` | `false` | Stop container when Cognithor quits |
| `skip_hardware_check` | `false` | Override for unusual setups |
| `request_timeout_seconds` | `60` | Per-request timeout |

HF token for gated models: set `huggingface_api_key` at the top level of
`config.yaml` (or via the OS keyring) — Cognithor passes it to the container
automatically as `HF_TOKEN`.

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

### Known limitation: rolling Docker image tag

Cognithor currently pins the vLLM image to `vllm/vllm-openai:cu130-nightly` — a
rolling tag that the vLLM project rebuilds daily. A breaking upstream change can
silently change behavior the next time Docker pulls the image.

**Symptoms of a bad pull**: video requests that worked yesterday return HTTP 500,
or the vLLM container fails to start after a fresh `docker pull`, or Qwen responses
become gibberish.

**Mitigation**:
1. Pin to a specific digest via Docker Desktop's Images panel (or `docker image tag
   vllm/vllm-openai@sha256:<digest> cognithor-pinned-vllm` and override
   `config.vllm.docker_image: cognithor-pinned-vllm` in `~/.cognithor/config.yaml`).
2. Before a fresh `docker pull`, take note of the current digest with
   `docker inspect vllm/vllm-openai:cu130-nightly --format='{{.Id}}'` so you can
   roll back to the previous image via Docker Desktop if the new pull breaks.
3. Watch the [vLLM releases page](https://github.com/vllm-project/vllm/releases)
   — once a tagged release ships the `FlashInferCutlassNvFp4LinearKernel` fix
   for SM120, switch `config.vllm.docker_image` to that stable tag.

This limitation is tracked as a follow-up in the video-input spike findings; a
future Cognithor release will add automatic digest-pinning during the installer
wizard.
