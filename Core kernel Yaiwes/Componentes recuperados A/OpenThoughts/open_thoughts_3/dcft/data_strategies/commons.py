import json
import logging
from typing import List, Dict, Optional, Union, Any

# from sentence_transformers import LoggingHandler, SentenceTransformer
from tqdm import tqdm
import re

import pandas as pd
import torch
from datasets import Dataset, Sequence, Value

# from sentence_transformers import LoggingHandler, SentenceTransformer
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer


def remove_nones(dataset: Dataset, column: str) -> Dataset:
    return dataset.filter(lambda x: x[column] is not None)


def openai_to_sharegpt(messages: list) -> list:
    role_map = {"user": "human", "assistant": "gpt", "system": "system"}
    return [
        {"from": role_map[message["role"]], "value": message["content"]}
        for message in messages
    ]


def convert_openai_to_sharegpt(
    dataset: Dataset, conversations_column: str, output_column: str
) -> Dataset:
    def f(row: dict):
        row[output_column] = openai_to_sharegpt(row[conversations_column])
        return row

    dataset = dataset.map(f)
    return dataset


def sharegpt_to_instruction_response(
    conversation: list,
    role_tag: str = "from",
    user_tag: str = "human",
    content_tag: str = "value",
    assistant_tag: str = "gpt",
) -> tuple[str, str]:
    instruction = next(
        (item[content_tag] for item in conversation if item[role_tag] == user_tag), None
    )
    response = next(
        (item[content_tag] for item in conversation if item[role_tag] == assistant_tag),
        None,
    )
    return instruction, response


def alpaca_to_sharegpt(
    instruction: str, input: str, output: str
) -> list[dict[str, str]]:
    if input is not None and input not in ["<noinput>", ""]:
        return [
            {"from": "human", "value": instruction + "\n" + input},
            {"from": "gpt", "value": output},
        ]
    else:
        return [
            {"from": "human", "value": instruction},
            {"from": "gpt", "value": output},
        ]


def instruction_response_to_sharegpt(
    instruction: str, response: str
) -> list[dict[str, str]]:
    instruction = {"from": "human", "value": instruction}
    response = {"from": "gpt", "value": response}
    return [instruction, response]


def change_tags(
    dataset: Dataset,
    conversation_column: str,
    tags_to_change: Dict[str, str],
    role_tag: str = "from",
    content_tag: str = "value",
) -> Dataset:
    def f(x):
        messages = x[conversation_column]
        x[conversation_column] = [
            {"from": tags_to_change[message[role_tag]], "value": message[content_tag]}
            for message in messages
        ]
        return x

    dataset = dataset.map(f)
    return dataset


def convert_sharegpt_to_openai_helper(conversations: List[Dict]):
    messages = []
    for msg in conversations:
        # Map ShareGPT roles to OpenAI roles
        role_map = {"human": "user", "gpt": "assistant", "system": "system"}

        role = role_map.get(msg["from"])
        if role:
            messages.append({"role": role, "content": msg["value"].strip()})
    return messages


def filter_columns(dataset: Dataset, columns_to_keep: List[str]) -> Dataset:
    remove_cols = [col for col in dataset.column_names if col not in columns_to_keep]
    return dataset.remove_columns(remove_cols)


def convert_sharegpt_to_openai(
    dataset: Dataset, conversations_column: str, output_column: str
) -> Dataset:
    def f(row: dict):
        row[output_column] = convert_sharegpt_to_openai_helper(
            row[conversations_column]
        )
        return row

    dataset = dataset.map(f)
    return dataset


def upsample_dataset(dataset: Dataset, num_samples: int) -> Dataset:
    """Upsample a dataset by a factor of num_samples."""
    dataset = dataset.shuffle(seed=42)
    # If dataset is smaller than num_samples, repeat entries until we reach num_samples
    if len(dataset) < num_samples:
        repetitions = num_samples // len(dataset) + 1
        repeated_indices = list(range(len(dataset))) * repetitions
        dataset = dataset.select(repeated_indices[:num_samples])
    else:
        # If dataset is larger than num_samples, just select the first num_samples
        dataset = dataset.select(range(num_samples))
    return dataset


