from collections import Counter
from typing import List

from datasets import Dataset
from math_verify import parse, verify
from openai import OpenAI


def annotate_kluster(
    dataset: Dataset, input_problem_column: str, output_reasoning_column: str
):
    def f(x):
        client = OpenAI(
            base_url="https://api.kluster.ai/v1",
            api_key="053c3c16-b021-4323-8014-4c1d3bf50bbb",  # Replace with your actual API key
        )
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": x[input_problem_column]},
            ],
        )
        x[output_reasoning_column] = chat_completion.choices[0].content.message
        return x

    breakpoint()
    dataset = dataset.map(f)
    return dataset


def merge_together_existing(dataset: Dataset) -> Dataset:
    def f(x):
        x["extra_deepseek_reasoning"].append(x["reasoning"])
        x["extra_deepseek_solution"].append(x["depseek_solution"])
        return x

    dataset = dataset.map(f)
    return dataset


def choose_shortest(dataset: Dataset, input_column: str, output_column: str) -> Dataset:
    def f(x):
        x[output_column] = min(x[input_column], key=len)
        return x

    dataset = dataset.map(f)
    return dataset


def huggingface_parse_answers(
    dataset: Dataset, solution_column: str, parsed_answer_column: str
) -> Dataset:
    def f(x):
        solutions = x[solution_column]
        answers = [parse(s) for s in solution_column]
        x[parsed_answer_column] = answers
        return x

    dataset = dataset.map(f)
    return dataset


def choose_majority_answer(
    dataset: Dataset,
    solution_column: str,
    parsed_answer_column: str,
    chosen_answer_column: str,
) -> Dataset:
    def f(x):
        parsed_answers = dataset[parsed_answer_column]
        orig_answers = dataset[solution_column]
        correct_answers = find_majority_answers(orig_answers, parsed_answers)
        x[chosen_answer_column] = correct_answers[0]
        return x

    dataset = dataset.map(f)
    return dataset


def find_majority_answers(
    orig_answers: List[str], parsed_answers: List[str]
) -> List[str]:
    """
    Find all strings that represent the same answer as the most common answer.

    Args:
        orig_answers: List of original answer strings
        parsed_answers: List of parsed versions of those answers

    Returns:
        List of original strings that match the most common answer
    """
    # Create groups of equivalent answers
    answer_groups = {}  # maps index of representative answer to list of indices

    for i, parsed in enumerate(parsed_answers):
        # Try to find an existing equivalent group
        found_group = False
        for rep_idx in answer_groups.keys():
            if verify(parsed, parsed_answers[rep_idx]):
                answer_groups[rep_idx].append(i)
                found_group = True
                break

        # If no equivalent group found, create new one
        if not found_group:
            answer_groups[i] = [i]

    # Find the largest group's representative index
    largest_group_idx = max(
        answer_groups.keys(), key=lambda idx: len(answer_groups[idx])
    )

    # Return original strings for all answers in largest group
    return [orig_answers[i] for i in answer_groups[largest_group_idx]]


def choose_first_correct(
    dataset: Dataset,
    input_column: str,
    input_is_correct_column: str,
    output_column: str,
) -> Dataset:
    def f(x):
        try:
            first_correct_idx = x[input_is_correct_column].index(True)
            x[output_column] = x[input_column][first_correct_idx]
        except ValueError:
            return None

    dataset = dataset.map(f)
    return dataset


from typing import List

from datasets import Dataset
from math_verify.metric import math_metric
from math_verify.parser import ExprExtractionConfig, LatexExtractionConfig


def math_verify_map(
    dataset: Dataset,
    ground_truth_column: str,
    solution_column: str,
    output_extracted_answer_column: str,
    output_extracted_gold_column: str,
    output_verifier_label_column: str,
    output_error_column: str,
):
    gold_is_latex = True
    verify_func = math_metric(
        gold_extraction_target=(
            LatexExtractionConfig() if gold_is_latex else ExprExtractionConfig(),
        ),
        pred_extraction_target=(ExprExtractionConfig(), LatexExtractionConfig()),
        aggregation_function=max,
        fallback_mode="first_match",
        precision=6,
    )

    def f(row):
        """Validate a single solution using the verification function."""
        extracted_answers = ""  # Initialize as empty string instead of None
        gold_answers = ""  # Initialize as empty string instead of None
        grade = 0
        try:
            # Use the verification function
            grade, extracted_answers = verify_func(
                [row[ground_truth_column]], [row[solution_column]]
            )

            if extracted_answers is None:
                extracted_answers = ""  # Use empty string instead of None
                gold_answers = ""  # Use empty string instead of None
            else:
                gold_answers = str(extracted_answers[0])  # Convert to string
                extracted_answers = str(extracted_answers[1])  # Convert to string

            return {
                **row,  # Keep all existing fields
                output_extracted_answer_column: extracted_answers,
                output_extracted_gold_column: gold_answers,
                output_verifier_label_column: grade == 1,
                output_error_column: "",  # Empty string instead of None
            }

        except Exception as e:
            return {
                **row,  # Keep all existing fields
                output_extracted_answer_column: extracted_answers,
                output_extracted_gold_column: gold_answers,
                output_verifier_label_column: grade == 1,
                output_error_column: str(e),
            }

    return dataset.map(f)


