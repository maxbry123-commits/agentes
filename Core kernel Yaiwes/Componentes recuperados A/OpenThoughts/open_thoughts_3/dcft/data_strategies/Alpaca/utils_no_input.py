import json
import multiprocessing
import random
import re
import string
from ctypes import c_bool
from typing import Optional

import faiss
import numpy as np
import pandas as pd
from datasets import Dataset
import faiss

# from sentence_transformers import SentenceTransformer
from rouge_score import rouge_scorer
from tqdm import tqdm


def create_alpaca_prompts(
    seed_tasks: Dataset,
    num_instructions_to_generate: int,
    num_prompt_instructions: int,
    output_column: str,
    input_completion_column: Optional[str] = "completion",
) -> Dataset:
    num_cycles = num_instructions_to_generate // (19 - num_prompt_instructions) + 1
    prompts = []
    for _ in range(num_cycles):
        seed_idxs = random.sample(range(len(seed_tasks)), num_prompt_instructions)
        prompt_instructions = [seed_tasks[i] for i in seed_idxs]
        prompt = encode_prompt(prompt_instructions, input_completion_column)
        prompts.append(prompt)

    return Dataset.from_dict({output_column: prompts})


def encode_prompt(
    prompt_instructions: list,
    completion_column: str,
    prompt_file: str = "dcft/data_strategies/Alpaca/resources/alpaca_prompt.txt",
) -> str:
    """
    Encodes multiple prompt instructions into a single string by formatting them with the required structure.

    Args:
        prompt_instructions (list): A list of dictionaries containing the prompt instructions, each having 'instruction', 'input', and 'output'.
        prompt_file (str, optional): Path to the file containing the initial part of the prompt.

    Returns:
        str: A string containing the encoded prompt instructions.
    """
    prompt = open(prompt_file).read() + "\n"

    for idx, task_dict in enumerate(prompt_instructions):
        (instruction, output) = task_dict["instruction"], task_dict[completion_column]
        instruction = re.sub(r"\s+", " ", instruction).strip().rstrip(":")
        prompt += f"###\n"
        prompt += f"{idx + 1}. Instruction: {instruction}\n"
        prompt += f"{idx + 1}. Output:\n{output}\n"
    prompt += f"###\n"
    prompt += f"{idx + 2}. Instruction:"
    return prompt


def filter_instructions_rouge(
    dataset: Dataset, seed_instructions: Dataset, similarity_threshold: float = 0.7
) -> Dataset:
    """
    Filters instructions based on ROUGE-L score similarity to seed instructions.

    Args:
        dataset (Dataset): The dataset to filter.
        seed_instructions (Dataset): The dataset of seed instructions for comparison.

    Returns:
        Dataset: A dataset containing instructions that passed the ROUGE filtering.
    """
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
    current_pool_instructions = list(seed_instructions["instruction"])
    current_pool_instruction_tokens = [
        scorer._tokenizer.tokenize(inst) for inst in current_pool_instructions
    ]
    not_filtered, filtered = [], []

    for instruction_dict in tqdm(dataset):
        inst, input_text, output_text = (
            instruction_dict["instruction"].strip(),
            instruction_dict["output"].strip(),
        )
        # computing similarity with the pre-tokenzied instructions
        new_instruction_tokens = scorer._tokenizer.tokenize(inst)

        rouge_scores = np.array(
            [
                rouge_scorer._score_lcs(new_instruction_tokens, tokens).fmeasure
                for tokens in current_pool_instruction_tokens
            ]
        )

        if max(rouge_scores) > similarity_threshold:
            filtered.append(
                {
                    "instruction": inst,
                    "output": output_text,
                    "filtered_reason": "rouge_similarity",
                    "most_similar_score": max(rouge_scores),
                    "most_similar_instruction": current_pool_instructions[
                        np.argmax(rouge_scores)
                    ],
                }
            )
            continue

        not_filtered.append({"instruction": inst, "output": output_text})
        current_pool_instructions.append(inst)
        current_pool_instruction_tokens.append(new_instruction_tokens)

    not_filtered_dataset = Dataset.from_pandas(pd.DataFrame(not_filtered))
    return not_filtered_dataset
