from datasets import Dataset, load_dataset
from dcft.data_strategies.MultipleSamples.utils import extract_with_math_verify_safe
from data_strategies.TestTime.generator import merge_duplicate_rows
from data_strategies.MultipleSamples.utils import majority_consensus
from data_strategies.commons import (
    remove_columns,
    convert_instruction_response_to_sharegpt,
)


def process_majority_consensus(dataset: Dataset) -> Dataset:
    dataset = extract_with_math_verify_safe(
        dataset, input_column="generation", output_column="generation_extracted_answer"
    )
    dataset = merge_duplicate_rows(
        dataset, diff_columns=["generation_extracted_answer", "generation"]
    )
    dataset = majority_consensus(
        dataset,
        response_column="generation",
        verified_response_column="verified_generation",
        extracted_answer_column="generation_extracted_answer",
    )
    dataset = remove_columns(dataset, columns=["_majority_responses"])
    dataset = convert_instruction_response_to_sharegpt(
        dataset,
        input_instruction_column="problem",
        input_response_column="verified_generation",
        output_sharegpt_column="conversations",
    )
    # dataset.push_to_hub("mlfoundations-dev/multiple_samples_majority_consensus_openr1_math_verify_temp")
    return dataset
