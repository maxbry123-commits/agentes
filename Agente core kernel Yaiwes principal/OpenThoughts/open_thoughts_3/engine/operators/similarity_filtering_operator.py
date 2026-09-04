import logging
from typing import Dict, List, Literal, Optional, Union

import faiss
import numpy as np
import ray
from datasets import Dataset

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
)


class SimilarityFilteringOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for SimilarityFilteringOperator.

    Attributes:
        type (str): The type of the operator, should be 'similarity_filtering'.
        input_embedding_column (str): The column containing embeddings to compare.
        input_min_distance_column (str): The column containing minimum distance thresholds.
        output_filter_decision_column (str): The column to store filtering decisions.
        should_filter (bool): Whether to actually filter out similar items or just mark them.
        input_text_column (str): The column containing the text to store for similar matches.
    """

    type: Literal["similarity_filtering"] = "similarity_filtering"
    input_embedding_column: str
    input_min_distance_column: str
    output_filter_decision_column: str = "should_filter"
    output_similar_input_text_column: str = (
        "similar_text"  # Column to store matching text
    )
    input_text_column: str = "text"  # Column containing the text to compare
    should_filter: bool = True


@ray.remote
class FaissIndex:
    """A Ray actor that maintains a FAISS index and processes shards."""

    def __init__(self, index_type: str = "index_flat_l2"):
        self.index = None
        self.stored_texts = []  # Store texts in order of addition to index
        self.index_type = index_type
        # L2 distance indices use min_distance mode, IP indices use max_similarity mode
        self.comparison_mode = (
            "min_distance" if index_type == "index_flat_l2" else "max_similarity"
        )

    def initialize_if_needed(self, dim: int) -> None:
        if self.index is None:
            if self.index_type == "index_flat_l2":
                self.index = faiss.IndexFlatL2(dim)
            elif self.index_type == "index_flat_ip":
                self.index = faiss.IndexFlatIP(dim)

    def process_shard(
        self,
        dataset: Dataset,
        input_embedding_column: str,
        input_threshold_column: str,
        output_filter_decision_column: str,
        output_similar_input_text_column: str,
        input_text_column: str,
        should_filter: bool,
    ) -> Dataset:
        """Process a dataset shard."""

        def process_batch(examples: Dict[str, List]) -> Dict[str, List]:
            embeddings = np.array(examples[input_embedding_column], dtype=np.float32)
            thresholds = np.array(examples[input_threshold_column], dtype=np.float32)
            texts = examples[input_text_column]

            self.initialize_if_needed(embeddings.shape[1])

            # Search for nearest neighbors for all vectors in batch
            if self.index.ntotal == 0:
                vectors_to_add = embeddings
                texts_to_add = texts
                should_filter = [False] * len(texts)
                indices = np.full((len(texts), 1), None)
                # Default values depend on mode
                default_value = (
                    -1.0 if self.comparison_mode == "max_similarity" else 1.0
                )
                distances = np.full((len(texts), 1), default_value)
            else:
                distances, indices = self.index.search(embeddings, k=1)
                nearest_scores = distances[:, 0]

                # Determine which items to filter based on mode
                if self.comparison_mode == "max_similarity":
                    # For IP index: filter if similarity is higher than threshold
                    should_filter = nearest_scores > thresholds
                else:
                    # For L2 index: filter if distance is lower than threshold
                    should_filter = nearest_scores < thresholds

                # Add vectors that pass the threshold to the index
                vectors_to_add = embeddings[~should_filter]
                texts_to_add = [
                    texts[i]
                    for i, filter_out in enumerate(should_filter)
                    if not filter_out
                ]

            if len(vectors_to_add) > 0:
                self.index.add(vectors_to_add)
                self.stored_texts.extend(texts_to_add)

            # Add filter decision to examples
            examples[output_filter_decision_column] = should_filter

            # Add similar texts and distances in separate columns
            similar_texts = []
            similar_scores = []
            default_value = -1.0 if self.comparison_mode == "max_similarity" else 1.0

            for should_filter, idx, score in zip(
                should_filter, indices[:, 0], distances[:, 0]
            ):
                if idx is not None:
                    similar_texts.append(self.stored_texts[idx])
                    similar_scores.append(float(score))
                else:
                    similar_texts.append("")
                    similar_scores.append(default_value)

            examples[output_similar_input_text_column] = similar_texts
            score_column = (
                output_similar_input_text_column + "_similarity"
                if self.comparison_mode == "max_similarity"
                else output_similar_input_text_column + "_distance"
            )
            examples[score_column] = similar_scores

            return examples

        # Process the dataset
        filtered_dataset = dataset.map(process_batch, batched=True, batch_size=32)

        # If should_filter is True, remove filtered items
        if should_filter:
            filtered_dataset = filtered_dataset.filter(
                lambda x: not x[output_filter_decision_column]
            )

        return filtered_dataset

    def get_size(self) -> int:
        return 0 if self.index is None else self.index.ntotal


class SimilarityFilteringOperator(Operator):
    """
    Operator for filtering similar items using FAISS.

    This operator is used to filter out similar items from a dataset based on a minimum distance threshold.

    Attributes:
        id (str): Unique identifier for the operator.
        input_ids (List[str]): List of input identifiers for the operator.
        config (SimilarityFilteringOperatorConfig): Configuration for the filtering operator.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: SimilarityFilteringOperatorConfig,
        execution_context: ExecutionContext,
        index_type: str = "index_flat_l2",
    ):
        super().__init__(id, input_ids, config, execution_context)
        self._faiss_index = FaissIndex.options(name=f"faiss_index_{self.id}").remote(
            index_type
        )

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Filter similar items from the input datasets.

        Args:
            inputs (DatasetRefs): Dictionary of inputs mapping identifiers to shard references.

        Returns:
            ManyShardRefsGenerator: Generator of filtered output shard references.
        """
        # Process each shard sequentially
        for _, shard_refs in inputs.items():
            for shard_ref in shard_refs:
                yield self._faiss_index.process_shard.remote(
                    shard_ref,
                    self.config.input_embedding_column,
                    self.config.input_min_distance_column,
                    self.config.output_filter_decision_column,
                    self.config.output_similar_input_text_column,
                    self.config.input_text_column,
                    self.config.should_filter,
                )


class IndexFlatIPSimilarityFilteringOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for IndexFlatIPSimilarityFilteringOperatorConfig.

    Attributes:
        type (str): The type of the operator, should be 'index_flat_ip_similarity_filtering'.
        input_embedding_column (str): The column containing embeddings to compare.
        input_threshold_column (str): The column containing maximum similarity thresholds.
        output_filter_decision_column (str): The column to store filtering decisions.
        should_filter (bool): Whether to actually filter out similar items or just mark them.
        input_text_column (str): The column containing the text to store for similar matches.
    """

    type: Literal["index_flat_ip_similarity_filtering"] = (
        "index_flat_ip_similarity_filtering"
    )
    input_embedding_column: str
    input_max_similarity_column: str
    output_filter_decision_column: str = "should_filter"
    output_similar_input_text_column: str = "similar_text"
    input_text_column: str = "text"
    should_filter: bool = True


class IndexFlatIPSimilarityFilteringOperator(SimilarityFilteringOperator):
    """
    Operator for filtering similar items using FAISS with IndexFlatIP.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: IndexFlatIPSimilarityFilteringOperatorConfig,
        execution_context: ExecutionContext,
    ):
        super().__init__(
            id, input_ids, config, execution_context, index_type="index_flat_ip"
        )

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Filter similar items from the input datasets.

        Args:
            inputs (DatasetRefs): Dictionary of inputs mapping identifiers to shard references.

        Returns:
            ManyShardRefsGenerator: Generator of filtered output shard references.
        """
        # Process each shard sequentially
        for _, shard_refs in inputs.items():
            for shard_ref in shard_refs:
                yield self._faiss_index.process_shard.remote(
                    shard_ref,
                    self.config.input_embedding_column,
                    self.config.input_max_similarity_column,
                    self.config.output_filter_decision_column,
                    self.config.output_similar_input_text_column,
                    self.config.input_text_column,
                    self.config.should_filter,
                )
