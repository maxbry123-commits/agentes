import copy
import logging
import random
import string
import logging
from collections import Counter
from datasets import Dataset, load_dataset

from math_verify import parse, verify
from math_verify.metric import math_metric
from math_verify.parser import (
    ExprExtractionConfig,
    LatexExtractionConfig,
    StringExtractionConfig,
)


def extract_with_math_verify(dataset: Dataset, input_column: str, output_column: str):
    def f(x):
        x[output_column] = str(
            parse(
                x[input_column],
                extraction_config=[
                    StringExtractionConfig(),
                    ExprExtractionConfig(),
                    LatexExtractionConfig(),
                ],
            )[1]
        )
        return x

    dataset = dataset.map(f)
    return dataset


def extract_with_math_verify_safe(
    dataset: Dataset, input_column: str, output_column: str
):
    def f(x):
        output = parse(
            x[input_column],
            extraction_config=[
                StringExtractionConfig(),
                ExprExtractionConfig(),
                LatexExtractionConfig(),
            ],
        )
        if len(output) >= 2:
            x[output_column] = str(output[1])
        else:
            x[output_column] = ""
        return x

    dataset = dataset.map(f)
    return dataset


def random_perturb(dataset: Dataset, column_to_perturb: str) -> Dataset:
    def f(x):
        x[column_to_perturb] = change_random_letter(x[column_to_perturb])
        return x

    dataset = dataset.map(f)
    return dataset


def find_majority_indices_safe(numbers):
    counts = Counter(numbers)
    majority_value = max(counts.items(), key=lambda x: x[1])[0]

    return [i for i, x in enumerate(numbers) if x == majority_value]


def majority_consensus(
    dataset: Dataset,
    response_column: str,
    extracted_answer_column: str,
    verified_response_column: str,
) -> Dataset:
    def f(x):
        answers = x[extracted_answer_column]
        majority_answers_indices = find_majority_indices_safe(answers)
        majority_responses = [x[response_column][i] for i in majority_answers_indices]
        x["_majority_responses"] = majority_responses
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[verified_response_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)


def majority_consensus_pick_one(
    dataset: Dataset,
    response_column: str,
    extracted_answer_column: str,
    verified_response_column: str,
) -> Dataset:
    def f(x):
        answers = x[extracted_answer_column]
        majority_answers_indices = find_majority_indices_safe(answers)
        majority_responses = [x[response_column][i] for i in majority_answers_indices]
        x["_majority_responses"] = [majority_responses[0]]
        return x

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.warning(dataset)
    dataset = dataset.map(f)
    logger.warning(dataset)

    all_rows = []
    for row in dataset:
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[verified_response_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)


def all_verification(
    dataset: Dataset, response_column: str, verified_response_column: str
) -> Dataset:
    def f(x):
        x["_majority_responses"] = x[response_column]
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[verified_response_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)


def random_verification(
    dataset: Dataset, response_column: str, verified_response_column: str
) -> Dataset:
    def f(x):
        x["_majority_responses"] = [random.choice(x[response_column])]
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[verified_response_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)


def ground_truth_verification(
    dataset: Dataset, response_column, solution_column, output_column
) -> Dataset:
    verify_func = math_metric(
        gold_extraction_target=[
            StringExtractionConfig(),
            ExprExtractionConfig(),
            LatexExtractionConfig(),
        ],
        pred_extraction_target=[
            StringExtractionConfig(),
            ExprExtractionConfig(),
            LatexExtractionConfig(),
        ],
        aggregation_function=max,
        fallback_mode="first_match",
        precision=6,
    )

    def f(x):
        try:
            x["_majority_responses"] = [
                response
                for idx, response in enumerate(x[response_column])
                if verify_func([x[solution_column]], [x[response_column][idx]])[0] == 1
            ]
        except:
            x["_majority_responses"] = [response for response in x[response_column]]
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        if len(row["_majority_responses"]) == 0:
            continue
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[output_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)


def ground_truth_verification_patch(
    dataset: Dataset, response_column, solution_column, output_column
) -> Dataset:
    verify_func = math_metric(
        gold_extraction_target=[
            StringExtractionConfig(),
            ExprExtractionConfig(),
            LatexExtractionConfig(),
        ],
        pred_extraction_target=[
            StringExtractionConfig(),
            ExprExtractionConfig(),
            LatexExtractionConfig(),
        ],
        aggregation_function=max,
        precision=6,
    )

    def f(x):
        try:
            x["_majority_responses"] = [
                response
                for idx, response in enumerate(x[response_column])
                if verify_func([x[solution_column]], [x[response_column][idx]])[0] == 1
            ]
        except:
            x["_majority_responses"] = [response for response in x[response_column]]
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        if len(row["_majority_responses"]) == 0:
            continue
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[output_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)


def shortest_verification(
    dataset: Dataset, response_column: str, verified_response_column: str
) -> Dataset:
    def f(x):
        x["_majority_responses"] = [min(x[response_column], key=len)]
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[verified_response_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)


def code_same_verification(
    dataset: Dataset,
    verification_column: str,
    code_answers_column: str,
    output_column: str,
) -> Dataset:
    def f(x):
        answers = x[code_answers_column]
        x["_majority_responses"] = [answers[int(i)] for i in x[verification_column]]
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[output_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)


def filter_out_proofs(dataset: Dataset, problem_column: str) -> Dataset:
    dataset = dataset.filter(
        lambda x: "show " not in x[problem_column].lower()
        and "prove " not in x[problem_column].lower()
        and "proof" not in x[problem_column].lower()
    )
    return dataset


def select_correct_multiple_samples(
    dataset: Dataset, response_column: str, verified_response_column: str
) -> Dataset:
    def f(x):
        answers = x[response_column]
        majority_answers_indices = [
            idx for idx, item in enumerate(x["correct"]) if item
        ]
        majority_responses = [x[response_column][i] for i in majority_answers_indices]
        x["_majority_responses"] = majority_responses
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[verified_response_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)
