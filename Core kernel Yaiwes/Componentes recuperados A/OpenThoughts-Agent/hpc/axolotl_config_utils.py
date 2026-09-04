"""LF-exp-args -> axolotl-YAML config translation (Stage 2 of the axolotl SFT backend).

Selected when ``--sft_backend axolotl``. Emits a valid axolotl SFT YAML from the
launcher's canonical exp-args + a small axolotl base template (``sft/axolotl_configs/``),
mirroring the LF ``construct_config_yaml`` prelude (job name, paths, dataset/model
materialize, grad-accum math) but writing an axolotl-schema dict.

See ``notes/axolotl-sft-launch/README.md`` §Config-translation map for the LF<->axolotl
key map. The delphi fork keys (``chat_template: delphi`` + ``tokenizer_save_jinja_files:
false``, ``mfu``, ``supabase_register``, ``plugins``) pass straight through; LF-only keys
are dropped with a warning.

Flag-off (``--sft_backend llamafactory``) never reaches this module — the LF emit path
is byte-identical to pre-change.
"""

import os


# axolotl plugin module paths (assembled into the emitted `plugins:` list from the
# enabled fork-key flags). Names must match the fork's integration modules.
_PLUGIN_TEMPLATE_INTEGRITY = (
    "axolotl.integrations.template_integrity.TemplateIntegrityPlugin"
)
_PLUGIN_MFU = "axolotl.integrations.mfu.MFUPlugin"
_PLUGIN_SUPABASE = "axolotl.integrations.supabase_registry.SupabaseRegistryPlugin"
_PLUGIN_LIGER = "axolotl.integrations.liger.LigerPlugin"

# LF-YAML / launcher keys that have NO axolotl equivalent. Dropped with a warning
# so a translated config never carries a silently-ignored LF knob. (README §map:
# "LF-only keys with NO axolotl equivalent (drop-with-warning)".)
_LF_ONLY_DROP_KEYS = {
    "overwrite_output_dir",
    "data_shared_file_system",
    "plot_loss",
    "include_num_input_tokens_seen",
    "load_best_model_at_end",
    "logging_strategy",
    "dataloader_persistent_workers",
    "dataloader_pin_memory",
    "dataloader_num_workers",
    "overwrite_cache",
    "preprocessing_num_workers",
    "stage",
    "do_train",
    "finetuning_type",
    "formatting",
    "messages",
    "neat_packing",
    "use_cce",
    "pure_bf16",
    "use_unsloth_gc",
    "eval_strategy",
    "save_strategy",
}

# Direct 1:1 renames LF-key -> axolotl-key (README §map, the ✅ rows).
_RENAME_MAP = {
    "model_name_or_path": "base_model",
    "cutoff_len": "sequence_len",
    "num_train_epochs": "num_epochs",
    "lr_scheduler_type": "lr_scheduler",
    "packing": "sample_packing",
}


def _warn(msg: str) -> None:
    print(f"[axolotl-translate] WARNING: {msg}")


def _map_optimizer(lf_optim):
    """optim: adamw_torch_fused -> optimizer: adamw_torch_fused (else adamw_torch)."""
    if not lf_optim:
        return "adamw_torch"
    if lf_optim == "adamw_torch_fused":
        return "adamw_torch_fused"
    if lf_optim.startswith("adamw"):
        return lf_optim
    _warn(f"optimizer '{lf_optim}' has no verified axolotl mapping; using adamw_torch")
    return "adamw_torch"


