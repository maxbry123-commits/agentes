from datasets import Dataset, Value


def str_to_float(dataset: Dataset) -> Dataset:
    def f(x):
        x["ground_truth_solution"] = str(x["ground_truth_solution"])
        return x

    dataset = dataset.map(f)
    dataset = dataset.cast_column("ground_truth_solution", Value("string"))
    return dataset
