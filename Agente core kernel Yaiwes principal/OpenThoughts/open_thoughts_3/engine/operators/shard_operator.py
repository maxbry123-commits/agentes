import gc
import logging
import os
import shutil
import tempfile
from typing import List, Literal

import ray
from datasets import Dataset, load_from_disk
from pydantic import Field

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
)


class ShardOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for shard operators.

    Attributes:
        type (Literal["shard"]): The type of the operator, always set to "shard".
        num_shards (int): Number of shards to split the dataset into.
    """

    type: Literal["shard"] = "shard"
    num_shards: int = Field(gt=0)


class ShardOperator(Operator):
    """
    Operator that shards a dataset into multiple parts.

    Attributes:
        num_shards (int): Number of shards to create.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: ShardOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the ShardOperator.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (ShardOperatorConfig): Specific configuration for the shard operator.
            execution_context (ExecutionContext): Execution context for the operator.
        """
        super().__init__(id, input_ids, config, execution_context)
        self.num_shards = config.num_shards

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Execute the shard operator on the input dataset.

        Args:
            inputs (DatasetRefs): Map of input datasets to shard

        Returns:
            ManyShardRefsGenerator: Generator of sharded datasets
        """
        # We expect only one input dataset
        input_shards = next(iter(inputs.values()))
        # And only one shard in that dataset
        input_shard = next(input_shards)

        # Schedule the sharding work
        yield from self.shard_dataset.remote(input_shard, self.num_shards)

    @staticmethod
    @ray.remote
    def shard_dataset(dataset: Dataset, num_shards: int) -> ManyShardRefsGenerator:
        """
        Process the input dataset and create shards.

        Args:
            dataset (Dataset): The input dataset
            num_shards (int): Number of shards to create

        Returns:
            List[ray.ObjectRef]: List of references to the created shards
        """
        tmp_dir = tempfile.mkdtemp()
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Save dataset to disk
            dataset.save_to_disk(tmp_dir)

            # Calculate shard sizes
            shard_size = len(dataset) // num_shards

            # Release the dataset from memory
            del dataset
            gc.collect()

            dataset = load_from_disk(tmp_dir)

            # Create shard references
            i = 0
            while i < len(dataset):
                start_idx = i
                end_idx = min(start_idx + shard_size, len(dataset))
                shard = dataset.select(range(start_idx, end_idx))
                i += shard_size

                is_remote = os.environ.get("IS_REMOTE", "0") == "1"
                if is_remote:
                    shard = Dataset.from_pandas(shard.to_pandas())
                yield shard
