from datasets import concatenate_datasets, load_dataset

code_stratos_scale = load_dataset(
    "mlfoundations-dev/code_stratos_scale_share_gpt", split="train"
)
math_stratos_scale = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated", split="train"
)
science_and_puzzle_stratos_scale = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_annotated_with_answers",
    split="train",
)

# filter for verification
science_and_puzzle_stratos_scale = science_and_puzzle_stratos_scale.filter(
    lambda x: x["correct"]
)
math_stratos_scale = math_stratos_scale.filter(lambda x: x["correct"])


# remove long code examples (longer than context length)
# code_stratos_scale = code_stratos_scale.filter(lambda x: len(x["deepseek_solution"]) < 16384)


stratos_scale = concatenate_datasets(
    [code_stratos_scale, math_stratos_scale, science_and_puzzle_stratos_scale]
)
stratos_scale.push_to_hub("mlfoundations-dev/stratos_verified_mix")
