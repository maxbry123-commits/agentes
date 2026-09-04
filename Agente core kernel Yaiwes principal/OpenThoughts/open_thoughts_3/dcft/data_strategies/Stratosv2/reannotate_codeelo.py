import os

from bespokelabs import curator
from datasets import load_dataset

num_cpus = os.cpu_count()


class Reasoner(curator.LLM):
    """Curator class for processing Numina dataset."""

    return_completions_object = True

    def prompt(self, input):
        return input["problem"]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        response_text = response["choices"][0]["message"]["content"]

        # Extract reasoning between <think> tags
        reasoning_start = response_text.find("<think>") + len("<think>")
        reasoning_end = response_text.find("</think>")
        input["r1_reasoning"] = response_text[reasoning_start:reasoning_end].strip()

        # Everything after </think> is the solution
        solution_start = reasoning_end + len("</think>")
        input["r1_solution"] = response_text[solution_start:].strip()

        return input


# https://api.together.ai/models/deepseek-ai/DeepSeek-R1
llm = Reasoner(
    model_name="deepseek-ai/DeepSeek-R1",
    backend="openai",
    generation_params={
        "max_tokens": 16000,
    },
    backend_params={
        "base_url": "https://api.together.xyz/v1",
        "api_key": os.environ.get("TOGETHER_API_KEY"),
        "max_retries": 20,
        "request_timeout": 60 * 30,
        "max_requests_per_minute": 90,
        "max_tokens_per_minute": 249_960,
        "require_all_responses": True,
    },
)


# description, input, output, interaction and note are in Markdown format
# combine these all to give the prompt
# https://huggingface.co/datasets/Qwen/CodeElo
# https://codeelo-bench.github.io/
ds = load_dataset("Qwen/CodeElo", split="train")
ds = ds.filter(lambda x: x["question_type"] != "proof")
ds = ds.filter(
    lambda x: x["source"]
    in ["inequalities", "number_theory", "cn_contest", "olympiads_ref"]
)
ds = ds.filter(
    lambda x: x["problem_is_valid"] == "Yes" and x["solution_is_valid"] == "Yes"
)
ds = ds.filter(lambda x: x["problem"] not in [None, "", " ", "  "])
ds = ds.filter(lambda x: x["answer"] not in [None, "", " ", "  ", "not found", "proof"])
ds = llm(ds)
ds.push_to_hub("mlfoundations-dev/numina_math_1_5_extra_r1")
