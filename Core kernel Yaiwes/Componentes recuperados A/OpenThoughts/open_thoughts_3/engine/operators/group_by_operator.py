import logging
from typing import Any, Dict, List, Literal

import ray
import xxhash
from datasets import Dataset, concatenate_datasets

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
    ShardRef,
)


@ray.remote(num_cpus=1)
class _MapActor:
    def map(self, dataset: Dataset) -> Dataset:
        return self.function(dataset)


class GroupByOperatorConfig(OperatorSpecificConfig):
    """
    Configuration for the GroupBy operator.

    Attributes:
        type (Literal["group_by"]): The type of operator, always "group_by"
        columns (List[str]): Columns to use for grouping/partitioning
        num_partitions (int): Number of partitions to create
    """

    type: Literal["group_by"] = "group_by"
    columns: List[str]
    num_partitions: int = 10


class GroupByOperator(Operator):
    """
    Operator that partitions data based on xxhash of specified columns.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: GroupByOperatorConfig,
        execution_context: ExecutionContext,
    ):
        super().__init__(id, input_ids, config, execution_context)
        self.columns = config.columns
        self.num_partitions = config.num_partitions

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Partition the input datasets based on xxhash of specified columns.

        Args:
            inputs (DatasetRefs): Input datasets to partition

        Returns:
            ManyShardRefsGenerator: Generator of partitioned dataset shards
        """
        if len(inputs) == 0:
            raise ValueError(f"Operator {self.id}: No input datasets provided")

        # Process each input dataset
        for input_dataset in inputs.values():
            # Partition the merged dataset
            partitioned_shards = self.partition_dataset.options(
                name=f"partitioning::{self.id}"
            ).remote(merged_dataset, self.columns, self.num_partitions)

            # Yield each partition
            for shard in partitioned_shards:
                yield shard

    @staticmethod
    @ray.remote
    def partition_dataset(
        dataset: Dataset, columns: List[str], num_partitions: int
    ) -> ray.ObjectRefGenerator:
        """
        Partition a dataset based on xxhash of specified columns.

        Args:
            dataset (Dataset): Dataset to partition
            columns (List[str]): Columns to use for hashing
            num_partitions (int): Number of partitions to create

        Returns:
            ray.ObjectRefGenerator: Generator of dataset partitions
        """
        # Create partition buckets
        partitions: Dict[int, List[int]] = {i: [] for i in range(num_partitions)}

        # Calculate partition for each row
        for idx, row in enumerate(dataset):
            # Create a string combining all column values
            key = "|".join(str(row[col]) for col in columns)

            # Calculate partition using xxhash
            partition = xxhash.xxh32(key).intdigest() % num_partitions

            # Add row index to appropriate partition
            partitions[partition].append(idx)

        # Create and yield each partition
        for partition_indices in partitions.values():
            if partition_indices:  # Only yield non-empty partitions
                partition = dataset.select(partition_indices)
                yield partition
