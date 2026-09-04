from datasets import load_dataset

datasets = [
    "bespokelabs/sky-t1-numina-rejection-sampled",  # 39k
    "bespokelabs/sky-t1-apps-rejection-sampled",  # 5k
    "bespokelabs/sky-t1-taco-rejection-sampled",  # 4.2k
    "bespokelabs/sky-t1-numina-olympiads-subset-unfiltered",  # 20k
    "bespokelabs/sky-t1-numina-amc-aime-subset-unfiltered",  # 4k
    "bespokelabs/sky-t1-numina-math-subset-unfiltered",  # 15k
]

datasets = [
    "bespokelabs/sky-t1-taco-train-unfiltered",
    "bespokelabs/sky-t1-taco-train-unfiltered-curated",
    "bespokelabs/sky-t1-taco-test-unfiltered",
    "bespokelabs/sky-t1-apps-unfiltered",
]

for dataset_name in datasets:
    print(dataset_name)

    dataset = load_dataset(dataset_name)
    print(dataset)

    dataset.push_to_hub(
        dataset_name.replace("bespokelabs/", "mlfoundations-dev/bespokelabs-")
    )


# from datasets import concatenate_datasets, load_dataset

# datasets = [
#     "bespokelabs/sky-t1-numina-rejection-sampled", #39k
#     "bespokelabs/sky-t1-apps-rejection-sampled",   #5k
#     "bespokelabs/sky-t1-taco-rejection-sampled",   #4.2k
# ]

# all_datasets = []
# for dataset_name in datasets:
#     print(f"Loading {dataset_name}")
#     dataset = load_dataset(dataset_name, split="train")
#     all_datasets.append(dataset)

# # Concatenate all datasets
# concatenated_dataset = concatenate_datasets(all_datasets)
# print(f"Concatenated dataset size: {len(concatenated_dataset)}")

# # Push to hub with the new name
# concatenated_dataset.push_to_hub("mlfoundations-dev/bespokelabs-Stratos-50k")