def _build_datasets(base_config: dict, exp_args: dict, dataset_paths):
    """LF `--dataset A,B` + role/content tags -> axolotl `datasets: [{path,type,...}]`.

    Role/content tags map to `message_property_mappings` so assistant turns are
    found (the LF "0 assistant messages -> garbage" failure has an axolotl analogue).
    To reproduce the LF delphi inline-`<think>` loss mask, reasoning stays inline in
    assistant content: `split_thinking: false`, no `field_thinking` (README §map,
    Gate M / Open-decision #6 = "match LF exactly").
    """
    role_tag = exp_args.get("role_tag") or base_config.get("role_tag") or "from"
    content_tag = (
        exp_args.get("content_tag") or base_config.get("content_tag") or "value"
    )
    messages_field = (
        exp_args.get("messages") or base_config.get("messages") or "conversations"
    )

    # LF's ShareGPT default: role under `from`, content under `value`, turns under
    # `conversations`. Map to axolotl property mappings + field_messages.
    property_mappings = {"role": role_tag, "content": content_tag}

    entries = []
    for path in dataset_paths:
        entry = {
            "path": path,
            "type": "chat_template",
            "field_messages": messages_field,
            "message_property_mappings": property_mappings,
        }
        # Match LF delphi inline-think masking (Gate M). Only meaningful for the
        # delphi/qwen3 reasoning templates but harmless elsewhere.
        entry["split_thinking"] = False
        entries.append(entry)
    return entries


def _assemble_plugins(base_config: dict) -> list:
    """Build the axolotl `plugins:` list from the enabled fork-key flags."""
    plugins = []
    chat_template = base_config.get("chat_template") or base_config.get("template")
    # delphi needs the save-time footgun fix plugin whenever an embedded template
    # is required.
    if chat_template == "delphi":
        plugins.append(_PLUGIN_TEMPLATE_INTEGRITY)
    if base_config.get("mfu") or base_config.get("include_mfu"):
        plugins.append(_PLUGIN_MFU)
    if base_config.get("supabase_register"):
        plugins.append(_PLUGIN_SUPABASE)
    # Liger fused kernels (the load-bearing memory lever for the 32B@32k OOM):
    # LigerFusedLinearCrossEntropy fuses the LM head + cross-entropy so the full
    # ~18 GB logit tensor (seq 32768 × vocab ~152k × bf16) never materializes —
    # the exact allocation that OOM'd in the ZeRO-3 backward. Mirrors LF's
    # `enable_liger_kernel: true`. See .agents/projects/axolotl/axolotl.md
    # §Qwen3-32B + agent_logs/2026-07-09_sft_32b_axolotl_oom_config_gap.md.
    if base_config.get("enable_liger_kernel"):
        plugins.append(_PLUGIN_LIGER)
    return plugins


