import logging
import os
from typing import Dict, List, Literal, Optional

import huggingface_hub
import ray
from datasets import Dataset, concatenate_datasets, load_dataset

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
)


class HFUploadOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for Hugging Face dataset upload operators.

    Attributes:
        type: The type of operator, always "hf_upload"
        repo_id: The repository ID to upload to (format: username/dataset_name)
        private: Whether the dataset should be private
        config_paths: Optional paths to configuration files to upload
    """

    type: Literal["hf_upload"] = "hf_upload"
    repo_id: str
    private: bool = True
    config_paths: Optional[List[str]] = None


class HFUploadOperator(Operator):
    """
    Operator that uploads a dataset to Hugging Face's dataset hub.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: HFUploadOperatorConfig,
        execution_context: ExecutionContext,
    ):
        super().__init__(id, input_ids, config, execution_context)
        self.repo_id = config.repo_id
        self.private = config.private
        self.config_paths = config.config_paths

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Uploads the input dataset to HuggingFace and returns metadata.
        """
        # Since we expect only one input dataset
        input_datasets = []
        for key in inputs.keys():
            input_datasets.extend(list(inputs[key]))

        yield self.upload_dataset.remote(
            input_datasets, self.repo_id, self.private, self.config_paths
        )

    @staticmethod
    @ray.remote
    def upload_dataset(
        dataset_refs: Dataset,
        repo_id: str,
        private: bool,
        config_paths: Optional[List[str]] = None,
    ) -> Dict:
        """
        Uploads dataset to HuggingFace and returns metadata without materializing full dataset.
        """
        results = ray.get(dataset_refs)
        dataset = concatenate_datasets(results)
        # Get dataset stats before upload

        # Upload dataset
        commit_info = dataset.push_to_hub(
            repo_id=repo_id,
            private=private,
        )
        del dataset
        # Upload any config files if provided
        if config_paths:
            for config_path in config_paths:
                huggingface_hub.upload_file(
                    path_or_fileobj=config_path,
                    path_in_repo=f"config/{os.path.basename(config_path)}",
                    repo_id=repo_id,
                    repo_type="dataset",
                    commit_message="Upload configuration file",
                )

        uploaded_dataset = load_dataset(repo_id)
        dataset_length = len(uploaded_dataset["train"])
        dataset_fingerprint = uploaded_dataset["train"]._fingerprint

        return {
            "length": dataset_length,
            "fingerprint": dataset_fingerprint,
            "commit_hash": commit_info.oid,
            "repo_id": repo_id,
        }
