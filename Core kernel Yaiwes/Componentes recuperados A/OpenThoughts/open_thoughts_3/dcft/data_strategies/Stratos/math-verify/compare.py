from datasets import load_dataset

ds = load_dataset(
    "mlfoundations-dev/math_stratos_scale_verified_with_hf", split="train"
)

ds = ds.filter(lambda x: x["verifier_label"] and not x["correct"])
print(ds)
