from datasets import load_dataset, concatenate_datasets

dataset1 = load_dataset("mlfoundations-dev/glaive_reasoning_100k")["train"]
dataset2 = load_dataset("mlfoundations-dev/openthoughts_114k_thinkprompt")["train"]

combined = concatenate_datasets([dataset1, dataset2])
combined = combined.shuffle(seed=42)
combined.push_to_hub("mlfoundations-dev/openthoughts_plus_glaive_reasoning_100k")