def convert_alpaca_to_sharegpt(
    dataset: Dataset,
    input_instruction_column: str,
    input_input_column: str,
    input_output_column: str,
    output_sharegpt_column: str,
    drop_non_output_columns: bool = False,
) -> Dataset:
    def f(row: dict) -> dict:
        row[output_sharegpt_column] = alpaca_to_sharegpt(
            row[input_instruction_column],
            row[input_input_column],
            row[input_output_column],
        )
        return row

    dataset = dataset.map(f)

    if drop_non_output_columns:
        dataset = dataset.select_columns([output_sharegpt_column])

    return dataset


from typing import Any, List, Optional, Union

from datasets import Dataset


def filter_dataset(
    dataset: Dataset,
    filter_column: str,
    to_include: Optional[Union[List[Any], Any]] = None,
    to_not_include: Optional[Union[List[Any], Any]] = None,
) -> Dataset:
    """
    Filter a Hugging Face dataset based on inclusion or exclusion criteria for a specific column.

    Args:
        dataset: The Hugging Face dataset to filter
        filter_column: The column name to filter on
        to_include: Values to include (can be a single value or list of values)
        to_not_include: Values to exclude (can be a single value or list of values)

    Returns:
        Filtered dataset

    Raises:
        ValueError: If both to_include and to_not_include are set or if neither is set
    """
    # Validate that exactly one filter is provided
    if (to_include is None and to_not_include is None) or (
        to_include is not None and to_not_include is not None
    ):
        raise ValueError("Exactly one of to_include or to_not_include must be set")

    # Convert single values to lists for consistent handling
    if to_include is not None:
        values = [to_include] if not isinstance(to_include, list) else to_include
        return dataset.filter(lambda x: x[filter_column] in values)
    else:
        values = (
            [to_not_include] if not isinstance(to_not_include, list) else to_not_include
        )
        return dataset.filter(lambda x: x[filter_column] not in values)


def convert_sharegpt_to_instruction_response(
    dataset: Dataset,
    input_sharegpt_column: str,
    output_instruction_column: str,
    output_response_column: str,
    drop_non_output_columns: bool = False,
    role_tag: str = "from",
    user_tag: str = "human",
    content_tag: str = "value",
    assistant_tag: str = "gpt",
) -> Dataset:
    """
    Convert a dataset from ShareGPT format to instruction-response format.
    """

    def f(row: dict) -> dict:
        row[output_instruction_column], row[output_response_column] = (
            sharegpt_to_instruction_response(
                row[input_sharegpt_column],
                role_tag=role_tag,
                user_tag=user_tag,
                content_tag=content_tag,
                assistant_tag=assistant_tag,
            )
        )
        return row

    dataset = dataset.map(f)

    if drop_non_output_columns:
        dataset = dataset.select_columns(
            [output_instruction_column, output_response_column]
        )

    return dataset


def convert_instruction_response_to_sharegpt(
    dataset: Dataset,
    input_instruction_column: str,
    input_response_column: str,
    output_sharegpt_column: str,
    drop_non_output_columns: bool = False,
) -> Dataset:
    """
    Convert a dataset from instruction-response format to ShareGPT format.
    """

    def f(row: dict) -> dict:
        row[output_sharegpt_column] = instruction_response_to_sharegpt(
            row[input_instruction_column], row[input_response_column]
        )
        return row

    dataset = dataset.map(f)

    if drop_non_output_columns:
        dataset = dataset.select_columns([output_sharegpt_column])

    return dataset


def select_columns(dataset: Dataset, columns: list[str]) -> Dataset:
    return dataset.select_columns(columns)


def convert_instruction_response_to_sharegpt_with_system_prompt(
    dataset: Dataset,
    input_instruction_column: str,
    input_response_column: str,
    output_sharegpt_column: str,
    system_prompt: str,
    drop_non_output_columns: bool = False,
) -> Dataset:
    """
    Convert a dataset from instruction-response format to ShareGPT format.
    """

    def f(row: dict) -> dict:
        ele = instruction_response_to_sharegpt(
            row[input_instruction_column], row[input_response_column]
        )
        ele.insert(0, {"from": "system", "value": system_prompt})
        row[output_sharegpt_column] = ele
        return row

    dataset = dataset.map(f)

    if drop_non_output_columns:
        dataset = dataset.select_columns([output_sharegpt_column])

    return dataset


