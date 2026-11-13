import dataclasses
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import argparse


@dataclass
class LlamaFactoryArgs:
    """Arguments for LlamaFactory training"""

    # Model arguments
    model_name_or_path: Optional[str] = field(
        default=None,
        metadata={
            "help": "Path to pretrained model or model identifier from huggingface.co/models"
        },
    )

    # Method arguments
    stage: Optional[str] = field(
        default=None, metadata={"help": "Training stage: sft, rm, ppo, dpo"}
    )
    do_train: Optional[bool] = field(
        default=None, metadata={"help": "Whether to run training or not"}
    )
    finetuning_type: Optional[str] = field(
        default=None, metadata={"help": "Finetuning type: full, lora, qlora"}
    )
    deepspeed: Optional[str] = field(
        default="dcft/train/zero3.json",
        metadata={"help": "Path to deepspeed config file"},
    )
    packing: Optional[bool] = field(
        default=None,
        metadata={"help": "Whether to pack multiple sequences into one batch"},
    )
    neat_packing: Optional[bool] = field(
        default=None, metadata={"help": "Whether to use neat packing"}
    )
    enable_liger_kernel: Optional[bool] = field(
        default=None, metadata={"help": "Whether to use liger kernel"}
    )

    # Dataset arguments
    dataset: Optional[str] = field(
        default=None,
        metadata={
            "help": "Dataset identifier from huggingface.co/datasets or local dataset"
        },
    )
    dataset_dir: Optional[str] = field(
        default=None, metadata={"help": "Directory containing dataset files"}
    )
    template: Optional[str] = field(
        default=None, metadata={"help": "Chat template to use"}
    )
    system: Optional[str] = field(
        default=None, metadata={"help": "System column in dataset"}
    )
    messages: Optional[str] = field(
        default="conversations", metadata={"help": "Message column in dataset"}
    )
    cutoff_len: Optional[int] = field(
        default=None, metadata={"help": "Maximum length of input sequences"}
    )
    overwrite_cache: Optional[bool] = field(
        default=None,
        metadata={
            "help": "Whether to overwrite the cached training and evaluation sets"
        },
    )
    preprocessing_num_workers: Optional[int] = field(
        default=None, metadata={"help": "Number of workers for preprocessing"}
    )
    role_tag: Optional[str] = field(
        default="from", metadata={"help": "Role tag for the dataset"}
    )
    user_tag: Optional[str] = field(
        default="human", metadata={"help": "User tag for the dataset"}
    )
    content_tag: Optional[str] = field(
        default="value", metadata={"help": "Content tag for the dataset"}
    )
    assistant_tag: Optional[str] = field(
        default="gpt", metadata={"help": "Assistant tag for the dataset"}
    )

    # Output arguments
    save_strategy: Optional[str] = field(
        default=None, metadata={"help": "The checkpoint save strategy to use"}
    )
    output_dir: Optional[str] = field(
        default=None, metadata={"help": "Directory to store the model checkpoints"}
    )
    logging_steps: Optional[int] = field(
        default=None, metadata={"help": "Log metrics every X updates steps"}
    )
    plot_loss: Optional[bool] = field(
        default=None, metadata={"help": "Whether to plot losses"}
    )
    overwrite_output_dir: Optional[bool] = field(
        default=None, metadata={"help": "Whether to overwrite the output directory"}
    )

    # Training arguments
    per_device_train_batch_size: Optional[int] = field(
        default=None, metadata={"help": "Batch size per GPU for training"}
    )
    gradient_accumulation_steps: Optional[int] = field(
        default=None,
        metadata={"help": "Number of updates steps to accumulate before backward"},
    )
    global_batch_size: Optional[int] = field(
        default=None, metadata={"help": "Global batch size across all devices"}
    )
    gradient_checkpointing: Optional[bool] = field(
        default=None,
        metadata={"help": "Whether to use gradient checkpointing to save memory"},
    )
    learning_rate: Optional[float] = field(
        default=None, metadata={"help": "The initial learning rate"}
    )
    num_train_epochs: Optional[int] = field(
        default=None, metadata={"help": "Total number of training epochs"}
    )
    lr_scheduler_type: Optional[str] = field(
        default=None, metadata={"help": "The scheduler type to use"}
    )
    warmup_ratio: Optional[float] = field(
        default=None, metadata={"help": "Linear warmup ratio"}
    )
    bf16: Optional[bool] = field(
        default=None, metadata={"help": "Whether to use bf16 mixed precision"}
    )
    ddp_timeout: Optional[int] = field(default=None, metadata={"help": "DDP timeout"})
    report_to: Optional[str] = field(default=None, metadata={"help": "Report to wandb"})
    run_name: Optional[str] = field(
        default=None, metadata={"help": "Run name for wandb"}
    )
    use_unsloth_gc: Optional[bool] = field(
        default=None, metadata={"help": "Whether to use unsloth gc", "store_true": True}
    )

    # Eval arguments
    eval_strategy: Optional[str] = field(
        default=None, metadata={"help": "The evaluation strategy to use"}
    )
    push_to_db: Optional[bool] = field(
        default=None, metadata={"help": "Whether to push to database"}
    )
    push_to_hub: Optional[bool] = field(
        default=None, metadata={"help": "Whether to push to hub"}
    )
    hub_model_id: Optional[str] = field(
        default=None, metadata={"help": "Repo name to push to hub"}
    )

    # Extra arguments that might be used depending on finetuning type
    lora_rank: Optional[int] = field(default=None, metadata={"help": "Rank of LoRA"})
    lora_alpha: Optional[float] = field(
        default=None, metadata={"help": "Alpha of LoRA"}
    )
    lora_dropout: Optional[float] = field(
        default=None, metadata={"help": "Dropout of LoRA"}
    )


