import json
import multiprocessing as mp
from collections import defaultdict
from functools import partial
from multiprocessing import Pool
from typing import Dict, List, Optional, Tuple

import numpy as np
from datasets import Dataset, concatenate_datasets, load_dataset
from rapidfuzz import fuzz, process
from tqdm import tqdm

SKY_T1_FIXED = "Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered thinking process. Please structure your response into two main sections: Thought and Solution. In the Thought section, detail your reasoning process using the specified format: <|begin_of_thought|> {thought with steps separated with '\n\n'} <|end_of_thought|> Each step should include detailed considerations such as analisying questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps. In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. The solution should remain a logical, accurate, concise expression style and detail necessary step needed to reach the conclusion, formatted as follows: <|begin_of_solution|> {final formatted, precise, and clear solution} <|end_of_solution|> Now, try to solve the following question through the above guidelines:"


def map_numina_conversations(x):
    """Map the Numina dataset to the required format."""
    user_message = f"Return your final response within \\boxed{{}}. {x['problem']}"
    assistant_message = f"<|begin_of_thought|>\n\n{x['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_solution']}\n\n<|end_of_solution|>"
    return {
        "system": SKY_T1_FIXED,
        "conversations": [
            {"from": "user", "value": user_message},
            {"from": "assistant", "value": assistant_message},
        ],
    }


def apply_numina_map(dataset: Dataset) -> Dataset:
    numina_conversations = dataset.map(map_numina_conversations)
    return numina_conversations


def map_apps_conversations(x):
    """Map the APPS dataset to the required format."""
    test_case = json.loads(x["input_output"])
    starter_code = x["starter_code"]
    prompt = x["question"]

    user_message = ""
    data = test_case
    if not data.get("fn_name"):
        user_message += "Generate an executable Python function generated from the given prompt. The function should take stdin as input and print the output. Simply call the function after the definition."  # "\nUse Standard Input format"#\n" #noqa
    else:
        user_message += "Generate an executable Python function generated from the given prompt. Return the function body without invoking it at the final solution."  # "\nUse Call-Based format"#\n" #noqa
    data = prompt
    user_message += data
    if starter_code is not None:
        data = starter_code
        data = "\n" + data
        user_message += data
    else:
        pass
    assistant_message = f"<|begin_of_thought|>\n\n{x['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_solution']}\n\n<|end_of_solution|>"

    return {
        "system": SKY_T1_FIXED,
        "conversations": [
            {"from": "user", "value": user_message},
            {"from": "assistant", "value": assistant_message},
        ],
    }


def apply_apps_map(dataset: Dataset) -> Dataset:
    apps_conversations = dataset.map(map_apps_conversations)
    return apps_conversations


def map_taco_conversations(x):
    """Map the TACO dataset to the required format."""
    test_case = json.loads(x["input_output_x"])
    starter_code = x["starter_code"]
    prompt = x["question"]

    user_message = ""
    data = test_case
    if not data.get("fn_name"):
        user_message += "Generate an executable Python function generated from the given prompt. The function should take stdin as input and print the output. Simply call the function after the definition."  # "\nUse Standard Input format"#\n" #noqa
    else:
        user_message += "Generate an executable Python function generated from the given prompt. Return the function body without invoking it at the final solution."  # "\nUse Call-Based format"#\n" #noqa
    data = prompt
    user_message += data
    if starter_code is not None:
        data = starter_code
        data = "\n" + data
        user_message += data
    else:
        pass
    assistant_message = f"<|begin_of_thought|>\n\n{x['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_solution']}\n\n<|end_of_solution|>"

    return {
        "system": SKY_T1_FIXED,
        "conversations": [
            {"from": "user", "value": user_message},
            {"from": "assistant", "value": assistant_message},
        ],
    }


def apply_taco_map(dataset: Dataset) -> Dataset:
    taco_conversations = dataset.map(map_taco_conversations)
    return taco_conversations


