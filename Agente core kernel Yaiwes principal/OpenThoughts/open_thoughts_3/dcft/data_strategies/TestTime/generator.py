import os
import pickle
import tempfile
from collections import defaultdict
from typing import Dict, List, Optional

from datasets import Dataset
from tqdm import tqdm


def duplicate_rows(dataset: Dataset, n_copies: int) -> Dataset:
    """
    Create n copies of each row in a Hugging Face dataset.

    Args:
        dataset: The input Hugging Face dataset
        n_copies: Number of copies to create for each row

    Returns:
        A new dataset with duplicated rows
    """
    # Convert to list of dictionaries for easier manipulation
    data_dicts = dataset.to_dict()

    # Initialize new dictionaries for the expanded dataset
    expanded_dict = {k: [] for k in data_dicts.keys()}

    # Get the length of any column (they should all be the same length)
    dataset_length = len(next(iter(data_dicts.values())))

    # For each row in the original dataset
    for idx in range(dataset_length):
        # For each requested copy
        for _ in range(n_copies):
            # Add the values from each column
            for col_name, col_values in data_dicts.items():
                expanded_dict[col_name].append(col_values[idx])

    # Create new dataset from the expanded dictionary
    return Dataset.from_dict(expanded_dict)


from collections import defaultdict
from typing import Dict, List, Optional

from datasets import Dataset
from tqdm import tqdm

# def merge_duplicate_rows_memory_efficient(dataset: Dataset, diff_columns: List[str], id_column: Optional[str] = None) -> Dataset:
#     """
#     Merge rows that are identical except for specified columns, combining the differing values into lists.

#     Args:
#         dataset: Input HuggingFace dataset
#         diff_columns: Names of columns that contain different values across duplicate rows
#         id_column: Column name to use as unique identifier. If None, uses first column that's not in diff_columns

#     Returns:
#         Dataset with merged rows where diff_columns values are combined into lists
#     """
#     # Convert dataset to pandas DataFrame for processing
#     df = dataset.to_pandas()

#     # If id_column not specified, use first column that's not in diff_columns
#     if id_column is None:
#         id_column = next(col for col in df.columns if col not in diff_columns)

#     # Define aggregation functions for each column
#     agg_dict = {}
#     for col in df.columns:
#         if col in diff_columns:
#             # For diff columns, collect all values into a list
#             agg_dict[col] = lambda x: x.tolist()
#         else:
#             # For non-diff columns, take the first value
#             agg_dict[col] = 'first'

#     # Group by id_column and apply aggregation
#     grouped_df = df.groupby(id_column, as_index=False).agg(agg_dict)

#     # Convert back to HuggingFace Dataset
#     result_dict = grouped_df.to_dict('list')
#     return Dataset.from_dict(result_dict)


def merge_duplicate_rows(
    dataset: Dataset, diff_columns: List[str], id_column: Optional[str] = None
) -> Dataset:
    """
    Merge rows that are identical except for specified columns, combining the differing values into lists.

    Args:
        dataset: Input HuggingFace dataset
        diff_columns: Names of columns that contain different values across duplicate rows
        id_column: Column name to use as unique identifier. If None, uses first column that's not in diff_columns

    Returns:
        Dataset with merged rows where diff_columns values are combined into lists
    """
    # If id_column not specified, use first column that's not in diff_columns
    if id_column is None:
        id_column = next(col for col in dataset.column_names if col not in diff_columns)

    # Convert dataset to list of dictionaries for faster processing
    data = dataset.to_dict()

    # Group rows by id_column
    grouped_data: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

    # Process all rows in one pass
    for idx in tqdm(range(len(dataset))):
        current_id = data[id_column][idx]

        for col in dataset.column_names:
            if col in diff_columns:
                # For diff columns, append each value
                grouped_data[current_id][col].append(data[col][idx])
            else:
                # For non-diff columns, only keep the first value
                if not grouped_data[current_id][col]:
                    grouped_data[current_id][col].append(data[col][idx])

    # Build result dictionary
    result_dict = {col: [] for col in dataset.column_names}

    # Convert grouped data to final format
    for grouped_rows in grouped_data.values():
        for col in dataset.column_names:
            if col in diff_columns:
                result_dict[col].append(grouped_rows[col])
            else:
                result_dict[col].append(grouped_rows[col][0])

    return Dataset.from_dict(result_dict)
