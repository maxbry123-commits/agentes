import asyncio
import time
from typing import List, Optional, Union, Dict, Any
from datasets import Dataset, load_dataset
from openai import AsyncOpenAI
from tqdm import tqdm
import numpy as np

async def get_embedding(
    text: str,
    client: AsyncOpenAI,
    semaphore: asyncio.Semaphore,
    model: str,
    retry_count: int = 3,
    backoff_factor: int = 2,
) -> Optional[List[float]]:
    """Get embeddings for a single text with retry logic"""
    if not text:
        return [0] * 1536  # Return zeros for empty strings

    attempts = 0
    while attempts < retry_count:
        try:
            async with semaphore:  # Control concurrency
                response = await client.embeddings.create(input=str(text), model=model)
                return response.data[0].embedding
        except Exception as e:
            attempts += 1
            if attempts == retry_count:
                print(f"Failed after {retry_count} attempts: {text[:50]}... Error: {e}")
                return None
            wait_time = backoff_factor**attempts
            print(f"Attempt {attempts} failed. Retrying in {wait_time}s. Error: {e}")
            await asyncio.sleep(wait_time)


async def process_batch(
    batch: Dict[str, List[Any]], text_column: str, client: AsyncOpenAI, semaphore: asyncio.Semaphore, model: str
) -> List[Optional[List[float]]]:
    """Process a batch of data to get embeddings"""
    tasks = []
    for text in batch[text_column]:
        task = asyncio.create_task(get_embedding(text, client, semaphore, model))
        tasks.append(task)

    return await asyncio.gather(*tasks)


async def _async_main(
    dataset: Dataset,
    text_column: str,
    client: AsyncOpenAI,
    embedding_column_name: str = "embedding",
    batch_size: int = 100,
    max_concurrent_requests: int = 10,
    model: str = "text-embedding-3-small",
) -> Dataset:
    """Async implementation of the main processing logic"""
    start_time = time.time()

    # Create a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent_requests)

    # Create a new list to store all embeddings
    all_embeddings = []

    # Process the dataset in batches to avoid memory issues
    for i in tqdm(range(0, len(dataset), batch_size), desc="Processing batches"):
        batch = dataset[i : i + batch_size]
        batch_embeddings = await process_batch(batch, text_column, client, semaphore, model)
        all_embeddings.extend(batch_embeddings)

    # Add embeddings to dataset
    dataset = dataset.add_column(embedding_column_name, all_embeddings)

    # Calculate and print statistics
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Completed embedding generation in {total_time:.2f} seconds.")
    print(f"Average time per embedding: {total_time/len(dataset):.4f} seconds.")

    return dataset


def apply_embedding_openai(
    dataset: Dataset,
    text_column: str,
    embedding_column_name: str = "embedding",
    split: str = "train",
    batch_size: int = 100,
    max_concurrent_requests: int = 10,
    model: str = "text-embedding-3-small",
    api_key: Optional[str] = None,
) -> Dataset:
    """
    Non-async main function that creates embeddings for a Hugging Face dataset.

    Args:
        dataset_name: Name of the Hugging Face dataset
        text_column: Column containing text to embed
        embedding_column_name: Name for the new column that will store embeddings
        split: Dataset split to use (e.g., "train", "test")
        batch_size: Number of examples to process in each batch
        max_concurrent_requests: Maximum number of concurrent API requests
        model: OpenAI embedding model to use
        api_key: Optional OpenAI API key (uses environment variable if not provided)

    Returns:
        Dataset with added embedding column
    """
    print(f"Dataset loaded. Size: {len(dataset)}")
    print(f"Using model: {model}")
    print(f"Max concurrent requests: {max_concurrent_requests}")

    # Initialize the OpenAI client
    client = AsyncOpenAI()

    # Run the async part in the event loop
    return asyncio.run(
        _async_main(
            dataset=dataset,
            text_column=text_column,
            client=client,
            embedding_column_name=embedding_column_name,
            batch_size=batch_size,
            max_concurrent_requests=max_concurrent_requests,
            model=model,
        )
    )


def calc_embedding_score_mean_memory_efficient(
    dataset: Dataset,
    embedding_column: str,
    positive_dataset: Dataset,
    negative_dataset: Dataset,
    positive_embedding_column: str,
    negative_embedding_column: str,
    batch_size: int = 128
) -> Dataset:
    print("GETTING HERE")
    # Initialize arrays to store the final scores
    n_samples = len(dataset)
    mean_positive_scores = np.zeros(n_samples)
    mean_negative_scores = np.zeros(n_samples)
    
    # Convert positive and negative embeddings to numpy arrays once
    positive_embeddings = np.array(positive_dataset[positive_embedding_column])
    negative_embeddings = np.array(negative_dataset[negative_embedding_column])
    
    # Process the main dataset in batches
    for i in tqdm(range(0, n_samples, batch_size), desc="Processing cosine batches"):
        # Get the current batch
        end_idx = min(i + batch_size, n_samples)
        batch_embeddings = np.array(dataset[embedding_column][i:end_idx])
        
        # Calculate similarities for this batch
        batch_positive_similarities = np.dot(batch_embeddings, positive_embeddings.T)
        batch_negative_similarities = np.dot(batch_embeddings, negative_embeddings.T)
        
        # Store the mean scores for this batch
        mean_positive_scores[i:end_idx] = np.mean(batch_positive_similarities, axis=1)
        mean_negative_scores[i:end_idx] = np.mean(batch_negative_similarities, axis=1)
        
        # Clean up batch variables to free memory
        del batch_embeddings
        del batch_positive_similarities
        del batch_negative_similarities
    
    # Add new columns to the dataset
    difference_scores = mean_positive_scores - mean_negative_scores
    dataset = dataset.add_column("mean_positive_score", mean_positive_scores)
    dataset = dataset.add_column("mean_negative_score", mean_negative_scores)
    dataset = dataset.add_column("difference_score", difference_scores)
    
    return dataset
