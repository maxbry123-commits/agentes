from datasets import Dataset

from dcft.data_strategies.Stratos.prompts import SKY_T1_SYSTEM_PROMPT_FINAL


def convert_to_share_gpt(dataset: Dataset, user_column: str) -> Dataset:
    def map_to_share_gpt(x):
        user = x[user_column]

        return {
            "system": SKY_T1_SYSTEM_PROMPT_FINAL,
            "conversations": [
                {"from": "user", "value": user},
                {
                    "from": "assistant",
                    "value": f"<|begin_of_thought|>\n\n{x['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_solution']}\n\n<|end_of_solution|>",
                },
            ],
        }

    dataset = dataset.map(map_to_share_gpt)
    return dataset
