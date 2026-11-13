import os
from functools import partial

from datasets import concatenate_datasets, load_dataset

from dcft.data_strategies.Stratos.convert import map_to_share_gpt

num_cpus = os.cpu_count()

math_dataset_unverified = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated", split="train"
)
code_dataset_unverified = load_dataset(
    "mlfoundations-dev/code_stratos_scale_rejection_sampled_test", split="train"
)
science_and_puzzle_dataset_unverified = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_annotated_with_answers",
    split="train",
)

math_dataset_unverified_converted = math_dataset_unverified.map(
    partial(
        map_to_share_gpt,
        user_column="problem",
        value_word="content",
        key_word="role",
        math=True,
    ),
    num_proc=num_cpus,
)
code_dataset_unverified_converted = code_dataset_unverified.map(
    partial(
        map_to_share_gpt,
        value_word="content",
        user_column="prompt_formatted",
        key_word="role",
        code=True,
    ),
    num_proc=num_cpus,
)
science_and_puzzle_dataset_unverified_converted = (
    science_and_puzzle_dataset_unverified.map(
        partial(
            map_to_share_gpt,
            value_word="content",
            user_column="problem",
            key_word="role",
        ),
        num_proc=num_cpus,
    )
)

math_dataset_unverified_converted_no_proofs = math_dataset_unverified_converted.filter(
    lambda x: "show " not in x["problem"].lower()
    and "prove " not in x["problem"].lower(),
    num_proc=num_cpus,
)
unverified_stratos_mix_no_proofs = concatenate_datasets(
    [
        math_dataset_unverified_converted_no_proofs,
        code_dataset_unverified_converted,
        science_and_puzzle_dataset_unverified_converted,
    ]
)
unverified_stratos_mix_no_proofs.select_columns(
    ["system", "conversations"]
).push_to_hub("mlfoundations-dev/unverified_stratos_mix_no_proofs_without_metadata")

math_dataset_verified_converted_no_proofs = (
    math_dataset_unverified_converted_no_proofs.filter(
        lambda x: x["correct"], num_proc=num_cpus
    )
)
code_dataset_verified_converted = code_dataset_unverified_converted.filter(
    lambda x: x["correctness"], num_proc=num_cpus
)
science_and_puzzle_dataset_verified_converted = (
    science_and_puzzle_dataset_unverified_converted
)

verified_stratos_mix_no_proofs = concatenate_datasets(
    [
        math_dataset_verified_converted_no_proofs,
        code_dataset_verified_converted,
        science_and_puzzle_dataset_verified_converted,
    ]
)
verified_stratos_mix_no_proofs.select_columns(["system", "conversations"]).push_to_hub(
    "mlfoundations-dev/verified_stratos_mix_no_proofs_without_metadata"
)