def translate_lf_to_axolotl(
    base_config: dict,
    exp_args: dict,
    dataset_paths,
    model_path: str,
    *,
    num_nodes: int,
    gpus_per_node: int,
) -> dict:
    """Pure translation: LF-schema `base_config` + geometry -> axolotl-schema dict.

    No I/O; unit-testable. `base_config` may carry the LF keys and/or already-merged
    axolotl fork keys (from the axolotl base template). Grad-accum is computed here
    from `global_batch_size` if present.
    """
    ax: dict = {}

    # --- 1:1 renames ---
    for lf_key, ax_key in _RENAME_MAP.items():
        if lf_key in base_config and base_config[lf_key] is not None:
            ax[ax_key] = base_config[lf_key]

    # base_model: prefer the resolved local model_path on no-internet clusters
    # (configure_sft_reporting sets model_name_or_path = model_path there).
    if model_path:
        ax["base_model"] = model_path

    # --- same-name passthroughs ---
    for key in (
        "learning_rate",
        "warmup_ratio",
        "warmup_steps",
        "weight_decay",
        "max_grad_norm",
        "gradient_checkpointing",
        "trust_remote_code",
        "logging_steps",
        "seed",
        "output_dir",
        "save_steps",
        "save_total_limit",
        "num_epochs",
        "max_steps",
        "sequence_len",
        "sample_packing",
        "val_set_size",
        "adam_beta1",
        "adam_beta2",
        "special_tokens",
        "dataset_num_proc",
        "dataset_prepared_path",
        # resume-from-checkpoint (so --max_restarts / an afterany chain leg RESUMES for the
        # axolotl backend instead of restarting from step 0 — axolotl only auto-resumes when
        # auto_resume_from_checkpoints/resume_from_checkpoint is set; HF-Trainer's implicit
        # auto-resume that the LF path relies on does NOT apply here).
        "auto_resume_from_checkpoints",
        "resume_from_checkpoint",
        # ddp_timeout -> HF TrainingArguments.ddp_timeout -> accelerate InitProcessGroupKwargs
        # -> the c10d/NCCL collective-watchdog timeout (axolotl forwards it in causal.py). Lets a
        # transient IB blip during a ZeRO-3 reduce-scatter self-heal instead of SIGABRT at the 600s
        # default (env NCCL_TIMEOUT is NOT honored for this). Value mirrors the LF parity config.
        "ddp_timeout",
    ):
        if key in base_config and base_config[key] is not None:
            ax[key] = base_config[key]

    # dataset_prepared_path may reference env vars (e.g. $SCRATCH) so a shared prepared
    # dir is cluster-portable; axolotl reads it literally, so expand here.
    if ax.get("dataset_prepared_path"):
        ax["dataset_prepared_path"] = os.path.expandvars(ax["dataset_prepared_path"])

    # --- optimizer ---
    ax["optimizer"] = _map_optimizer(
        base_config.get("optim") or base_config.get("optimizer")
    )

    # --- bf16 / tf32 (semantics close; assert dtype in the GPU smoke) ---
    if base_config.get("bf16") or str(base_config.get("bf16")).lower() == "auto":
        ax["bf16"] = "auto"
        ax.setdefault("tf32", False)

    # --- effective batch: global_batch_size -> micro_batch_size + grad_accum ---
    # Reuse the LF math (per_device=1, dp = nodes*gpus). Non-1:1 shape (README §map).
    gbs = base_config.get("global_batch_size")
    micro = (
        base_config.get("micro_batch_size")
        or base_config.get("per_device_train_batch_size")
        or 1
    )
    if gbs is not None:
        # CLI passes --global_batch_size as a string; cast (mirrors the int()
        # coercion already applied to micro/num_nodes/gpus_per_node below) so the
        # modulo/floordiv below are integer math, not str-formatting (TypeError).
        gbs = int(gbs)
        dp = max(int(num_nodes) * int(gpus_per_node), 1)
        denom = int(micro) * dp
        if denom <= 0 or gbs % denom != 0:
            raise ValueError(
                f"global_batch_size={gbs} not divisible by micro_batch_size({micro}) * "
                f"data_parallel({dp}); cannot derive gradient_accumulation_steps."
            )
        ax["micro_batch_size"] = int(micro)
        ax["gradient_accumulation_steps"] = gbs // denom
    else:
        # No global_batch_size: take axolotl's explicit pair straight from the template.
        if "micro_batch_size" in base_config:
            ax["micro_batch_size"] = base_config["micro_batch_size"]
        if "gradient_accumulation_steps" in base_config:
            ax["gradient_accumulation_steps"] = base_config[
                "gradient_accumulation_steps"
            ]

    # --- attention: LF `attn`/`fa2` -> axolotl attn_implementation (varlen) ---
    # An explicit `attn_implementation` in the base config wins (e.g. `sdpa` on
    # aarch64 clusters like TACC Vista, which have NO flash-attn-2 wheel for
    # torch 2.11+cu128 — see .agents/ops/tacc/ops.md). Otherwise, sample_packing
    # without a varlen backend warns about cross-sample decontamination, so a
    # flash backend matches LF throughput/semantics.
    lf_attn = base_config.get("attn")
    if base_config.get("attn_implementation"):
        ax["attn_implementation"] = base_config["attn_implementation"]
    elif (
        lf_attn in ("fa2", "fa3")
        or base_config.get("flash_attention")
        or ax.get("sample_packing")
    ):
        ax["attn_implementation"] = "flash_attention_2"

    # --- chat_template + fork keys ---
    chat_template = base_config.get("chat_template") or base_config.get("template")
    if chat_template:
        ax["chat_template"] = chat_template
    # Footgun fix: embed the template into tokenizer_config.json (delphi especially).
    if "tokenizer_save_jinja_files" in base_config:
        ax["tokenizer_save_jinja_files"] = base_config["tokenizer_save_jinja_files"]
    elif chat_template == "delphi":
        ax["tokenizer_save_jinja_files"] = False

    # MFU fork key
    if base_config.get("mfu") or base_config.get("include_mfu"):
        ax["mfu"] = True
        ax["mfu_profile_every"] = base_config.get("mfu_profile_every", 50)
        ax["mfu_warmup_steps"] = base_config.get("mfu_warmup_steps", 5)

    # Supabase fork key (opt-in, default OFF). Creds via env NAME only — never here.
    if base_config.get("supabase_register"):
        ax["supabase_register"] = True

    # Liger fused kernels. `enable_liger_kernel: true` -> register LigerPlugin
    # (in _assemble_plugins) AND turn on the individual fused ops. The load-bearing
    # one is `liger_fused_linear_cross_entropy` (kills the ~18 GB LM-head logit
    # tensor that OOM'd); rope/rms_norm/glu are the standard companion fusions and
    # match LF's liger enablement. Learning-neutral, memory-saving.
    if base_config.get("enable_liger_kernel"):
        ax["liger_rope"] = True
        ax["liger_rms_norm"] = True
        ax["liger_glu_activation"] = True
        ax["liger_fused_linear_cross_entropy"] = True

    # --- datasets ---
    ax["datasets"] = _build_datasets(base_config, exp_args, dataset_paths)

    # --- deepspeed (ZeRO-3 intent; use axolotl's proven json, not the LF one) ---
    if base_config.get("deepspeed") or base_config.get("deepspeed_config"):
        ax["deepspeed"] = (
            base_config.get("deepspeed_config")
            or "sft/axolotl/deepspeed_configs/zero3_bf16.json"
        )

    # --- hub push (mirror LF offline handling: omit hub_model_id offline) ---
    if exp_args.get("internet_node"):
        if base_config.get("hub_model_id"):
            ax["hub_model_id"] = base_config["hub_model_id"]
        if base_config.get("report_to") == "wandb":
            ax["wandb_project"] = base_config.get("wandb_project", "otagent-sft")
    # else: offline -> no hub_model_id (axolotl offline init_hf_repo crash); upload at cleanup.

    # --- plugins ---
    plugins = _assemble_plugins(base_config)
    if plugins:
        ax["plugins"] = plugins

    # --- drop-with-warning for LF-only keys that slipped into base_config ---
    for k in sorted(base_config.keys()):
        if k in _LF_ONLY_DROP_KEYS:
            _warn(f"dropping LF-only key '{k}' (no axolotl equivalent)")

    return ax


