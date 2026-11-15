from datasets import Dataset
import random


def stratified_sample(dataset: Dataset, column_name: str, num_samples: int):
    """
    Stratified sample from a HuggingFace dataset based on a column,
    taking an equal number of samples from each stratum.

    Args:
        dataset: The HuggingFace dataset to sample from
        column_name: The column to stratify by
        num_samples: The total number of samples to return

    Returns:
        A stratified sample of the dataset with equal representation
    """
    # Get unique values in the column
    unique_values = set(dataset[column_name])
    num_strata = len(unique_values)

    # Calculate samples per stratum (equal distribution)
    samples_per_stratum = num_samples // num_strata
    remaining = num_samples % num_strata

    # Sample from each stratum
    all_indices = []

    for i, value in enumerate(unique_values):
        stratum = dataset.filter(lambda example: example[column_name] == value)

        # Add one extra sample to early strata if we have remainder
        current_samples = samples_per_stratum + (1 if i < remaining else 0)

        # Handle case where there aren't enough samples
        if len(stratum) < current_samples:
            # Take all available samples
            all_indices.extend(list(range(len(stratum))))

            # Log a warning
            print(
                f"Warning: Not enough samples for value '{value}' in column '{column_name}'. "
                f"Requested {current_samples}, but only {len(stratum)} available."
            )
        else:
            sampled_indices = random.sample(list(range(len(stratum))), k=current_samples)
            all_indices.extend(sampled_indices)

    # Return sampled dataset using selected indices
    return dataset.select(all_indices)