def remove_columns(dataset: Dataset, columns: list[str]) -> Dataset:
    return dataset.remove_columns(columns)


def keep_only_columns(dataset: Dataset, columns_to_keep: str) -> Dataset:
    all_columns = dataset.column_names
    columns_to_remove = [col for col in all_columns if col not in columns_to_keep]
    dataset = dataset.remove_columns(columns_to_remove)
    return dataset


def force_rename_columns(dataset: Dataset, column_maps: dict) -> Dataset:
    """
    Force renaming columns in the dataset, removing any existing column with the new name.

    Args:
        dataset (Dataset): The input dataset.
        map_config (dict): A dictionary containing the mapping of old to new column names.
    Returns:
        Dataset: The dataset with the renamed columns.
    """
    column_names = dataset.column_names

    for old_column, new_column in column_maps.items():
        if new_column in column_names:
            dataset = dataset.remove_columns(new_column)

        name_mapping = {old_column: new_column}
        dataset = dataset.rename_columns(name_mapping)

    return dataset


def dummy(dataset: Dataset) -> Dataset:
    return dataset


# Do we need a more efficient dedup? Options below from Sedrick and Etash
def dedup_on_columns(dataset: Dataset, dedup_columns: list[str]) -> Dataset:
    """
    Remove duplicate rows from the dataset based on a specific column.

    Args:
        dataset (Dataset): The input dataset.
        input_column (str): The name of the column to check for duplicates.

    Returns:
        Dataset: The dataset with duplicate rows removed.
    """
    num_before = len(dataset)
    # Convert to pandas DataFrame
    df = dataset.to_pandas()

    # Drop duplicate rows based on the specified column
    df_cleaned = df.drop_duplicates(subset=dedup_columns, keep="first")

    # Convert back to Hugging Face Dataset
    cleaned_dataset = Dataset.from_pandas(df_cleaned)
    cleaned_dataset = cleaned_dataset.remove_columns(["__index_level_0__"])

    num_after = len(cleaned_dataset)
    percentage_removed = (num_before - num_after) / num_before * 100
    logging.info(
        f"Dedupped {num_before - num_after} out of {num_before} samples, removing ({percentage_removed:.2f}%)"
    )
    return cleaned_dataset


def dedup_on_columns_fix(dataset: Dataset, dedup_columns: list[str]) -> Dataset:
    """
    Remove duplicate rows from the dataset based on a specific column.

    Args:
        dataset (Dataset): The input dataset.
        input_column (str): The name of the column to check for duplicates.

    Returns:
        Dataset: The dataset with duplicate rows removed.
    """
    num_before = len(dataset)
    # Convert to pandas DataFrame
    df = dataset.to_pandas()

    # Drop duplicate rows based on the specified column
    df_cleaned = df.drop_duplicates(subset=dedup_columns, keep="first")

    # Convert back to Hugging Face Dataset
    cleaned_dataset = Dataset.from_pandas(df_cleaned)
    if "__index_level_0__" in cleaned_dataset.column_names:
        cleaned_dataset = cleaned_dataset.remove_columns(["__index_level_0__"])

    num_after = len(cleaned_dataset)
    percentage_removed = (num_before - num_after) / num_before * 100
    logging.info(
        f"Dedupped {num_before - num_after} out of {num_before} samples, removing ({percentage_removed:.2f}%)"
    )
    return cleaned_dataset

    # Alternative from Sedrick
    # seen: Set[Tuple[str, str]] = set()
    # unique_examples: List[Dict[str, str]] = []
    # for example in dataset:
    #     key = tuple(example[column] for column in dedup_columns)
    #     if key not in seen:
    #         seen.add(key)
    #         unique_examples.append(example)
    # return Dataset.from_list(unique_examples)


