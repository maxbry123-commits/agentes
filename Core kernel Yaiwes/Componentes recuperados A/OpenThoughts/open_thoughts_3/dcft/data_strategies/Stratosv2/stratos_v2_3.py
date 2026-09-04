import os

from datasets import concatenate_datasets, load_dataset

datasets = []


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
datasets.append(ds)

ds = load_dataset("mlfoundations-dev/numina_math_1_5_extra_r1", split="train")
ds = ds.rename_column("r1_reasoning", "deepseek_reasoning")
ds = ds.rename_column("r1_solution", "deepseek_solution")
ds = ds.map(map_to_sharegpt, num_proc=os.cpu_count())
ds = ds.select_columns(["conversations"])
datasets.append(ds)

# Combine into final mix
combined = concatenate_datasets(datasets)
combined.push_to_hub("mlfoundations-dev/stratos_verified_v2_3")
