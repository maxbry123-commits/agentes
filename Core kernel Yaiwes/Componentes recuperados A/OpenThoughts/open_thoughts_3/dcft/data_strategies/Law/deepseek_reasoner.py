import os

from bespokelabs import curator


DEEPSEEK_R1_SYSTEM_PROMPT = """
Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process
before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of
analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered
thinking process.
"""


class Reasoner(curator.LLM):
    return_completions_object = True

    def prompt(self, input):
        """Create a prompt for the LLM to reason about the problem."""
        return [
            {"role": "system", "content": DEEPSEEK_R1_SYSTEM_PROMPT},
            {"role": "user", "content": input["problem"]},
        ]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        input["reasoning"] = response["choices"][0]["message"]["reasoning_content"]
        input["deepseek_solution"] = response["choices"][0]["message"]["content"]
        return input


def deepseek_reason(ds):
    reasoner = Reasoner(
        model_name="deepseek-reasoner",
        backend_params={
            "max_requests_per_minute": 600,
            "max_tokens_per_minute": 10000000,
            "request_timeout": 30 * 60,
            "base_url": "https://api.deepseek.com/",
            "require_all_responses": False,
        },
        backend="openai",
        generation_params={
            "temp": 0.6,
            "max_tokens": 8192,
        },
    )
    ds = reasoner(ds)
    return ds
