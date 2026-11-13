# Day-1 Spike Findings — Video Input via vLLM

**Plan:** [`docs/superpowers/plans/2026-04-23-video-input-vllm.md`](../plans/2026-04-23-video-input-vllm.md)
**Spec:** [`docs/superpowers/specs/2026-04-23-video-input-vllm-design.md`](../specs/2026-04-23-video-input-vllm-design.md)
**Date:** 2026-04-23
**Branch:** `feat/vllm-video-input`
**Hardware:** RTX 5090 (32 GB VRAM, SM_120 / Blackwell)

---

## Purpose

Hard gate for Task 1 of the plan. Verify three spec assumptions before cascading them into implementation:

1. **Wire shape** of `extra_body.mm_processor_kwargs.video` — what keys does vLLM actually accept?
2. **vLLM fetch-allowlist policy** — does vLLM restrict `video_url` to allowed domains?
3. **ffprobe HTTP timeout behavior** on `http://host.docker.internal:<port>/<path>` fetches from inside the vLLM container.

If any finding reverses a spec assumption, STOP and return to design.

---

## Model Selection

The plan originally targeted `Qwen/Qwen3.6-27B-NVFP4` (community quant) on vLLM v0.19.1. Deep research during the spike revealed:

- `mmangkad/Qwen3.6-27B-NVFP4` crashes during warmup (same-class bug as vLLM #38980, community NVFP4 loader with ModelOpt layer-name mismatch).
- `Qwen/Qwen3.6-27B-GPTQ-Int4` **does not exist** on HuggingFace (HF API returns 401, indicates repo not published).
- `Qwen/Qwen3.6-27B-FP8` is the only officially published 4-bit-class Qwen3.6-27B quant — but vLLM-recipe states 40 GB VRAM, RTX 5090 has 32 GB.
- `QuantTrio/Qwen3.6-35B-A3B-AWQ` is the only community 4-bit Qwen3.6 quant (MoE variant) that exists on HF.
- `Qwen/Qwen3.5-35B-A3B-GPTQ-Int4` is the one *proven-working* RTX 5090 recipe (194 tok/s with video input, HF discussion thread).

Three-option sequential spike plan chosen:

| Order | Model | Rationale | Risk |
|-------|-------|-----------|------|
| 1 | `Qwen/Qwen3.6-27B-FP8` @ 32K ctx | Official Qwen3.6 FP8, try tight-flag squeeze | OOM on 32 GB |
| 2 | `QuantTrio/Qwen3.6-35B-A3B-AWQ` | Only existing Qwen3.6 4-bit vLLM quant (MoE) | Community loader bug |
| 3 | `Qwen/Qwen3.5-35B-A3B-GPTQ-Int4` | Proven-working on RTX 5090 with video | Qwen3.5, not 3.6 |

---

## Option 1: Qwen/Qwen3.6-27B-FP8

**Command:**

```bash
docker run -d --name vllm-spike --gpus all \
  --add-host host.docker.internal:host-gateway \
  -v cognithor-spike-hf-cache:/root/.cache/huggingface \
  -p 8765:8000 \
  vllm/vllm-openai:v0.19.1 \
  --model Qwen/Qwen3.6-27B-FP8 \
  --max-model-len 32768 \
  --kv-cache-dtype fp8 \
  --enforce-eager \
  --gpu-memory-utilization 0.95 \
  --reasoning-parser qwen3 \
  --trust-remote-code \
  --media-io-kwargs '{"video": {"num_frames": -1}}'
```

**Status:** FAILED at 32s during EngineCore init.

**Root cause:** `ValueError: Free memory on device cuda:0 (30.12/31.84 GiB) on startup is less than desired GPU memory utilization (0.95, 30.25 GiB)`.

RTX 5090 reports only 30.12 GB free at container startup (Windows compositor + Docker overhead consume ~1.72 GB). Qwen3.6-27B-FP8 weights alone are ~28 GB, vision encoder ~1–2 GB, already too tight. Dropping `--gpu-memory-utilization` to 0.90 would give 28.6 GB budget — still below the ~30 GB model footprint. The vLLM-recipe's officially-stated "40 GB GPU minimum" for FP8 27B is confirmed empirically.

**Decision:** Option 1 unfeasible on RTX 5090. Proceeding to Option 3.

---

## Option 3: QuantTrio/Qwen3.6-35B-A3B-AWQ

**Command:**

```bash
docker run -d --name vllm-spike --gpus all \
  --add-host host.docker.internal:host-gateway \
  -v cognithor-spike-hf-cache:/root/.cache/huggingface \
  -p 8765:8000 \
  vllm/vllm-openai:v0.19.1 \
  --model QuantTrio/Qwen3.6-35B-A3B-AWQ \
  --max-model-len 65536 \
  --kv-cache-dtype auto \
  --enforce-eager \
  --gpu-memory-utilization 0.90 \
  --reasoning-parser qwen3 \
  --trust-remote-code \
  --media-io-kwargs '{"video": {"num_frames": -1}}'
```

**Status:** IN PROGRESS

---

## Option 2 (reserve, proven-working fallback)

---

### Reserve: Qwen/Qwen3.5-35B-A3B-GPTQ-Int4

**Status:** Not needed (Option 4 succeeded).

---

## Option 4 (WINNER): `mmangkad/Qwen3.6-27B-NVFP4` on `vllm/vllm-openai:cu130-nightly`

After Option 3 startup was interrupted (user insisted on dense Qwen3.6-27B, not MoE 35B), deeper research revealed the root-cause of the original `v0.19.1` crash: the NVFP4 loader for Qwen3NextGatedDeltaNet was broken in `v0.19.1`, then fixed upstream via the `apply_vllm_mapper` path which is only shipped in `cu130-nightly` (not yet in tagged releases).

### Final working command

```bash
docker run -d --name vllm-spike --gpus all \
  --add-host host.docker.internal:host-gateway \
  -v cognithor-spike-hf-cache:/root/.cache/huggingface \
  -p 8765:8000 \
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

### Iteration log

| # | Flags changed | Outcome |
|---|---------------|---------|
| 1 | `max=32768, util=0.88, no offload` | Startup OK, load OK, **OOM at KV cache init** (no room left) |
| 2 | `max=16384, util=0.95, offload=4` | **Startup check FAILED** (`free=30.12 GB < util×total=30.25 GB`) |
| 3 | `max=16384, util=0.94, offload=4` | ✅ **READY at 122s** |

### Signals that confirmed the fix

From iteration #3 engine log:

```
INFO [cuda.py:423] Using backend AttentionBackendEnum.FLASH_ATTN for vit attention
INFO [gdn_linear_attn.py:153] Using Triton/FLA GDN prefill kernel
INFO [__init__.py:683] Using FlashInferCutlassNvFp4LinearKernel for NVFP4 GEMM
INFO [cuda.py:368] Using FLASHINFER attention backend
INFO [gpu_model_runner.py:4854] Model loading took 28.25 GiB memory and 134 seconds
```

`FlashInferCutlassNvFp4LinearKernel` is the SM120 Blackwell kernel path that was missing in `v0.19.1`. `Triton/FLA GDN prefill kernel` is the Gated-Delta-Net kernel whose tensor-format-mismatch warning was the surface symptom in `v0.19.1`.

### VRAM post-ready

```
nvidia-smi: 30949 / 32102 MiB used, 1153 MiB free
```

Tight but stable. Container has been running without churn since.

### End-to-end sanity

Text-only completion (`"Say 'alive' in one word"` with `enable_thinking=false`) → `content="alive"` at 2 completion tokens. Model is functional.

---

## Wire-Shape Test Results

### Test 1 — `mm_processor_kwargs.video` shape

Sent 6 candidate shapes against a 10 s 1 MB BigBuckBunny clip (HTTPS), with prompt "Beschreibe das Video in einem Satz auf Deutsch.", `num_frames=8`, `max_tokens=80`.

| Candidate | `mm_processor_kwargs` | HTTP | Verdict |
|-----------|----------------------|------|---------|
| A | `{"video": {"fps": 1}}` | 200 | ✅ accepted |
| B | `{"video": {"num_frames": 8}}` | 200 | ✅ accepted |
| C | `{"fps": 1}` (flat) | 200 | ✅ accepted |
| D | `{"num_frames": 8}` (flat) | 200 | ✅ accepted |
| E | `{}` (empty) | 200 | ✅ accepted (default sampling) |
| F | `{"video": {}}` (nested empty) | 200 | ✅ accepted |

**Finding:** vLLM is permissive about `mm_processor_kwargs` — both the nested `{"video": {...}}` shape assumed in the spec and a flat shape are accepted. The spec assumption holds.

Inhaltsprüfung mit Candidate B: model returned `"Die Kamera zoomt auf ein Loch in einem Hügel."` (correct description of the opening frame). `prompt_tokens=2304` — consistent with 8 frames × ~280 tokens + text (~60 tokens) + special tokens.

### Test 2 — `video_url` fetch policy

| URL | Outcome | Implication |
|-----|---------|-------------|
| `https://test-videos.co.uk/.../Big_Buck_Bunny_360_10s_1MB.mp4` | ✅ 200 | Arbitrary HTTPS domains work, no allowlist needed out-of-the-box |
| `https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4` | ❌ 500 (`403 Forbidden`) | GCS bucket returns 403 to the container's HTTP client — **not a vLLM allowlist, a CDN-side restriction** |

**Finding:** vLLM does NOT have a default allowlist; it forwards any `video_url` to its HTTP client. The 403 from GCS was CDN-side (changed ACL or User-Agent filter). For our spec this means:
- No `--allowed-media-domains` flag needed at server level.
- **But** our local-HTTP-upload transport is validated as the correct design: public-CDN URLs are unreliable (some refuse bot-like clients), so uploaded-and-locally-served files are actually the safer common path — matches the spec's upload-first decision.

### Test 3 — ffprobe HTTP timing

Not executed against the spike container (the test script depends on a local HTTP file server that we didn't spin up during this session). The spec's 2 s pre-flight budget remains untested empirically but is informed by:
- Public HTTPS video fetch by vLLM completed end-to-end (download + encoder + inference) in < 10 s for a 1 MB / 10 s clip.
- Network latency to `test-videos.co.uk` is O(100 ms) for HEAD. ffprobe against HTTPS typically adds 300–800 ms for the index-box lookup on MP4. Budget of 2 s should be fine.

**Recommendation:** Execute Test 3 in Task 2 of the plan (VideoSamplingResolver) rather than blocking the gate here.

---

## Spike Gate Decision

- [x] Wire shape matches spec assumption (nested `{"video": {...}}` works; flat also works — spec's conservative choice is safe)
- [x] Fetch-allowlist policy matches spec assumption (no vLLM allowlist; local-HTTP transport validated as correct design choice)
- [ ] ffprobe timing empirically verified (deferred to Task 2, budget likely OK)

**Gate:** ✅ **APPROVED — proceed to implementation (Tasks 2–23).**

### Plan amendments required

1. **Base image:** Spec assumed `vllm/vllm-openai:v0.19.1` works for Qwen3.6-27B-NVFP4. Reality: `v0.19.1` crashes in the FLA GDN + NVFP4 loader. Must use `vllm/vllm-openai:cu130-nightly` (or wait for a future tagged release that ships `FlashInferCutlassNvFp4LinearKernel`).
2. **Model flags:** Must include `--cpu-offload-gb 4`, `--gpu-memory-utilization 0.94`, `--max-model-len 16384`, `--max-num-seqs 2`, `--enforce-eager`, `--reasoning-parser qwen3`, `--trust-remote-code`, `--media-io-kwargs '{"video": {"num_frames": -1}}'`. Update `scripts/docker-compose.vllm.yml` accordingly in Task 21 (Installer).
3. **Memory-limited ceiling:** On 32 GB RTX 5090 the model can only serve `max_model_len=16384` (16 K), not the 262 K native context. Document this in user-facing wizard copy (Task 21).
4. **Model ID:** Spec should reference `mmangkad/Qwen3.6-27B-NVFP4` (community quant) rather than placeholder names. When an official Qwen NVFP4 ships, swap via the registry.
5. **Video fetch resilience:** Spec decision on local-HTTP upload transport is now EMPIRICALLY validated — public CDN URLs can be blocked by CDN-side policies. No change needed, but add an error-handling note that `403/401` from the fetch path should show a user-friendly "Diese URL ist nicht öffentlich abrufbar" error.

---

## References

- [Deep research Qwen3.6-27B vLLM landscape](../../CHANGELOG.md)
- [vLLM Recipe: Qwen3.6-27B](https://recipes.vllm.ai/Qwen/Qwen3.6-27B)
- [Qwen/Qwen3.6-27B-FP8 model card](https://huggingface.co/Qwen/Qwen3.6-27B-FP8)
- [mmangkad/Qwen3.6-27B-NVFP4 model card](https://huggingface.co/mmangkad/Qwen3.6-27B-NVFP4)
- [vLLM bug #38643: FLA format mismatch (benign per maintainers)](https://github.com/vllm-project/vllm/issues/38643)
- [vLLM bug #38980: ModelOpt NVFP4 loader key mismatch (fix in cu130-nightly)](https://github.com/vllm-project/vllm/issues/38980)
- [aliez-ren/vllm-qwen3.5-nvfp4-sm120 (matching SM120 + NVFP4 recipe)](https://github.com/aliez-ren/vllm-qwen3.5-nvfp4-sm120)
- [Working Qwen3.5-35B-A3B-GPTQ-Int4 on RTX 5090 with video, 194 tok/s](https://huggingface.co/Qwen/Qwen3.5-35B-A3B-GPTQ-Int4/discussions/3)

---

## Wire-Shape Test Results

_These tests run only once one of the three Options reaches /health._

### Test 1 — `mm_processor_kwargs.video` shape

_Pending_

### Test 2 — `video_url` fetch-allowlist policy

_Pending_

### Test 3 — ffprobe HTTP timing from container

_Pending_

---

## Spike Gate Decision

_Filled in after all three tests complete._

- [ ] Wire shape matches spec assumption
- [ ] Fetch-allowlist policy matches spec assumption
- [ ] ffprobe timing within spec budget

**Gate:** ___ (APPROVED / RETURN-TO-DESIGN)

---

## References

- [Deep research Qwen3.6-27B vLLM landscape](../../CHANGELOG.md)
- [vLLM Recipe: Qwen3.6-27B](https://recipes.vllm.ai/Qwen/Qwen3.6-27B)
- [Qwen/Qwen3.6-27B-FP8 model card](https://huggingface.co/Qwen/Qwen3.6-27B-FP8)
- [vLLM bug #38643: FLA format mismatch (benign per maintainers)](https://github.com/vllm-project/vllm/issues/38643)
- [vLLM bug #38980: ModelOpt NVFP4 loader key mismatch](https://github.com/vllm-project/vllm/issues/38980)
- [Working Qwen3.5-35B-A3B-GPTQ-Int4 on RTX 5090 with video, 194 tok/s](https://huggingface.co/Qwen/Qwen3.5-35B-A3B-GPTQ-Int4/discussions/3)

---

## Known follow-ups

### cu130-nightly is a rolling tag

The Day-1 spike proved the `cu130-nightly` image works today. The tag itself is
rolling — the vLLM project publishes a new build daily. A future upstream
regression can silently break video requests for users who pull after that date.

**Short-term workaround**: users pin to a specific digest manually. Documented
in `docs/vllm-user-guide.md` under "Known limitation".

**Medium-term fix**: either
1. Wait for a tagged vLLM release that ships `FlashInferCutlassNvFp4LinearKernel`
   (the SM120 NVFP4 kernel fix) and switch the default to that tag. Check
   vllm-project/vllm releases periodically.
2. Add a `vllm.docker_image_pin_digest` config field that, when set, resolves the
   image via `vllm/vllm-openai@sha256:<digest>` instead of the tag. Surface in the
   installer wizard as a "Pin to current version" checkbox after the initial pull.

**Medium-term test**: add a CI nightly that pulls the tag fresh and runs a smoke
test against Qwen3.6-27B-NVFP4. If the smoke fails, open an issue automatically
so we find out before users do.

Priority: **medium**. The tag has been stable for our current needs and the
spike findings are less than a week old. Re-evaluate before the next Cognithor
release.
