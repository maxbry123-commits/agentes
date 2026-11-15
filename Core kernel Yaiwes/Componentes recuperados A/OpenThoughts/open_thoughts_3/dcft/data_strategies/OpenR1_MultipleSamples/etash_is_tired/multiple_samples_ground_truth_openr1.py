from datasets import load_dataset, Dataset
from data_strategies.MultipleSamples.utils import (
    select_correct_multiple_samples,
    ground_truth_verification,
)
from data_strategies.TestTime.generator import merge_duplicate_rows
from data_strategies.commons import (
    remove_columns,
    select_rows_without,
    convert_instruction_response_to_sharegpt,
)


def process_ground_truth(dataset: Dataset) -> Dataset:
    dataset = select_rows_without(dataset, conditions={"answer": "proof"})
    dataset = merge_duplicate_rows(
        dataset, diff_columns=["generation", "correct", "judge_reasoning"]
    )
    dataset = ground_truth_verification(
        dataset,
        response_column="generation",
        solution_column="solution",
        output_column="verified_generation",
    )
    dataset = convert_instruction_response_to_sharegpt(
        dataset,
        input_instruction_column="problem",
        input_response_column="verified_generation",
        output_sharegpt_column="conversations",
    )
    # dataset.push_to_hub("mlfoundations-dev/multiple_samples_ground_truth_openr1_temp")
    return dataset