def construct_axolotl_config_yaml(exp_args):
    """Axolotl analogue of launch.construct_config_yaml (selected on sft_backend=axolotl).

    Reuses the LF prelude helpers (base-config load, job-name/paths, dataset/model
    materialize, reporting) then emits an axolotl-schema YAML instead of the LF one.
    Returns (axolotl_config_dict, train_config_path_out) matching the LF signature.
    """
    # Imported lazily to avoid a launch<->axolotl_config_utils import cycle.
    from hpc.launch import (
        _load_base_train_config,
        _maybe_include_model_in_job_name,
        _merge_launch_overrides,
        _extract_dataset_entries,
        _materialize_dataset_and_model,
        _configure_output_and_logging,
        _write_train_config,
        derive_default_job_name,
    )
    from hpc.sft_launch_utils import configure_sft_reporting, resolve_job_and_paths

    train_config_path = exp_args.get("train_config_path")
    datasets_dir = os.path.expandvars(
        os.environ.get("DATASETS_DIR", exp_args.get("datasets_dir") or "")
    )
    checkpoints_dir = os.path.expandvars(
        os.environ.get("CHECKPOINTS_DIR", exp_args.get("checkpoints_dir") or "")
    )
    if checkpoints_dir:
        os.makedirs(checkpoints_dir, exist_ok=True)

    base_config = _load_base_train_config(train_config_path)

    if not exp_args.get("job_name"):
        exp_args["job_name"] = derive_default_job_name(exp_args)
    exp_args = _maybe_include_model_in_job_name(base_config, exp_args)

    job_setup = resolve_job_and_paths(exp_args, job_type_label="SFT")
    configs_dir = str(job_setup.paths.configs)
    exp_args["logs_dir"] = str(job_setup.paths.logs)

    base_config = _merge_launch_overrides(base_config, exp_args)

    if base_config.get("dataset_dir") is None:
        base_config["dataset_dir"] = "ONLINE"
    dataset_entries = _extract_dataset_entries(base_config.get("dataset"))

    # The axolotl base template names the model `base_model`; the shared LF prelude
    # helpers (materialize/reporting) read `model_name_or_path`. Bridge it so the
    # model resolves + downloads exactly as the LF path does.
    if not base_config.get("model_name_or_path") and base_config.get("base_model"):
        base_config["model_name_or_path"] = base_config["base_model"]
    exp_args["_original_model_name_or_path"] = base_config.get("model_name_or_path")

    artifacts = _materialize_dataset_and_model(
        base_config, exp_args, dataset_entries, datasets_dir
    )

    # Reporting/offline handling (sets model_name_or_path=model_path, push_to_hub).
    base_config = configure_sft_reporting(base_config, exp_args, artifacts.model_path)
    # Route output_dir under $CHECKPOINTS_DIR + the launcher's resume/overwrite guards,
    # exactly like the LF path (so the WORKDIR write-path guard + checkpoint dirs match).
    base_config = _configure_output_and_logging(base_config, exp_args, checkpoints_dir)

    num_nodes = int(exp_args.get("num_nodes") or 1)
    gpus_per_node = int(exp_args.get("gpus_per_node") or 1)

    axolotl_config = translate_lf_to_axolotl(
        base_config,
        exp_args,
        dataset_paths=(artifacts.dataset_paths or [artifacts.dataset_path]),
        model_path=artifacts.model_path,
        num_nodes=num_nodes,
        gpus_per_node=gpus_per_node,
    )
    # output_dir from the LF path if not already set in the axolotl config.
    if "output_dir" not in axolotl_config and base_config.get("output_dir"):
        axolotl_config["output_dir"] = base_config["output_dir"]

    train_config_path_out = _write_train_config(
        configs_dir, exp_args["job_name"], axolotl_config
    )
    exp_args["output_dir"] = axolotl_config.get("output_dir")
    exp_args["model_name_or_path"] = axolotl_config.get("base_model")
    exp_args["hub_model_id"] = axolotl_config.get("hub_model_id")
    return axolotl_config, train_config_path_out