@dataclass
class EvalArgs:
    """Arguments for evaluation"""
    eval_tasks: Optional[str] = field(
        default=None, metadata={"help": "Comma-separated list of tasks to evaluate"}
    )
    eval_num_nodes: Optional[int] = field(
        default=None, metadata={"help": "Number of nodes to evaluate"}
    )
    eval_time_limit: Optional[int] = field(
        default=None, metadata={"help": "Time limit for evaluation"}
    )

@dataclass
class LaunchArgs:
    """Arguments for job launching"""

    # Core launch arguments
    job_name: Optional[str] = field(
        default=None, metadata={"help": "Job name. This will determine outputs, including HF repo."}
    )
    train_sbatch_path: Optional[str] = field(
        default=None, metadata={"help": "Path to training sbatch file"}
    )
    train_config_path: Optional[str] = field(
        default=None, metadata={"help": "Path to config file"}
    )
    experiments_dir: Optional[str] = field(
        default="experiments",
        metadata={
            "help": "Output for storing experiment outputs - logs, configs, sbatch scripts"
        },
    )
    image: Optional[str] = field(
        default=None, metadata={"help": "Container image to use"}
    )
    checkpoints_dir: Optional[str] = field(
        default=None, metadata={"help": "Checkpoints directory"}
    )
    models_dir: Optional[str] = field(
        default=None, metadata={"help": "Models directory"}
    )
    datasets_dir: Optional[str] = field(
        default=None, metadata={"help": "Datasets directory"}
    )
    tokenized_dir: Optional[str] = field(
        default=None, metadata={"help": "Tokenized datasets directory"}
    )
    base_model: Optional[str] = field(
        default=None, metadata={"help": "Base model name for output directory naming"}
    )
    chat_template: Optional[str] = field(
        default=None, metadata={"help": "Chat template to use"}
    )
    time_limit: Optional[str] = field(
        default=None, metadata={"help": "Time limit for the job"}
    )
    max_restarts: Optional[int] = field(
        default=None, metadata={"help": "Maximum number of job restarts"}
    )

    # Pretokenize
    pretokenize: bool = field(
        default=False, metadata={"help": "Whether to pretokenize", "store_true": True}
    )
    pretok_large: bool = field(
        default=False, metadata={"help": "If true, pretokenize on boost_qos_bprod 128 nodes", "store_true": True}
    )

    # Job parameters
    num_nodes: Optional[int] = field(
        default=None, metadata={"help": "Number of nodes to use"}
    )
    num_gpus: Optional[int] = field(
        default=None, metadata={"help": "Number of GPUs per node to use"}
    )

    # Dry run
    dry_run: bool = field(
        default=False,
        metadata={
            "help": "When present, the job will not be submitted",
            "store_true": True,
        },
    )


def _add_dataclass_arguments(arg_group, dataclass_type, exclude_fields=None):
    """
    Helper function to add arguments from a dataclass to an argument group.

    Args:
        arg_group: The argument group to add arguments to
        dataclass_type: The dataclass type to extract fields from
        exclude_fields: Optional list of field names to exclude
    """
    exclude_fields = exclude_fields or []

    for field in dataclasses.fields(dataclass_type):
        if field.name in exclude_fields:
            continue

        if field.metadata.get("store_true"):
            arg_group.add_argument(
                f"--{field.name}",
                action="store_true",
                help=field.metadata.get("help"),
                default=field.default,
            )
        else:
            arg_group.add_argument(
                f"--{field.name}",
                type=type(field.default) if field.default is not None else str,
                help=field.metadata.get("help"),
                default=field.default,
            )


def parse_args():
    parser = argparse.ArgumentParser(description="Launch HPC jobs for dcft experiment")

    # Create argument groups for better organization
    launch_group = parser.add_argument_group("Launch Arguments")
    hpc_group = parser.add_argument_group("HPC Arguments")
    train_group = parser.add_argument_group("Training Arguments")
    eval_group = parser.add_argument_group("Evaluation Arguments")

    # Add LaunchArgs arguments
    _add_dataclass_arguments(launch_group, LaunchArgs)

    # Add HPC arguments
    # Note: HPC is a Pydantic model, not a dataclass, so we need to handle it differently
    hpc_fields = [
        "name",
        "account",
        "partition",
        "gpus_per_node",
        "cpus_per_node",
        "gpus_type",
        "total_partition_nodes",
        "qos",
    ]
    for field in hpc_fields:
        hpc_group.add_argument(
            f"--{field}",
            type=(
                str
                if field == "name"
                or field == "account"
                or field == "partition"
                or field == "gpus_type"
                or field == "qos"
                else int
            ),
            help=f"HPC {field}",
        )

    # Add LlamaFactoryArgs arguments
    _add_dataclass_arguments(train_group, LlamaFactoryArgs)

    # Add EvalArgs arguments
    _add_dataclass_arguments(eval_group, EvalArgs, exclude_fields=["tasks"])

    args = parser.parse_args()
    args_dict = {k: v for k, v in vars(args).items() if v is not None}
    return args_dict