def filter_out_falsey_values(dataset: Dataset, filter_column: str) -> Dataset:
    """Filter out instances with falsey values in specified column.

    Args:
        dataset_name (str): Name of the dataset to load
        filter_column (str): Column to use for filtering

    Returns:
        Dataset: Filtered dataset
    """
    num_before = len(dataset)
    # filters out python Falsey values (e.g. 0, 0.0, False, None, "", etc.)
    dataset = dataset.filter(lambda x: x[filter_column])
    num_after = len(dataset)
    percentage_removed = (num_before - num_after) / num_before * 100
    logging.info(
        f"Filtered {num_before - num_after} out of {num_before} samples, removing ({percentage_removed:.2f}%)"
    )
    return dataset


def filter_out_truey_values(dataset: Dataset, filter_column: str) -> Dataset:
    """Filter out instances with truey values in specified column.

    Args:
        dataset_name (str): Name of the dataset to load
        filter_column (str): Column to use for filtering

    Returns:
        Dataset: Filtered dataset
    """
    num_before = len(dataset)
    # filters out python Truey values (e.g. 1, 1.0, True, "hello", etc.)
    dataset = dataset.filter(lambda x: not x[filter_column])
    num_after = len(dataset)
    percentage_removed = (num_before - num_after) / num_before * 100
    logging.info(
        f"Filtered {num_before - num_after} out of {num_before} samples, removing ({percentage_removed:.2f}%)"
    )
    return dataset


def load_json_string_to_dataset(json_string: str) -> Dataset:
    """
    Convert a JSON string into a Hugging Face Dataset object.

    Args:
        json_string (str): A JSON string containing data in a dictionary format where
            each key represents a column name and its value is a list of column values.

    Returns:
        Dataset: A Hugging Face Dataset object created from the JSON data.

    Example:
        >>> json_str = '{"text": ["hello", "world"], "label": [1, 0]}'
        >>> dataset = load_json_string_to_dataset(json_str)
        >>> print(dataset)
        Dataset({
            features: ['text', 'label'],
            num_rows: 2
        })
    """
    json_dict = json.loads(json_string)
    return Dataset.from_dict(json_dict)


def convert_reasoning_trace_to_final(
    dataset: Dataset, reasoning_column: str, solution_column: str, output_column: str
):
    def f(x):
        x[output_column] = (
            f"<think>\n{x[reasoning_column]}\n</think>\n\n{x[solution_column]}"
        )
        return x

    dataset = dataset.map(f)
    return dataset


def convert_final_to_reasoning_trace(
    dataset: Dataset,
    input_column: str,
    output_reasoning_column: str,
    output_solution_column: str,
):
    def f(x):
        thinking_pattern = r"<\|begin_of_thought\|>\n*([\s\S]*?)\n*<\|end_of_thought\|>"
        solution_pattern = (
            r"<\|begin_of_solution\|>\n*([\s\S]*?)\n*<\|end_of_solution\|>"
        )

        thinking_match = re.search(thinking_pattern, x[input_column], re.DOTALL)
        solution_match = re.search(solution_pattern, x[input_column], re.DOTALL)

        x[output_reasoning_column] = thinking_match.group(1)
        x[output_solution_column] = solution_match.group(1)

        return x

    dataset = dataset.map(f)
    return dataset


def strip_column(
    dataset: Dataset, input_column: str, strip_str: str, output_column: str = None
):
    def f(x):
        x[output_column] = x[input_column].strip(strip_str)
        return x

    dataset = dataset.map(f)
    return dataset


def create_constant_dataset(**kwargs) -> Dataset:
    """
    Create a dataset from a dictionary of arguments.
    """
    for key, value in kwargs.items():
        kwargs[key] = [value]
    return Dataset.from_dict(kwargs)


def add_constant_columns(dataset: Dataset, **kwargs) -> Dataset:
    """
    Add arguments columns to the dataset to use later (e.g. string prompt formatting for completions)
    """
    for key, value in kwargs.items():
        dataset = dataset.add_column(key, [value] * len(dataset))
    return dataset


