# Copyright 2024 the LlamaFactory team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import torch
from transformers import PreTrainedModel
from transformers.trainer_callback import TrainerCallback

from ..data import get_template_and_fix_tokenizer
from ..extras import logging
from ..extras.constants import V_HEAD_SAFE_WEIGHTS_NAME, V_HEAD_WEIGHTS_NAME
from ..hparams import get_infer_args, get_train_args
from ..model import load_model, load_tokenizer
from ..utils.memory_profiler import (
    PREFIX,
    create_profiler,
    save_memory_snapshot,
    start_memory_snapshot,
)
from .callbacks import LogCallback, MemoryProfileCallback
from .dpo import run_dpo
from .kto import run_kto
from .ppo import run_ppo
from .pt import run_pt
from .rm import run_rm
from .sft import run_sft

if TYPE_CHECKING:
    from transformers import TrainerCallback


logger = logging.get_logger(__name__)


def _run(
    model_args, data_args, training_args, finetuning_args, generating_args, callbacks
):
    if finetuning_args.stage == "pt":
        run_pt(model_args, data_args, training_args, finetuning_args, callbacks)
    elif finetuning_args.stage == "sft":
        run_sft(
            model_args,
            data_args,
            training_args,
            finetuning_args,
            generating_args,
            callbacks,
        )
    elif finetuning_args.stage == "rm":
        run_rm(model_args, data_args, training_args, finetuning_args, callbacks)
    elif finetuning_args.stage == "ppo":
        run_ppo(
            model_args,
            data_args,
            training_args,
            finetuning_args,
            generating_args,
            callbacks,
        )
    elif finetuning_args.stage == "dpo":
        run_dpo(model_args, data_args, training_args, finetuning_args, callbacks)
    elif finetuning_args.stage == "kto":
        run_kto(model_args, data_args, training_args, finetuning_args, callbacks)
    else:
        raise ValueError(f"Unknown task: {finetuning_args.stage}.")


def run_exp(
    args: Optional[Dict[str, Any]] = None, callbacks: List["TrainerCallback"] = []
) -> None:
    """Run the training experiment."""
    callbacks.append(LogCallback())
    model_args, data_args, training_args, finetuning_args, generating_args = (
        get_train_args(args)
    )

    try:
        if model_args.profile_torch_memory:
            print(f"{PREFIX}: Setting up memory profiling")
            # Start memory snapshot recording
            start_memory_snapshot(True)

            # Create profiler
            profiler = create_profiler(
                output_dir=model_args.profile_torch_memory_dir,
                skip_first=model_args.profile_skip_first,
                wait=model_args.profile_wait,
                warmup=model_args.profile_warmup,
                active=model_args.profile_active,
                repeat=model_args.profile_repeat,
            )

            # Add memory profiling callback with profiler
            callbacks.append(
                MemoryProfileCallback(
                    output_dir=model_args.profile_torch_memory_dir,
                    save_steps=model_args.profile_torch_memory_snapshot_save_steps,  # Use configured snapshot frequency
                    profiler=profiler,  # Pass the profiler instance
                )
            )

            # Run with profiler context
            print(f"{PREFIX}: Starting training with profiler")
            with profiler as active_profiler:
                _run(
                    model_args,
                    data_args,
                    training_args,
                    finetuning_args,
                    generating_args,
                    callbacks,
                )
                print(f"{PREFIX}: Training completed with profiler")
        else:
            _run(
                model_args,
                data_args,
                training_args,
                finetuning_args,
                generating_args,
                callbacks,
            )

    finally:
        # Ensure we save and cleanup memory profiling if it was enabled
        if model_args.profile_torch_memory:
            print(f"{PREFIX}: Cleaning up memory profiling")
            # Save final memory snapshot
            save_memory_snapshot(model_args.profile_torch_memory_dir)
            # Stop memory snapshot recording
            start_memory_snapshot(False)

    return model_args, data_args, training_args, finetuning_args, generating_args


