from datasets import Dataset


def subsample_row(dataset: Dataset, num_samples: int, column_name: str) -> Dataset:
    def f(x):
        x[column_name] = x[column_name][:num_samples]
        return x

    print(f"Subsampling {column_name} to {num_samples} samples")
    dataset = dataset.map(f)
    return dataset
