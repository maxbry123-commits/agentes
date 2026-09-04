from typing import List, Literal

import ray
from datasets import Dataset, concatenate_datasets
from pydantic import Field

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
    ShardRef,
)


class TruncateOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for truncate operators.

    Attributes:
        type (Literal["truncate"]): The type of the operator, always set to "truncate".
        num_truncate (int): The maximum number of examples to keep.
    """

    type: Literal["truncate"] = "truncate"
    num_truncate: int = Field(..., description="Number of examples to keep")


class TruncateOperator(Operator):
    """
    Operator that truncates the dataset to a specified number of examples.

    Attributes:
        num_truncate (int): The maximum number of examples to keep.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: TruncateOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the TruncateOperator.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (TruncateOperatorConfig): Specific configuration for the truncate operator.
            execution_context (ExecutionContext): Execution context for the operator.
        """
        super().__init__(id, input_ids, config, execution_context)
        self.num_truncate = config.num_truncate

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Execute the truncate operator on the input datasets.

        Args:
            inputs (DatasetRefs): Map of input datasets to truncate

        Returns:
            ManyShardRefsGenerator: Generator of truncated datasets
        """
        # We expect only one input dataset
        if len(inputs) != 1:
            raise ValueError(
                f"TruncateOperator expects exactly one input dataset, got {len(inputs)}"
            )

        input_shards = next(iter(inputs.values()))
        remaining = self.num_truncate
        collected_shards = []

        for shard in input_shards:
            if remaining <= 0:
                break

            collected_shards.append(shard)
            # Get the length of the current shard
            shard_len = ray.get(self.get_shard_length.remote(shard))
            remaining -= shard_len

        if remaining > 0:
            raise ValueError(
                f"TruncateOperator: Expected to truncate to {self.num_truncate} examples, but only found {len(collected_shards)} examples"
            )

        if collected_shards:
            yield self.truncate_shards.remote(collected_shards, self.num_truncate)

    @staticmethod
    @ray.remote
    def get_shard_length(shard: Dataset) -> int:
        """
        Get the length of a shard.

        Args:
            shard (ShardRef): The shard reference.

        Returns:
            int: Length of the shard.
        """
        return len(shard)

    @staticmethod
    @ray.remote
    def truncate_shards(shards: List[ShardRef], num_truncate: int) -> Dataset:
        """
        Truncate the combined shards to the specified number of examples.

        Args:
            shards (List[ShardRef]): List of dataset shard references.
            num_truncate (int): Maximum number of examples to keep.

        Returns:
            Dataset: Truncated dataset.
        """
        datasets = [ray.get(shard) for shard in shards]
        combined_dataset = concatenate_datasets(datasets)
        return combined_dataset.select(range(num_truncate))
