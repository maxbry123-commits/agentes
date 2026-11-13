import logging
import math
import random
import re

from datasets import Dataset

logger = logging.getLogger(__name__)


def filter_yes_responses_map(row, response_column):
    response = row[response_column]
    response = response[-20:]
    if "Yes" in response and "No" not in response:
        return {"label_educational": True}
    else:
        return {"label_educational": False}


def filter_yes_responses(dataset: Dataset, response_column: str):
    dataset = dataset.map(
        filter_yes_responses_map, fn_kwargs={"response_column": response_column}
    )
    before_filter = len(dataset)
    dataset = dataset.filter(lambda x: x["label_educational"])
    after_filter = len(dataset)
    logger.info(
        f"Filtered out {before_filter - after_filter} rows which are not edcuational according to the model response."
    )
    return dataset.remove_columns(["label_educational"])


# response columns contains text like "Yes, this is educational" or "No, this is not educational"
def extract_qa_pairs(dataset: Dataset, response_column: str):
    # Define a regex to capture <|Instruct|> and <|Output|> pairs
    pattern = r"<\|Instruct\|>(.*?)<\|Output\|>(.*?)(?=<\|Instruct\|>|$)"

    logger.info(f"Extracting QA pairs from a dataset of size {len(dataset)}.")

    def extract_pairs(example):
        text = example[response_column]
        matches = re.findall(pattern, text, re.DOTALL)
        pairs = []

        for match in matches:
            instruction = match[0].strip()
            output = match[1].strip()
            pairs.append(
                {
                    "text": example["text"],
                    "number of questions": len(matches),
                    "response": example[response_column],
                    "instruction": instruction,
                    "output": output,
                }
            )
            # log the extracted pairs for debugging

        return pairs

    # Flatten the results into a new dataset
    new_data = []
    for example in dataset:
        pairs = extract_pairs(example)
        new_data.extend(pairs)

    # log dataset size
    logger.info(f"Extracted {len(new_data)} QA pairs from the dataset.")

    return Dataset.from_list(new_data)


def filter_endoftext(dataset: Dataset, text_column: str = "text"):
    """
    Filters out rows in a HuggingFace dataset where the specified column contains the 'endoftext' token.

    Args:
        dataset (Dataset): The dataset to filter.
        text_column (str): The name of the text column to check.

    Returns:
        Dataset: The filtered dataset.
    """
    before_filter = len(dataset)

    # Filtering function
    def contains_endoftext(example):
        return "<|endoftext|>" not in example[text_column]

    # Apply the filter
    filtered_dataset = dataset.filter(contains_endoftext)

    # Log the size of the dataset after filtering
    after_filter = len(filtered_dataset)
    logger.info(
        f"Filtered out {before_filter - after_filter} rows containing 'endoftext'."
    )

    return filtered_dataset


def extract_revised_pairs(dataset: Dataset, response_column: str):
    # Define a regex to capture <|RevisedQuestion|> and <|RevisedAnswer|> pairs
    # pattern = r'<\|RevisedQuestion\|>\s(.?)\s<\|RevisedAnswer\|>\s(.?)\s(?=<\|RevisedQuestion\|>|$)'
    pattern = (
        r"<\|RevisedQuestion\|>(.*?)<\|RevisedAnswer\|>(.*?)(?=<\|RevisedQuestion\|>|$)"
    )
    logger.info(f"Revising QA pairs from a dataset of size {len(dataset)}.")

    def extract_pairs(example):
        text = example[response_column]
        matches = re.findall(pattern, text, re.DOTALL)
        pairs = []

        for match in matches:
            revised_question = match[0].strip()
            revised_answer = match[1].strip()
            pairs.append(
                {
                    "text": example["text"],
                    "response": example[response_column],
                    "instruction": example["instruction"],
                    "output": example["output"],
                    "response_stage_3": example[response_column],
                    "revised_question": revised_question,
                    "revised_answer": revised_answer,
                }
            )

        return pairs

    # Flatten the results into a new dataset
    new_data = []
    for example in dataset:
        pairs = extract_pairs(example)
        new_data.extend(pairs)

    return Dataset.from_list(new_data)


def filter_quality_checked_responses_map(row, response_column):
    response = row[response_column]
    if "<|passed|>" in response:
        return {"label_quality_check": True}
    else:
        return {"label_quality_check": False}


def filter_quality_checked_responses(dataset: Dataset, response_column: str):
    dataset = dataset.map(
        filter_quality_checked_responses_map,
        fn_kwargs={"response_column": response_column},
    )
    before_filter = len(dataset)
    dataset = dataset.filter(lambda x: x["label_quality_check"])
    after_filter = len(dataset)
    logger.info(
        f"Filtered out {before_filter - after_filter} rows ({(before_filter - after_filter)/before_filter} percent) have not passed."
    )
    return dataset.remove_columns(["label_quality_check"])


def dict_to_response(conversation: dict) -> str:
    response = conversation["value"]
    return response


def convert_dict_to_response(
    dataset: Dataset,
    input_column: str,
    output_response_column: str,
) -> Dataset:
    """
    Convert a dataset from ShareGPT format to instruction-response format.
    """

    def f(row: dict) -> dict:
        row[output_response_column] = dict_to_response(row[input_column])
        return row

    dataset = dataset.map(f)

    return dataset
