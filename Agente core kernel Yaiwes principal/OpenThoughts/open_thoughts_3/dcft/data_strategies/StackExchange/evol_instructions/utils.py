import logging
import random
from typing import Dict

from datasets import Dataset

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def combine_seed_task_and_seed_data(
    seed_task_dataset: Dataset,
    seed_content_dataset: Dataset,
    seed_tasks_column: str,
    seed_content_column: str,
    output_column: str,
):
    all_seed_tasks = list(set(seed_task_dataset[seed_tasks_column]))
    logger.info(f"Number of unique tasks: {len(all_seed_tasks)}")

    def f(row):
        seed_tasks = random.choice(all_seed_tasks)
        prompt = f"""
            Here is an example:
            \n
            Seed Task: Create a code snippet.
            Question: What are the design implications of using OrderedDict in Python?
            Instruction: Create a code snippet that demonstrate the design choices of when to use an OrderedDict in Python.
            \n\n

            You are asked to turn a question into a task or instruction. This task instruction will be given to a GPT model and we will evaluate the GPT model for completing the instruction. Please try to keep as much of the content in the original question as possible. Use as many exact words from the seed task as possible. 
            \n\n
            Seed Task: {seed_tasks}
            Question: {row[seed_content_column]}
            Instruction: 
        """
        row["seed_tasks"] = seed_tasks
        row[output_column] = prompt
        return row

    seed_content_dataset = seed_content_dataset.map(f)
    return seed_content_dataset


def get_conversation(
    dataset: Dataset, conversation_column: str, output_column: str
) -> Dataset:
    def f(row):
        row[output_column] = row[conversation_column][0]["content"]
        return row

    dataset = dataset.map(f)
    return dataset


def repeat_if_needed(
    dataset: Dataset,
    old_instruction_column: str,
    new_instruction_column: str,
    old_response_column: str,
    new_response_column: str,
    output_instruction_column: str,
    output_response_column: str,
    percent_original: float,
) -> Dataset:
    def f(row):
        if random.random() < percent_original:
            row[output_instruction_column] = row[old_instruction_column]
            row[output_response_column] = row[old_response_column]
        else:
            row[output_instruction_column] = row[new_instruction_column]
            row[output_response_column] = row[new_response_column]
        return row

    dataset = dataset.map(f)
    return dataset


def filter(dataset: Dataset) -> Dataset:
    return dataset.filter(lambda x: x["language"] == "English")
