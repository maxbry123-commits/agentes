import json
import multiprocessing
import random
import re
import string
from ctypes import c_bool

import faiss
import numpy as np
import pandas as pd
from datasets import Dataset
import faiss

# from sentence_transformers import SentenceTransformer
from rouge_score import rouge_scorer
from tqdm import tqdm


def load_seed_instructions(seed_tasks_path: str) -> Dataset:
    """
    Loads alpaca seed instruction tasks from a given JSON file path.

    Args:
        seed_tasks_path (str): Path to the JSON file containing the seed tasks.

    Returns:
        Dataset: A dataset containing the seed instructions, inputs, and outputs.
    """
    seed_tasks = [json.loads(l) for l in open(seed_tasks_path, "r")]
    seed_instruction_data = [
        {
            "instruction": t["instruction"],
            "input": t["instances"][0]["input"],
            "output": t["instances"][0]["output"],
        }
        for t in seed_tasks
    ]
    seed_instructions_dataset = Dataset.from_list(seed_instruction_data)
    return seed_instructions_dataset


def create_alpaca_prompts(
    seed_tasks: Dataset,
    num_instructions_to_generate: int,
    num_prompt_instructions: int,
    output_column: str,
) -> Dataset:
    num_cycles = num_instructions_to_generate // (19 - num_prompt_instructions) + 1
    prompts = []
    for _ in range(num_cycles):
        seed_idxs = random.sample(range(len(seed_tasks)), num_prompt_instructions)
        prompt_instructions = [seed_tasks[i] for i in seed_idxs]
        prompt = encode_prompt(prompt_instructions)
        prompts.append(prompt)

    return Dataset.from_dict({output_column: prompts})


def encode_prompt(
    prompt_instructions: list,
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
        (instruction, input, output) = (
            task_dict["instruction"],
            task_dict["input"],
            task_dict["output"],
        )
        instruction = re.sub(r"\s+", " ", instruction).strip().rstrip(":")
        input = "<noinput>" if input.lower() == "" else input
        prompt += f"###\n"
        prompt += f"{idx + 1}. Instruction: {instruction}\n"
        prompt += f"{idx + 1}. Input:\n{input}\n"
        prompt += f"{idx + 1}. Output:\n{output}\n"
    prompt += f"###\n"
    prompt += f"{idx + 2}. Instruction:"
    return prompt


def find_word_in_string(w: str, s: str) -> re.Match:
    return re.compile(r"\b({0})\b".format(w), flags=re.IGNORECASE).search(s)


def instructions_heuristics(
    dataset: Dataset,
    input_instruction_column: str,
    output_filtered_reason_column: str,
    output_filtered_decision_column: str,
) -> Dataset:
    """
    Filters a dataset of instructions using various heuristics.
    Decision is True if the instruction is filtered out.

    Args:
        dataset (Dataset): The dataset to filter.

    Returns:
        Dataset: A dataset containing instructions that passed the heuristics filtering.
    """

    blacklist = [
        "image",
        "images",
        "graph",
        "graphs",
        "picture",
        "pictures",
        "file",
        "files",
        "map",
        "maps",
        "draw",
        "plot",
        "go to",
        "video",
        "audio",
        "music",
        "flowchart",
        "diagram",
    ]

    # NOTE(Ryan): We keep track of these if we want to keep them in the output dataset and inspect which samples are filtered out and why.
    def filter_hueristics_map(row):
        inst = row[input_instruction_column].strip()
        reason = None
        decision = False

        if len(inst.split()) <= 3:
            reason = "too_short"
            decision = True
        elif len(inst.split()) > 150:
            reason = "too_long"
            decision = True
        elif any(find_word_in_string(word, inst) for word in blacklist):
            reason = "blacklisted"
            decision = True
        elif inst.startswith("Write a program"):
            reason = "write_a_program_prefix"
            decision = True
        elif inst[0] in string.punctuation:
            reason = "punctuation_prefix"
            decision = True
        elif not inst[0].isascii():
            reason = "ascii_prefix"
            decision = True

        row[output_filtered_reason_column] = reason
        row[output_filtered_decision_column] = decision
        return row

    return dataset.map(filter_hueristics_map)


def process_indices(
    index_range,
    embeddings,
    visited_array,
    lock,
    selected_indices,
    similarity_threshold,
    num_sentences,
):
    # Each process creates its own FAISS index
    local_index = faiss.IndexFlatIP(embeddings.shape[1])
    local_index.add(embeddings)

    local_selected = []
    for i in index_range:
        with lock:
            if visited_array[i]:
                continue
            visited_array[i] = True
            local_selected.append(i)

        # Search for similar sentences
        D, I = local_index.search(embeddings[i : i + 1], num_sentences)
        similar_indices = [
            idx
            for idx, score in zip(I[0], D[0])
            if score > similarity_threshold and idx != i
        ]

        with lock:
            for idx in similar_indices:
                visited_array[idx] = True

    # Append local selected indices to the global list
    selected_indices.extend(local_selected)


# Step 3: Parallel processing
def parallel_greedy_selection(
    embeddings,
    visited_array,
    lock,
    selected_indices,
    similarity_threshold,
    num_sentences,
):
    num_processes = multiprocessing.cpu_count()
    batch_size = (
        num_sentences + num_processes - 1
    ) // num_processes  # Ceiling division

    processes = []
    for i in range(num_processes):
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, num_sentences)
        index_range = range(start_idx, end_idx)
        p = multiprocessing.Process(
            target=process_indices,
            args=(
                index_range,
                embeddings,
                visited_array,
                lock,
                selected_indices,
                similarity_threshold,
                num_sentences,
            ),
        )
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    # Convert selected indices to a regular list
    final_selected_indices = list(selected_indices)
    return final_selected_indices


def filter_instructions_cosine_similarity(
    dataset: Dataset, similarity_threshold: float, input_instruction_column: str
) -> Dataset:
    """
    Filters instructions based on a similarity threshold using SentenceTransformer and FAISS for fast processing.

    Args:
        dataset (Dataset): The dataset to filter.
        seed_instructions (Dataset): A dataset of seed instructions for comparison.
        similarity_threshold (float, optional): Threshold for filtering based on cosine similarity. Default is 0.7.

    Returns:
        Dataset: A dataset containing the filtered instructions.
    """
    sentences = list(dataset[input_instruction_column])

    # Step 1: Convert sentences to embeddings
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(sentences, convert_to_numpy=True)
    # Step 2: Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)

    num_sentences = len(sentences)

    # Shared data structures for multiprocessing
    manager = multiprocessing.Manager()
    selected_indices = manager.list()
    visited_array = multiprocessing.Array(c_bool, num_sentences)
    lock = multiprocessing.Lock()

    # Run the parallel greedy selection
    selected_indices = parallel_greedy_selection(
        embeddings,
        visited_array,
        lock,
        selected_indices,
        similarity_threshold,
        num_sentences,
    )

    out = dataset.select(selected_indices)
    return out


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
            instruction_dict["input"].strip(),
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
                    "input": input_text,
                    "output": output_text,
                    "filtered_reason": "rouge_similarity",
                    "most_similar_score": max(rouge_scores),
                    "most_similar_instruction": current_pool_instructions[
                        np.argmax(rouge_scores)
                    ],
                }
            )
            continue

        not_filtered.append(
            {"instruction": inst, "input": input_text, "output": output_text}
        )
        current_pool_instructions.append(inst)
        current_pool_instruction_tokens.append(new_instruction_tokens)

    not_filtered_dataset = Dataset.from_pandas(pd.DataFrame(not_filtered))
    return not_filtered_dataset
