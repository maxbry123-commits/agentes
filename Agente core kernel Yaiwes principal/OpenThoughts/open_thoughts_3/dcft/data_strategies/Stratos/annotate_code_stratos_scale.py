import json

from bespokelabs import curator
from datasets import load_dataset

from dcft.data_strategies.Stratos.convert import format_code_prompt
from dcft.data_strategies.Stratos.prompts import (
    SKY_T1_SYSTEM_PROMPT,
    SKY_T1_SYSTEM_PROMPT_FINAL,
)


class Reasoner(curator.LLM):
    return_completions_object = True

    def prompt(self, input):
        """Create a prompt for the LLM to reason about the problem."""

        formatted_prompt = format_code_prompt(input)

        return [
            {"role": "system", "content": SKY_T1_SYSTEM_PROMPT},
            {"role": "user", "content": formatted_prompt},
        ]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        input["reasoning"] = response["choices"][0]["message"]["reasoning_content"]
        input["deepseek_solution"] = response["choices"][0]["message"]["content"]
        input["formatted_prompt"] = format_code_prompt(input)
        return input


code_dataset = load_dataset("mlfoundations-dev/code_stratos_scale")["train"]

reasoner = Reasoner(
    model_name="deepseek-reasoner",
    backend_params={
        "max_requests_per_minute": 600,
        "max_tokens_per_minute": 10000000,
        "request_timeout": 30 * 60,
    },
    generation_params={
        "temp": 0.0,
        "max_tokens": 8192,
    },
)
deepseek_result = reasoner(code_dataset)
deepseek_result.push_to_hub("mlfoundations-dev/code_stratos_scale_annotated")

# Rejection sampling is done in code_stratos_scale_rejection_sampled_test.yaml
# Dataset pushed to mlfoundations-dev/code_stratos_scale_rejection_sampled_test


def map_code_to_share_gpt(x):
    test_case = json.loads(x["test_cases"])
    starter_code = x["starter_code"]
    prompt = x["problem"]

    user_message = ""
    data = test_case
    if not data.get("fn_name"):
        user_message += "Generate an executable Python function generated from the given prompt. The function should take stdin as input and print the output. Simply call the function after the definition."  # "\nUse Standard Input format"#\n" #noqa
    else:
        user_message += "Generate an executable Python function generated from the given prompt. Return the function body without invoking it at the final solution."  # "\nUse Call-Based format"#\n" #noqa
    data = prompt
    user_message += data
    if starter_code is not None:
        data = starter_code
        data = "\n" + data
        user_message += data
    else:
        pass
    assistant_message = f"<|begin_of_thought|>\n\n{x['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_solution']}\n\n<|end_of_solution|>"

    return {
        "system": SKY_T1_SYSTEM_PROMPT_FINAL,
        "conversations": [
            {"from": "user", "value": user_message},
            {"from": "assistant", "value": assistant_message},
        ],
    }


rejection_sampled_code = load_dataset(
    "mlfoundations-dev/code_stratos_scale_rejection_sampled_test"
)["train"]
rejection_sampled_code = rejection_sampled_code.filter(lambda x: x["correctness"])
rejection_sampled_code = rejection_sampled_code.map(map_code_to_share_gpt, num_proc=32)
rejection_sampled_code = rejection_sampled_code.select_columns(
    ["system", "conversations"]
)
rejection_sampled_code.push_to_hub("mlfoundations-dev/code_stratos_scale_share_gpt")
