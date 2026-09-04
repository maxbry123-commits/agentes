import os
import tempfile
from typing import Iterator, List, Literal, Optional, Union

import pandas as pd
import ray
from datasets import Dataset, concatenate_datasets
from tqdm import tqdm

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
)


class MergeOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for merge operators.

    Attributes:
        type (Literal["merge"]): The type of the operator, always set to "merge".
        function (str): The name or identifier of the function.
        function_config (Dict[str, Any]): Additional configuration for the function.
        sharded (bool): Indicates whether the function can operate across only a shard
        num_shards (int): The number of shards if the function is sharded.
        input_dataset_map (Dict[str, str]): Mapping of function argument names to input datasets from previous operators
    """

    type: Literal["merge"] = "merge"
    join_column: str
    fill_value: Optional[Union[str, int, float]] = None
    escapechar: Optional[str] = None
    chunk_size: Optional[int] = 10000


class MergeOperator(Operator):
    """
    Operator that joins multiple datasets along a given column
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: MergeOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the MergeOperator.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (MergeOperatorConfig): Specific configuration for the Merge operator.
            execution_context (ExecutionContext): Execution context for the operator.
            remote_kwargs (Dict): Keyword argument to be passed into ray remote call
        """
        super().__init__(id, input_ids, config, execution_context)

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Execute the function operator on the input datasets.

        Args:
            inputs (DatasetRefs): Map of input datasets to apply function on

        Returns:
            ManyShardRefsGenerator: Generator of shards outputted by the function
        """
        input_datasets = {key: [] for key in inputs.keys()}
        for key in inputs.keys():
            input_datasets[key] = list(inputs[key])

        gen_shards = self.join_datasets.options(name="merge").remote(
            input_datasets,
            self.config.join_column,
            self.config.fill_value,
            self.config.chunk_size,
            self.config.escapechar,
        )
        yield gen_shards

    @staticmethod
    @ray.remote
    def join_datasets(
        dataset_refs: DatasetRefs,
        join_column: str,
        fill_value: Optional[Union[str, int, float]] = None,
        chunk_size=10000,
        escapechar=None,
    ) -> Iterator[Dataset]:
        dataset_refs_keys = list(dataset_refs.keys())
        result_df = concatenate_datasets(
            ray.get(dataset_refs[dataset_refs_keys[0]])
        ).to_pandas()
        existing_columns = set(result_df.columns)
        datasets = []

        for i in range(1, len(dataset_refs_keys)):
            for dataset_obj in dataset_refs[dataset_refs_keys[i]]:
                datasets.append(dataset_obj)

        if len(datasets) == 0:
            raise ValueError("Need at least 2 datasets to perform join")
        num_datasets = len(datasets)
        for i in range(num_datasets):
            new_df = ray.get(datasets[i]).to_pandas()
            new_columns = [
                col
                for col in new_df.columns
                if col not in existing_columns and col != join_column
            ]

            with tempfile.TemporaryDirectory() as tmpdirname:
                print("created temporary directory", tmpdirname)
                if new_columns:
                    df_subset = new_df[[join_column] + new_columns]
                    length_of_df_subset = len(df_subset)
                    if escapechar:
                        df_subset.to_csv(
                            os.path.join(tmpdirname, "temp.csv"),
                            index=False,
                            escapechar="\\",
                        )
                    else:
                        df_subset.to_csv(
                            os.path.join(tmpdirname, "temp.csv"), index=False
                        )
                    del df_subset

                    # Add new columns to result_df if they don't exist
                    for col in new_columns:
                        if col not in result_df.columns:
                            result_df[col] = None

                    reader = pd.read_csv(
                        os.path.join(tmpdirname, "temp.csv"), chunksize=chunk_size
                    )
                    for chunk in tqdm(
                        reader, total=int(length_of_df_subset / chunk_size) + 1
                    ):
                        # Create a mapping from join_column to new values
                        for col in new_columns:
                            # Update only null values in result_df using the mapping
                            mask = result_df[col].isna()
                            if mask.any():
                                # Create a mapping dictionary for this column
                                value_map = dict(zip(chunk[join_column], chunk[col]))
                                # Update only null values using the mapping
                                result_df.loc[
                                    mask
                                    & result_df[join_column].isin(chunk[join_column]),
                                    col,
                                ] = result_df.loc[
                                    mask
                                    & result_df[join_column].isin(chunk[join_column]),
                                    join_column,
                                ].map(
                                    value_map
                                )
                    existing_columns.update(new_columns)
            if fill_value is not None:
                result_df = result_df.fillna(fill_value)

        return Dataset.from_pandas(result_df)
