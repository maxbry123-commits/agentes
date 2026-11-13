import os

from bespokelabs import curator
from datasets import concatenate_datasets, load_dataset


class Reasoner(curator.LLM):
    """Curator class for processing Numina dataset."""

    return_completions_object = True

    def prompt(self, input):
        return input["question"]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        input["deepseek_thinking_trajectory"] = response["choices"][0]["message"][
            "reasoning"
        ]
        input["deepseek_attempt"] = response["choices"][0]["message"]["content"]
        return input


# https://openrouter.ai/deepseek/deepseek-r1/providers
llm = Reasoner(
    model_name="deepseek/deepseek-r1",
    backend="openai",
    generation_params={
        "include_reasoning": True,
        "max_tokens": 32000,
        "provider": {
            "order": ["Fireworks", "Kluster"],
            "allow_fallbacks": False,
            "sort": "throughput",
            "require_parameters": True,
        },
    },
    backend_params={
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.environ.get("OPENROUTER_API_KEY"),
        "invalid_finish_reasons": [
            "content_filter",
        ],
        "max_retries": 5,
        "max_requests_per_minute": 20,
        "max_tokens_per_minute": 10000000000000,
        "request_timeout": 60 * 30,
    },
)


num_cpus = os.cpu_count()
dataset = load_dataset("simplescaling/s1K", split="train")


def unroll_trajectory(example):
    example["gemini_thinking_trajectory"] = example["thinking_trajectories"][0]
    example["gemini_attempt"] = example["attempt"]
    return example


dataset = dataset.map(unroll_trajectory, num_proc=num_cpus)
dataset = dataset.remove_columns(["thinking_trajectories", "cot", "attempt"])
print(dataset)

response = llm(dataset)
print(response)

successfuls = []
nones = response.filter(lambda x: x["deepseek_attempt"] is None)
successfuls.append(response.filter(lambda x: x["deepseek_attempt"] is not None))
print(len(nones))
again = llm(nones)
successfuls.append(again.filter(lambda x: x["deepseek_attempt"] is not None))
nones = again.filter(lambda x: x["deepseek_attempt"] is None)
print(len(nones))

try_three = llm(nones)
successfuls.append(try_three.filter(lambda x: x["deepseek_attempt"] is not None))
nones = try_three.filter(lambda x: x["deepseek_attempt"] is None)
print(len(nones))

# https://openrouter.ai/deepseek/deepseek-r1/providers
llm = Reasoner(
    model_name="deepseek/deepseek-r1",
    backend="openai",
    generation_params={
        "include_reasoning": True,
        "max_tokens": 32000,
        "provider": {
            "order": ["Fireworks", "Kluster"],
            "allow_fallbacks": False,
            "sort": "throughput",
            "require_parameters": True,
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

try_four = llm(nones)
successfuls.append(try_four.filter(lambda x: x["deepseek_attempt"] is not None))
nones = try_four.filter(lambda x: x["deepseek_attempt"] is None)
print(len(nones))

# https://openrouter.ai/deepseek/deepseek-r1/providers
llm = Reasoner(
    model_name="deepseek/deepseek-r1",
    backend="openai",
    generation_params={
        "include_reasoning": True,
        "max_tokens": 32000,
        "provider": {
            "order": ["Fireworks", "Kluster"],
            "allow_fallbacks": False,
            "sort": "throughput",
            "require_parameters": True,
        },
    },
    backend_params={
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.environ.get("OPENROUTER_API_KEY"),
        "invalid_finish_reasons": [
            "content_filter",
            "length",
            "unkown",
        ],  # in future releases, this should be "unknown" - I did a PR to fix the tpo
        "max_retries": 5,  # increase this to 20
        "max_requests_per_minute": 20,
        "max_tokens_per_minute": 10000000000000,
        "request_timeout": 60 * 30,
    },
)

try_five = llm(nones)
successfuls.append(try_five.filter(lambda x: x["deepseek_attempt"] is not None))
nones = try_five.filter(lambda x: x["deepseek_attempt"] is None)
print(len(nones))

success = concatenate_datasets(successfuls)
success.push_to_hub("simplescaling/s1K-with-deepseek-r1")
assert len(success) == 1000
