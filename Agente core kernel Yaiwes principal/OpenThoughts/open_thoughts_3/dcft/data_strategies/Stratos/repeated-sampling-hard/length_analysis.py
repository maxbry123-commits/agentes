import os

import matplotlib.pyplot as plt
import pandas as pd
from datasets import load_dataset
from transformers import AutoTokenizer

num_cpus = os.cpu_count()
dataset = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated_with_difficulty",
    split="train",
)

# Initialize tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True
)


# Define function to count tokens
def count_tokens(example):
    example["reasoning_tokens"] = len(tokenizer.encode(example["reasoning"]))
    example["solution_tokens"] = len(tokenizer.encode(example["deepseek_solution"]))
    return example


# Compute token lengths efficiently using parallel processing
dataset = dataset.map(count_tokens, num_proc=num_cpus)

# Convert to pandas DataFrame after token counting
df = pd.DataFrame(dataset)

# Calculate average lengths and counts for each difficulty level and correctness
results = (
    df.groupby("difficulty")
    .agg(
        {
            "correct": ["mean", "count", "sum"],
            "reasoning_tokens": "mean",  # Now using pre-computed token counts
            "solution_tokens": "mean",  # Now using pre-computed token counts
        }
    )
    .reset_index()
)

# Calculate separate stats for correct vs incorrect
correct_stats = (
    df[df["correct"]]
    .groupby("difficulty")
    .agg({"reasoning_tokens": "mean", "solution_tokens": "mean"})
    .reset_index()
)

incorrect_stats = (
    df[~df["correct"]]
    .groupby("difficulty")
    .agg({"reasoning_tokens": "mean", "solution_tokens": "mean"})
    .reset_index()
)

# Create subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Plot reasoning lengths
ax1.plot(
    correct_stats["difficulty"],
    correct_stats["reasoning_tokens"],
    marker="o",
    label="Correct",
    color="green",
)
ax1.plot(
    incorrect_stats["difficulty"],
    incorrect_stats["reasoning_tokens"],
    marker="o",
    label="Incorrect",
    color="red",
)
ax1.set_xlabel("Difficulty Level")
ax1.set_ylabel("Average Reasoning Length (tokens)")
ax1.set_title("Reasoning Length by Difficulty and Correctness")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot solution lengths
ax2.plot(
    correct_stats["difficulty"],
    correct_stats["solution_tokens"],
    marker="o",
    label="Correct",
    color="green",
)
ax2.plot(
    incorrect_stats["difficulty"],
    incorrect_stats["solution_tokens"],
    marker="o",
    label="Incorrect",
    color="red",
)
ax2.set_xlabel("Difficulty Level")
ax2.set_ylabel("Average Solution Length (tokens)")
ax2.set_title("Solution Length by Difficulty and Correctness")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Print detailed statistics
print("\nDetailed Statistics:")
for difficulty in sorted(df["difficulty"].unique()):
    correct_mask = (df["difficulty"] == difficulty) & df["correct"]
    incorrect_mask = (df["difficulty"] == difficulty) & ~df["correct"]

    print(f"\nDifficulty {difficulty:.0f}:")
    print(
        f"Correct answers   (n={correct_mask.sum():4d}): "
        f"Reasoning {df[correct_mask]['reasoning_tokens'].mean():6.0f} tokens, "
        f"Solution {df[correct_mask]['solution_tokens'].mean():6.0f} tokens"
    )
    print(
        f"Incorrect answers (n={incorrect_mask.sum():4d}): "
        f"Reasoning {df[incorrect_mask]['reasoning_tokens'].mean():6.0f} tokens, "
        f"Solution {df[incorrect_mask]['solution_tokens'].mean():6.0f} tokens"
    )
