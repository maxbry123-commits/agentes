from datasets import Dataset


def filter_rank(dataset: Dataset, top_percentage: float, rating_column: str):
    """
    Filter a dataset to keep only the top percentage of items based on a rating column.

    Args:
        dataset (Dataset): The input Hugging Face dataset
        top_percentage (float): Percentage of top items to keep (between 0 and 1)
        rating_column (str): Name of the column containing ratings

    Returns:
        Dataset: Filtered dataset containing only the top-rated items
    """
    # Convert to list of dictionaries for sorting
    items = dataset.to_list()

    # Sort items by rating in descending order
    sorted_items = sorted(items, key=lambda x: x[rating_column], reverse=True)

    # Calculate how many items to keep
    num_items_to_keep = int(len(sorted_items) * top_percentage)

    # Keep only the top items
    filtered_items = sorted_items[:num_items_to_keep]

    # Convert back to Dataset format
    filtered_dataset = Dataset.from_list(filtered_items)

    return filtered_dataset
