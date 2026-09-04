from datasets import load_dataset, Dataset
from data_strategies.MultipleSamples.utils import select_correct_multiple_samples
from data_strategies.commons import (
    remove_columns,
    convert_instruction_response_to_sharegpt,
)


def process_ground_truth(dataset: Dataset) -> Dataset:
    dataset = remove_columns(dataset, columns=["generations"])
    dataset = select_correct_multiple_samples(
        dataset,
        response_column="generation",
        verified_response_column="verified_generation",
    )
    dataset = convert_instruction_response_to_sharegpt(
        dataset,
        input_instruction_column="problem",
        input_response_column="verified_generation",
        output_sharegpt_column="conversations",
    )
    # dataset.push_to_hub("mlfoundations-dev/multiple_samples_ground_truth_openr1_llm_verifier_temp")
    return dataset
