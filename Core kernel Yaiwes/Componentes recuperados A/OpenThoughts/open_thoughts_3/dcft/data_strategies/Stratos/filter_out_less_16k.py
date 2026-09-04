import os
from functools import partial

from convert import map_to_share_gpt
from datasets import concatenate_datasets, load_dataset
from transformers import AutoTokenizer

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

print(math_dataset_unverified)
print(code_dataset_unverified)
print(science_and_puzzle_dataset_unverified)

tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True
)


def count_tokens(example):
    reasoning_tokens = len(tokenizer.encode(example["reasoning"]))
    solution_tokens = len(tokenizer.encode(example["deepseek_solution"]))
    problem_tokens = len(tokenizer.encode(example["problem"]))
    example["reasoning_tokens"] = reasoning_tokens
    example["solution_tokens"] = solution_tokens
    example["total_tokens"] = reasoning_tokens + solution_tokens + problem_tokens
    example["problem_tokens"] = problem_tokens
    return example


math_dataset_unverified = math_dataset_unverified.map(count_tokens, num_proc=num_cpus)
code_dataset_unverified = code_dataset_unverified.map(count_tokens, num_proc=num_cpus)
science_and_puzzle_dataset_unverified = science_and_puzzle_dataset_unverified.map(
    count_tokens, num_proc=num_cpus
)

for dataset, name in [
    (math_dataset_unverified, "Math"),
    (code_dataset_unverified, "Code"),
    (science_and_puzzle_dataset_unverified, "Science & Puzzle"),
]:
    print(f"\n{name} Dataset Token Statistics:")
    print(
        f"Average problem tokens: {sum(dataset['problem_tokens']) / len(dataset):.2f}"
    )
    print(
        f"Average reasoning tokens: {sum(dataset['reasoning_tokens']) / len(dataset):.2f}"
    )
    print(
        f"Average solution tokens: {sum(dataset['solution_tokens']) / len(dataset):.2f}"
    )
    print(f"Average total tokens: {sum(dataset['total_tokens']) / len(dataset):.2f}")

for dataset, name in [
    (math_dataset_unverified, "Math"),
    (code_dataset_unverified, "Code"),
    (science_and_puzzle_dataset_unverified, "Science & Puzzle"),
]:
    num_over_16k = len([x for x in dataset["total_tokens"] if x > 16384])
    print(f"\n{name} Dataset Over 16k Tokens:")
    print(f"Number of rows with >16k tokens: {num_over_16k}")
    print(f"Percentage of dataset: {(num_over_16k/len(dataset))*100:.2f}%")

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


def count_formatted_tokens(example):
    formatted_text = tokenizer.apply_chat_template(
        example["conversations"], tokenize=False
    )
    example["formatted_text"] = formatted_text
    example["total_templated_tokens"] = len(tokenizer.encode(formatted_text))
    return example


# Count tokens on the converted datasets
math_dataset_unverified_converted = math_dataset_unverified_converted.map(
    count_formatted_tokens, num_proc=num_cpus
)
code_dataset_unverified_converted = code_dataset_unverified_converted.map(
    count_formatted_tokens, num_proc=num_cpus
)
science_and_puzzle_dataset_unverified_converted = (
    science_and_puzzle_dataset_unverified_converted.map(
        count_formatted_tokens, num_proc=num_cpus
    )
)

# Print statistics for the formatted datasets
for dataset, name in [
    (math_dataset_unverified_converted, "Math"),
    (code_dataset_unverified_converted, "Code"),
    (science_and_puzzle_dataset_unverified_converted, "Science & Puzzle"),
]:
    print(f"\n{name} Dataset Token Statistics (with chat template):")
    print(
        f"Average total tokens: {sum(dataset['total_templated_tokens']) / len(dataset):.2f}"
    )

    num_over_16k = len([x for x in dataset["total_templated_tokens"] if x > 16384])
    print(f"Number of rows with >16k tokens: {num_over_16k}")
    print(f"Percentage of dataset: {(num_over_16k/len(dataset))*100:.2f}%")

# Calculate combined statistics
all_tokens = (
    math_dataset_unverified_converted["total_templated_tokens"]
    + code_dataset_unverified_converted["total_templated_tokens"]
    + science_and_puzzle_dataset_unverified_converted["total_templated_tokens"]
)
total_rows = (
    len(math_dataset_unverified_converted)
    + len(code_dataset_unverified_converted)
    + len(science_and_puzzle_dataset_unverified_converted)
)

