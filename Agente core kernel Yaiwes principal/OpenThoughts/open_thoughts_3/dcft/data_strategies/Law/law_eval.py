# usage: python dcft/data_strategies/Law/law_eval.py --model mlfoundations-dev/qwen_lawma_filtered_deepseek-all-1x --truncate 1000
# usage: python dcft/data_strategies/Law/law_eval.py --model mlfoundations-dev/qwen_lawma_filtered_deepseek-2k-5x --truncate 1000
# usage: python dcft/data_strategies/Law/law_eval.py --model Qwen/Qwen2.5-7B-Instruct --truncate 100
# usage: python dcft/data_strategies/Law/law_eval.py --model meta-llama/Llama-3.1-8B-Instruct --truncate 100


# usage: python dcft/data_strategies/Law/law_eval.py --model mlfoundations-dev/qwen_lawma_filtered_deepseek-2k-5x-v2 --truncate 1000
# usage: python dcft/data_strategies/Law/law_eval.py --model mlfoundations-dev/qwen_lawma_filtered_deepseek-all-1x-v2 --truncate 1000


from vllm import LLM, SamplingParams
from datasets import load_dataset
from utils import format_prompt, veryify, duplicate_rows
from functools import partial
import argparse
import pandas as pd
from transformers import AutoTokenizer


SKY_T1_SYSTEM_PROMPT = "Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered thinking process. Please structure your response into two main sections: Thought and Solution. In the Thought section, detail your reasoning process using the specified format: <|begin_of_thought|> {thought with steps separated with '\\n\\n'} <|end_of_thought|> Each step should include detailed considerations such as analisying questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps. In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. The solution should remain a logical, accurate, concise expression style and detail necessary step needed to reach the conclusion, formatted as follows: <|begin_of_solution|> {final formatted, precise, and clear solution} <|end_of_solution|> Now, try to solve the following question through the above guidelines:"  # noqa


def generate_batch_responses(batch, sampling_params, llm):
    # Prepend the system prompt to each input prompt
    prompts = [f"{SKY_T1_SYSTEM_PROMPT}\n\n{p}" for p in batch["truncated_task"]]

    # Generate responses
    outputs = llm.generate(prompts, sampling_params)
    generated_texts = [output.outputs[0].text for output in outputs]

    # Add the generated texts as a new column in the batch
    batch["completion"] = generated_texts
    return batch


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Evaluate model")
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-7B-Instruct",
        help="Model to use for evaluation",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="ricdomolm/lawma-tasks",
        help="Dataset to use for evaluation",
    )
    parser.add_argument("--truncate", type=int, default=50, help="Truncate evals to")
    parser.add_argument(
        "--Q", type=int, default=5, help="Number of outputs for majority vote"
    )
    args = parser.parse_args()

    ds = load_dataset(
        "ricdomolm/lawma-tasks", name="sc_lcdispositiondirection", split="test"
    )
    ds = ds.shuffle(seed=42)
    # get a subset of the dataset
    ds = ds.select(range(min(args.truncate, len(ds))))
    # add a field to the dataset that contains the formatted prompt
    ds = ds.map(
        lambda row: {
            "truncated_task": format_prompt(row, max_tokens=8192, token_multiplier=4)
        }
    )

    # get the length of the prompts
    prompts = [f"{SKY_T1_SYSTEM_PROMPT}\n\n{p}" for p in ds["truncated_task"]]

    # Load the tokenizer (replace with your model's actual name)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    token_counts = [len(tokenizer(prompt)["input_ids"]) for prompt in prompts]
    ds = ds.add_column("token_count", token_counts)

    print(pd.Series(token_counts).describe())
    print(f"Max context length: {tokenizer.model_max_length} tokens")

    ### standard eval one-shot

    # llm = LLM(  model=args.model,
    #            dtype="bfloat16",
    #            max_model_len=16384,
    #            trust_remote_code=True,
    #            tokenizer=args.model,
    #            gpu_memory_utilization=0.8,
    #            )
    sampling_params = SamplingParams(temperature=0.0, max_tokens=16384)
    llm = LLM(
        model=args.model,
        dtype="bfloat16",
        max_model_len=16384,
        trust_remote_code=True,
    )
    ds = ds.map(
        partial(generate_batch_responses, sampling_params=sampling_params, llm=llm),
        batched=True,
        batch_size=args.truncate,
    )
    ds = ds.map(partial(verify, solution_key="completion"))

    average_verify = ds["verify"].count(True) / len(ds)
    print(f"Average verify: {average_verify}")
    average_format_wrong = ds["format_correct"].count(False) / len(ds)
    print(f"Average format error: {average_format_wrong}")

    # save the dataset
    model_name = args.model.split("/")[1]
    ds.push_to_hub(f"mlfoundations-dev/eval-lawma-tasks-{model_name}")

    ###### eval with majority vote

    # add an id to each row
    ds = ds.map(lambda row, idx: {"id": idx + 1}, with_indices=True)
    # duplicate each row Q times
    ds = duplicate_rows(ds, args.Q)

    # Define sampling parameters
    # sampling_params = SamplingParams(temperature=0.7, top_p=0.9, top_k=20, max_tokens=9216)
    sampling_params = SamplingParams(
        temperature=1.2, top_p=0.95, top_k=60, max_tokens=9216
    )

    ds = ds.map(
        partial(generate_batch_responses, sampling_params=sampling_params, llm=llm),
        batched=True,
        batch_size=args.truncate * args.Q,
    )
    ds = ds.map(partial(verify, solution_key="completion"))
    # Convert dataset to a DataFrame
    df = pd.DataFrame(ds)
    # Group by "id" and compute sum of "verify" for each group
    df_grouped = df.groupby("id")["verify"].sum().reset_index()
    # Apply threshold to determine verification status
    df_grouped["verify"] = df_grouped["verify"] >= (args.Q / 2)

    # Compute the average verification rate
    average_verify = df_grouped["verify"].mean()

    print("Average majority accuracy: ", average_verify)
