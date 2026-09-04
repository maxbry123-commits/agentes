import os

from datasets import load_dataset


def map_to_sharegpt(x):
    x["conversations"] = [
        {"from": "user", "value": x["problem"]},
        {
            "from": "assistant",
            "value": f"<think>\n{x['deepseek_reasoning']}\n</think>\n\n{x['deepseek_solution']}",
        },
    ]
    return x


ds = load_dataset("open-thoughts/Open-Thoughts-114k", "metadata", split="train")
ds = ds.map(map_to_sharegpt, num_proc=os.cpu_count())
ds = ds.select_columns(["conversations"])
ds.push_to_hub("mlfoundations-dev/openthoughts-114k-no-special-template")
