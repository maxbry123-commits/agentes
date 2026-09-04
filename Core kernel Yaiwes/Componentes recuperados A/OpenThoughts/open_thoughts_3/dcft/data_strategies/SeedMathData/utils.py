import json

from datasets import Dataset


def mathcoder_map(dataset: Dataset) -> Dataset:
    def f(x):
        data = json.loads(x["text"])
        return {"instruction_seed": data["question"], "response_seed": data["answer"]}

    dataset = dataset.map(f)
    return dataset


def deepmind_map(dataset: Dataset) -> Dataset:
    def f(data):
        return {"instruction_seed": data["question"], "response_seed": data["answer"]}

    dataset = dataset.map(f)
    return dataset


def open2math_map(dataset: Dataset) -> Dataset:
    def f(x):
        instruction = x["messages"][0]["content"]
        response = x["messages"][0]["content"]
        return {"instruction_seed": instruction, "response_seed": response}

    dataset = dataset.map(f)
    return dataset