def export_model(args: Optional[Dict[str, Any]] = None) -> None:
    model_args, data_args, finetuning_args, _ = get_infer_args(args)

    if model_args.export_dir is None:
        raise ValueError("Please specify `export_dir` to save model.")

    if (
        model_args.adapter_name_or_path is not None
        and model_args.export_quantization_bit is not None
    ):
        raise ValueError("Please merge adapters before quantizing the model.")

    tokenizer_module = load_tokenizer(model_args)
    tokenizer = tokenizer_module["tokenizer"]
    processor = tokenizer_module["processor"]
    get_template_and_fix_tokenizer(tokenizer, data_args)
    model = load_model(
        tokenizer, model_args, finetuning_args
    )  # must after fixing tokenizer to resize vocab

    if (
        getattr(model, "quantization_method", None) is not None
        and model_args.adapter_name_or_path is not None
    ):
        raise ValueError("Cannot merge adapters to a quantized model.")

    if not isinstance(model, PreTrainedModel):
        raise ValueError("The model is not a `PreTrainedModel`, export aborted.")

    if (
        getattr(model, "quantization_method", None) is not None
    ):  # quantized model adopts float16 type
        setattr(model.config, "torch_dtype", torch.float16)
    else:
        if model_args.infer_dtype == "auto":
            output_dtype = getattr(model.config, "torch_dtype", torch.float16)
        else:
            output_dtype = getattr(torch, model_args.infer_dtype)

        setattr(model.config, "torch_dtype", output_dtype)
        model = model.to(output_dtype)
        logger.info_rank0(f"Convert model dtype to: {output_dtype}.")

    model.save_pretrained(
        save_directory=model_args.export_dir,
        max_shard_size=f"{model_args.export_size}GB",
        safe_serialization=(not model_args.export_legacy_format),
    )
    if model_args.export_hub_model_id is not None:
        model.push_to_hub(
            model_args.export_hub_model_id,
            token=model_args.hf_hub_token,
            max_shard_size=f"{model_args.export_size}GB",
            safe_serialization=(not model_args.export_legacy_format),
        )

    if finetuning_args.stage == "rm":
        if model_args.adapter_name_or_path is not None:
            vhead_path = model_args.adapter_name_or_path[-1]
        else:
            vhead_path = model_args.model_name_or_path

        if os.path.exists(os.path.join(vhead_path, V_HEAD_SAFE_WEIGHTS_NAME)):
            shutil.copy(
                os.path.join(vhead_path, V_HEAD_SAFE_WEIGHTS_NAME),
                os.path.join(model_args.export_dir, V_HEAD_SAFE_WEIGHTS_NAME),
            )
            logger.info_rank0(f"Copied valuehead to {model_args.export_dir}.")
        elif os.path.exists(os.path.join(vhead_path, V_HEAD_WEIGHTS_NAME)):
            shutil.copy(
                os.path.join(vhead_path, V_HEAD_WEIGHTS_NAME),
                os.path.join(model_args.export_dir, V_HEAD_WEIGHTS_NAME),
            )
            logger.info_rank0(f"Copied valuehead to {model_args.export_dir}.")

    try:
        tokenizer.padding_side = "left"  # restore padding side
        tokenizer.init_kwargs["padding_side"] = "left"
        tokenizer.save_pretrained(model_args.export_dir)
        if model_args.export_hub_model_id is not None:
            tokenizer.push_to_hub(
                model_args.export_hub_model_id, token=model_args.hf_hub_token
            )

        if processor is not None:
            processor.save_pretrained(model_args.export_dir)
            if model_args.export_hub_model_id is not None:
                processor.push_to_hub(
                    model_args.export_hub_model_id, token=model_args.hf_hub_token
                )

    except Exception as e:
        logger.warning_rank0(
            f"Cannot save tokenizer, please copy the files manually: {e}."
        )
