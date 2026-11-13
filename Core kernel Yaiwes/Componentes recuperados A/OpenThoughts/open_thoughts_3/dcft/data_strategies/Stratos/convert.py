import json

from dcft.data_strategies.Stratos.prompts import SKY_T1_SYSTEM_PROMPT_FINAL


def format_code_prompt(x):
    formatted_prompt = ""

    data = json.loads(x["test_cases"])
    if not data.get("fn_name"):
        formatted_prompt += "Generate an executable Python function generated from the given prompt. The function should take stdin as input and print the output. Simply call the function after the definition."  # noqa
    else:
        formatted_prompt += "Generate an executable Python function generated from the given prompt. Return the function body without invoking it at the final solution."  # noqa

    formatted_prompt += x["problem"]
    if x["starter_code"] is not None:
        data = x["starter_code"]
        data = "\n" + data
        formatted_prompt += data
    return formatted_prompt


def map_to_share_gpt(
    x, user_column, value_word="value", code=False, math=False, key_word="from"
):
    if code and "formatted_prompt" not in x:
        user = format_code_prompt(x)
    elif math:
        user = f"Return your final response within \\boxed{{}}. {x[user_column]}"
    else:
        user = x[user_column]

    x["conversations"] = [
        {key_word: "user", value_word: user},
        {
            key_word: "assistant",
            value_word: f"<|begin_of_thought|>\n\n{x['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_solution']}\n\n<|end_of_solution|>",
        },
    ]
    x["system"] = SKY_T1_SYSTEM_PROMPT_FINAL
    return x
