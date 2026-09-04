from datasets import Dataset, load_dataset
from data_strategies.DeepSeekR1.utils import process_string_pair
from transformers import AutoTokenizer
from typing import List, Optional, Dict
import multiprocessing as mp
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from functools import partial


def remove_duplicates(dataset: Dataset, column_name: str) -> Dataset:
    """
    Remove duplicate rows from a Hugging Face dataset based on a specific column.
    
    Args:
        dataset: A Hugging Face Dataset object
        column_name: The name of the column to check for duplicates
        
    Returns:
        A new Dataset with duplicates removed (keeping the first occurrence)
    """
    # Convert to pandas DataFrame for easier duplicate handling
    df = dataset.to_pandas()
    
    # Drop duplicates, keeping the first occurrence
    df_no_duplicates = df.drop_duplicates(subset=[column_name], keep='first')
    
    # Convert back to a Hugging Face Dataset
    clean_dataset = Dataset.from_pandas(df_no_duplicates)
    
    return clean_dataset

def get_ngrams_autotokenizer(tokens, n):
    """
    Extract n-grams from text using AutoTokenizer for more accurate tokenization.

    Args:
        text (str): The input text to extract n-grams from
        n (int): The size of n-grams to extract
        no_punctuation (bool): Whether to remove punctuation

    Returns:
        list: List of n-gram tuples
    """
    ngrams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    return ngrams


def process_single_text(text_ngrams, all_benchmark_ngrams):
    if text_ngrams & all_benchmark_ngrams:
        return True
    return False


def decontaminate_ngram_overlap(
    values: List[str],
    benchmark_questions: List[str],
    ngram_size: int = 8,
    tokenizer_name: str = "bert-base-uncased",
) -> List[bool]:
    """
    Remove rows from dataset that have similar strings in eval_datasets based on fuzzy matching.
    """
    n_processes = mp.cpu_count()
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    all_text_tokens = tokenizer(values)["input_ids"]
    all_benchmark_tokens = tokenizer(benchmark_questions)["input_ids"]
    # Process n-grams for benchmarks
    all_text_ngrams = []
    all_benchmark_ngrams = set()
    for benchmark_tokens in tqdm(
        all_benchmark_tokens, desc="Processing benchmark n-grams"
    ):
        all_benchmark_ngrams.update(
            set(get_ngrams_autotokenizer(benchmark_tokens, ngram_size))
        )

    # Process n-grams for texts
    for text_tokens in tqdm(all_text_tokens, desc="Processing text n-grams"):
        text_ngrams = set(get_ngrams_autotokenizer(text_tokens, ngram_size))
        all_text_ngrams.append(text_ngrams)

    # Process each text with a normal for loop
    contaminated_mask = []
    for text_ngram in tqdm(all_text_ngrams, desc="Checking contamination"):
        is_contaminated = process_single_text(text_ngram, all_benchmark_ngrams)
        contaminated_mask.append(is_contaminated)
    return contaminated_mask


def decontaminate_fuzzy_w_ngram(
    dataset: Dataset,
    column: str,
    eval_datasets: List[str],
    eval_columns: List[str],
    eval_splits: List[str],
    similarity_threshold: float,
    ngram_size: int = 13,
    eval_subsets: Optional[Dict[str, str]] = {},
) -> Dataset:
    """
    Remove rows from dataset that have similar strings in eval_datasets based on fuzzy matching.
    """
    n_processes = mp.cpu_count()

    # Get values from input dataset
    values1 = [str(x) for x in dataset[column] if x is not None]

    # Load eval datasets
    pair_values = {}
    for idx in range(len(eval_datasets)):
        dataset_name_and_config = eval_datasets[idx]
        dataset_name_and_config_split = dataset_name_and_config.split("::")
        dataset_name = dataset_name_and_config_split[0]
        dataset_config = (
            dataset_name_and_config_split[1]
            if len(dataset_name_and_config_split) > 1
            else None
        )

        split = eval_splits[idx]
        eval_column = eval_columns[idx]
        if dataset_name in eval_subsets:
            ds = load_dataset(
                dataset_name,
                eval_subsets[dataset_name],
                split=split,
                trust_remote_code=True,
            )
        else:
            ds = load_dataset(dataset_name, split=split, trust_remote_code=True)
        values = [str(x) for x in ds[eval_column] if x is not None]
        pair_values[(dataset_name, split, eval_column)] = values

    # Track indices to remove
    indices_to_remove = set()

    # Compare with each eval dataset
    for (dataset_name, split, eval_column), values2 in tqdm(
        pair_values.items(), desc="Processing datasets"
    ):
        process_pair = partial(
            process_string_pair,
            values2=values2,
            similarity_threshold=similarity_threshold,
        )

        with Pool(n_processes) as pool:
            matches = list(
                tqdm(
                    pool.imap(process_pair, values1, chunksize=100),
                    total=len(values1),
                    desc=f"Processing {dataset_name}",
                )
            )

        # Find indices where matches were found
        for i, match_list in enumerate(matches):
            if any(score >= similarity_threshold for _, _, score in match_list):
                indices_to_remove.add(i)
    keep_mask_fuzzy = [i for i in range(len(dataset)) if i not in indices_to_remove]
    all_contaminated_masks = []
    for (dataset_name, split, eval_column), benchmark_values in tqdm(
        pair_values.items(), desc="Processing datasets"
    ):
        contaminated_mask = decontaminate_ngram_overlap(
            values1,
            benchmark_values,
            ngram_size,
            tokenizer_name="Qwen/Qwen2-7B-Instruct",
        )
        all_contaminated_masks.append(contaminated_mask)

    # Combine all contamination masks with logical AND
    combined_contamination_mask = []
    if all_contaminated_masks:
        # Initialize with the first mask
        combined_contamination_mask = all_contaminated_masks[0].copy()
        # Apply logical AND with each subsequent mask
        for mask in all_contaminated_masks[1:]:
            for i in range(len(combined_contamination_mask)):
                combined_contamination_mask[i] = (
                    combined_contamination_mask[i] or mask[i]
                )
    keep_indices = [
        i
        for i in range(len(dataset))
        if not combined_contamination_mask[i] and i in keep_mask_fuzzy
    ]
    clean_dataset = dataset.select(keep_indices)

    print(f"Removed {len(dataset) - len(clean_dataset)} contaminated rows")
    print(f"Original size: {len(dataset)}, New size: {len(clean_dataset)}")

    return clean_dataset
