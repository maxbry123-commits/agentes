from datasets import Dataset


def convert_instruction_to_row(dataset: Dataset, column_name: str) -> Dataset:
    def f(example):
        example[column_name] = [example[column_name]]
        return example

    updated_dataset = dataset.map(f)
    return updated_dataset


def get_all_feedback(dataset: Dataset) -> Dataset:
    all_rows = dataset.iter(batch_size=1)
    all_feedbacks = []
    for row in all_rows:
        all_feedbacks.append(row["feedback"][0])
    return Dataset.from_dict(
        {
            "feedback": ["\n\n".join(all_feedbacks)],
            "evol_prompt": [dataset["evol_prompt"]],
        }
    )


def add_new_prompt(
    dataset_with_evol_prompt: Dataset, original_dataset: Dataset, column_name: str
) -> Dataset:
    value_to_add = dataset_with_evol_prompt[column_name][0]
    original_dataset = original_dataset.add_column(
        column_name, [value_to_add] * len(original_dataset)
    )
    return original_dataset
