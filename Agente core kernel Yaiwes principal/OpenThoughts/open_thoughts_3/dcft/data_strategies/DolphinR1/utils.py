from datasets import Dataset


def map_dolphin(dataset: Dataset):
    def f(x):
        x["conversations"].append({"from": "gpt", "value": x["reasoning"]})
        return x

    dataset = dataset.map(f)
    return dataset
