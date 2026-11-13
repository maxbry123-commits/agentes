import os

from datasets import concatenate_datasets, load_dataset


def convert_sharegpt_skyt1_to_r1_template(x):
    """
    SkyT1 is in the following format:
    value_word: f"<|begin_of_thought|>\n\n{x['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_solution']}\n\n<|end_of_solution|>",

    We want to convert it to the following format:
    value_word: f"<think>\n{x['reasoning']}\n</think>\n\n{x['deepseek_solution']}"

    However, we don't have the x['reasoning'] and x['deepseek_solution'] columns, just the conversations column.
    So we will parse the conversations column to get the reasoning and deepseek_solution.
    Then re-template the conversations column to the new format.
    """
    # Create a copy of the input to avoid modifying the original
    result = dict(x)

    # Process each conversation in the list
    for i, conv in enumerate(result["conversations"]):
        # Only process assistant messages
        if conv["from"] == "assistant":
            value = conv["value"]

            # Extract reasoning and solution from the SkyT1 format
            reasoning = ""
            solution = ""

            # Check if the message contains the SkyT1 format markers
            if (
                "<|begin_of_thought|>" in value
                and "<|end_of_thought|>" in value
                and "<|begin_of_solution|>" in value
                and "<|end_of_solution|>" in value
            ):
                # Extract reasoning between begin_of_thought and end_of_thought
                thought_start = value.find("<|begin_of_thought|>") + len(
                    "<|begin_of_thought|>"
                )
                thought_end = value.find("<|end_of_thought|>")
                if thought_start >= 0 and thought_end >= 0:
                    reasoning = value[thought_start:thought_end].strip()

                # Extract solution between begin_of_solution and end_of_solution
                solution_start = value.find("<|begin_of_solution|>") + len(
                    "<|begin_of_solution|>"
                )
                solution_end = value.find("<|end_of_solution|>")
                if solution_start >= 0 and solution_end >= 0:
                    solution = value[solution_start:solution_end].strip()

                # Create the new R1 template format
                result["conversations"][i][
                    "value"
                ] = f"<think>\n{reasoning}\n</think>\n\n{solution}"
        if conv["from"] == "user":
            if "Return your final response within \\boxed{}. " in conv["value"]:
                result["question"] = conv["value"].split(
                    "Return your final response within \\boxed{}. "
                )[1]
            else:
                result["question"] = conv["value"]

    return result


datasets = []

ds = load_dataset("mlfoundations-dev/extra_unverified", split="train")
ds = ds.map(convert_sharegpt_skyt1_to_r1_template, num_proc=os.cpu_count())
ds = ds.select_columns(["conversations", "question"])
datasets.append(ds)

ds = load_dataset(
    "mlfoundations-dev/OpenR1-Math-Raw-all-correct-sharegpt", split="train"
)
ds = ds.map(convert_sharegpt_skyt1_to_r1_template, num_proc=os.cpu_count())
ds = ds.select_columns(["conversations", "question"])
datasets.append(ds)

ds = concatenate_datasets(datasets)

import multiprocessing as mp
from collections import defaultdict
from functools import partial
from multiprocessing import Pool
from typing import List, Tuple

from datasets import Dataset
from rapidfuzz import fuzz, process
from tqdm import tqdm

EVALUATION_DATASETS = {
    "HuggingFaceH4/MATH-500": {
        "eval_columns": ["problem"],
        "eval_splits": ["test"],
    },
    "Maxwell-Jia/AIME_2024": {
        "eval_columns": ["Problem"],
        "eval_splits": ["train"],
    },
    "yentinglin/aime_2025": {
        "eval_columns": ["problem"],
        "eval_splits": ["train"],
    },
    "AI-MO/aimo-validation-amc": {
        "eval_columns": ["problem"],
        "eval_splits": ["train"],
    },
    "livecodebench/code_generation_lite": {
        "eval_columns": ["question_content"],
        "eval_splits": ["test"],
    },
    "Idavidrein/gpqa": {
        "eval_columns": ["Question"],
        "eval_splits": ["train"],
        "eval_subset": "gpqa_diamond",
    },
}


def decontaminate(
    dataset: Dataset, column="question", evals=EVALUATION_DATASETS, threshold=95.0
) -> Dataset:
    """Remove rows from dataset that have similar strings in eval_datasets based on fuzzy matching."""
    n_processes = mp.cpu_count()

    # Get values from input dataset
    dataset_strings = [str(x) for x in dataset[column] if x is not None]
    indices_to_remove = set()

    for eval_name, eval_info in evals.items():
        eval_splits = eval_info["eval_splits"]
        eval_columns = eval_info["eval_columns"]
        eval_subset = eval_info.get("eval_subset", None)
        if eval_subset is not None:
            ds = load_dataset(
                eval_name, eval_subset, split=eval_splits, trust_remote_code=True
            )
        else:
            ds = load_dataset(eval_name, split=eval_splits, trust_remote_code=True)

        # for each split, column, and value
        eval_strings = [
            str(x)
            for split in ds
            for column in eval_columns
            for x in split[column]
            if x is not None
        ]

        # Track indices to remove
        process_pair = partial(
            fuzz_string_pair,
            values2=eval_strings,
            similarity_threshold=threshold,
        )

        with Pool(n_processes) as pool:
            matches = list(
                tqdm(
                    pool.imap(process_pair, dataset_strings, chunksize=100),
                    total=len(dataset_strings),
                    desc=f"Decontaminating against {eval_name}",
                )
            )

        # Find indices where matches were found
        for i, match_list in enumerate(matches):
            if any(score >= threshold for _, _, score in match_list):
                indices_to_remove.add(i)

    keep_mask = [i for i in range(len(dataset)) if i not in indices_to_remove]
    clean_dataset = dataset.select(keep_mask)

    print(f"Removed {len(indices_to_remove)} contaminated rows")
    print(f"Original size: {len(dataset)}, New size: {len(clean_dataset)}")

    return clean_dataset


def fuzz_string_pair(
    str1: str, values2: List[str], similarity_threshold: float
) -> List[Tuple]:
    matches_with_scores = process.extract(
        str1, values2, scorer=fuzz.ratio, score_cutoff=similarity_threshold
    )
    return [
        (str1, match_tuple[0], match_tuple[1]) for match_tuple in matches_with_scores
    ]


def deduplicate(
    dataset: Dataset, column="question", similarity_threshold: float = 95.0
) -> Dataset:
    """Fuzzy deduplicate dataset rows based on fuzzy string matching within specified column."""
    values = [str(x) for x in dataset[column] if x is not None]
    unique_values = list(set(values))
    n_processes = mp.cpu_count()

    process_pair = partial(
        fuzz_string_pair,
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


# ds = deduplicate(ds) # don't do dedup for now
ds = decontaminate(ds)
ds.push_to_hub("mlfoundations-dev/hero-1")
