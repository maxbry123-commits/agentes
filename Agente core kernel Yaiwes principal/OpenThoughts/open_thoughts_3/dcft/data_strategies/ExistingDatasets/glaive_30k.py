from datasets import load_dataset

dataset = load_dataset("glaiveai/reasoning-v1-20m")["train"]

from dcft.data_strategies.commons import uniform_sample_fixed

dataset = uniform_sample_fixed(dataset, num_samples=30000)

from dcft.data_strategies.commons import convert_instruction_response_to_sharegpt

dataset = convert_instruction_response_to_sharegpt(
    dataset,
    input_instruction_column="prompt",
    input_response_column="response",
    output_sharegpt_column="conversations",
)

dataset.push_to_hub("mlfoundations-dev/glaive_reasoning_30k")
