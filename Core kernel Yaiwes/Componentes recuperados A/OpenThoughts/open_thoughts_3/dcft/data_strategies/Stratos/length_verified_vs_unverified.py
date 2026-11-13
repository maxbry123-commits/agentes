import os

import matplotlib.pyplot as plt
import numpy as np
from datasets import load_dataset
from transformers import AutoTokenizer

ds = load_dataset("mlfoundations-dev/stratos_verified_mix", split="train")
unverified_ds = load_dataset("mlfoundations-dev/stratos_unverified_mix", split="train")

tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True
)


def count_tokens(example):
    example["conversations"] = [
        {"role": "user", "content": example["conversations"][0]["value"]},
        {"role": "assistant", "content": example["conversations"][1]["value"]},
    ]
    example["conversation_num_tokens"] = len(
        tokenizer.apply_chat_template(example["conversations"])
    )
    return example


num_cpus = os.cpu_count()
counts = ds.map(count_tokens, num_proc=num_cpus)
unverified_counts = unverified_ds.map(count_tokens, num_proc=num_cpus)

# Calculate and print means
verified_mean = np.mean(counts["conversation_num_tokens"])
unverified_mean = np.mean(unverified_counts["conversation_num_tokens"])

print(f"Mean tokens for verified conversations: {verified_mean:.2f}")
print(f"Mean tokens for unverified conversations: {unverified_mean:.2f}")


# Create a plot for verified vs unverified conversations
plt.figure(figsize=(10, 6))

# Calculate common bins for both distributions
min_tokens = min(
    min(counts["conversation_num_tokens"]),
    min(unverified_counts["conversation_num_tokens"]),
)
max_tokens = max(
    max(counts["conversation_num_tokens"]),
    max(unverified_counts["conversation_num_tokens"]),
)
bins = np.linspace(min_tokens, max_tokens, 50)

# Plot both distributions with common bins
plt.hist(
    counts["conversation_num_tokens"],
    bins=bins,
    color="blue",
    alpha=0.5,
    label="Verified",
)
plt.hist(
    unverified_counts["conversation_num_tokens"],
    bins=bins,
    color="red",
    alpha=0.5,
    label="Unverified",
)

plt.title("Conversation Token Count Distribution: Verified vs Unverified")
plt.xlabel("Number of Tokens")
plt.ylabel("Frequency")
plt.legend()
plt.tight_layout()
plt.show()
