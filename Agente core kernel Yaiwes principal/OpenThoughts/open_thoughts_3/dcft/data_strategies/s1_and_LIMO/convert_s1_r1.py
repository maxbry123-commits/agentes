import os

from datasets import load_dataset

dataset = load_dataset("simplescaling/s1K-with-deepseek-r1", split="train")
# save to downloads folder as json
# dataset.to_json(os.path.expanduser("~/Downloads/s1K-with-deepseek-r1.jsonl"))


def map_to_share_gpt(x):
    x["conversations"] = [
        {"from": "user", "value": x["question"]},
        {
            "from": "assistant",
            "value": x["deepseek_thinking_trajectory"] + "\n\n" + x["deepseek_attempt"],
        },
    ]
    return x


dataset = dataset.map(map_to_share_gpt, num_proc=os.cpu_count())
dataset = dataset.select_columns(["conversations"])
dataset.push_to_hub("mlfoundations-dev/s1K-with-deepseek-r1-sharegpt")


def map_to_sharegpt(x):
    x["conversations"] = [
        {"from": "user", "value": x["question"]},
        {
            "from": "assistant",
            "value": x["gemini_thinking_trajectory"] + "\n\n" + x["gemini_attempt"],
        },
    ]
    return x


dataset = load_dataset("simplescaling/s1K-with-deepseek-r1", split="train")
dataset = dataset.map(map_to_share_gpt, num_proc=os.cpu_count())
dataset = dataset.select_columns(["conversations"])
dataset.push_to_hub("mlfoundations-dev/s1K-sharegpt")
