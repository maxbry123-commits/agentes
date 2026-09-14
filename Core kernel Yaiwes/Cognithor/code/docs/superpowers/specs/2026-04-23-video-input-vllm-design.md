# Video Input via vLLM — Design Spec

**Status:** Day-1 spike complete (2026-04-23), gate **APPROVED**. Ready for implementation plan Tasks 2–23.

**Goal:** Let Cognithor users attach or paste videos in the chat, have them analyzed end-to-end by Qwen3.6-27B (or any vLLM-served VLM with video support), and receive a response referring to visual content across time. No frame-extraction workarounds — this rides on vLLM's native `video_url` content-item, which Qwen3.6-27B's modelcard explicitly supports.

**Non-goal:** Video generation. Video output. Frame-extraction fallbacks when vLLM is unavailable (Ollama has no vision, let alone video — video requests on a non-vLLM backend hard-error). YouTube URL support (Qwen's examples use direct `.mp4` URLs; YouTube needs `yt-dlp` and cookie-handling which is out of scope).

---

## Approved Decisions (Brainstorming Outcomes)

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Scope:** URL paste + local file upload (Option B) | URL-only is too limiting — the important video use-cases (screencasts, meetings, drones) are local files |
| 2 | **Transport for local uploads:** local HTTP file-server (Option B2) | Stable, no reliance on vLLM `file://` support. Matches how external URLs already work — vLLM fetches via HTTP |
| 3 | **Frame sampling:** adaptive buckets via `ffprobe` duration detection (Option Z) | Fixed count (X) wastes detail on short clips, fixed fps (Y) blows context on long videos. Adaptive is the only option that gives sensible behavior across the full 5 s – 60 min range |
| 4 | **Flutter attach UX:** Paperclip menu with explicit "Video hochladen" entry (Option A) | Discoverability without disruption. Dedicated video button (B) is too intrusive for the 95 % who never use it; automatic MIME-detection (C) hides the capability |
| 5 | **Fail-flow:** Hybrid pre-flight gate + post-send error (Option Z) | Cheap local pre-flight (is vLLM the active backend?) prevents wasted uploads; runtime breaker state checked on send for DEGRADED. Videos never silent-fallback to Ollama |
| 6 | **Cleanup policy:** Session-lifetime + 24 h hard cap (Option Y) | Follow-up questions about the same video work during the session; nothing accumulates forever |
| 7 | **Single video per chat turn** (not multi-video) | vLLM's `extra_body.mm_processor_kwargs.video` is one config, not per-video. Allowing 2+ videos in a turn would force us to either use the most-conservative bucket (losing detail on short clips) or reject the request. YAGNI: single-video covers every realistic use-case for v1 |

---

## Spike Findings (2026-04-23) — Plan Amendments

See [`docs/superpowers/spikes/2026-04-23-video-input-vllm-spike-findings.md`](../spikes/2026-04-23-video-input-vllm-spike-findings.md) for the full run log.

| # | Original assumption | Reality | Plan change |
|---|---------------------|---------|-------------|
| A | `vllm/vllm-openai:v0.19.1` runs Qwen3.6-27B-NVFP4 | v0.19.1 **crashes at warmup** — FLA Gated-Delta-Net tensor format mismatch + NVFP4 loader missing `FlashInferCutlassNvFp4LinearKernel` on SM120. Fix is only in `cu130-nightly`. | **Pin base image to `vllm/vllm-openai:cu130-nightly`**. Tagged releases adopted when `FlashInferCutlassNvFp4LinearKernel` lands in a stable tag. |
| B | `extra_body.mm_processor_kwargs.video.{fps,num_frames}` is the correct shape | Confirmed ✅ — vLLM accepted this AND a flat form. Spec's nested shape is safe and preferred (more explicit). | No change. |
| C | vLLM may have a `--allowed-media-domains` policy that blocks `host.docker.internal` | No allowlist enforced by default ✅. Any HTTP URL is fetched by vLLM's client. | No `--allowed-media-domains` flag needed in `VLLMOrchestrator`. |
| D | Public HTTPS video URLs are a reliable fallback path | ❌ Some CDNs (Google Cloud Storage public bucket) return 403 to vLLM's container HTTP client. Local-HTTP-upload is **empirically the safer path**. | User-facing fail message for 4xx during URL paste must hint at the option to upload instead. Other spec decisions unchanged. |
| E | 27B model fits on 32 GB RTX 5090 at native 262K context | ❌ Even NVFP4 weights = 28.25 GiB. `--gpu-memory-utilization 0.94` is the ceiling (free VRAM is 30.12 GiB after Windows compositor overhead). With `--cpu-offload-gb 4` we stabilize at **max-model-len 16384**, max-num-seqs 2. | Default profile for 32 GB class: 16 K context, 2 parallel sequences. Document the trade-off (max 60-sec-at-fps=4 video per turn, which covers 95 % of use cases). |
| F | ffprobe HTTP timing < 2 s budget is realistic | Not empirically tested in the spike (local-HTTP server wasn't spun up). Spec's 30 s default HTTP timeout remains conservative. | Move empirical verification to Task 2 (VideoSamplingResolver). If budget proves wrong, tune there. |

**Working baseline (single-GPU RTX 5090, 32 GB):**

```bash
docker run -d --name vllm --gpus all \
  --add-host host.docker.internal:host-gateway \
  -v cognithor-hf-cache:/root/.cache/huggingface \
  -p 8000:8000 \
  vllm/vllm-openai:cu130-nightly \
  --model mmangkad/Qwen3.6-27B-NVFP4 \
  --max-model-len 16384 \
  --max-num-seqs 2 \
  --max-num-batched-tokens 2048 \
  --gpu-memory-utilization 0.94 \
  --cpu-offload-gb 4 \
  --enforce-eager \
  --reasoning-parser qwen3 \
  --trust-remote-code \
  --media-io-kwargs '{"video": {"num_frames": -1}}'
```

Load time ~2 min. VRAM stabilizes at 30.9 / 32 GiB. End-to-end video inference (8 frames from BigBuckBunny 10 s 1 MB clip + German description prompt) produces a grounded response.

---

## Architecture

Video input rides on the existing `VLLMBackend` from PR #137 — no new backend, no architectural shift. Three new modules:

- **`MediaUploadServer`** (`src/cognithor/channels/media_server.py`) — minimal FastAPI app with a static-mount on `/media/<uuid>.ext`, running on its own localhost port (not the main Cognithor API port). vLLM inside the Docker container fetches uploaded videos via `http://host.docker.internal:<media-port>/media/<uuid>.mp4`.
- **`VideoSamplingResolver`** (`src/cognithor/core/video_sampling.py`) — pure function wrapping `ffprobe` for duration detection, with a bucket table that maps duration → `{"fps": N}` or `{"num_frames": N}`. Graceful fallback to `{"num_frames": 32}` on any probe failure.
- **`VideoCleanupWorker`** (`src/cognithor/gateway/video_cleanup.py`) — async task in the Gateway tracking per-session uploads in an in-memory `dict[session_id, list[uuid]]`. Deletes files on session close. Periodic 60 s sweep enforces the 24 h hard TTL. App-start sweep scans the uploads directory and removes any file not referenced by a live session + older than the TTL. No persistent state — if Cognithor crashes with uploads in flight, the next app-start sweep catches them via TTL. Keeps the worker to ~80 LOC.

Existing code changed:

- `VLLMBackend.chat()` — new `video: dict | None = None` kwarg alongside the existing `images`. Shape: `{"url": str, "sampling": {"fps": float} | {"num_frames": int}}`. A sibling helper `_attach_video_to_last_user()` produces **one** OpenAI `video_url` content item (single video per turn, Decision 7) and attaches the pre-resolved sampling payload to `extra_body.mm_processor_kwargs.video`.
- `VLLMOrchestrator.start_container()` — `docker run` command gains `--media-io-kwargs '{"video": {"num_frames": -1}}'` so per-request sampling via `extra_body.mm_processor_kwargs` actually takes effect. Also adds `--add-host host.docker.internal:host-gateway` for the Docker-in-Linux case (requires Docker ≥ 20.10; documented in prerequisites).
- `WorkingMemory` — new `video_attachment: dict | None` field holding `{"url": str, "sampling": {"fps": 2} | {"num_frames": 32}}`. `Planner.formulate_response()` routes to `config.vision_model_detail` when `image_attachments` is non-empty **or** `video_attachment` is not None.
- Gateway — at the start of each chat turn, extracts at-most-one video-extension attachment from the incoming message into `WorkingMemory.video_attachment` (rejects additional videos with an error to the client), and registers the upload with `VideoCleanupWorker` under the current `session_id`.
- Flutter `chat_input.dart` — Paperclip becomes a `PopupMenuButton` with entries for Image / Video / File / URL. "Video hochladen" is disabled once the pending message already holds a video attachment (visual tooltip: "Ein Video pro Nachricht. Sende oder entferne erst das aktuelle.").

Video requests never fall back to Ollama — if vLLM is DEGRADED, the `chat()` path raises `VLLMNotReadyError` and the Flutter Gateway renders a red error bubble. This matches the existing image-request fail-flow from PR #137.

---

## Components

### Media Layer

**`src/cognithor/channels/media_server.py` — ~120 LOC, new**

```python
class MediaUploadServer:
    """Serves uploaded media to the vLLM Docker container over localhost.

    Separate FastAPI app on its own port so the main Cognithor API retains
    its auth/CORS policy, while vLLM can fetch without auth.
    """
    def __init__(self, config: CognithorConfig) -> None: ...
    async def start(self) -> int: ...       # returns bound port
    async def stop(self) -> None: ...
    def save_upload(self, data: bytes, ext: str) -> str:
        """Store `data` in `~/.cognithor/media/vllm-uploads/<uuid>.<ext>`,
        return the uuid.

        Raises:
            MediaUploadTooLargeError: if `len(data)` exceeds `video_max_upload_mb`.
            MediaUploadUnsupportedFormatError: if `ext` not in allow-list.
            MediaUploadQuotaExceededError: if the upload would exceed `video_quota_gb`
                AND LRU eviction of older files wouldn't free enough space.

        Before writing, if `len(data) + current_dir_size > quota`, oldest files
        (by mtime) are evicted one by one until there is room.
        """
    def public_url(self, uuid: str) -> str:
        """Return `http://host.docker.internal:<port>/media/<uuid>.<ext>`"""
    def delete(self, uuid: str) -> None: ...
```

- Binds to `127.0.0.1:0` (ephemeral port). The orchestrator receives the port at container-start time and includes it in the `docker run` command as `--env COGNITHOR_MEDIA_URL=http://host.docker.internal:<port>`.
- `save_upload` checks the 500 MB hard cap AND the 5 GB quota. Over quota → LRU-evict the oldest file until space is free, log the eviction.
- Allowed extensions: `.mp4`, `.webm`, `.mov`, `.mkv`, `.avi`. Anything else raises `LLMBadRequestError`.
- Authentication: **none**. The server only binds on `127.0.0.1`, so only processes on the host machine can reach it — and the only intended process is the Cognithor-managed Docker container on the same machine. Documented explicitly so security reviewers don't flag it.

### Video Sampling

**`src/cognithor/core/video_sampling.py` — ~80 LOC, new**

```python
@dataclass(frozen=True)
class VideoSampling:
    """Resolved per-video sampling spec, ready to drop into `extra_body.mm_processor_kwargs.video`."""
    fps: float | None = None
    num_frames: int | None = None
    duration_sec: float | None = None  # for logging/UI, not sent to vLLM

    def as_mm_kwargs(self) -> dict:
        """Returns the payload vLLM expects, e.g. {"fps": 2.0} or {"num_frames": 32}."""


def resolve_sampling(
    source: str,  # local path OR http(s) URL
    *,
    ffprobe_path: str = "ffprobe",
    timeout_seconds: int = 5,
    override: Literal["adaptive","fixed_32","fixed_64","fps_1"] = "adaptive",
) -> VideoSampling:
    """Run ffprobe for duration, apply bucket rules, return a VideoSampling."""
```

**Bucket rules (for `override="adaptive"`):**

| Duration | Sampling | Max frames | Approx. tokens |
|----------|----------|------------|----------------|
| < 10 s | `fps=3` | ~30 | ~9 K |
| 10 s – 30 s | `fps=2` | ~60 | ~18 K |
| 30 s – 2 min | `fps=1` | up to 120 | ~36 K |
| 2 min – 5 min | `num_frames=64` | 64 fix | ~19 K |
| 5 min – 15 min | `num_frames=32` | 32 fix | ~10 K |
| > 15 min | `num_frames=32` + UI banner recommending splitting | 32 fix | ~10 K |

For `override="fixed_32"` / `"fixed_64"` / `"fps_1"` → skip ffprobe, return constant.

**Fallback chain:**
1. `ffprobe` not found in `$PATH` (and not bundled) → `VideoSampling(num_frames=32)`
2. `ffprobe` timeout (5 s) → `VideoSampling(num_frames=32)`, log `video_duration_detection_timeout`
3. `ffprobe` succeeds but returns negative / > 86400 / non-parseable duration → `VideoSampling(num_frames=32)`

### Video Cleanup

**`src/cognithor/gateway/video_cleanup.py` — ~80 LOC, new**

No persistent state. In-memory `dict[session_id, list[uuid]]` plus filesystem-based TTL enforcement — simpler and correct even after a crash:

```python
class VideoCleanupWorker:
    def __init__(self, media_dir: Path, ttl_hours: int = 24) -> None:
        self._media_dir = media_dir
        self._ttl_hours = ttl_hours
        self._by_session: dict[str, list[str]] = {}
        self._sweep_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Run TTL sweep once at start (catches files left over from a crashed
        previous run — pure filesystem-mtime-based, no registry needed), then
        kick off the periodic 60 s sweep."""
    async def stop(self) -> None: ...

    def register_upload(self, uuid: str, session_id: str) -> None: ...
    async def on_session_close(self, session_id: str) -> None:
        """Delete all uploads linked to this session."""
    async def _periodic_sweep(self) -> None:
        """Every 60 s: scan media_dir, delete files whose mtime is older than ttl_hours."""
```

**Why no SQLite:** the 24 h TTL sweep is authoritative — any file older than `ttl_hours` gets deleted regardless of session state. Session-close cleanup is a nice-to-have optimization for users who close and reopen Cognithor within the TTL window; if it misses one (e.g. crash before `on_session_close` fires), the TTL sweep picks it up within an hour. No crash-recovery registry needed, ~80 LOC saved.

Quota enforcement is **not** in the cleanup worker — it lives in `MediaUploadServer.save_upload` (LRU-evict when adding a new file would exceed 5 GB, ordered by mtime).

### Backend Layer — `VLLMBackend.chat()` Extension

Add `video: dict | None = None` parameter (single video per turn, Decision 7). Implementation mirrors `_attach_images_to_last_user` from PR #137:

```python
def _attach_video_to_last_user(
    messages: list[dict[str, Any]],
    video: dict[str, Any],  # {"url": "...", "sampling": {"fps": 2}} | {"url": "...", "sampling": {"num_frames": 32}}
) -> tuple[list[dict[str, Any]], dict]:
    """Returns (new_messages, extra_body_mm_kwargs).

    new_messages: last user message gets a {"type":"video_url","video_url":{"url":"..."}}
    content item prepended to the existing text parts.

    extra_body_mm_kwargs: {"mm_processor_kwargs": {"video": {"fps": 2}}}
    — the per-request sampling payload for vLLM, ready to merge into the
    outgoing chat-completion body.
    """
```

Callers pass the video dict with pre-resolved sampling (Gateway resolves via `VideoSamplingResolver` before the call). Why pre-resolved? Separation — the backend shouldn't know about `ffprobe`, it just formats payloads.

Multi-video turns are rejected one layer up: if `WorkingMemory.video_attachment` is already set when the Gateway encounters a second video in the incoming message, it surfaces a user-visible validation error ("Ein Video pro Nachricht") and drops the extra. The backend never sees more than one video.

### Config Layer

Additions to `VLLMConfig`:

```python
class VLLMConfig(BaseModel):
    # ... existing fields ...
    video_sampling_mode: Literal["adaptive", "fixed_32", "fixed_64", "fps_1"] = "adaptive"
    video_ffprobe_path: str = "ffprobe"  # override to absolute path on Windows
    video_ffprobe_timeout_seconds: int = Field(default=5, ge=1, le=30)
    """Local file ffprobe timeout (reads are fast, usually <100 ms)."""

    video_ffprobe_http_timeout_seconds: int = Field(default=30, ge=5, le=120)
    """Remote URL ffprobe timeout. Higher default because HTTP header fetches
    on slow networks or large files can take longer — ffprobe streams the MP4
    header which for some servers + 2 GB files means ~20-30 s just to reach
    the duration metadata."""
    video_max_upload_mb: int = Field(default=500, ge=1, le=5000)
    video_quota_gb: int = Field(default=5, ge=1, le=100)
    video_upload_ttl_hours: int = Field(default=24, ge=1, le=168)
```

### Flutter Layer

- `flutter_app/lib/widgets/chat_input.dart` — `IconButton` for paperclip becomes `PopupMenuButton<String>` with entries: `Bild hochladen / Video hochladen / Datei hochladen / URL einfügen`. The "Video" entry is `enabled: activeBackend == 'vllm'`, tooltip explains the gating when disabled.
- `flutter_app/lib/widgets/chat_bubble.dart` — new branch for `metadata['kind'] == 'video'`: renders a 96×54 thumbnail (first frame extracted by ffmpeg on upload, stored as sidecar `<uuid>.jpg`), filename, `duration + sampling-mode`.
- `flutter_app/lib/providers/chat_provider.dart` — `sendVideo(path)` uploads bytes to the new `/api/media/upload` endpoint, receives back `{uuid, url, duration_sec, sampling}`, adds to message metadata, sends chat request.
- Banner widget at top of `_ModelCard`-style column when the latest video is > 15 min: "Video 32 min — nur 32 Frames werden gesampled. Zerlege in 5-Min-Clips für mehr Detail."

### Dependency: ffmpeg / ffprobe

- **Windows**: bundle ffmpeg + ffprobe in the installer under `%LOCALAPPDATA%\Cognithor\ffmpeg\`. **Use an LGPL-build** (BtbN "ffmpeg-master-latest-win64-lgpl" or Gyan's LGPL variant) — a GPL build would contaminate Cognithor's Apache-2.0 license. Adds ~80 MB to the Windows installer (acceptable relative to the existing 1.5 GB). CI builds the installer with a verification step that greps the included ffmpeg binary metadata for "LGPL" and fails if "GPL" is present.
- **Linux**: expect `ffmpeg` in `$PATH`. Document `apt install ffmpeg` in the user guide. If absent, `VideoSamplingResolver` falls back to `num_frames=32` — functional but sub-optimal.
- **macOS**: same as Linux. `brew install ffmpeg`.

### vLLM Container Launch Flag

`VLLMOrchestrator.start_container()` generates the command below. Flags marked **[spike]** are empirically required on 32 GB consumer GPUs (RTX 5090) per the 2026-04-23 spike; on larger GPUs they can be loosened via `VLLMConfig`.

```bash
docker run -d \
    --gpus all \
    --add-host host.docker.internal:host-gateway \
    -v cognithor-hf-cache:/root/.cache/huggingface \
    -e HF_TOKEN=$token \
    -p $port:8000 \
    --label cognithor.managed=true \
    vllm/vllm-openai:cu130-nightly \
    --model $model \
    --max-model-len $max_model_len \
    --max-num-seqs $max_num_seqs \
    --max-num-batched-tokens $max_num_batched_tokens \
    --gpu-memory-utilization $gpu_memory_utilization \
    --cpu-offload-gb $cpu_offload_gb \
    --enforce-eager \
    --reasoning-parser qwen3 \
    --trust-remote-code \
    --media-io-kwargs '{"video": {"num_frames": -1}}'
```

- `--add-host host.docker.internal:host-gateway` — makes the Docker container able to reach the host's MediaUploadServer port via `http://host.docker.internal:$media_port/...`. On Docker Desktop Windows/macOS it's already provided, but on Linux Docker CE it isn't — this flag makes behavior uniform.
- `--media-io-kwargs '{"video": {"num_frames": -1}}'` — tells vLLM "use no server-side default for video sampling; let each request specify via `extra_body.mm_processor_kwargs.video`". Without this, vLLM falls back to model-default sampling which can't be overridden per request.
- **[spike]** `vllm/vllm-openai:cu130-nightly` (not `:v0.19.1`) — the `v0.19.1` tag is missing `FlashInferCutlassNvFp4LinearKernel` and the `apply_vllm_mapper` fix that stops the Qwen3NextGatedDeltaNet loader from misbinding NVFP4-quantized weights on SM120. The nightly ships both. Adopt a tagged release once it lands upstream.
- **[spike]** `--max-model-len 16384 --max-num-seqs 2 --max-num-batched-tokens 2048` (32 GB GPU profile) — KV-cache init OOMs at native 262 K context with NVFP4 weights. 16 K context comfortably covers 60 s of adaptive-sampled video (30 frames × ~280 tokens + prompt headroom).
- **[spike]** `--gpu-memory-utilization 0.94 --cpu-offload-gb 4` — `0.95` fails the startup check because Windows compositor overhead leaves only ~30.12 GiB free on a 32 GiB card. `0.94` passes; the 4 GiB CPU offload recovers enough room for KV cache blocks. Higher-tier GPUs (A100/H100) can use `0.90` with no offload.
- **[spike]** `--enforce-eager` — disables CUDA graph capture. Graphs need additional VRAM during warmup and this model + setup already sits at 97 % utilization. Eager mode trades ~10 % throughput for stable warmup. Drop once a larger-VRAM profile is available.
- `--reasoning-parser qwen3` — required so vLLM routes Qwen's thinking-mode tokens correctly. Without it, responses come back with empty `content` when `enable_thinking=true` is the implicit default.
- `--trust-remote-code` — Qwen3.6 ships a custom `Qwen3NextGatedDeltaNet` module in the tokenizer/processor config. Required.

---

## Data Flows

### Flow A — Local Video Upload and Send

1. User clicks paperclip → popup menu → "Video hochladen". Popup is only enabled if `provider.activeBackend == 'vllm'` (pre-flight gate, Decision 5).
2. OS file picker opens filtered to `.mp4, .webm, .mov, .mkv, .avi`. Client-side: `file_picker` package.
3. Flutter sends a `POST /api/media/upload` (multipart) to Cognithor. On a separate Cognithor endpoint (not the MediaUploadServer itself — users never hit the media server directly).
4. Cognithor backend `/api/media/upload` handler:
   - Writes bytes to `MediaUploadServer.save_upload(...)` → returns `uuid`
   - Runs `ffmpeg` to extract first frame as `<uuid>.jpg` sidecar (sync, ~100 ms)
   - Runs `VideoSamplingResolver.resolve_sampling(<path>)` → `VideoSampling(fps=1.0, duration_sec=93.5)` (or similar)
   - Returns `{"uuid": "...", "url": "http://host.docker.internal:<p>/media/<uuid>.mp4", "duration_sec": 93.5, "sampling": {"fps": 1.0}, "thumb_url": "/api/media/thumb/<uuid>.jpg"}`
5. Flutter adds a message-metadata entry: `{"kind": "video", "uuid": "...", "filename": "drone.mp4", "duration_sec": 93.5, "sampling": {"fps": 1.0}, "thumb_url": "..."}`. Renders the video bubble preview (thumbnail + meta).
6. User types prompt, hits send. `chat_provider.sendMessage` includes the video metadata in the WebSocket message.
7. Gateway pulls the single video attachment out (rejecting any additional videos with a user-visible validation error), stuffs it into `WorkingMemory.video_attachment` as `{"url": "...", "sampling": {"fps": 1.0}}`. Registers the upload with `VideoCleanupWorker` under the current `session_id`.
8. Planner sees non-None `video_attachment` → selects `config.vision_model_detail` → calls `unified_llm.chat(..., video=working_memory.video_attachment)`.
9. `VLLMBackend.chat()` wraps with circuit breaker, `_attach_video_to_last_user` builds the OpenAI payload:
   ```json
   {
     "model": "Qwen/Qwen3.6-27B-FP8",
     "messages": [
       {"role": "system", "content": "..."},
       {"role": "user", "content": [
         {"type": "video_url", "video_url": {"url": "http://host.docker.internal:4711/media/abc.mp4"}},
         {"type": "text", "text": "Was siehst du in diesem Video?"}
       ]}
     ],
     "extra_body": {
       "mm_processor_kwargs": {"video": {"fps": 1.0}}
     }
   }
   ```
10. vLLM inside the container `GET`s `http://host.docker.internal:4711/media/abc.mp4`, which resolves to the Cognithor host's MediaUploadServer → streams the file → vLLM samples per `fps=1`, feeds frames into Qwen3.6-27B's vision encoder.
11. vLLM responds via HTTP stream → Gateway → Flutter renders tokens as they arrive.

### Flow B — URL Paste

1. User pastes `https://example.com/clip.mp4` as plain text in the chat input.
2. On send, Flutter's `chat_provider` detects the URL via regex (allow-list of video extensions), treats it as a video reference (no upload needed).
3. Cognithor backend receives the chat request with `working_memory.video_attachment = {"url": "https://example.com/clip.mp4", "sampling": null}`.
4. `VideoSamplingResolver.resolve_sampling("https://...")` — `ffprobe` accepts HTTP URLs directly (with the higher `video_ffprobe_http_timeout_seconds` of 30 s) — returns the adaptive bucket sampling.
5. From step 8 onwards, identical to Flow A. The URL is just passed through; vLLM fetches from the remote origin instead of `host.docker.internal`.

### Flow C — Fail Flow (vLLM DEGRADED Mid-Session)

1. User has attached a video and clicks send. Pre-flight passed (vLLM was active when Paperclip was opened).
2. `VLLMBackend.chat()` inside `CircuitBreaker.call(...)` — breaker may be `CLOSED`, `OPEN`, or `HALF_OPEN`.
3. If `OPEN` (or raises `VLLMNotReadyError` on actual send): `UnifiedLLMClient` catches, inspects the request kind.
4. Because `video_attachment` is not None, **no silent fallback** to Ollama. The error propagates as a red bubble in chat:
   ```
   ⚠ vLLM offline — Video kann nicht verarbeitet werden.
   Versuch's in ~X s erneut oder starte vLLM neu unter Settings → LLM Backends.
   ```
5. The user can retry. After `recovery_timeout` (60 s), the next send probes vLLM; success → back to normal.

### Flow D — Session Close / Cleanup

1. User closes the chat tab or closes Cognithor entirely.
2. Gateway calls `video_cleanup_worker.on_session_close(session_id)`.
3. Worker reads `self._by_session[session_id]` (in-memory), deletes each referenced file + its sidecar thumbnail, removes the session entry.
4. Separate periodic sweep (60 s interval) deletes any file in `media_dir` whose mtime is older than `ttl_hours` (24 h default) — session-independent, authoritative.
5. App start: the sweep runs once immediately before entering the 60 s loop, catching any files left over from a crashed previous run (their mtime is already > 24 h or will be shortly). No registry, no orphan concept — the filesystem mtime IS the source of truth.

---

## Error Handling

### Error Hierarchy Additions

- `MediaUploadError(LLMBackendError)` — base for upload issues.
  - `MediaUploadTooLargeError(MediaUploadError)` — over `video_max_upload_mb`.
  - `MediaUploadUnsupportedFormatError(MediaUploadError)` — extension not in allow-list.
  - `MediaUploadQuotaExceededError(MediaUploadError)` — would exceed `video_quota_gb` even after LRU eviction (never happens unless the single upload itself is larger than the quota).

### Setup-Time Errors

- `MediaUploadServer.start()` port bind fails → logged, server disabled, video uploads return `503 Service Unavailable`. vLLM still works for images.
- `ffprobe` missing at resolver call time → fallback to `num_frames=32`, log once per Cognithor session.
- `ffmpeg` missing at upload thumbnail generation → skip thumbnail, bubble shows a generic 🎬 icon instead. Not a fatal error.

### Runtime Errors

- vLLM returns HTTP 400 "context length exceeded" because a video exploded the token budget (e.g., custom model with different token-per-frame ratio than we expected) → propagates as `LLMBadRequestError` → red bubble with recovery hint: "Try a shorter video clip or set `vllm.video_sampling_mode: fixed_32` in config."
- Container started without the `--add-host host.docker.internal:host-gateway` flag (e.g., someone ran `docker run` manually, `reuse_existing()` adopts it) → vLLM inside the container can't resolve `host.docker.internal` on Linux, fetches fail with DNS error → `VLLMNotReadyError` with recovery hint: "Restart vLLM from LLM Backends settings to pick up host-gateway config."
- URL paste but the remote server returns 404 / 5xx when vLLM tries to fetch → vLLM raises its own error → we pass through as `VLLMNotReadyError` with a hint about checking the URL.

### Circuit Breaker (reuses existing `cognithor.utils.circuit_breaker.CircuitBreaker`)

No changes to the breaker itself. `MediaUploadError` subclasses are added to `excluded_exceptions` on the vLLM breaker (upload errors are our problem, not vLLM's fault), alongside `LLMBadRequestError`.

### Privacy / Security

- `MediaUploadServer` binds `127.0.0.1` only. Never exposed on a non-loopback interface. Documented explicitly.
- Sidecar thumbnails are deleted alongside the video on cleanup.
- Uploaded files live under `~/.cognithor/media/vllm-uploads/` with user-only read permissions: `0o600` on POSIX (`chmod 600`), and a restrictive ACL on Windows (inherits from `%LOCALAPPDATA%\Cognithor\` which is already user-scoped by default).

---

## Testing Strategy

### Unit Layer (GitHub Actions, free runners)

- **`tests/test_core/test_video_sampling.py`** — `VideoSamplingResolver` against a mocked `subprocess.run` for ffprobe
  - Real ffprobe JSON output → correct bucket
  - ffprobe missing → fallback to `num_frames=32`
  - ffprobe timeout → fallback
  - ffprobe returns negative / absurd duration → fallback
  - `override="fixed_32"` skips ffprobe entirely
  - All 6 bucket boundaries (< 10 s, 10–30 s, 30 s – 2 min, 2–5 min, 5–15 min, > 15 min) have a dedicated test
- **`tests/test_core/test_vllm_backend_video.py`** — `VLLMBackend.chat(video=...)` against `pytest-httpx`
  - Single video → correct `video_url` content item + `extra_body.mm_processor_kwargs.video` in outgoing payload
  - Video + image mixed → both content items present in last user message, video's `extra_body.mm_processor_kwargs.video` is set
  - Video only, no text → the text part stays empty-string (verify vLLM accepts this; fallback: synthetic single-space text)
- **`tests/test_channels/test_media_server.py`** — `MediaUploadServer` against a `TestClient`
  - Upload within size cap → success, file on disk
  - Upload over 500 MB → 413 Payload Too Large
  - Upload unsupported extension → 400
  - Quota exceeded → oldest file LRU-evicted, log message, new file saved
  - `public_url()` returns the expected `host.docker.internal` URL
- **`tests/test_gateway/test_video_cleanup.py`** — worker
  - `register_upload` → uuid appears in `_by_session[session_id]`
  - `on_session_close` deletes all files linked to the session, removes the session entry
  - Periodic sweep deletes files whose mtime is older than `ttl_hours` — independent of session state (tested by patching `os.path.getmtime`)
  - Start-up sweep catches leftover files from a crashed previous run (tested by creating old-mtime files in a tmp dir before `worker.start()`)

### Integration Layer

- **`tests/test_integration/test_vllm_video_fake_server.py`** — extends the fake vLLM server from PR #137 to return a stubbed video response. Verifies that `VLLMBackend.chat(video={"url": ..., "sampling": ...})` produces a wire-shape that the fake server can parse and respond to.

### Flutter Layer

- **`test/widgets/chat_input_video_menu_test.dart`** — paperclip opens popup menu, "Video hochladen" disabled when `activeBackend != 'vllm'`.
- **`test/widgets/chat_bubble_video_test.dart`** — video-kind metadata renders thumbnail + filename + duration.
- Manual-only: actual file upload dialog flow (integration-tests via `flutter_driver` are out of scope).

### Cross-Repo Guard

- **`tests/test_ffmpeg_bundled.py`** — at CI build time (Windows installer only), verify the bundled `ffmpeg.exe` and `ffprobe.exe` report `LGPL` in their `-version` output. Fail the build if `GPL` appears. Prevents a copyleft-contaminated Cognithor release.

### Manual Smoke Tests

Added to `docs/vllm-manual-test.md` (from PR #137) as a new section:

- **Upload flow**: drone_clip.mp4 (42 s) → upload → bubble shows thumbnail + `0:42 · fps=2` → "What happens at 0:30?" → Qwen responds correctly
- **URL paste**: paste `https://qianwen-res.oss-accelerate.aliyuncs.com/...mp4` → no upload step → correct response
- **Long video**: upload 32-min video → banner appears → Qwen responds to rough timeline questions
- **Fail flow**: `docker stop $(docker ps -q --filter label=cognithor.managed=true)` mid-chat → video request → red error bubble, no Ollama fallback
- **Cleanup**: close Cognithor, verify `~/.cognithor/media/vllm-uploads/` is empty

### Coverage Target

≥ 90 % on `video_sampling.py`, `media_server.py`, `video_cleanup.py`, and the video paths in `vllm_backend.py`. Flutter ~70 % analogous to existing screens.

---

## Dependencies & Prerequisites

**Python (in-repo):**
- No new pip packages. Uses existing `httpx`, `fastapi`, `pydantic`, `structlog`, stdlib `subprocess` / `asyncio` / `uuid` / `pathlib`.

**User environment:**
- `ffmpeg` + `ffprobe` — **bundled on Windows** (LGPL build in installer), expected in `$PATH` on Linux/macOS (documented in the user guide). Graceful degradation when absent: videos still work, just with fixed `num_frames=32` sampling and no thumbnails.
- **Docker Engine ≥ 20.10** (released Dec 2020). Earlier versions don't recognize `host-gateway` as a value for `--add-host` and the container can't reach the local media server on Linux. On Docker Desktop (Windows/macOS) the flag is redundant but harmless. Documented as a prerequisite bump in the user guide.
- vLLM (already a prerequisite from PR #137).
- A vLLM-served model with video capability. Currently confirmed: `Qwen/Qwen3.6-27B` variants, `Qwen/Qwen2.5-VL-7B-Instruct`, `Qwen/Qwen3.6-35B-A3B` variants. Models without video support return HTTP 400 on video requests — handled via `LLMBadRequestError`.

**CI:** unchanged — no GPU, no real video processing, all tests mock `ffprobe` and vLLM.

---

## Scope Boundaries

**In scope:**
- `MediaUploadServer` + cleanup worker + sampling resolver
- `VLLMBackend.chat(video=...)` extension (single video) + per-request `extra_body.mm_processor_kwargs.video`
- Flutter paperclip popup-menu + video bubble + URL detection on paste
- `docker run` flag additions (`--media-io-kwargs`, `--add-host host.docker.internal:host-gateway`)
- Session-lifetime + 24 h cleanup
- Bundled LGPL ffmpeg on Windows installer
- User-facing documentation in `docs/vllm-user-guide.md` (video section) and `docs/vllm-manual-test.md` (video smoke tests)

**Out of scope:**
- YouTube URL support (needs `yt-dlp`, separate auth/cookie handling, rate-limit concerns).
- Video generation or editing.
- Audio-only tracks (Qwen3.6-27B is vision-centric; audio is not parsed).
- Per-session quota (5 GB is global across all sessions).
- WebM VP9 and AV1 specifically — should work because they're in LGPL ffmpeg, but not explicitly listed in manual test matrix.
- Streaming video input (live feed): vLLM accepts only complete-file URLs, not rtmp/hls/webrtc streams.
- Multiple videos per single chat turn: **not supported in v1** (Decision 7). The API is single-video (`video: dict | None`), and the Gateway rejects a second video on the same turn with a user-visible validation error. Adding multi-video later requires either accepting a common-sampling trade-off or solving the `extra_body.mm_processor_kwargs.video` per-video problem at the vLLM layer — separate design work if the use-case materializes.

---

## Estimate

**~1.5 calendar weeks (7–8 working days), single engineer.**

- **Day-1 spike** — verify `extra_body.mm_processor_kwargs.video` shape + vLLM media-domain fetch policy + ffprobe HTTP timing (see Open Questions): 0.5 day
- `VideoSamplingResolver` + unit tests: 1 day
- `MediaUploadServer` + unit tests + integration wiring: 1 day
- `VideoCleanupWorker` (simplified: in-memory + filesystem TTL, no SQLite) + unit tests + session hooks: 0.5 day
- `VLLMBackend.chat(video=...)` + `_attach_video_to_last_user` + integration test against the fake server: 1 day
- Config extension (`VLLMConfig` additions) + `VLLMOrchestrator` `docker run` flag changes: 0.5 day
- Flutter paperclip popup-menu + video bubble + URL-paste detection + "Ein Video pro Nachricht"-state + widget tests: 1.5 days
- Windows installer ffmpeg bundling + CI verification step: 0.5 day
- Docs (user-guide section + manual-test matrix entries) + CHANGELOG: 0.5 day
- Manual smoke test on real NVIDIA hardware + fixes: 0.5 day
- Buffer / polish / PR cycle / spec-reviewer loops: 0.5 day

Total ≈ 7.5 days = **1.5 weeks** calendar. Day-1 spike is a go/no-go gate: if `extra_body` shape or media-domain policy requires a significantly different approach, the estimate and design come back to the table before further work.

---

## Open Questions Deferred to Plan

Three of these are genuine implementation-time unknowns that MUST be resolved before serious code is written (the first implementation task is a dedicated spike). The others are lower-risk polish questions.

### High-priority spikes (plan Day 1) — RESOLVED 2026-04-23

- ✅ **`extra_body.mm_processor_kwargs.video` exact wire shape**: verified against `mmangkad/Qwen3.6-27B-NVFP4` on `cu130-nightly`. Nested shape `{"video": {"fps": N}}` / `{"video": {"num_frames": N}}` accepted; flat form also accepted. Spec's nested shape is safe.
- ✅ **vLLM `--allowed-media-domains` / fetch policy**: no allowlist enforced. Arbitrary HTTPS URLs work. Separately, *some CDNs* (observed: GCS public buckets) return 403 to vLLM's container client — handled by spec's local-HTTP-upload path.
- ⏸️ **`ffprobe` remote-HTTP behavior**: deferred to Task 2 (`VideoSamplingResolver`). The 30 s HTTP timeout default remains; empirical calibration happens during unit-test-driven implementation.

### Lower-priority, plan-level details

- **ffmpeg LGPL-build source**: pick between BtbN's and Gyan's LGPL builds based on which has smaller size + broader codec support at implementation time.
- **Session-ID propagation into `MediaUploadServer`**: the media server itself shouldn't know about sessions (single responsibility), so the upload endpoint in `channels/api.py` is where `session_id` is captured from the WebSocket context and passed to `VideoCleanupWorker.register_upload`.
- **vLLM response for "video + empty text"**: if the user attaches a video without typing a prompt, the last user message has only a `video_url` content item. Some LLM APIs reject messages with no text. Test at implementation time; fallback is to inject a synthetic single-space text part.
- **Thumbnail frame selection**: currently specced as "first frame". First frame is often a black intro / logo. Consider extracting at 10% or midpoint instead. Pure UX polish, not a correctness question.
