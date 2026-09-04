import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Set, Tuple

from datasets import Dataset, DatasetDict, load_dataset
from tqdm import tqdm

SOURCE_DATASET_INFO = {
    "Airoboros 2.2": {
        "path": "jondurbin/airoboros-2.2",
        "instruction_key": "instruction",
        "response_key": "response",
    },
    "OriginalOpenHermes": {
        "path": "teknium/OpenHermes-2.5",
        "convo_key": "conversations",
        "message_key": "value",
        "from_key": "from",
        "human_value": "human",
        "gpt_value": "gpt",
    },
    "mlfoundations-dev/oh-dcft-v1-no-curation-sharegpt-format": {
        "path": "mlfoundations-dev/oh-dcft-v1-no-curation-sharegpt-format",
        "convo_key": "sample",
        "message_key": "value",
        "from_key": "from",
        "human_value": "human",
        "gpt_value": "gpt",
    },
    "mlfoundations-dev/oh-dcft-v3-sharegpt-format": {
        "path": "mlfoundations-dev/oh-dcft-v3-sharegpt-format",
        "message_key": "value",
        "from_key": "from",
        "human_value": "human",
        "gpt_value": "gpt",
    },
    "CamelAI Biology": {
        "path": "camel-ai/biology",
        "instruction_key": "message_1",
        "response_key": "message_2",
    },
    "CamelAI Chemistry": {
        "path": "camel-ai/chemistry",
        "instruction_key": "message_1",
        "response_key": "message_2",
    },
    "CamelAI Math": {
        "path": "camel-ai/math",
        "instruction_key": "message_1",
        "response_key": "message_2",
    },
    "CamelAI Physics": {
        "path": "camel-ai/physics",
        "instruction_key": "message_1",
        "response_key": "message_2",
    },
    "Chatbot Arena": {
        "path": "lmsys/chatbot_arena_conversations",
        "convo_key": "conversation_b",
        "message_key": "content",
        "from_key": "role",
        "human_value": "user",
        "gpt_value": "assistant",
    },
    "lmsys-1m": {
        "path": "lmsys/lmsys-chat-1m",
        "convo_key": "conversation",
        "message_key": "content",
        "from_key": "role",
        "human_value": "user",
        "gpt_value": "assistant",
    },
    "Collective Cognition": {
        "path": "CollectiveCognition/chats-data-2023-09-22",
        "convo_key": "conversations",
        "message_key": "value",
        "from_key": "from",
        "human_value": "human",
        "gpt_value": "gpt",
    },
    "Evol Instruct 70K": {
        "path": "WizardLM/WizardLM_evol_instruct_70k",
        "instruction_key": "instruction",
        "response_key": "output",
    },
    "Evol Instruct 140K": {
        "path": "WizardLM/WizardLM_evol_instruct_V2_196k",
        "convo_key": "conversations",
        "message_key": "value",
        "from_key": "from",
        "human_value": "human",
        "gpt_value": "gpt",
    },
    "Glaive Code Assistant": {
        "path": "glaiveai/glaive-code-assistant",
        "instruction_key": "question",
        "response_key": "answer",
    },
    # "GPT4-LLM": {"path": "teknium/GPT4-LLM-Cleaned"
    #              },
    # "GPTeacher": {"path": "teknium/GPTeacher-General-Instruct"},
    "MetaMath 40k": {
        "path": "meta-math/MetaMathQA",
        "instruction_key": "query",
        "response_key": "response",
    },
    "SlimOrca 550K": {
        "path": "Open-Orca/SlimOrca",
        "convo_key": "conversations",
        "message_key": "value",
        "from_key": "from",
        "human_value": "human",
        "gpt_value": "gpt",
    },
    "Platypus": {
        "path": "garage-bAInd/Open-Platypus",
        "instruction_key": "instruction",
        "response_key": "output",
    },
    "ShareGPT": {
        "path": "anon8231489123/ShareGPT_V3_unfiltered_cleaned_split.json",
        "convo_key": "conversations",
        "message_key": "value",
        "from_key": "from",
        "human_value": "human",
        "gpt_value": "gpt",
    },
    # "CogStack": {
    #     "path": "./cogstack/prepared_generated_data*.csv",
    #     "convo_key": "conversations",
    #     "message_key": "value",
    #     "from_key": "from",
    #     "human_value": "human",
    # },
    # "CoT Alpaca": {
    #     "path": "causal-lm/cot_alpaca_gpt4",
    #     "convo_key": "conversations",
    #     "message_key": "value",
    #     "from_key": "from",
    #     "human_value": "human",
    # },
    # "Unnatural Instructions": {
    #     "path": "mrm8488/unnatural-instructions-full",
    #     "convo_key": "instances",
    # },
    "caseus_custom": {
        "path": "Locutusque/caseus_custom",
        "convo_key": "conversations",
        "message_key": "value",
        "from_key": "from",
        "human_value": "human",
        "gpt_value": "gpt",
    },
    "dataforge_economics": {
        "path": "teknium/dataforge-economics",
        "convo_key": "conversations",
        "message_key": "value",
        "from_key": "from",
        "human_value": "human",
        "gpt_value": "gpt",
    },
}