print(f"\nCombined Dataset Token Statistics (with chat template):")
print(f"Average total tokens: {sum(all_tokens) / total_rows:.2f}")

num_over_16k_combined = len([x for x in all_tokens if x > 16384])
print(f"Number of rows with >16k tokens: {num_over_16k_combined}")
print(f"Percentage of dataset: {(num_over_16k_combined/total_rows)*100:.2f}%")

# math_dataset_unverified_converted.push_to_hub("mlfoundations-dev/math_stratos_scale_unverified_converted_with_counts")
# code_dataset_unverified_converted.push_to_hub("mlfoundations-dev/code_stratos_scale_unverified_converted_with_counts")
# science_and_puzzle_dataset_unverified_converted.push_to_hub("mlfoundations-dev/science_and_puzzle_stratos_scale_unverified_converted_with_counts")

math_dataset_unverified_converted_filtered = math_dataset_unverified_converted.filter(
    lambda x: x["total_templated_tokens"] < 16384, num_proc=num_cpus
)
code_dataset_unverified_converted_filtered = code_dataset_unverified_converted.filter(
    lambda x: x["total_templated_tokens"] < 16384, num_proc=num_cpus
)
science_and_puzzle_dataset_unverified_converted_filtered = (
    science_and_puzzle_dataset_unverified_converted.filter(
        lambda x: x["total_templated_tokens"] < 16384, num_proc=num_cpus
    )
)

# Remap conversations since we need to use from and value instead of role and content
math_dataset_unverified_converted_filtered = (
    math_dataset_unverified_converted_filtered.remove_columns(["conversations"])
)
code_dataset_unverified_converted_filtered = (
    code_dataset_unverified_converted_filtered.remove_columns(["conversations"])
)
science_and_puzzle_dataset_unverified_converted_filtered = (
    science_and_puzzle_dataset_unverified_converted_filtered.remove_columns(
        ["conversations"]
    )
)

math_dataset_unverified_converted_filtered = (
    math_dataset_unverified_converted_filtered.map(
        partial(map_to_share_gpt, user_column="problem", math=True), num_proc=num_cpus
    )
)
code_dataset_unverified_converted_filtered = (
    code_dataset_unverified_converted_filtered.map(
        partial(map_to_share_gpt, user_column="prompt_formatted", code=True),
        num_proc=num_cpus,
    )
)
science_and_puzzle_dataset_unverified_converted_filtered = (
    science_and_puzzle_dataset_unverified_converted_filtered.map(
        partial(map_to_share_gpt, user_column="problem"), num_proc=num_cpus
    )
)

unverified_stratos_mix_below_16394_cutoff = concatenate_datasets(
    [
        math_dataset_unverified_converted_filtered,
        code_dataset_unverified_converted_filtered,
        science_and_puzzle_dataset_unverified_converted_filtered,
    ]
)
# unverified_stratos_mix_below_16394_cutoff.push_to_hub("mlfoundations-dev/unverified_stratos_mix_below_16384_cutoff")

math_dataset_verified_converted_filtered = (
    math_dataset_unverified_converted_filtered.filter(
        lambda x: x["correct"], num_proc=num_cpus
    )
)
code_dataset_verified_converted_filtered = (
    code_dataset_unverified_converted_filtered.filter(
        lambda x: x["correctness"], num_proc=num_cpus
    )
)
science_and_puzzle_dataset_verified_converted_filtered = (
    science_and_puzzle_dataset_unverified_converted_filtered
)

verified_stratos_mix_below_16394_cutoff = concatenate_datasets(
    [
        math_dataset_verified_converted_filtered,
        code_dataset_verified_converted_filtered,
        science_and_puzzle_dataset_verified_converted_filtered,
    ]
)
# verified_stratos_mix_below_16394_cutoff.push_to_hub("mlfoundations-dev/verified_stratos_mix_below_16384_cutoff")
verified_stratos_mix_below_16394_cutoff.select_columns(
    ["system", "conversations"]
).push_to_hub(
    "mlfoundations-dev/verified_stratos_mix_below_16384_cutoff_without_metadata"
)