def validate_axolotl_config(axolotl_config: dict):
    """GPU-free pydantic validation against axolotl's AxolotlInputConfig.

    Registers the config's `plugins:` first so fork keys (mfu/supabase_register)
    are accepted, then validates. Requires torch/accelerate/transformers importable
    (CPU arm64 fine); no CUDA/flash-attn. Returns the validated config dict.
    """
    import sys

    axolotl_src = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "sft", "axolotl", "src"
    )
    if os.path.isdir(axolotl_src) and axolotl_src not in sys.path:
        sys.path.insert(0, axolotl_src)

    # Lean, GPU-free path: register plugins on the PluginManager + build the
    # plugin-augmented AxolotlInputConfig via merge_input_args(), then pydantic-
    # validate. Avoids axolotl.utils.config (which imports axolotl.loaders ->
    # bitsandbytes, unavailable on arm64 Mac). See notes agent_logs for why.
    from axolotl.integrations.base import PluginManager
    from axolotl.integrations.config import merge_input_args
    from axolotl.utils.schemas.config import AxolotlInputConfig as _Base

    plugins = axolotl_config.get("plugins") or []
    input_cls = _Base
    if plugins:
        pm = PluginManager.get_instance()
        for name in plugins:
            pm.register(name)
        _, input_cls = merge_input_args()

    return input_cls(**{k: v for k, v in axolotl_config.items()})