def repeat_dataset(dataset: Dataset, n: int) -> Dataset:
    """
    Repeat each row in the dataset n times.

    Args:
        dataset (Dataset): The input dataset to repeat
        n (int): Number of times to repeat each row

    Returns:
        Dataset: A new dataset with each row repeated n times

    Example:
        >>> dataset = Dataset.from_dict({"text": ["hello"], "label": [1]})
        >>> repeated = repeat_dataset(dataset, 3)
        >>> print(repeated)
        Dataset({
            features: ['text', 'label'],
            num_rows: 3
        })
        >>> print(repeated["text"])
        ['hello', 'hello', 'hello']
    """
    # When batched=True and batch_size=1 you can return a dictionary of lists which will be expanded to the correct number of rows
    return dataset.map(
        lambda x: {k: v * n for k, v in x.items()}, batched=True, batch_size=1
    )


# DO NOT USE DO NOT USE DO NOT USE DO NOT USE
# def uniform_sample(dataset: Dataset, num_samples: int, seed: int = 42) -> Dataset:
#     """Uniformly sample a dataset to a given number of samples."""
#     dataset.shuffle(seed=seed)
#     return dataset.select(range(num_samples))


# DO NOT USE DO NOT USE DO NOT USE DO NOT USE
def uniform_sample_limited(
    dataset: Dataset, num_samples: int, seed: int = 42
) -> Dataset:
    """Uniformly sample a dataset up to a given number of samples.
    Returns min(num_samples, len(dataset)) samples."""
    dataset.shuffle(seed=seed)
    dataset = dataset.select(range(min(num_samples, len(dataset))))
    return dataset


def choose_range(dataset: Dataset, start_idx: int, end_idx: int):
    return dataset.select(range(start_idx, end_idx))


def uniform_sample_fixed(dataset: Dataset, num_samples: int, seed: int = 42) -> Dataset:
    """Uniformly sample a dataset up to a given number of samples.
    Returns min(num_samples, len(dataset)) samples."""

    # This fixes the previous implementations, which are wrong due to shuffle not being an inplace operator
    dataset = dataset.shuffle(seed=seed)
    return dataset.select(range(min(num_samples, len(dataset))))


def select_rows_regex(dataset: Dataset, column: str, regex: str) -> Dataset:
    """
    Select rows from the dataset where the values in the specified columns
    match the given values.
    """
    return dataset.filter(lambda x: re.search(regex, x[column]))


def select_rows_without(dataset: Dataset, conditions: dict[str, str]) -> Dataset:
    """
    Select rows from the dataset where the values in the specified columns
    match the given values.
    """
    return dataset.filter(
        lambda x: not any(x[col] == val for col, val in conditions.items())
    )


def select_rows(dataset: Dataset, conditions: dict[str, str]) -> Dataset:
    """
    Select rows from the dataset where the values in the specified columns
    match the given values.
    """
    return dataset.filter(
        lambda x: all(x[col] == val for col, val in conditions.items())
    )


def select_rows_multi(dataset: Dataset, conditions: dict[str, List[str]]) -> Dataset:
    """
    Select rows from the dataset where the values in the specified columns
    match the given values.
    """

    def filter_func(x):
        for_each_key = []
        for key in conditions:
            for_each_val = []
            for val in conditions[key]:
                for_each_val.append(val == x[key])
            for_each_key.append(any(for_each_val))
        return all(for_each_key)

    return dataset.filter(filter_func)


def calc_sentence_transformers_embedding(
    dataset: Dataset,
    text_column: str,
    model_name: str = "sentence-transformers/all-mpnet-base-v2",
) -> Dataset:
    # Define the model
    model = SentenceTransformer(model_name)

    # Start the multi-process pool on all available CUDA devices
    pool = model.start_multi_process_pool()
    sentences = dataset[text_column]
    # Compute the embeddings using the multi-process pool
    emb = model.encode_multi_process(sentences, pool, show_progress_bar=True)
    print("Embeddings computed. Shape:", emb.shape)
    list_emb = list(emb)
    # Optional: Stop the processes in the pool
    model.stop_multi_process_pool(pool)
    # Add embeddings to dataset
    dataset = dataset.add_column("embeddings", list_emb)
    dataset = dataset.cast_column("embeddings", Sequence(Value("float64")))

    return dataset


