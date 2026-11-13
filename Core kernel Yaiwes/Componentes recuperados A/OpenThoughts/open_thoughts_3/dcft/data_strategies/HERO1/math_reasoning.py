import os

from bespokelabs import curator
from datasets import Dataset, load_dataset


class Reasoner(curator.LLM):
    """Curator class for reasoning."""

    return_completions_object = True

    def prompt(self, input):
        """Create a prompt for the LLM to reason about the problem."""
        return [{"role": "user", "content": input["question"]}]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        input["deepseek_reasoning"] = response["choices"][0]["message"][
            "reasoning_content"
        ]
        input["deepseek_solution"] = response["choices"][0]["message"]["content"]
        return input


llm = Reasoner(
    model_name="deepseek-reasoner",
    backend="openai",
    generation_params={
        "temp": 0.0
    },  # https://api-docs.deepseek.com/quick_start/parameter_settings recommended temperature for coding / math is 0.0
    backend_params={
        "max_requests_per_minute": 3,
        "max_tokens_per_minute": 100_000_000,
        "base_url": "https://api.deepseek.com/",
        "api_key": os.environ.get("DEEPSEEK_API_KEY"),
        "max_retries": 30,
    },
)

ds = load_dataset("mlfoundations-dev/herorun1_math", split="train")
ds = ds.rename_column("instruction_seed", "question")
ds = ds.take(10)
print(ds[0]["question"])
ds = llm(ds)
print("REASONING: ", ds[0]["deepseek_reasoning"])
print("\n\nSOLUTION: ", ds[0]["deepseek_solution"])