def extract_instruction_response_pair(dataset_name: str) -> Dataset:
    dataset_info = SOURCE_DATASET_INFO[dataset_name]
    dataset = load_dataset(dataset_info["path"])
    if isinstance(dataset, DatasetDict):
        dataset = dataset["train"]

    def apply(ex: Dict):
        if "instruction_key" in dataset_info:
            instruction = ex[dataset_info["instruction_key"]]
            response = ex[dataset_info["response_key"]]
        else:
            convo = ex[dataset_info["convo_key"]]
            for message in convo:
                if message[dataset_info["from_key"]] == dataset_info["human_value"]:
                    instruction = message[dataset_info["message_key"]]
                if message[dataset_info["from_key"]] == dataset_info["gpt_value"]:
                    response = message[dataset_info["message_key"]]
        ex["trainable_text"] = f"{instruction} ||| {response}"
        return ex

    dataset = dataset.map(apply)
    return dataset


def find_unincluded_examples(
    whole_dataset: Dataset,
    original_subset: Dataset,
    dataset_to_be_filtered: Dataset,
    max_n: int = 4,
    threshold: int = 30,
):
    """
    Filter out examples from whole_dataset that contain n-grams unique to original_subset.

    Args:
        whole_dataset: Dataset containing all examples
        original_subset: Dataset containing subset examples
        max_n: Maximum n-gram size to consider
        threshold: Minimum frequency threshold for n-grams

    Returns:
        List of examples from whole_dataset that don't contain any unique n-grams
    """
    whole_dataset_examples = set(whole_dataset["trainable_text"])
    original_subset_examples = set(original_subset["trainable_text"])

    filtered_out_examples = []
    for example in original_subset_examples:
        if example not in whole_dataset_examples:
            filtered_out_examples.append(example)

    # Get unique n-grams from subset
    unique_grams = find_unique_ngrams(
        whole_dataset_examples, original_subset_examples, max_n, threshold
    )

    # Convert unique_grams into a more efficient lookup structure
    ngram_lookup = {n: set() for n in range(1, max_n + 1)}
    for n, ngrams in unique_grams.items():
        for ngram, _ in ngrams:
            if n == 1:
                ngram_lookup[n].add(ngram)
            else:
                ngram_lookup[n].add(tuple(ngram.split()))

    filtered_indices = []
    num_filtered = 0
    for i, text in tqdm(enumerate(dataset_to_be_filtered["trainable_text"])):
        if not contains_unique_ngrams(text, ngram_lookup, max_n):
            filtered_indices.append(i)
        else:
            num_filtered += 1
    print(f"Num Filtered: {num_filtered}")

    # Return filtered dataset
    return dataset_to_be_filtered.select(filtered_indices)


def contains_unique_ngrams(text: str, ngram_lookup: Dict[int, Set], max_n: int) -> bool:
    """Check if text contains any of the unique n-grams."""
    words = preprocess_text(text)

    # Check each n-gram size
    for n in range(1, max_n + 1):
        if n == 1:
            # For unigrams, simple word lookup
            if any(word in ngram_lookup[n] for word in words):
                return True
        else:
            # For n-grams, generate and check
            text_ngrams = set(get_ngrams(words, n))
            if any(ngram in ngram_lookup[n] for ngram in text_ngrams):
                return True
    return False


def get_ngrams(words: list, n: int) -> list:
    """Generate n-grams from pre-tokenized words."""
    return list(zip(*[words[i:] for i in range(n)]))


def preprocess_text(text: str) -> list:
    """Preprocess text into words once."""
    return re.findall(r"\b[a-zA-Z]+\b", text.lower())


def find_unique_ngrams(
    original_texts: List[str],
    subset_texts: List[str],
    max_n: int = 4,
    threshold: int = 1,
) -> Dict[int, List[Tuple[str, int]]]:
    """
    Find n-grams that appear in subset_texts but not in original_texts,
    returning only those that appear more than threshold times.

    Args:
        original_texts: List of strings from original dataset
        subset_texts: List of strings from subset
        max_n: Maximum n-gram size to consider
        threshold: Minimum number of times an n-gram must appear to be included

    Returns:
        Dictionary mapping n-gram size to list of tuples (ngram, count)
    """
    # Get all n-grams from original dataset
    original_ngrams = {n: set() for n in range(1, max_n + 1)}
    for text in original_texts:
        words = preprocess_text(text)
        for n in range(1, max_n + 1):
            original_ngrams[n].update(get_ngrams(words, n))

    # Count n-grams in subset
    subset_ngram_counts = {n: Counter() for n in range(1, max_n + 1)}
    for text in subset_texts:
        words = preprocess_text(text)
        for n in range(1, max_n + 1):
            subset_ngram_counts[n].update(get_ngrams(words, n))

    # Find unique n-grams that appear more than threshold times
    unique_ngrams = {n: [] for n in range(1, max_n + 1)}

    for n in range(1, max_n + 1):
        for ngram, count in subset_ngram_counts[n].items():
            # Check if n-gram is unique to subset and appears more than threshold times
            if ngram not in original_ngrams[n] and count > threshold:
                ngram_str = ngram if n == 1 else " ".join(ngram)
                unique_ngrams[n].append((ngram_str, count))

        # Sort by frequency
        unique_ngrams[n].sort(key=lambda x: x[1], reverse=True)

    return unique_ngrams
