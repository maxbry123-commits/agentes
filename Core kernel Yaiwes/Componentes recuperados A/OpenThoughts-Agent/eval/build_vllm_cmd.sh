#!/bin/bash
# ==============================================================================
# eval/build_vllm_cmd.sh — Shared vLLM command builder for eval scripts
#
# Reads EVAL_VLLM_* env vars (set by unified_eval_listener.py from the shared model-config
# registry eval/configs/model_configs.yaml — the default; the legacy
# --baseline-model-configs path is deprecated) and builds a vLLM launch command array.
#
# Usage (source from any eval sbatch/pbs script):
#
#   source "$DCFT/eval/build_vllm_cmd.sh"
#   build_vllm_cmd "$PYTHON_BIN" "$MODEL" "$GPU_MEMORY_UTIL"
#   # Result is in VLLM_CMD array; launch with:
#   env ... "${VLLM_CMD[@]}" > logfile 2>&1 &
#
# Env vars consumed (all optional, set by listener):
#   EVAL_VLLM_TENSOR_PARALLEL_SIZE  (default: 4)
#   EVAL_VLLM_MAX_MODEL_LEN         (default: unset = model native)
#   EVAL_VLLM_MAX_NUM_SEQS          (default: unset = vLLM default; listener sets 256 for Qwen3.5/3.6 family)
#   EVAL_VLLM_SWAP_SPACE            (default: 32)
#   EVAL_VLLM_TRUST_REMOTE_CODE     (default: unset; set to "1" to enable)
#   EVAL_VLLM_TOOL_CALL_PARSER      (default: unset)
#   EVAL_VLLM_REASONING_PARSER      (default: unset)
#   EVAL_VLLM_DATA_PARALLEL_SIZE    (default: unset; vLLM v0.8+ only)
#   EVAL_VLLM_EXTRA_ARGS            (default: unset; space-separated string)
#   EVAL_VLLM_HF_OVERRIDES          (default: unset; JSON string for --hf-overrides)
# ==============================================================================

