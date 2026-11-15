# usage: python dcft/data_strategies/Law/law_annotate.py --Q 5 --output mlfoundations-dev/thoughts-lawma-annotations-deepseek-2k-5x
# usage: python dcft/data_strategies/Law/law_annotate.py --truncate 2 --Q 1 --output mlfoundations-dev/lawma-annotations-deepseek-all-1x

from bespokelabs import curator

import argparse
from datasets import Dataset, load_dataset

from deepseek_reasoner import deepseek_reason
from utils import verify, format_prompt, duplicate_rows


class Reasoner(curator.LLM):
    """Curator class for processing claude reasoning."""

    return_completions_object = True

    def prompt(self, input):
        """Directly pass the question to the model."""
        return input["problem"]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        content = response["content"]
        thinking = ""
        text = ""
        for content_block in content:
            if content_block["type"] == "thinking":
                thinking = content_block["thinking"]
            elif content_block["type"] == "text":
                text = content_block["text"]
            elif content_block["type"] == "redacted_thinking":
                print("Redacted thinking block! (notifying you for fun)")

        if text == "" or thinking == "":
            print(
                "WARNING: No text or thinking found in this response (likely due to 'finish_reason': 'length')"
            )

        input["claude_thinking_trajectory"] = thinking
        input["claude_attempt"] = text
        return input


def reason(ds):
    reasoner = Reasoner(
        model_name="claude-3-7-sonnet-20250219",
        generation_params={
            "max_tokens": 16000,
            "thinking": {"type": "enabled", "budget_tokens": 14000},
        },
        batch=True,
        backend="anthropic",
        backend_params={"require_all_responses": False},
    )
    ds = reasoner(ds)
    return ds


def map_text_to_share_gpt(row):
    user_message = row["prompt"]
    assistant_message = f"<|begin_of_thought|>\n\n{row['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{row['deepseek_solution']}\n\n<|end_of_solution|>"

    return {
        "system": SKY_T1_SYSTEM_PROMPT,
        "conversations": [
            {"from": "user", "value": user_message},
            {"from": "assistant", "value": assistant_message},
        ],
    }


# add main to parse parameters
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate finetuning data for lawma annotations"
    )
    parser.add_argument(
        "--Q", type=int, default=5, help="Number of times to duplicate each row"
    )
    parser.add_argument(
        "--truncate", type=int, default=-1, help="Truncate the dataset if > 0"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="mlfoundations-dev/thoughts-lawma-annotations-claude",
        help="Output dataset",
    )
    args = parser.parse_args()

    ds = load_dataset(
        "ricdomolm/lawma-tasks", name="sc_lcdispositiondirection", split="train"
    )
    ds = ds.shuffle(seed=42)
    # add an id to each row
    ds = ds.map(lambda row, idx: {"id": idx + 1}, with_indices=True)

    if args.truncate > 0:
        ds = ds.select(range(args.truncate))

    ds = ds.map(lambda row: {"problem": format_prompt(row)})

    ds = duplicate_rows(ds, args.Q)

    print(ds)

    # ds = reason(ds)
    ds = deepseek_reason(ds)

    ds = ds.map(verify)

    # ds.push_to_hub("mlfoundations-dev/thoughts-lawma-annotations-claude")
    ds.push_to_hub(args.output)
