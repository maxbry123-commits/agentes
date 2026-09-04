import os

from datasets import Dataset, concatenate_datasets, load_dataset

ds = load_dataset("open-thoughts/OpenThoughts-114k", split="train")
# ds.push_to_hub("mlfoundations-dev/OT-114k-mirror")
print(ds)

verified_datasets = []
unverified_datasets = []
ds = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated", split="train"
)
ds = ds.rename_column("reasoning", "deepseek_reasoning")
ds = ds.remove_columns(["judge_reasoning"])
ds = ds.add_column("domain", ["math"] * len(ds))
ds = ds.add_column("source", ["numina_math"] * len(ds))
unverified_datasets.append(ds)
ds = ds.filter(lambda x: x["correct"])
math_stratos_scale = load_dataset("mlfoundations-dev/math_stratos_scale_share_gpt")[
    "train"
]
assert len(ds) == len(math_stratos_scale)
verified_datasets.append(ds)

ds = load_dataset(
    "mlfoundations-dev/code_stratos_scale_rejection_sampled_test", split="train"
)
ds = ds.rename_column(
    "reasoning",
    "deepseek_reasoning",
)
ds = ds.remove_columns(
    [
        "language",
        "name",
        "num_solutions",
        "source",
        "difficulty",
        "problem_id",
        "reason",
    ]
)
ds = ds.rename_column("subset", "source")
ds = ds.rename_column("correctness", "correct")
ds = ds.add_column("domain", ["code"] * len(ds))
unverified_datasets.append(ds)
ds = ds.filter(lambda x: x["correct"])
code_stratos_scale = load_dataset("mlfoundations-dev/code_stratos_scale_share_gpt")[
    "train"
]
assert len(ds) == len(code_stratos_scale)
verified_datasets.append(ds)


def add_source(x):
    if x["ground_truth_solution"] is not None:
        source = "riddle_sense"
    elif x["domain"] == "biology":
        source = "camelai_biology"
    elif x["domain"] == "chemistry":
        source = "camelai_chemistry"
    elif x["domain"] == "physics":
        source = "camelai_physics"
    x["source"] = source
    return x


ds = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_annotated", split="train"
)
og = load_dataset("mlfoundations-dev/science_and_puzzle_stratos_scale", split="train")
og = og.rename_column("question", "problem")
ds_df = ds.to_pandas()
og_df = og.to_pandas()
merged_df = ds_df.merge(og_df, on="problem", suffixes=("", "_og"))
ds = Dataset.from_pandas(merged_df)
print(ds)
ds = ds.rename_column("reasoning", "deepseek_reasoning")
ds = ds.rename_column("answer", "ground_truth_solution")
ds = ds.remove_columns(["id", "topic", "sub_topic"])
ds = ds.map(add_source, num_proc=os.cpu_count())
science_and_puzzle_stratos_scale = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_share_gpt"
)["train"]
assert len(ds) == len(science_and_puzzle_stratos_scale)
unverified_datasets.append(ds)
verified_datasets.append(ds)
ds = concatenate_datasets(verified_datasets)
ds = ds.remove_columns(["correct"])
print(ds)
# ds.push_to_hub("mlfoundations-dev/OT-114k-mirror", config_name="metadata")
ds.push_to_hub("open-thoughts/OpenThoughts-114k", config_name="metadata")
ds = concatenate_datasets(unverified_datasets)
ds = ds.remove_columns(["correct"])
print(ds)
# ds.push_to_hub("mlfoundations-dev/OT-173k-unverified")
ds.push_to_hub("open-thoughts/OpenThoughts-Unfiltered-173k")