def map_still2_conversations(x):
    """Map the still2 dataset to the required format."""
    return {
        "system": SKY_T1_FIXED,
        "conversations": [
            {"from": "user", "value": x["question"]},
            {"from": "assistant", "value": x["combined_text"]},
        ],
    }


def apply_still2_map(dataset: Dataset) -> Dataset:
    still2_conversations = dataset.filter(
        lambda x: x["domain"] in ["puzzle", "physics", "biology", "chemistry"]
    ).map(map_still2_conversations)
    return still2_conversations


def process_string_pair(
    str1: str, values2: List[str], similarity_threshold: float
) -> List[Tuple]:
    matches_with_scores = process.extract(
        str1, values2, scorer=fuzz.ratio, score_cutoff=similarity_threshold
    )
    return [
        (str1, match_tuple[0], match_tuple[1]) for match_tuple in matches_with_scores
    ]


def decontaminate_table(
    dataset: Dataset,
    column: str,
    eval_datasets: List[str],
    eval_columns: List[str],
    eval_splits: List[str],
    similarity_threshold: float,
    eval_subsets: Optional[Dict[str, str]] = {},
) -> Dataset:
    """
    Remove rows from dataset that have similar strings in eval_datasets based on fuzzy matching.
    """
    n_processes = mp.cpu_count()

    # Get values from input dataset
    values1 = [str(x) for x in dataset[column] if x is not None]

    # Load eval datasets
    pair_values = {}
    for idx in range(len(eval_datasets)):
        dataset_name_and_config = eval_datasets[idx]
        dataset_name_and_config_split = dataset_name_and_config.split("::")
        dataset_name = dataset_name_and_config_split[0]
        dataset_config = (
            dataset_name_and_config_split[1]
            if len(dataset_name_and_config_split) > 1
            else None
        )

        split = eval_splits[idx]
        eval_column = eval_columns[idx]
        if dataset_name in eval_subsets:
            ds = load_dataset(
                dataset_name,
                eval_subsets[dataset_name],
                split=split,
                trust_remote_code=True,
            )
        else:
            ds = load_dataset(dataset_name, split=split, trust_remote_code=True)
        values = [str(x) for x in ds[eval_column] if x is not None]
        pair_values[(dataset_name, split, eval_column)] = values

    # Track indices to remove
    indices_to_remove = set()

    # Compare with each eval dataset
    for (dataset_name, split, eval_column), values2 in tqdm(
        pair_values.items(), desc="Processing datasets"
    ):
        process_pair = partial(
            process_string_pair,
            values2=values2,
            similarity_threshold=similarity_threshold,
        )

        with Pool(n_processes) as pool:
            matches = list(
                tqdm(
                    pool.imap(process_pair, values1, chunksize=100),
                    total=len(values1),
                    desc=f"Processing {dataset_name}",
                )
            )

        # Find indices where matches were found
        for i, match_list in enumerate(matches):
            if any(score >= similarity_threshold for _, _, score in match_list):
                indices_to_remove.add(i)
    keep_mask = [i for i in range(len(dataset)) if i not in indices_to_remove]
    clean_dataset = dataset.select(keep_mask)

    print(f"Removed {len(indices_to_remove)} contaminated rows")
    print(f"Original size: {len(dataset)}, New size: {len(clean_dataset)}")

    return clean_dataset


def create_question_column(dataset: Dataset) -> Dataset:
    def f(x):
        x["extracted_instruction"] = x["conversations"][0]["value"]
        return x

    dataset = dataset.map(f)
    return dataset


