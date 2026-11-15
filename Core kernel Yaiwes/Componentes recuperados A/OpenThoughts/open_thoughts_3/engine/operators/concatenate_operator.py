from collections import defaultdict
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


class ConcatenateOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for concatenate operators.

    Attributes:
        type (Literal["concatenate"]): The type of the operator, always set to "concatenate".
        seed (int): The seed for random shuffling (optional).
    """

    type: Literal["concatenate"] = "concatenate"
    add_shard_id_column: bool = Field(default=False)


class ConcatenateOperator(Operator):
    """
    Operator that concatenatees incoming shards by concatenating and shuffling them.

    Attributes:
        seed (int): The seed for random shuffling.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: ConcatenateOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the ConcatenateOperator.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (ConcatenateOperatorConfig): Specific configuration for the concatenate operator.
            execution_context (ExecutionContext): Execution context for the operator.
        """
        super().__init__(id, input_ids, config, execution_context)
        self.add_shard_id_column = config.add_shard_id_column

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Execute the concatenate operator on the input datasets.

        Args:
            inputs (DatasetRefs): Map of input datasets to concatenate

        Returns:
            ManyShardRefsGenerator: Generator of concatenateed and shuffled datasets
        """
        all_shards = defaultdict(list)
        for input_shards_id, input_shards in inputs.items():
            for input_shard in input_shards:
                all_shards[input_shards_id].append(input_shard)

        yield self.concatenate.remote(all_shards, self.add_shard_id_column)

    @staticmethod
    @ray.remote
    def concatenate(shards: List[ShardRef], add_shard_id_column: bool) -> Dataset:
        """
        Concatenate the input shards.

        Args:
            shards (List[ShardRef]): List of dataset shard references.

        Returns:
            Dataset: Concatenateed and shuffled dataset.
        """
        datasets = []
        for shard_id, shards in shards.items():
            for shard in shards:
                dataset_shard = ray.get(shard)
                if add_shard_id_column:
                    dataset_shard = dataset_shard.add_column(
                        "shard_id", [shard_id] * len(dataset_shard)
                    )
                datasets.append(dataset_shard)
        combined_dataset = concatenate_datasets(datasets)
        return combined_dataset