def get_embeddings_batched(
    dataset: Dataset,
    text_column: str,
    batch_size: int = 32,
    model_name: str = "sentence-transformers/all-mpnet-base-v2",
) -> Dataset:
    """
    Generate embeddings for text data in batches.

    Args:
        dataset: Hugging Face dataset containing the text
        text_column: Name of the column containing text to embed
        batch_size: Number of samples to process at once
        model_name: Name of the pre-trained model to use

    Returns:
        Dataset with new 'embedding' column containing the embeddings
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.eval()

    # Create a dataloader for batch processing
    def collate_fn(batch):
        return [item[text_column] for item in batch]

    dataloader = DataLoader(
        dataset, batch_size=batch_size, collate_fn=collate_fn, shuffle=False
    )

    all_embeddings = []

    with torch.no_grad():
        for batch_texts in tqdm(dataloader):
            # Tokenize the batch
            inputs = tokenizer(
                batch_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
            ).to(device)

            # Get model outputs
            outputs = model(**inputs)

            # Calculate embeddings (mean pooling)
            attention_mask = inputs["attention_mask"]
            mask = (
                attention_mask.unsqueeze(-1)
                .expand(outputs.last_hidden_state.size())
                .float()
            )
            masked_embeddings = outputs.last_hidden_state * mask
            sum_embeddings = torch.sum(masked_embeddings, dim=1)
            sum_mask = torch.clamp(mask.sum(dim=1), min=1e-9)
            batch_embeddings = (sum_embeddings / sum_mask).cpu().numpy()

            all_embeddings.extend(batch_embeddings)

    # Add embeddings to dataset
    dataset = dataset.add_column("embeddings", all_embeddings)
    dataset = dataset.cast_column("embeddings", Sequence(Value("float64")))

    return dataset


def list_to_string(
    dataset: Dataset,
    column_name: str,
) -> Dataset:
    """
    Convert [value] to "value"
    """

    def f(row: dict) -> dict:
        row[column_name] = row[column_name][0]
        return row

    dataset = dataset.map(f)
    return dataset


def concatenate_columns(
    dataset: Dataset,
    first_column: str,
    second_column: str,
    output_column: str,
    start_token: str = "",
    separator_token: str = "\n",
    end_token: str = "",
) -> Dataset:
    """
    Concatenates `first_column` with `second_column`.
    Stores result in `output_column`.
    Use `start_token` to append a prefix to the first column.
    Use `separator_token` to fill out the middle of the concatenation.
    Use `end_token` to append a suffix to the second column.
    """

    def f(row: dict) -> dict:
        row[output_column] = (
            start_token
            + row[first_column]
            + separator_token
            + row[second_column]
            + end_token
        )
        return row

    dataset = dataset.map(f)
    return dataset


def add_value_to_every_row(dataset: Dataset, column_name: str, value: Any) -> Dataset:
    def add_new_column(example):
        example[column_name] = value
        return example

    updated_dataset = dataset.map(add_new_column)
    return updated_dataset


def extract_list_index(
    dataset: Dataset, list_column: str, index: int, keep_original_columns: bool = True
) -> Dataset:
    """
    Extract the index-th element from a list column.
    """
    if keep_original_columns:
        return dataset.map(
            lambda x: {k: v for k, v in x.items() if k != list_column}
            | {list_column: x[list_column][index]}
        )
    else:
        return dataset.map(lambda x: x[list_column][index])


def add_value_to_every_row(dataset: Dataset, column_name: str, value: Any) -> Dataset:
    def add_new_column(example):
        example[column_name] = value
        return example

    updated_dataset = dataset.map(add_new_column)
    return updated_dataset


def add_row_ids(dataset: Dataset, column_name: str = "id") -> Dataset:
    """
    Add an incrementing ID to each row in the dataset.

    Args:
        dataset: The input dataset
        column_name: Name of the column to store the IDs (default: "id")

    Returns:
        Dataset with added ID column
    """

    def add_id(example, idx):
        example[column_name] = idx
        return example

    updated_dataset = dataset.map(add_id, with_indices=True)
    return updated_dataset


def create_dataset_from_list(items: List[str], column_name: str) -> Dataset:
    """
    Create a dataset from a list of URLs.

    Args:
        urls (List[str]): List of PDF URLs

    Returns:
        Dataset: HuggingFace dataset with columns:
            - url: source URL
    """
    return Dataset.from_dict({column_name: items})
