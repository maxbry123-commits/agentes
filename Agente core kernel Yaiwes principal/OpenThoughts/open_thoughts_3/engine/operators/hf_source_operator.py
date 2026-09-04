import logging
import os
from typing import List, Literal, Optional

import ray
from datasets import Dataset, load_dataset

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
)


class HFSourceOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for Hugging Face dataset source operators.

    Attributes:
        type (Literal["hf_source"]): The type of the operator, always set to "hf_source".
        dataset (str): The name of the Hugging Face dataset.
        split (str): The split of the dataset to use.
        columns (Optional[List[str]]): Specific columns to load from the dataset.
        num_truncate (Optional[int]): Number of samples to truncate the dataset to.
        data_dir (Optional[str]): The directory within the Hugging Face dataset repo to load from. For large repos where you only want a specific subset of the data.
    """

    type: Literal["hf_source"] = "hf_source"
    dataset: str
    subset: Optional[str] = None
    split: str
    columns: Optional[List[str]] = None
    data_dir: Optional[str] = None
    num_truncate: Optional[int] = None
    data_dir: Optional[str] = None
    trust_remote_code: Optional[bool] = False


class HFSourceOperator(Operator):
    """
    Operator that loads a dataset from Hugging Face's datasets library.

    Attributes:
        dataset (str): Name of the dataset to load.
        split (str): The split of the dataset to use.
        columns (Optional[List[str]]): Specific columns to load from the dataset.
        num_truncate (Optional[int]): Number of samples to truncate the dataset to.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: HFSourceOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the HFSourceOperator.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (HFSourceOperatorConfig): Specific configuration for the HF source operator.
            execution_context (ExecutionContext): Execution context for the operator.
        """
        super().__init__(id, input_ids, config, execution_context)
        self.dataset = config.dataset
        self.split = config.split
        self.columns = config.columns
        self.data_dir = config.data_dir
        self.num_truncate = config.num_truncate
        self.data_dir = config.data_dir
        self.trust_remote_code = config.trust_remote_code
        self.subset = config.subset

    def compute(self, _: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Execute the HF source operator to load the dataset.

        Args:
            _ (DatasetRefs): Unused input (for compatibility with the Operator interface).

        Returns:
            ManyShardRefs: List containing a single reference to the loaded dataset.
        """
        yield self.load_dataset.remote(
            self.dataset,
            self.split,
            self.columns,
            self.num_truncate,
            self.data_dir,
            trust_remote_code=self.trust_remote_code,
            subset=self.subset,
        )

    @staticmethod
    @ray.remote
    def load_dataset(
        dataset: str,
        split: str,
        columns: Optional[List[str]],
        num_truncate: Optional[int],
        data_dir: Optional[str],
        add_source_column: bool = False,
        trust_remote_code: bool = False,
        subset: Optional[str] = None,
    ) -> Dataset:
        """
        Load the dataset from Hugging Face's datasets library.

        Returns:
            Dataset: The loaded and potentially processed dataset.
        """
        # The keep_in_memory flag being set to True is crucial on multi-node remote clusters to allow us
        # to store the Dataset, along with its actual content, in Ray's object store.
        # Otherwise, Dataset only contains pointers to Arrow Tables written to a node's localdisk.
        # On local clusters, we can set keep_in_memory to False to avoid storing the
        # entire object in memory.
        is_remote = os.environ.get("IS_REMOTE", "0") == "1"
        if data_dir:
            if subset:
                ds = load_dataset(
                    dataset,
                    data_dir=data_dir,
                    split=split,
                    keep_in_memory=is_remote,
                    trust_remote_code=trust_remote_code,
                )
            else:
                ds = load_dataset(
                    dataset,
                    subset,
                    data_dir=data_dir,
                    split=split,
                    keep_in_memory=is_remote,
                    trust_remote_code=trust_remote_code,
                )
        else:
            if subset:
                ds = load_dataset(
                    dataset,
                    subset,
                    split=split,
                    keep_in_memory=is_remote,
                    trust_remote_code=trust_remote_code,
                )
            else:
                ds = load_dataset(
                    dataset,
                    split=split,
                    keep_in_memory=is_remote,
                    trust_remote_code=trust_remote_code,
                )

        if columns:
            ds = ds.select_columns(columns)
        if num_truncate is not None:
            ds = ds.select(range(min(len(ds), num_truncate)))

        if add_source_column:
            ds = ds.add_column("source", [dataset] * len(ds))

        logging.info(f"\nDataset loaded {dataset} split {split}:")
        logging.info(ds)
        return ds