build_vllm_cmd() {
    local python_bin="${1:?Usage: build_vllm_cmd <python_bin> <model> <gpu_mem_util> [served_name]}"
    local model="${2:?Missing model}"
    local gpu_mem_util="${3:-0.95}"
    # Optional 4th arg: the API-facing --served-model-name. vLLM's --model is the
    # LOAD path (HF repo / local dir); --served-model-name is the name clients
    # (harbor/litellm) address. They need not match — callers shorten the served
    # name when the real repo id has a >64-char segment that harbor's hosted_vllm
    # validator rejects (see eval/leonardo/eval_harbor.sbatch). Defaults to $model.
    local served_name="${4:-$model}"

    # Read overrides from env (set by listener via sbatch --export)
    local tp="${EVAL_VLLM_TENSOR_PARALLEL_SIZE:-4}"
    local dp="${EVAL_VLLM_DATA_PARALLEL_SIZE:-}"
    local max_model_len="${EVAL_VLLM_MAX_MODEL_LEN:-32768}"
    local swap_space="${EVAL_VLLM_SWAP_SPACE:-32}"
    local trust_remote_code="${EVAL_VLLM_TRUST_REMOTE_CODE:-}"
    local tool_call_parser="${EVAL_VLLM_TOOL_CALL_PARSER:-}"
    local reasoning_parser="${EVAL_VLLM_REASONING_PARSER:-}"
    local extra_args="${EVAL_VLLM_EXTRA_ARGS:-}"
    local hf_overrides="${EVAL_VLLM_HF_OVERRIDES:-}"
    local limit_mm="${EVAL_VLLM_LIMIT_MM_PER_PROMPT:-}"
    local max_num_seqs="${EVAL_VLLM_MAX_NUM_SEQS:-}"

    # --- transformers-5.x tokenizer compat coercion (serve-side) ---------------
    # A model exported by transformers 5.x (TokenizersBackend) can ship a
    # tokenizer_config.json whose `extra_special_tokens` is a LIST of token
    # strings instead of the {name: token} dict transformers expects (it calls
    # `.keys()`), crashing vLLM's tokenizer load at api_server startup BEFORE any
    # TP/DP placement: `AttributeError: 'list' object has no attribute 'keys'`.
    # prep_serve_tokenizer.py resolves the model's already-cached tokenizer and,
    # ONLY if coercion is needed, emits a NON-DESTRUCTIVE patched tokenizer dir
    # (every file symlinked, tokenizer_config.json normalized) whose path we pass
    # vLLM as --tokenizer (--model still loads weights from the repo). When the
    # config is already well-formed it prints nothing → no --tokenizer → the
    # serve is byte-identical to before. An explicit EVAL_VLLM_TOKENIZER wins.
    local tokenizer_override="${EVAL_VLLM_TOKENIZER:-}"
    local prep_script="${DCFT:-}/eval/prep_serve_tokenizer.py"
    if [ -z "$tokenizer_override" ] && [ -n "${DCFT:-}" ] && [ -f "$prep_script" ]; then
        # stdout -> the patched dir (or empty); stderr -> the job log.
        tokenizer_override=$("$python_bin" "$prep_script" "$model") || tokenizer_override=""
    fi

    # Build command array
    VLLM_CMD=(
        "$python_bin" -m vllm.entrypoints.openai.api_server
        --model "$model"
        --host 0.0.0.0 --port "${VLLM_PORT:-8000}"
        --served-model-name "$served_name"
        --tensor-parallel-size "$tp"
        --gpu-memory-utilization "$gpu_mem_util"
        --disable-custom-all-reduce
    )

    if [ -n "$tokenizer_override" ]; then
        VLLM_CMD+=(--tokenizer "$tokenizer_override")
    fi

    # --swap-space was REMOVED from `vllm serve` in recent vLLM (e.g. Jupiter's nightly
    # 0.1.devNNNNN rejects it: "unrecognized arguments: --swap-space" → instant vLLM death).
    # Only pass it if the installed vLLM still accepts it (probe cached per build; bounded by argparse).
    if [ -n "$swap_space" ] && \
       timeout 120 "$python_bin" -m vllm.entrypoints.openai.api_server --help 2>/dev/null | grep -q -- '--swap-space'; then
        VLLM_CMD+=(--swap-space "$swap_space")
    fi

    if [ -n "$dp" ] && [ "$dp" -gt 1 ] 2>/dev/null; then
        VLLM_CMD+=(--data-parallel-size "$dp")
    fi

    if [ -n "$max_model_len" ]; then
        VLLM_CMD+=(--max-model-len "$max_model_len")
    fi

    if [ -n "$max_num_seqs" ]; then
        VLLM_CMD+=(--max-num-seqs "$max_num_seqs")
    fi

    if [ "$trust_remote_code" = "1" ]; then
        VLLM_CMD+=(--trust-remote-code)
    fi

    if [ -n "$tool_call_parser" ]; then
        VLLM_CMD+=(--enable-auto-tool-choice --tool-call-parser "$tool_call_parser")
    fi

    if [ -n "$reasoning_parser" ]; then
        VLLM_CMD+=(--reasoning-parser "$reasoning_parser")
    fi

    # HF model config overrides (JSON string, properly quoted)
    if [ -n "$hf_overrides" ]; then
        VLLM_CMD+=(--hf-overrides "$hf_overrides")
    fi

    # Multimodal per-prompt caps (e.g. serve a VL arch text-only). Passed as a
    # SINGLE array element so the JSON value survives intact — recent vLLM
    # json.loads() this arg, so it MUST be a JSON object string
    # ('{"image":0,"video":0}'). Do NOT route this through EVAL_VLLM_EXTRA_ARGS:
    # that is word-split unquoted and the JSON quotes get stripped → invalid JSON
    # → "Value ... cannot be converted to <loads>" and the serve exits 2.
    if [ -n "$limit_mm" ]; then
        VLLM_CMD+=(--limit-mm-per-prompt "$limit_mm")
    fi

    # Append extra args (space-separated string)
    if [ -n "$extra_args" ]; then
        # shellcheck disable=SC2206
        VLLM_CMD+=($extra_args)
    fi

    # Log what we built
    echo "vLLM command config:"
    if [ "$served_name" != "$model" ]; then
        echo "  served-model-name='$served_name' (ALIAS; load path --model='$model')"
    fi
    if [ -n "$tokenizer_override" ]; then
        echo "  tokenizer=$tokenizer_override (transformers-5.x compat coercion; --model unchanged)"
    fi
    echo "  TP=$tp, DP=${dp:-1}, swap=$swap_space, max_model_len=${max_model_len:-auto}"
    echo "  trust_remote_code=${trust_remote_code:-no}"
    echo "  tool_call_parser=${tool_call_parser:-none}"
    echo "  reasoning_parser=${reasoning_parser:-none}"
    echo "  extra_args=${extra_args:-none}"
    echo "  Full command: ${VLLM_CMD[*]}"
}
