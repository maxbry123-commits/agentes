from datasets import load_dataset, Dataset


def get_combined_question_answer_string(
    dataset: Dataset, question_column: str, answer_column: str, output_column: str
) -> Dataset:
    return dataset.map(
        lambda x: {
            output_column: f"Question: {x[question_column]}\nAnswer: {x[answer_column]}"
        }
    )


def get_combined_question_answer_string_openthoughts(
    dataset: Dataset, output_column: str
) -> Dataset:
    return dataset.map(
        lambda x: {
            output_column: f"Question: {x['conversations'][0]['value']}\nAnswer: {x['conversations'][1]['value']}"
        }
    )