def choose_a_correct_answer(
    dataset: Dataset,
    solution_columns: List[str],
    reason_columns: List[str],
    is_correct_columns: List[str],
    output_solution_column: List[str],
    output_reason_column: List[str],
    output_is_correct_column: List[str],
):
    def f(row):
        correct_response_idx = [
            i for i, is_correct in enumerate(is_correct_columns) if row[is_correct]
        ]
        if not correct_response_idx:
            row[output_is_correct_column] = False
            row[output_solution_column] = ""
            row[output_reason_column] = ""
            return row
        else:
            shortest_correct_solution_idx = min(
                correct_response_idx, key=lambda x: len(row[solution_columns[x]])
            )
            return {
                **row,
                output_solution_column: row[
                    solution_columns[shortest_correct_solution_idx]
                ],
                output_reason_column: row[
                    reason_columns[shortest_correct_solution_idx]
                ],
                output_is_correct_column: row[
                    is_correct_columns[shortest_correct_solution_idx]
                ],
            }

    return dataset.map(f)


def annotate_kluster(
    dataset: Dataset, input_problem_column: str, output_reasoning_column: str
):
    def f(x):
        client = OpenAI(
            base_url="https://api.kluster.ai/v1",
            api_key="053c3c16-b021-4323-8014-4c1d3bf50bbb",  # Replace with your actual API key
        )
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": x[input_problem_column]},
            ],
        )
        x[output_reasoning_column] = chat_completion.choices[0].content.message
        return x

    breakpoint()
    dataset = dataset.map(f)
    return dataset


def merge_together_existing(dataset: Dataset) -> Dataset:
    def f(x):
        x["extra_deepseek_reasoning"].append(x["reasoning"])
        x["extra_deepseek_solution"].append(x["depseek_solution"])
        return x

    dataset = dataset.map(f)
    return dataset


def choose_shortest(dataset: Dataset, input_column: str, output_column: str) -> Dataset:
    def f(x):
        x[output_column] = min(x[input_column], key=len)
        return x

    dataset = dataset.map(f)
    return dataset


def huggingface_parse_answers(
    dataset: Dataset, solution_column: str, parsed_answer_column: str
) -> Dataset:
    def f(x):
        solutions = x[solution_column]
        answers = [parse(s) for s in solution_column]
        x[parsed_answer_column] = answers
        return x

    dataset = dataset.map(f)
    return dataset


def choose_majority_answer(
    dataset: Dataset,
    solution_column: str,
    parsed_answer_column: str,
    chosen_answer_column: str,
) -> Dataset:
    def f(x):
        parsed_answers = dataset[parsed_answer_column]
        orig_answers = dataset[solution_column]
        correct_answers = find_majority_answers(orig_answers, parsed_answers)
        x[chosen_answer_column] = correct_answers[0]
        return x

    dataset = dataset.map(f)
    return dataset


def find_majority_answers(
    orig_answers: List[str], parsed_answers: List[str]
) -> List[str]:
    """
    Find all strings that represent the same answer as the most common answer.

    Args:
        orig_answers: List of original answer strings
        parsed_answers: List of parsed versions of those answers

    Returns:
        List of original strings that match the most common answer
    """
    # Create groups of equivalent answers
    answer_groups = {}  # maps index of representative answer to list of indices

    for i, parsed in enumerate(parsed_answers):
        # Try to find an existing equivalent group
        found_group = False
        for rep_idx in answer_groups.keys():
            if verify(parsed, parsed_answers[rep_idx]):
                answer_groups[rep_idx].append(i)
                found_group = True
                break

        # If no equivalent group found, create new one
        if not found_group:
            answer_groups[i] = [i]

    # Find the largest group's representative index
    largest_group_idx = max(
        answer_groups.keys(), key=lambda idx: len(answer_groups[idx])
    )

    # Return original strings for all answers in largest group
    return [orig_answers[i] for i in answer_groups[largest_group_idx]]
