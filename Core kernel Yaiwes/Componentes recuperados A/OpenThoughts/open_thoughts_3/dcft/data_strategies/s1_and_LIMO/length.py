import os

from datasets import load_dataset
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True
)
x = load_dataset("simplescaling/s1K_tokenized", split="train")


def count_tokens(example):
    example["num_tokens"] = len(tokenizer.encode(example["text"]))
    return example


num_cpus = os.cpu_count()
x = x.map(count_tokens, num_proc=num_cpus)
print(max(x["num_tokens"]))

x = load_dataset("simplescaling/s1K", split="train")


def count_tokens(example):
    example["num_tokens"] = len(
        tokenizer.encode(
            example["thinking_trajectories"][0]
            + example["attempt"]
            + example["question"]
        )
    )
    return example


num_cpus = os.cpu_count()
x = x.map(count_tokens, num_proc=num_cpus)
print(max(x["num_tokens"]))

x = load_dataset("GAIR/LIMO", split="train")


def count_tokens(example):
    example["num_tokens"] = len(
        tokenizer.encode(example["question"] + example["solution"])
    )
    return example


num_cpus = os.cpu_count()
x = x.map(count_tokens, num_proc=num_cpus)
print(max(x["num_tokens"]))
