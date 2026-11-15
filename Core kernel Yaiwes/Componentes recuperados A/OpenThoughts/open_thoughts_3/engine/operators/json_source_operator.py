import json
import logging
import os
from typing import List, Literal, Optional

import pandas as pd
import ray
import zstandard as zstd
from datasets import Dataset
from google.cloud import storage

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
    register_operator,
)


class JSONSourceOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for JSON dataset source operators.

    Attributes:
        type (Literal["json_source"]): The type of the operator, always set to "json_source".
        directory (str): The name of the directory where the JSON files to be read are stored.
        columns (Optional[List[str]]): Specific columns to load from the dataset.
        num_truncate (Optional[int]): Number of samples to truncate the dataset to.
    """

    type: Literal["json_source"] = "json_source"
    directory: Optional[str] = None
    file: Optional[str] = None
    columns: Optional[List[str]] = None
    num_truncate: Optional[int] = None
    num_shards: Optional[int] = 1


class JSONSourceOperator(Operator):
    """
    Operator that loads a dataset from a directory containing jsons.

    Attributes:
        directory (str): Name of the directory with the jsons to read
        columns (Optional[List[str]]): Specific columns to load from the dataset.
        num_truncate (Optional[int]): Number of samples to truncate the dataset to.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: JSONSourceOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the JSONSourceOperator.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (JSONSourceOperatorConfig): Specific configuration for the JSON source operator.
            execution_context (ExecutionContext): Execution context for the operator.
        """
        super().__init__(id, input_ids, config, execution_context)
        self.file = config.file
        self.directory = config.directory
        self.columns = config.columns
        self.num_truncate = config.num_truncate
        self.num_shards = config.num_shards if config.num_shards else 1

    def compute(self, _: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Execute the JSON source operator to load the dataset.

        Args:
            _ (DatasetRefs): Unused input (for compatibility with the Operator interface).

        Returns:
            ManyShardRefs: List containing a single reference to the loaded dataset.
        """
        yield self.load_dataset.remote(
            directory=self.directory,
            file=self.file,
            columns=self.columns,
            num_truncate=self.num_truncate,
        )

    @staticmethod
    @ray.remote
    def load_dataset(
        directory: Optional[str] = None,
        file: Optional[str] = None,
        columns: Optional[List[str]] = None,
        num_truncate: Optional[int] = None,
    ) -> Dataset:
        """
        Build the dataset from the JSON files in the directory, GCS bucket, or a single GCS file.

        Args:
            directory: Directory containing JSON files
            file: Single JSON file path
            columns: Specific columns to load
            num_truncate: Number of samples to truncate to

        Returns:
            Dataset: The loaded and potentially processed dataset.
        """
        data = []
        json_filenames = []

        if (directory and directory.startswith("gs://")) or (
            file and file.startswith("gs://")
        ):
            # Handle GCS path
            if directory:
                bucket_name, prefix = JSONSourceOperator._parse_gcs_path(directory)
                json_filenames = JSONSourceOperator._list_gcs_files(bucket_name, prefix)
                for blob_name in json_filenames:
                    json_data = JSONSourceOperator._load_json_from_gcs(
                        bucket_name, blob_name
                    )
                    JSONSourceOperator._process_json_data(json_data, data)
            else:  # file is a GCS path
                bucket_name, blob_name = JSONSourceOperator._parse_gcs_path(file)
                json_filenames = [blob_name]
                json_data = JSONSourceOperator._load_json_from_gcs(
                    bucket_name, blob_name
                )
                JSONSourceOperator._process_json_data(json_data, data)
        else:
            # Handle local path
            if directory:
                file_list = [
                    os.path.join(directory, file_name)
                    for file_name in os.listdir(directory)
                ]
            else:
                file_list = [file]

            for file_path in file_list:
                if file_path.endswith((".json", ".jsonl", ".jsonl.zstd")):
                    json_filenames.append(file_path)
                    if file_path.endswith(".jsonl.zstd"):
                        with open(file_path, "rb") as f:
                            dctx = zstd.ZstdDecompressor()
                            with dctx.stream_reader(f) as reader:
                                json_data = [
                                    json.loads(line.strip())
                                    for line in reader.read().decode().splitlines()
                                ]
                    else:
                        with open(file_path, "r") as f:
                            if file_path.endswith(".json"):
                                json_data = json.load(f)
                            else:  # JSONL file
                                json_data = [json.loads(line.strip()) for line in f]
                    JSONSourceOperator._process_json_data(json_data, data)

        # Convert the list of dictionaries into a pandas DataFrame
        df = pd.DataFrame(data)

        # Create a Hugging Face Dataset from the DataFrame
        dataset = Dataset.from_pandas(df)

        if columns:
            dataset = dataset.select_columns(columns)
        if num_truncate is not None:
            dataset = dataset.select(range(min(len(dataset), num_truncate)))

        # log the json_filenames
        logging.info(
            f"\nDataset built from the JSONs in {directory or file} with names:"
        )
        for file_name in json_filenames:
            logging.info(file_name + "\n")
        logging.info(dataset)
        return dataset

    @staticmethod
    def _parse_gcs_path(gcs_path: str) -> tuple:
        """Parse a GCS path into bucket name and prefix."""
        parts = gcs_path.replace("gs://", "").split("/")
        bucket_name = parts[0]
        prefix = "/".join(parts[1:])
        return bucket_name, prefix

    @staticmethod
    def _list_gcs_files(bucket_name: str, prefix: str) -> List[str]:
        """List files in a GCS bucket with a given prefix."""
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs if blob.name.endswith((".json", ".jsonl"))]

    @staticmethod
    def _load_json_from_gcs(bucket_name: str, blob_name: str) -> dict:
        """Load JSON data from a GCS file."""
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        content = blob.download_as_text()
        if blob_name.endswith(".json"):
            return json.loads(content)
        else:  # JSONL file
            return [json.loads(line) for line in content.splitlines()]

    @staticmethod
    def _process_json_data(json_data, data):
        """Process JSON data and append to the data list."""
        if isinstance(json_data, dict):
            data.append(json_data)  # Append single dictionary
        elif isinstance(json_data, list):
            data.extend(json_data)  # Append multiple dictionaries


