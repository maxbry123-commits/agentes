from datasets import load_dataset

dataset = load_dataset("open-thoughts/OpenThoughts-114k", "metadata", split="train")


def f(row):
    row["response"] = (
        f"<think>\n{row['deepseek_reasoning']}\n</think>\n\n{row['deepseek_solution']}"
    )
    return row


dataset = dataset.map(f)

from dcft.data_strategies.commons import convert_instruction_response_to_sharegpt

dataset = convert_instruction_response_to_sharegpt(
    dataset,
    input_instruction_column="problem",
    input_response_column="response",
    output_sharegpt_column="conversations",
)

dataset.push_to_hub("mlfoundations-dev/openthoughts_114k_thinkprompt")
