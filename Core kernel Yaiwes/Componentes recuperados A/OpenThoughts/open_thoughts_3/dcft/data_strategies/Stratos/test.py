from datasets import load_dataset

ds = load_dataset("open-thoughts/OpenThoughts-114k", "metadata", split="train")
print(ds)
