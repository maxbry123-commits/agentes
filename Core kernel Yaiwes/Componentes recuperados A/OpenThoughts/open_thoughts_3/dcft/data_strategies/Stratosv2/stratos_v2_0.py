import os

from datasets import concatenate_datasets, load_dataset

SKY_T1_SYSTEM_PROMPT_FINAL = "Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered thinking process. Please structure your response into two main sections: Thought and Solution. In the Thought section, detail your reasoning process using the specified format: <|begin_of_thought|> {thought with steps separated with '\\n\\n'} <|end_of_thought|> Each step should include detailed considerations such as analisying questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps. In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. The solution should remain a logical, accurate, concise expression style and detail necessary step needed to reach the conclusion, formatted as follows: <|begin_of_solution|> {final formatted, precise, and clear solution} <|end_of_solution|> Now, try to solve the following question through the above guidelines:"  # noqa


def map_to_sharegpt(x):
    x["system"] = SKY_T1_SYSTEM_PROMPT_FINAL
    x["conversations"] = [
        {"from": "user", "value": x["question"]},
        {
            "from": "assistant",
            "value": f"<|begin_of_thought|>\n\n{x['deepseek_thinking_trajectory']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_attempt']}\n\n<|end_of_solution|>",
        },
    ]
    return x


dataset = load_dataset("simplescaling/s1K-with-deepseek-r1", split="train")
dataset = dataset.map(map_to_sharegpt, num_proc=os.cpu_count())
dataset = dataset.select_columns(["conversations", "system"])

stratos = load_dataset("mlfoundations-dev/stratos_verified_mix", split="train")
combined = concatenate_datasets([dataset, stratos])
combined.push_to_hub("mlfoundations-dev/stratos_verified_plus_s1r1")
