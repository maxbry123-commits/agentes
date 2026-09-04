# usage: python dcft/data_strategies/Law/law_generate_finetuning.py --dataset mlfoundations-dev/thoughts-lawma-annotations-deepseek-2k-5x-formated --output mlfoundations-dev/lawma-annotations-deepseek-2k-5x-deepseek-verified-share-gpt
# usage: python dcft/data_strategies/Law/law_generate_finetuning.py --dataset mlfoundations-dev/lawma-annotations-deepseek-all-1x-formated --output mlfoundations-dev/lawma-annotations-deepseek-all-1x-verified-share-gpt


from datasets import load_dataset
from utils import format_prompt, verify
import argparse
from transformers import AutoTokenizer


SKY_T1_SYSTEM_PROMPT = "Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered thinking process. Please structure your response into two main sections: Thought and Solution. In the Thought section, detail your reasoning process using the specified format: <|begin_of_thought|> {thought with steps separated with '\\n\\n'} <|end_of_thought|> Each step should include detailed considerations such as analisying questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps. In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. The solution should remain a logical, accurate, concise expression style and detail necessary step needed to reach the conclusion, formatted as follows: <|begin_of_solution|> {final formatted, precise, and clear solution} <|end_of_solution|> Now, try to solve the following question through the above guidelines:"  # noqa


def map_to_share_gpt(
    x,
    problem_key="truncated_task",
    reasoning_key="reasoning",
    solution_key="deepseek_solution_formatted",
):
    user = x[problem_key]
    return {
        "system": SKY_T1_SYSTEM_PROMPT,
        "conversations": [
            {"from": "human", "value": user},
            {
                "from": "gpt",
                "value": f"<|begin_of_thought|>\n\n{x[reasoning_key]}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x[solution_key]}\n\n<|end_of_solution|>",
            },
        ],
    }


# add main function to parse parameters
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate finetuning data for lawma annotations"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="mlfoundations-dev/thoughts-lawma-annotations-deepseek",
        help="Dataset to use for finetuning",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="mlfoundations-dev/thoughts-lawma-annotations-deepseek-verified-share-gpt",
        help="Output dataset",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-7B-Instruct",
        help="Model for tokenizer",
    )
    args = parser.parse_args()

    # Load dataset
    ds = load_dataset(args.dataset, split="train")

    # verify
    ds = ds.map(verify)

    # Compute average of 'verify' field for each unique index
    ds_avg = ds.to_dict()  # Convert to dictionary for processing

    # Create a dictionary to store sums and counts
    counts = {}
    avs = {}

    # iterate over each row in the dataset
    for row in ds:
        id = row["id"]
        if id not in counts:
            counts[id] = (0, 0)  # (true_count, false_count)
        true_count, false_count = counts[id]
        if row["verify"]:
            true_count += 1
        else:
            false_count += 1
        counts[id] = (true_count, false_count)
        avs[id] = true_count / (true_count + false_count)

    # make histogram of average values to print out
    hist = {}
    for id in avs:
        av = avs[id]
        if av not in hist:
            hist[av] = 0
        hist[av] += 1

    # Print out histogram
    for av in hist:
        print(f"{av}: {hist[av]}")

    # sum of hist values with average greater than 0.5
    sum_greater_than_half = 0
    for av in hist:
        if av > 0.5:
            sum_greater_than_half += hist[av]
    # print majority accuracy
    print(f"Majority accuracy: {sum_greater_than_half/sum(hist.values())}")

    # accuracty: count all counts that are true and divide by total count
    total_count = 0
    true_count = 0
    for id in counts:
        true_count += counts[id][0]
        total_count += counts[id][0] + counts[id][1]

    print(f"Accuracy: {true_count/total_count}")

    # only retain rows that are correctly verified
    ds = ds.filter(lambda row: row["verify"])

    # add a field to the dataset that contains the formatted prompt
    ds = ds.map(
        lambda row: {
            "truncated_task": format_prompt(row, max_tokens=8192, token_multiplier=2.9)
        }
    )

    # Load the tokenizer (replace with your model's actual name)
    # tokenizer = AutoTokenizer.from_pretrained(args.model)
    # token_counts = [len(tokenizer(prompt)["input_ids"]) for prompt in prompts]
    # ds = ds.add_column("token_count", token_counts)

    # map to share gpt, and retain only its output
    ds = ds.map(
        lambda x: map_to_share_gpt(x),
        remove_columns=ds.column_names,  # Removes all original columns, keeping only the function output
    )

    # shuffle the dataset
    ds = ds.shuffle(seed=42)

    # ds.push_to_hub("mlfoundations-dev/thoughts-lawma-annotations-deepseek-verified-share-gpt")
    ds.push_to_hub(args.output)
