from datasets import Dataset


def filter_top_n(dataset: Dataset, n: int, score_column: str) -> Dataset:
    """
    Filter a dataset to keep only the top n items based on a score column.

    Args:
        dataset: The input Hugging Face dataset
        n (int): Number of top items to keep
        score_column (str): Name of the column containing scores

    Returns:
        Dataset: Filtered dataset containing only the top n scored items
    """
    # Convert to list of dictionaries for sorting
    items = dataset.to_list()

    # Sort items by score in descending order
    sorted_items = sorted(items, key=lambda x: x[score_column], reverse=True)

    # Keep only the top n items (or all items if n is larger than dataset size)
    n = min(n, len(sorted_items))
    filtered_items = sorted_items[:n]

    # Convert back to Dataset format
    filtered_dataset = Dataset.from_list(filtered_items)

    return filtered_dataset
