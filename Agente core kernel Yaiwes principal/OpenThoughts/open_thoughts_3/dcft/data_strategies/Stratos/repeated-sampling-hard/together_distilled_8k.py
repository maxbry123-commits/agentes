import os

from bespokelabs import curator
from datasets import load_dataset


class Reasoner(curator.LLM):
    """Curator class for processing Numina dataset."""

    return_completions_object = True

    def prompt(self, input):
        """Create a prompt for the LLM to reason about the problem."""
        return [{"role": "user", "content": input["problem"]}]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        input["deepseek_reasoning_3"] = (
            response["choices"][0]["message"]["reasoning"],
        )
        input["deepseek_solution_3"] = (response["choices"][0]["message"]["content"],)

        return input


# https://openrouter.ai/deepseek/deepseek-r1/providers
# "order": ["DeepSeek", "Kluster", "Together", "Fireworks"],
llm = Reasoner(
    model_name="deepseek/deepseek-r1",
    backend="openai",
    generation_params={
        "include_reasoning": True,
        "max_tokens": 40000,
        "provider": {
            "ignore": ["Avian", "Nebius", "Featherless", "DeepInfra", "Novita"],
            "allow_fallbacks": False,
        },
    },
    backend_params={
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.environ.get("OPENROUTER_API_KEY"),
        "invalid_finish_reasons": ["content_filter"],
        "max_retries": 5,
        "max_requests_per_minute": 20,
        "max_tokens_per_minute": 10000000000000,
        "request_timeout": 60 * 30,
    },
)

dataset = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated_with_difficulty_incorrect_and_hardest_reannotated",
    split="train",
)
dataset = dataset.filter(lambda x: not x["correct"] and x["difficulty"] >= 9)
dataset = dataset.take(200)
dataset = dataset.rename_column("reasoning", "deepseek_reasoning_1")
dataset = dataset.rename_column("deepseek_solution", "deepseek_solution_1")
print(dataset)

response = llm(dataset)
print("REASONING: ", response["deepseek_reasoning_3"][0])
print("SOLUTION: ", response["deepseek_solution_3"][0])
