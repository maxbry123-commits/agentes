import os

from datasets import concatenate_datasets, load_dataset

ds = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated_with_difficulty",
    split="train",
)
print("Total math problems:", f"{len(ds):,}")  # 140,075

prove = ds.filter(lambda x: "prove " in x["problem"].lower(), num_proc=os.cpu_count())
show = ds.filter(lambda x: "show " in x["problem"].lower(), num_proc=os.cpu_count())

print("Problems with 'prove ':", f"{len(prove):,}")  # 25,094
print("Problems with 'show ':", f"{len(show):,}")  # 7,825

incorrect_ds = ds.filter(lambda x: not x["correct"], num_proc=os.cpu_count())
print("Incorrect problems:", f"{len(incorrect_ds):,}")

prove_incorrect = incorrect_ds.filter(
    lambda x: "prove " in x["problem"].lower(), num_proc=os.cpu_count()
)
show_incorrect = incorrect_ds.filter(
    lambda x: "show " in x["problem"].lower(), num_proc=os.cpu_count()
)

print("Incorrect problems with 'prove':", f"{len(prove_incorrect):,}")
print("Incorrect problems with 'show':", f"{len(show_incorrect):,}")

correct_ds = ds.filter(lambda x: x["correct"], num_proc=os.cpu_count())
print("Correct problems:", f"{len(correct_ds):,}")

prove_correct = correct_ds.filter(
    lambda x: "prove " in x["problem"].lower(), num_proc=os.cpu_count()
)
show_correct = correct_ds.filter(
    lambda x: "show " in x["problem"].lower(), num_proc=os.cpu_count()
)

print("Correct problems with 'prove ':", f"{len(prove_correct):,}")
print("Correct problems with 'show ':", f"{len(show_correct):,}")

# Sample 5 problems from each difficulty level for each category
samples = []

for difficulty in range(1, 11):
    # Correct problems with 'prove'
    prove_correct_difficulty = prove_correct.filter(
        lambda x: x["difficulty"] == difficulty
    )
    prove_correct_sample = prove_correct_difficulty.shuffle(seed=42).select(range(5))

    # Correct problems with 'show'
    show_correct_difficulty = show_correct.filter(
        lambda x: x["difficulty"] == difficulty
    )
    show_correct_sample = show_correct_difficulty.shuffle(seed=42).select(range(5))

    # Incorrect problems with 'prove'
    prove_incorrect_difficulty = prove_incorrect.filter(
        lambda x: x["difficulty"] == difficulty
    )
    prove_incorrect_sample = prove_incorrect_difficulty.shuffle(seed=42).select(
        range(5)
    )

    # Incorrect problems with 'show'
    show_incorrect_difficulty = show_incorrect.filter(
        lambda x: x["difficulty"] == difficulty
    )
    show_incorrect_sample = show_incorrect_difficulty.shuffle(seed=42).select(range(5))

    samples.extend(
        [
            prove_correct_sample,
            show_correct_sample,
            prove_incorrect_sample,
            show_incorrect_sample,
        ]
    )

# Combine all samples into one dataset
combined_ds = concatenate_datasets(samples)

# combine together into a dataset and save to json in downloads folder
downloads_path = os.path.expanduser("~/Downloads")
combined_json_path = os.path.join(downloads_path, "combined_problems.jsonl")
combined_ds.to_json(combined_json_path)

ds = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated_with_difficulty_incorrect_and_hardest_reannnotated_twice",
    split="train",
)
print("Total hardest incorrect problems:", f"{len(ds):,}")

prove_incorrect_ds = ds.filter(
    lambda x: "prove " in x["problem"].lower(), num_proc=os.cpu_count()
)
show_incorrect_ds = ds.filter(
    lambda x: "show " in x["problem"].lower(), num_proc=os.cpu_count()
)

print("Hardest incorrect problems with 'prove ':", f"{len(prove_incorrect_ds):,}")
print("Hardest incorrect problems with 'show ':", f"{len(show_incorrect_ds):,}")

ds = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated_with_difficulty_incorrect_and_hardest_reannotated",
    split="train",
)
print(
    "Total hard incorrect problems that are now correct after 3 tries:", f"{len(ds):,}"
)

prove_incorrect_ds = ds.filter(
    lambda x: "prove " in x["problem"].lower(), num_proc=os.cpu_count()
)
show_incorrect_ds = ds.filter(
    lambda x: "show " in x["problem"].lower(), num_proc=os.cpu_count()
)

print(
    "Hard incorrect now correct problems with 'prove ':", f"{len(prove_incorrect_ds):,}"
)
print(
    "Hard incorrect now correct problems with 'show ':", f"{len(show_incorrect_ds):,}"
)

prove_incorrect_ds.push_to_hub("mlfoundations-dev/correct_after_3_tries_prove")
show_incorrect_ds.push_to_hub("mlfoundations-dev/correct_after_3_tries_show")

# Get downloads folder path
downloads_path = os.path.expanduser("~/Downloads")

# Save prove dataset
prove_jsonl_path = os.path.join(downloads_path, "correct_after_3_tries_prove.jsonl")
prove_incorrect_ds.to_json(prove_jsonl_path)

# Save show dataset
show_jsonl_path = os.path.join(downloads_path, "correct_after_3_tries_show.jsonl")
show_incorrect_ds.to_json(show_jsonl_path)
