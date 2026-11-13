import glob
import os
import re
from typing import Dict, List

from datasets import Dataset


def load_seed_instructions(seed_tasks_path: str) -> Dataset:
    """
    Load seed instructions from text files and return as a Dataset.

    Args:
        seed_tasks_path (str): Path to directory containing seed task files

    Returns:
        Dataset: Dataset containing seed instructions
    """
    all_instructions = []

    # Get all text files in the directory
    files = glob.glob(os.path.join(seed_tasks_path, "*.txt"))

    # Read each file and collect instructions
    for file_path in files:
        with open(file_path, "r") as f:
            content = f.read().strip()
            if content:
                all_instructions.append(content)

    # Create a list of dictionaries for the Dataset
    data_dicts = [{"seeds": instruction} for instruction in all_instructions]

    # Create Dataset from list of dictionaries
    return Dataset.from_list(data_dicts)


def inline_input_in_instruction(dataset: Dataset) -> Dataset:
    """
    Inline the input in the instruction and drop rows where [INPUT] is not present.
    """

    def has_input_placeholder(sample):
        return "[INPUT]" in sample["alternative_formulation"]

    def inline_input(sample):
        sample["alternative_formulation_inlined"] = sample[
            "alternative_formulation"
        ].replace("[INPUT]", sample["input"])
        return sample

    dataset = dataset.filter(has_input_placeholder)
    dataset = dataset.map(inline_input)
    return dataset
