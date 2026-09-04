import os

from datasets import concatenate_datasets, load_dataset

datasets = []


def map_to_sharegpt(x):
    x["conversations"] = [
        {"from": "user", "value": x["problem"]},
        {
            "from": "assistant",
            "value": f"<think>\n\n{x['deepseek_reasoning']}\n\n</think>\n\n{x['deepseek_solution']}",
        },
    ]
    return x


ds = load_dataset("open-thoughts/Open-Thoughts-114k", "metadata", split="train")
ds = ds.map(map_to_sharegpt, num_proc=os.cpu_count())
ds = ds.select_columns(["conversations"])
datasets.append(ds)

ds = load_dataset(
    "mlfoundations-dev/OpenR1-Math-Raw-all-correct-sharegpt", split="train"
)
datasets.append(ds)

# Combine into final mix
combined = concatenate_datasets(datasets)
combined.push_to_hub("mlfoundations-dev/ot-114k_Math-Raw-all-correct")
