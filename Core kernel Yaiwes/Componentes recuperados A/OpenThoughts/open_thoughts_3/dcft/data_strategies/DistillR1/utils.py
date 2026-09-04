from datasets import Dataset


def extract_question(dataset: Dataset) -> Dataset:
    def f(x):
        x["problem"] = x["conversations"][0]["value"]
        return x

    dataset = dataset.map(f)
    return dataset
