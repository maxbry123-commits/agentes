import os

import matplotlib.pyplot as plt
import numpy as np
from datasets import load_dataset
from transformers import AutoTokenizer

# Load both datasets
dataset_r1 = load_dataset("simplescaling/s1K-with-deepseek-r1", split="train")
dataset_s12 = load_dataset("simplescaling/s1K-claude-3-7-sonnet", split="train")

print("R1 Dataset:", dataset_r1)
print("S1.2 Dataset:", dataset_s12)

tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True
)


def count_tokens_r1(example):
    example["question_num_tokens"] = len(tokenizer.encode(example["question"]))
    # R1
    r1_conversation = [
        {"role": "user", "content": example["question"]},
        {
            "role": "assistant",
            "content": example["deepseek_thinking_trajectory"]
            + example["deepseek_attempt"],
        },
    ]
    example["r1_thinking_trajectory_num_tokens"] = len(
        tokenizer.encode(example["deepseek_thinking_trajectory"])
    )
    example["r1_attempt_num_tokens"] = len(
        tokenizer.encode(example["deepseek_attempt"])
    )
    example["r1_templated_num_tokens"] = len(
        tokenizer.apply_chat_template(r1_conversation)
    )
    # Gemini
    gemini_conversation = [
        {"role": "user", "content": example["question"]},
        {
            "role": "assistant",
            "content": example["gemini_thinking_trajectory"]
            + example["gemini_attempt"],
        },
    ]
    example["gemini_thinking_trajectory_num_tokens"] = len(
        tokenizer.encode(example["gemini_thinking_trajectory"])
    )
    example["gemini_attempt_num_tokens"] = len(
        tokenizer.encode(example["gemini_attempt"])
    )
    example["gemini_templated_num_tokens"] = len(
        tokenizer.apply_chat_template(gemini_conversation)
    )
    return example


def count_tokens_s12(example):
    example["question_num_tokens"] = len(tokenizer.encode(example["question"]))
    # Claude
    claude_conversation = [
        {"role": "user", "content": example["question"]},
        {
            "role": "assistant",
            "content": example["claude_thinking_trajectory"]
            + example["claude_attempt"],
        },
    ]
    example["claude_thinking_trajectory_num_tokens"] = len(
        tokenizer.encode(example["claude_thinking_trajectory"])
    )
    example["claude_attempt_num_tokens"] = len(
        tokenizer.encode(example["claude_attempt"])
    )
    example["claude_templated_num_tokens"] = len(
        tokenizer.apply_chat_template(claude_conversation)
    )
    return example


num_cpus = os.cpu_count()
counts_r1 = dataset_r1.map(count_tokens_r1, num_proc=num_cpus)
counts_s12 = dataset_s12.map(count_tokens_s12, num_proc=num_cpus)

# Calculate common bins for thinking trajectories
thinking_min = min(
    min(counts_r1["r1_thinking_trajectory_num_tokens"]),
    min(counts_r1["gemini_thinking_trajectory_num_tokens"]),
    min(counts_s12["claude_thinking_trajectory_num_tokens"]),
)
thinking_max = max(
    max(counts_r1["r1_thinking_trajectory_num_tokens"]),
    max(counts_r1["gemini_thinking_trajectory_num_tokens"]),
    max(counts_s12["claude_thinking_trajectory_num_tokens"]),
)
thinking_bins = np.linspace(thinking_min, thinking_max, 50)

# Set global font sizes
plt.rcParams.update(
    {
        "font.size": 16,
        "axes.titlesize": 20,
        "axes.labelsize": 18,
        "xtick.labelsize": 16,
        "ytick.labelsize": 16,
        "legend.fontsize": 16,
        "figure.titlesize": 24,
    }
)

