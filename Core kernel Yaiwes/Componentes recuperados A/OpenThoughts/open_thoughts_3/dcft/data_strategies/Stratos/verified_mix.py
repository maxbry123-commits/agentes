from datasets import concatenate_datasets, load_dataset

code_stratos_scale = load_dataset("mlfoundations-dev/code_stratos_scale_share_gpt")[
    "train"
]
math_stratos_scale = load_dataset("mlfoundations-dev/math_stratos_scale_share_gpt")[
    "train"
]
science_and_puzzle_stratos_scale = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_share_gpt"
)["train"]

stratos_scale = concatenate_datasets(
    [code_stratos_scale, math_stratos_scale, science_and_puzzle_stratos_scale]
)
stratos_scale.push_to_hub("mlfoundations-dev/stratos_verified_mix")
