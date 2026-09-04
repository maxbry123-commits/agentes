from datasets import Dataset


def remove_multiturn(dataset: Dataset, messages: str = "messages") -> Dataset:
    return dataset.filter(lambda x: len(x[messages]) == 2)
