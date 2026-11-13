from bespokelabs import curator
from datasets import load_dataset

from dcft.data_strategies.Stratos.convert import map_to_share_gpt
from dcft.data_strategies.Stratos.prompts import SKY_T1_SYSTEM_PROMPT


class Reasoner(curator.LLM):
    return_completions_object = True

    def prompt(self, input):
        """Create a prompt for the LLM to reason about the problem."""
        return [
            {"role": "system", "content": SKY_T1_SYSTEM_PROMPT},
            {"role": "user", "content": input["problem"]},
        ]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        return {
            "problem": input["problem"],
            "reasoning": response["choices"][0]["message"]["reasoning_content"],
            "deepseek_solution": response["choices"][0]["message"]["content"],
        }


reasoner = Reasoner(
    model_name="deepseek-reasoner",
    generation_params={"temp": 0.0, "max_tokens": 8_000},
    backend_params={
        "max_requests_per_minute": 500,
        "max_tokens_per_minute": 100_000_000,
    },
)
science_and_puzzle_stratos_scale = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale"
)["train"]
science_and_puzzle_stratos_scale = science_and_puzzle_stratos_scale.map(
    lambda x: {"problem": x["question"]}
)
deepseek_result = reasoner(science_and_puzzle_stratos_scale)
deepseek_result.push_to_hub(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_annotated"
)

deepseek_result = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_annotated"
)["train"]
deepseek_result = deepseek_result.map(
    map_to_share_gpt, user_column="problem", num_proc=32
)
deepseek_result = deepseek_result.select_columns(["system", "conversations"])
deepseek_result.push_to_hub(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_share_gpt"
)