def fuzzy_dedup(
    dataset: Dataset, column: str, similarity_threshold: float = 95.0
) -> Dataset:
    """Deduplicate dataset rows based on fuzzy string matching within specified column."""
    values = [str(x) for x in dataset[column] if x is not None]
    unique_values = list(set(values))
    n_processes = mp.cpu_count()

    process_pair = partial(
        process_string_pair,
        values2=unique_values,
        similarity_threshold=similarity_threshold,
    )
    with Pool(n_processes) as pool:
        all_matches = list(
            tqdm(
                pool.imap(process_pair, unique_values, chunksize=100),
                total=len(unique_values),
                desc="Finding duplicates",
            )
        )

    str_to_indices = defaultdict(list)
    for i, val in enumerate(values):
        str_to_indices[val].append(i)

    indices_to_remove = set()
    for matches_list in all_matches:
        for str1, str2, score in matches_list:
            if score >= similarity_threshold:
                indices1 = str_to_indices[str1]
                indices2 = str_to_indices[str2]
                all_indices = list(set(indices1 + indices2))
                all_indices.sort()
                indices_to_remove.update(all_indices[1:])
    keep_mask = [i for i in range(len(dataset)) if i not in indices_to_remove]
    clean_dataset = dataset.select(keep_mask)

    print(f"Removed {len(indices_to_remove)} duplicate rows")
    print(f"Original size: {len(dataset)}, New size: {len(clean_dataset)}")
    return clean_dataset


def fuzzy_match_table(
    dataset: Dataset,
    column: str,
    eval_datasets: List[str],
    eval_columns: List[str],
    eval_splits: List[str],
    similarity_threshold: float,
) -> Dataset:
    """
    Annotate rows in dataset that have similar strings in eval_datasets based on fuzzy matching.

    Args:
        dataset: Input dataset to check for matches
        column: Column name in dataset to check for matches
        eval_datasets: List of dataset names to check against
        eval_columns: List of column names in eval datasets to check
        eval_splits: List of splits in eval datasets to check
        similarity_threshold: Minimum similarity score to consider a match

    Returns:
        Dataset with additional columns:
        - matched_dataset: Name of matched dataset (or empty if no match)
        - matched_text: Text that was matched (or empty if no match)
        - match_score: Similarity score of match (or 0 if no match)
    """
    n_processes = mp.cpu_count()

    # Get values from input dataset
    values1 = [str(x) for x in dataset[column] if x is not None]

    # Initialize match info
    match_info = [
        {"matched_dataset": "", "matched_text": "", "match_score": 0.0}
        for _ in range(len(dataset))
    ]

    # Load eval datasets
    for idx in range(len(eval_datasets)):
        dataset_name_and_config = eval_datasets[idx]
        split = eval_splits[idx]
        eval_column = eval_columns[idx]
        dataset_name_and_config_split = dataset_name_and_config.split("::")
        dataset_name = dataset_name_and_config_split[0]
        dataset_config = (
            dataset_name_and_config_split[1]
            if len(dataset_name_and_config_split) > 1
            else None
        )
        ds = load_dataset(
            dataset_name, name=dataset_config, split=split, trust_remote_code=True
        )
        values2 = [str(x) for x in ds[eval_column] if x is not None]

        process_pair = partial(
            process_string_pair,
            values2=values2,
            similarity_threshold=similarity_threshold,
        )

        with Pool(n_processes) as pool:
            matches = list(
                tqdm(
                    pool.imap(process_pair, values1, chunksize=100),
                    total=len(values1),
                    desc=f"Processing {dataset_name}",
                )
            )

        # Update match info with highest scoring match
        for i, match_list in enumerate(matches):
            if match_list:  # If any matches found
                # Get highest scoring match
                best_match = max(match_list, key=lambda x: x[2])
                score = best_match[2]

                # Only update if score is higher than current best match
                if score > match_info[i]["match_score"]:
                    match_info[i].update(
                        {
                            "matched_dataset": dataset_name,
                            "matched_text": best_match[1],
                            "match_score": score,
                        }
                    )

    # Add match info to dataset
    def add_match_info(example, idx):
        example.update(match_info[idx])
        return example

    annotated_dataset = dataset.map(add_match_info, with_indices=True)

    # Print summary
    matches_found = sum(
        1 for info in match_info if info["match_score"] >= similarity_threshold
    )
    print(
        f"Found {matches_found} rows with matches above threshold {similarity_threshold}"
    )
    print(f"Dataset size: {len(dataset)}")

    return annotated_dataset
