import json
import os
from functools import partial

from datasets import concatenate_datasets, load_dataset
from transformers import AutoTokenizer

SKY_T1_SYSTEM_PROMPT_FINAL = "Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered thinking process. Please structure your response into two main sections: Thought and Solution. In the Thought section, detail your reasoning process using the specified format: <|begin_of_thought|> {thought with steps separated with '\\n\\n'} <|end_of_thought|> Each step should include detailed considerations such as analisying questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps. In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. The solution should remain a logical, accurate, concise expression style and detail necessary step needed to reach the conclusion, formatted as follows: <|begin_of_solution|> {final formatted, precise, and clear solution} <|end_of_solution|> Now, try to solve the following question through the above guidelines:"  # noqa


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
            value_word: f"<|begin_of_thought|>\n\n{x['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_solution']}\n\n<|end_of_solution|>",  # noqa
        },
    ]
    x["system"] = SKY_T1_SYSTEM_PROMPT_FINAL
    return x


def count_tokens(example):
    reasoning_tokens = len(tokenizer.encode(example["reasoning"]))
    solution_tokens = len(tokenizer.encode(example["deepseek_solution"]))
    problem_tokens = len(tokenizer.encode(example["problem"]))
    formatted_text = tokenizer.apply_chat_template(
        example["conversations"], tokenize=False
    )
    formatted_text_tokens = len(tokenizer.encode(formatted_text))
    example["formatted_text"] = formatted_text
    example["formatted_text_tokens"] = formatted_text_tokens
    example["reasoning_tokens"] = reasoning_tokens
    example["solution_tokens"] = solution_tokens
    example["problem_tokens"] = problem_tokens
    return example


num_cpus = os.cpu_count()
tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True
)

math = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated", split="train"
)
code = load_dataset(
    "mlfoundations-dev/code_stratos_scale_rejection_sampled_test", split="train"
)
science_puzzle = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_annotated_with_answers",
    split="train",
)  # noqa

math = math.map(
    partial(
        map_to_share_gpt,
        user_column="problem",
        value_word="content",
        key_word="role",
        math=True,
    ),
    num_proc=num_cpus,
)  # noqa
code = code.map(
    partial(
        map_to_share_gpt,
        value_word="content",
        user_column="prompt_formatted",
        key_word="role",
        code=True,
    ),
    num_proc=num_cpus,
)  # noqa
science_puzzle = science_puzzle.map(
    partial(
        map_to_share_gpt, value_word="content", user_column="problem", key_word="role"
    ),
    num_proc=num_cpus,
)  # noqa

math = math.map(count_tokens, num_proc=num_cpus)
code = code.map(count_tokens, num_proc=num_cpus)
science_puzzle = science_puzzle.map(count_tokens, num_proc=num_cpus)

for dataset, name in [
    (math, "Math"),
    (code, "Code"),
    (science_puzzle, "Science & Puzzle"),
]:  # noqa
    print(f"\n{name} Dataset Token Statistics:")
    print(
        f"Average problem tokens: {sum(dataset['problem_tokens']) / len(dataset):.2f}"
    )
    print(
        f"Average reasoning tokens: {sum(dataset['reasoning_tokens']) / len(dataset):.2f}"
    )
    print(
        f"Average solution tokens: {sum(dataset['solution_tokens']) / len(dataset):.2f}"
    )
    print(
        f"Average templated tokens: {sum(dataset['total_templated_tokens']) / len(dataset):.2f}"
    )

for dataset, name in [
    (math, "Math"),
    (code, "Code"),
    (science_puzzle, "Science & Puzzle"),
]:  # noqa
    num_over_16k = len([x for x in dataset["total_templated_tokens"] if x > 16384])
    print(f"\n{name} Dataset Over 16k Tokens:")
    print(f"Number of rows with >16k tokens: {num_over_16k}")
    print(f"Percentage of dataset: {(num_over_16k/len(dataset))*100:.2f}%")

math = math.filter(lambda x: x["total_templated_tokens"] < 16384, num_proc=num_cpus)
code = code.filter(lambda x: x["total_templated_tokens"] < 16384, num_proc=num_cpus)
science_puzzle = science_puzzle.filter(
    lambda x: x["total_templated_tokens"] < 16384, num_proc=num_cpus
)

# Remap conversations since we need to use from and value (dcft training) instead of role and content (qwen tokenizer) # noqa
math = math.remove_columns(["conversations"])
code = code.remove_columns(["conversations"])
science_puzzle = science_puzzle.remove_columns(["conversations"])

math = math.map(
    partial(map_to_share_gpt, user_column="problem", math=True), num_proc=num_cpus
)
code = code.map(
    partial(map_to_share_gpt, user_column="prompt_formatted", code=True),
    num_proc=num_cpus,
)
science_puzzle = science_puzzle.map(
    partial(map_to_share_gpt, user_column="problem"), num_proc=num_cpus
)

ds = concatenate_datasets([math, code, science_puzzle])
ds = ds.select_columns(["system", "conversations"])
# ds.push_to_hub("mlfoundations-dev/unverified_stratos_mix_below_16384_cutoff_without_metadata")

math = math.filter(lambda x: x["correct"], num_proc=num_cpus)
code = code.filter(lambda x: x["correctness"], num_proc=num_cpus)
science_puzzle = science_puzzle.filter(lambda x: x["correctness"], num_proc=num_cpus)

ds = concatenate_datasets([math, code, science_puzzle])
ds = ds.select_columns(["system", "conversations"])
# ds.push_to_hub("mlfoundations-dev/verified_stratos_mix_below_16384_cutoff_without_metadata")
