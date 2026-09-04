import numpy as np
from Levenshtein import distance as levenshtein_distance
from datasets import Dataset, DatasetDict
from tqdm.auto import tqdm

from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def bag_of_words_similarity(text1, text2):
    """
    Calculate bag-of-words similarity between two texts using cosine similarity.

    Parameters:
        text1 (str): First text string
        text2 (str): Second text string

    Returns:
        float: Similarity score between 0 and 1, where 1 means identical texts
    """
    if not text1 and not text2:
        return 1.0  # Both empty strings are identical

    if not text1 or not text2:
        return 0.0  # One empty string means no similarity

    # Create word counters for both texts
    counter1 = Counter(text1.lower().split())
    counter2 = Counter(text2.lower().split())

    # Get all unique words
    all_words = set(counter1.keys()) | set(counter2.keys())

    # Calculate dot product
    dot_product = sum(
        counter1.get(word, 0) * counter2.get(word, 0) for word in all_words
    )

    # Calculate magnitudes
    magnitude1 = np.sqrt(sum(count**2 for count in counter1.values()))
    magnitude2 = np.sqrt(sum(count**2 for count in counter2.values()))

    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    # Calculate cosine similarity
    similarity = dot_product / (magnitude1 * magnitude2)

    return similarity


def calculate_bow_dataset_similarities(
    dataset1: Dataset,
    dataset2: Dataset,
    text_column="text",
    batch_size=None,
    use_vectorizer=True,
) -> Dataset:
    """
    Calculate bag-of-words similarity scores for each item in dataset1
    compared to all items in dataset2.

    Parameters:
        dataset1 (Dataset): HuggingFace dataset with text column
        dataset2 (Dataset): HuggingFace dataset with text column to compare against
        text_column (str): Name of the column containing text in both datasets
        batch_size (int, optional): Process dataset in batches of this size for memory efficiency
        use_vectorizer (bool): Whether to use sklearn's vectorizer (faster for large datasets)

    Returns:
        Dataset: A new dataset with original columns from dataset1 plus similarity metrics
    """
    # Ensure both datasets have the text column
    assert (
        text_column in dataset1.column_names
    ), f"'{text_column}' column not found in dataset1"
    assert (
        text_column in dataset2.column_names
    ), f"'{text_column}' column not found in dataset2"

    # Get texts from dataset2
    texts2 = dataset2[text_column]

    if use_vectorizer:
        # More efficient implementation using sklearn's vectorizer
        # This is much faster for large datasets
        vectorizer = CountVectorizer()

        # Combine all texts to fit the vectorizer
        all_texts = list(dataset1[text_column]) + texts2
        vectorizer.fit(all_texts)

        # Transform dataset2 texts (this will be reused for each comparison)
        texts2_vectors = vectorizer.transform(texts2)

        def compute_similarities_batch_vectorized(examples):
            batch_results = {
                "average_similarity": [],
                "max_similarity": [],
                "min_similarity": [],
                "most_similar_idx": [],
                "most_similar_text": [],
            }

            # Transform the batch texts
            texts1_vectors = vectorizer.transform(examples[text_column])

            # Calculate pairwise similarities
            similarities_matrix = cosine_similarity(texts1_vectors, texts2_vectors)

            for i, similarities in enumerate(similarities_matrix):
                # Store metrics
                batch_results["average_similarity"].append(float(np.mean(similarities)))
                batch_results["max_similarity"].append(float(np.max(similarities)))
                batch_results["min_similarity"].append(float(np.min(similarities)))

                most_similar_idx = np.argmax(similarities)
                batch_results["most_similar_idx"].append(int(most_similar_idx))
                batch_results["most_similar_text"].append(texts2[most_similar_idx])

            return batch_results

        # Process the dataset using the vectorized approach
        if batch_size:
            result_dataset = dataset1.map(
                compute_similarities_batch_vectorized,
                batched=True,
                batch_size=batch_size,
                desc="Computing bag-of-words similarities",
            )
        else:
            result_dataset = dataset1.map(
                compute_similarities_batch_vectorized,
                batched=True,
                desc="Computing bag-of-words similarities",
            )

    else:
        # Original approach using the custom similarity function
        def compute_similarities_batch(examples):
            batch_results = {
                "average_similarity": [],
                "max_similarity": [],
                "min_similarity": [],
                "most_similar_idx": [],
                "most_similar_text": [],
            }

            for text1 in examples[text_column]:
                similarities = []
                for text2 in texts2:
                    sim_score = bag_of_words_similarity(text1, text2)
                    similarities.append(sim_score)

                # Store metrics
                batch_results["average_similarity"].append(float(np.mean(similarities)))
                batch_results["max_similarity"].append(float(np.max(similarities)))
                batch_results["min_similarity"].append(float(np.min(similarities)))

                most_similar_idx = np.argmax(similarities)
                batch_results["most_similar_idx"].append(int(most_similar_idx))
                batch_results["most_similar_text"].append(texts2[most_similar_idx])

            return batch_results

        # Process the dataset with or without batching
        if batch_size:
            result_dataset = dataset1.map(
                compute_similarities_batch,
                batched=True,
                batch_size=batch_size,
                desc="Computing bag-of-words similarities",
            )
        else:
            result_dataset = dataset1.map(
                compute_similarities_batch,
                batched=True,
                desc="Computing bag-of-words similarities",
            )

    return result_dataset
