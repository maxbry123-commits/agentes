from datasets import concatenate_datasets, load_dataset

code_stratos_scale = load_dataset(
    "mlfoundations-dev/code_stratos_scale_rejection_sampled_test", split="train"
)
math_stratos_scale = load_dataset(
    "mlfoundations-dev/math_stratos_scale_verified_with_hf", split="train"
)
science_and_puzzle_stratos_scale = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_annotated_with_answers",
    split="train",
)

# filter for verification
science_and_puzzle_stratos_scale = science_and_puzzle_stratos_scale.filter(
    lambda x: x["correct"]
)
math_stratos_scale = math_stratos_scale.filter(lambda x: x["verifier_label"])
code_stratos_scale = code_stratos_scale.filter(lambda x: x["correctness"])

stratos_scale = concatenate_datasets(
    [code_stratos_scale, math_stratos_scale, science_and_puzzle_stratos_scale]
)
stratos_scale.push_to_hub("mlfoundations-dev/stratos_new_verified_mix")
