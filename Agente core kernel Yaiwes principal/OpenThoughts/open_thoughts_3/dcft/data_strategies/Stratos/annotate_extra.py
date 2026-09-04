from bespokelabs import curator
from datasets import load_dataset
from prompts import SKY_T1_SYSTEM_PROMPT


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
extra_puzzle = load_dataset("mlfoundations-dev/etash_science_puzzle")["train"]
deepseek_result_puzzle = reasoner(extra_puzzle)
deepseek_result_puzzle.push_to_hub("mlfoundations-dev/etash_science_puzzle_annotated")

extra_code_golf = load_dataset("mlfoundations-dev/etash_code_golf")["train"]
deepseek_result_code_golf = reasoner(extra_code_golf)
deepseek_result_code_golf.push_to_hub("mlfoundations-dev/etash_code_golf_annotated")
