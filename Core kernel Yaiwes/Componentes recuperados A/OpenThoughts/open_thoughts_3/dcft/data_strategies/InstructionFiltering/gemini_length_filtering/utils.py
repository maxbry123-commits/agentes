from datasets import Dataset


def get_lengths(dataset: Dataset, input_column: str, output_column: str) -> Dataset:
    def f(x):
        x[output_column] = len(x[input_column])
        return x

    dataset = dataset.map(f)
    return dataset
