import numpy as np
from datasets import Dataset


def calc_embedding_score(
    dataset: Dataset,
    embedding_column: str,
    positive_dataset: Dataset,
    negative_dataset: Dataset,
    positive_embedding_column: str,
    negative_embedding_column: str,
) -> Dataset:
    # Convert embeddings to numpy arrays for efficient computation
    embeddings = np.array(dataset[embedding_column])
    positive_embeddings = np.array(positive_dataset[positive_embedding_column])
    negative_embeddings = np.array(negative_dataset[negative_embedding_column])

    # Calculate max similarity with positive embeddings for each input embedding
    positive_similarities = np.dot(
        embeddings, positive_embeddings.T
    )  # Shape: (n_samples, n_positives)
    max_positive_scores = np.max(positive_similarities, axis=1)  # Shape: (n_samples,)

    # Calculate max similarity with negative embeddings for each input embedding
    negative_similarities = np.dot(
        embeddings, negative_embeddings.T
    )  # Shape: (n_samples, n_negatives)
    max_negative_scores = np.max(negative_similarities, axis=1)  # Shape: (n_samples,)

    # Add new columns to the dataset
    dataset = dataset.add_column("max_positive_score", max_positive_scores)
    dataset = dataset.add_column("max_negative_score", max_negative_scores)
    dataset = dataset.add_column(
        "difference_score", max_positive_scores - max_negative_scores
    )
    return dataset


def calc_embedding_score_mean(
    dataset: Dataset,
    embedding_column: str,
    positive_dataset: Dataset,
    negative_dataset: Dataset,
    positive_embedding_column: str,
    negative_embedding_column: str,
) -> Dataset:
    # Convert embeddings to numpy arrays for efficient computation
    embeddings = np.array(dataset[embedding_column])
    positive_embeddings = np.array(positive_dataset[positive_embedding_column])
    negative_embeddings = np.array(negative_dataset[negative_embedding_column])

    # Calculate mean similarity with positive embeddings for each input embedding
    positive_similarities = np.dot(
        embeddings, positive_embeddings.T
    )  # Shape: (n_samples, n_positives)
    mean_positive_scores = np.mean(positive_similarities, axis=1)  # Shape: (n_samples,)

    # Calculate mean similarity with negative embeddings for each input embedding
    negative_similarities = np.dot(
        embeddings, negative_embeddings.T
    )  # Shape: (n_samples, n_negatives)
    mean_negative_scores = np.mean(negative_similarities, axis=1)  # Shape: (n_samples,)

    # Add new columns to the dataset
    dataset = dataset.add_column("mean_positive_score", mean_positive_scores)
    dataset = dataset.add_column("mean_negative_score", mean_negative_scores)
    dataset = dataset.add_column(
        "difference_score", mean_positive_scores - mean_negative_scores
    )
    return dataset