class LocalJSONSourceConfig(OperatorSpecificConfig):
    """
    Configuration class for a local JSON source operator.
    """

    type: Literal["local_json_source"] = "local_json_source"
    directory: str  # Directory containing JSON files
    num_shards: int  # Number of shards to split data into


class LocalJSONSourceOperator(Operator):
    """
    Operator that loads and processes data from local JSON files.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: LocalJSONSourceConfig,
        execution_context: ExecutionContext,
    ):
        super().__init__(id, input_ids, config, execution_context)
        self.directory = config.directory
        self.num_shards = config.num_shards

    def compute(self, _: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Execute the local JSON source operator to load and process the data.
        """
        json_files = [
            os.path.join(self.directory, f)
            for f in os.listdir(self.directory)
            if f.endswith(".json") or f.endswith(".jsonl") or f.endswith(".jsonl.zstd")
        ]
        logging.info(f"Processing {len(json_files)} JSON files from {self.directory}")

        for file in json_files:
            yield self._load_json_file.remote(file)

    @staticmethod
    @ray.remote
    def _load_json_file(file_path: str) -> Dataset:
        """Loads and processes a single JSON file, including jsonl.zstd."""
        data = []

        if file_path.endswith(".jsonl.zstd"):
            with open(file_path, "rb") as f:
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(f) as reader:
                    json_data = [
                        json.loads(line.strip())
                        for line in reader.read().decode().splitlines()
                    ]
        else:
            with open(file_path, "r") as f:
                if file_path.endswith(".json"):
                    json_data = json.load(f)
                else:  # JSONL file
                    json_data = [json.loads(line.strip()) for line in f]

        if isinstance(json_data, dict):
            data.append(json_data)
        else:
            data.extend(json_data)

        df = pd.DataFrame(data)
        return Dataset.from_pandas(df)


register_operator(LocalJSONSourceConfig, LocalJSONSourceOperator)
