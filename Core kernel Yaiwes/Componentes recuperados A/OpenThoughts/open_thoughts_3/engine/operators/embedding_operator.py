import logging
from typing import Any, Dict, List, Literal, Optional

import numpy as np
import ray
import torch

# from sentence_transformers import SentenceTransformer

from datasets import Dataset, concatenate_datasets
from transformers import AutoTokenizer

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
)


class EmbeddingOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for EmbeddingOperator.

    Attributes:
        type (str): The type of the operator, should be 'embedding'.
        model (str): The name of the model to use for embeddings.
        num_workers_per_shard (int): The number of workers to use per shard.
        input_text_column (str): The column containing text to embed.
        output_embedding_column (str): The column to store embeddings in.
    """

    type: Literal["embedding"] = "embedding"
    model: str
    num_workers_per_shard: int = 10
    input_text_column: str
    output_embedding_column: str


def average_pool(
    last_hidden_states: torch.Tensor, attention_mask: torch.Tensor
) -> torch.Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def calculate_embeddings_batch(
    texts: List[str], model: Any, tokenizer: Any
) -> List[List[float]]:
    """Calculate the vector embeddings for a batch of input texts."""
    max_length = model.max_seq_length

    all_embeddings = []
    all_lengths = []
    all_fragments = []

    # Split each text into fragments
    for text in texts:
        inputs = tokenizer(text, padding=False, truncation=False, return_tensors="pt")
        chunks = [
            torch.Tensor(inputs["input_ids"][0][i : i + max_length].tolist()).int()
            for i in range(0, len(inputs["input_ids"][0]), max_length)
        ]
        fragments = [tokenizer.decode(chunk) for chunk in chunks]

        # Store fragments and their lengths
        for fragment in fragments:
            all_fragments.append(fragment)
            all_lengths.append(len(fragment))

    all_fragment_embeddings = model.encode(
        all_fragments, normalize_embeddings=True, batch_size=32
    )

    # Group embeddings by original text
    current_idx = 0
    for text in texts:
        # Count number of fragments for this text
        inputs = tokenizer(text, padding=False, truncation=False, return_tensors="pt")
        num_fragments = (len(inputs["input_ids"][0]) + max_length - 1) // max_length

        # Get embeddings and lengths for this text's fragments
        text_embeddings = all_fragment_embeddings[
            current_idx : current_idx + num_fragments
        ]
        text_lengths = all_lengths[current_idx : current_idx + num_fragments]

        # Calculate weighted average for this text
        avg_embedding = np.average(text_embeddings, axis=0, weights=text_lengths)
        normalized_embedding = avg_embedding / np.linalg.norm(avg_embedding)

        all_embeddings.append(normalized_embedding)
        current_idx += num_fragments

    # Sanity checks to make sure splitting and re-aggregating worked as expected.
    if len(all_embeddings) != len(texts):
        raise ValueError("Lengths and fragment embeddings must be the same length.")

    if current_idx != len(all_lengths):
        raise ValueError("Current index and lengths must be the same length.")

    return all_embeddings


@ray.remote
def process_sub_shard(
    dataset: Dataset,
    model_name: str,
    input_text_column: str,
    output_embedding_column: str,
) -> Dataset:
    """Process a sub-shard of the dataset by adding embeddings to each example."""
    logging.info(f"Dataset size: {len(dataset)}")
    # Load model and tokenizer in each worker
    model = SentenceTransformer(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Get all texts from the dataset
    texts = dataset[input_text_column]

    # Calculate embeddings for all texts
    embeddings = calculate_embeddings_batch(texts, model, tokenizer)

    # Add embeddings to dataset
    dataset = dataset.add_column(output_embedding_column, embeddings)

    return dataset


@ray.remote
def embed_dataset(
    dataset: Dataset,
    model_name: str,
    num_workers: int,
    input_text_column: str,
    output_embedding_column: str,
) -> Dataset:
    """Process a dataset by calculating embeddings for each text entry."""
    # Calculate sub-shard size
    total_size = len(dataset)
    sub_shard_size = total_size // num_workers
    if sub_shard_size == 0:
        sub_shard_size = 1

    # Process sub-shards in parallel
    sub_shard_refs = []
    for i in range(0, total_size, sub_shard_size):
        end_idx = min(i + sub_shard_size, total_size)
        sub_dataset = dataset.select(range(i, end_idx))
        sub_shard_refs.append(
            process_sub_shard.remote(
                sub_dataset, model_name, input_text_column, output_embedding_column
            )
        )

    # Wait for all sub-shards and merge
    sub_shards = ray.get(sub_shard_refs)
    return concatenate_datasets(sub_shards)


class EmbeddingOperator(Operator):
    """
    Operator for calculating embeddings on text data.

    Attributes:
        id (str): Unique identifier for the operator.
        input_ids (List[str]): List of input identifiers for the operator.
        config (EmbeddingOperatorConfig): Specific configuration for the embedding operator.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: EmbeddingOperatorConfig,
        execution_context: ExecutionContext,
    ):
        super().__init__(id, input_ids, config, execution_context)

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Compute embeddings on the given inputs.

        Args:
            inputs (DatasetRefs): Dictionary of inputs mapping identifiers to a list of shard references.

        Returns:
            ManyShardRefsGenerator: Generator of processed output shard references for each input shard.
        """
        for _, shard_refs in inputs.items():
            for shard_ref in shard_refs:
                yield embed_dataset.remote(
                    shard_ref,
                    self.config.model,
                    self.config.num_workers_per_shard,
                    self.config.input_text_column,
                    self.config.output_embedding_column,
                )
