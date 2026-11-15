import random
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


class MixOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for mix operators.

    Attributes:
        type (Literal["mix"]): The type of the operator, always set to "mix".
        seed (int): The seed for random shuffling (optional).
    """

    type: Literal["mix"] = "mix"
    seed: int = Field(default=42)
    add_shard_id_column: bool = Field(default=False)


class MixOperator(Operator):
    """
    Operator that mixes incoming shards by concatenating and shuffling them.

    Attributes:
        seed (int): The seed for random shuffling.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: MixOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the MixOperator.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (MixOperatorConfig): Specific configuration for the mix operator.
            execution_context (ExecutionContext): Execution context for the operator.
        """
        super().__init__(id, input_ids, config, execution_context)
        self.seed = config.seed
        self.add_shard_id_column = config.add_shard_id_column

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Execute the mix operator on the input datasets.

        Args:
            inputs (DatasetRefs): Map of input datasets to mix

        Returns:
            ManyShardRefsGenerator: Generator of mixed and shuffled datasets
        """
        all_shards = defaultdict(list)
        for input_shards_id, input_shards in inputs.items():
            for input_shard in input_shards:
                all_shards[input_shards_id].append(input_shard)

        yield self.mix_and_shuffle.remote(
            all_shards, self.seed, self.add_shard_id_column
        )

    @staticmethod
    @ray.remote
    def mix_and_shuffle(
        shards: List[ShardRef], seed: int, add_shard_id_column: bool
    ) -> Dataset:
        """
        Mix and shuffle the input shards.

        Args:
            shards (List[ShardRef]): List of dataset shard references.

        Returns:
            Dataset: Mixed and shuffled dataset.
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
        return combined_dataset.shuffle(seed=seed)
