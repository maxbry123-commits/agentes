from functools import partial

from convert import map_to_share_gpt
from datasets import concatenate_datasets, load_dataset

science_and_puzzle_stratos_scale_unverified = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_annotated"
)[
    "train"
]  # noqa
science_and_puzzle_stratos_scale_unverified = (
    science_and_puzzle_stratos_scale_unverified.map(
        partial(map_to_share_gpt, user_column="problem")
    )
)  # noqa
science_and_puzzle_stratos_scale_unverified = (
    science_and_puzzle_stratos_scale_unverified.select_columns(
        ["system", "conversations"]
    )
)

math_stratos_scale_unverified = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated"
)[
    "train"
]  # noqa
math_stratos_scale_unverified = math_stratos_scale_unverified.map(
    partial(map_to_share_gpt, user_column="problem", math=True)
)  # noqa
math_stratos_scale_unverified = math_stratos_scale_unverified.select_columns(
    ["system", "conversations"]
)

code_stratos_scale_unverified = load_dataset(
    "mlfoundations-dev/code_stratos_scale_annotated"
)[
    "train"
]  # noqa
code_stratos_scale_unverified = code_stratos_scale_unverified.map(
    partial(map_to_share_gpt, user_column="prompt_formatted", code=True)
)  # noqa
code_stratos_scale_unverified = code_stratos_scale_unverified.select_columns(
    ["system", "conversations"]
)

unverified_mix = concatenate_datasets(
    [
        code_stratos_scale_unverified,
        science_and_puzzle_stratos_scale_unverified,
        math_stratos_scale_unverified,
    ]
)
print(unverified_mix)

unverified_mix.push_to_hub("mlfoundations-dev/stratos_unverified_mix")