# Create overlaid plot for thinking trajectories
plt.figure(figsize=(14, 8))
plt.hist(
    counts_r1["r1_thinking_trajectory_num_tokens"],
    bins=thinking_bins,
    color="blue",
    alpha=0.5,
    label="R1 Thinking",
)
plt.hist(
    counts_r1["gemini_thinking_trajectory_num_tokens"],
    bins=thinking_bins,
    color="red",
    alpha=0.5,
    label="Gemini Thinking",
)
plt.hist(
    counts_s12["claude_thinking_trajectory_num_tokens"],
    bins=thinking_bins,
    color="purple",
    alpha=0.5,
    label="Claude Thinking",
)
plt.title("Thinking Trajectory Token Count Distribution Comparison")
plt.xlabel("Number of Tokens")
plt.ylabel("Frequency")
plt.legend()
plt.tight_layout()
plt.show()

# Create figure for thinking trajectories with subplots
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 14))
fig.suptitle("Thinking Trajectory Token Count Distributions")

# Plot thinking trajectory counts in separate subplots
ax1.hist(
    counts_r1["r1_thinking_trajectory_num_tokens"],
    bins=thinking_bins,
    color="blue",
    alpha=0.7,
)
ax1.set_title("R1 Thinking")
ax1.set_ylabel("Frequency")

ax2.hist(
    counts_r1["gemini_thinking_trajectory_num_tokens"],
    bins=thinking_bins,
    color="red",
    alpha=0.7,
)
ax2.set_title("Gemini Thinking")
ax2.set_ylabel("Frequency")

ax3.hist(
    counts_s12["claude_thinking_trajectory_num_tokens"],
    bins=thinking_bins,
    color="purple",
    alpha=0.7,
)
ax3.set_title("Claude Thinking")
ax3.set_xlabel("Number of Tokens")
ax3.set_ylabel("Frequency")

plt.tight_layout()
plt.show()

# Calculate common bins for attempts
attempt_min = min(
    min(counts_r1["r1_attempt_num_tokens"]),
    min(counts_r1["gemini_attempt_num_tokens"]),
    min(counts_s12["claude_attempt_num_tokens"]),
)
attempt_max = max(
    max(counts_r1["r1_attempt_num_tokens"]),
    max(counts_r1["gemini_attempt_num_tokens"]),
    max(counts_s12["claude_attempt_num_tokens"]),
)
attempt_bins = np.linspace(attempt_min, attempt_max, 50)

# Create overlaid plot for attempts
plt.figure(figsize=(14, 8))
plt.hist(
    counts_r1["r1_attempt_num_tokens"],
    bins=attempt_bins,
    color="green",
    alpha=0.5,
    label="R1 Attempt",
)
plt.hist(
    counts_r1["gemini_attempt_num_tokens"],
    bins=attempt_bins,
    color="orange",
    alpha=0.5,
    label="Gemini Attempt",
)
plt.hist(
    counts_s12["claude_attempt_num_tokens"],
    bins=attempt_bins,
    color="brown",
    alpha=0.5,
    label="Claude Attempt",
)
plt.title("Attempt Token Count Distribution Comparison")
plt.xlabel("Number of Tokens")
plt.ylabel("Frequency")
plt.legend()
plt.tight_layout()
plt.show()

# Create figure for attempts with subplots
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 14))
fig.suptitle("Attempt Token Count Distributions")

# Plot attempt counts in separate subplots
ax1.hist(
    counts_r1["r1_attempt_num_tokens"], bins=attempt_bins, color="green", alpha=0.7
)
ax1.set_title("R1 Attempt")
ax1.set_ylabel("Frequency")

ax2.hist(
    counts_r1["gemini_attempt_num_tokens"], bins=attempt_bins, color="orange", alpha=0.7
)
ax2.set_title("Gemini Attempt")
ax2.set_ylabel("Frequency")

ax3.hist(
    counts_s12["claude_attempt_num_tokens"], bins=attempt_bins, color="brown", alpha=0.7
)
ax3.set_title("Claude Attempt")
ax3.set_xlabel("Number of Tokens")
ax3.set_ylabel("Frequency")

plt.tight_layout()
plt.show()
