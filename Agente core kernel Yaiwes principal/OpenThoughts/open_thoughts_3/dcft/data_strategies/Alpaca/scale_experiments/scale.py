from datasets import Dataset


def generate_icl_example(dataset: Dataset) -> Dataset:
    rows = iter(dataset.select(list(range(5))))
    prompt = "I want you to generate more seed tasks. Here are some examples"
    for row in rows:
        prompt += f"'instruction': {row['instruction']}, 'input': {row['input']}, output: {row['output']}\n\n"
    dataset = dataset.add_column("seed_task_prompt", [prompt] * len(dataset))
    return dataset
