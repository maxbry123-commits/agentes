import logging
import os
import tempfile
from typing import List, Literal, Optional

import fasttext
import gcsfs
import ray
from datasets import Dataset, concatenate_datasets
from huggingface_hub import HfApi

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
)


class TrainFastTextOperatorConfig(OperatorSpecificConfig):
    """
    Configuration for FastText training operator.

    Attributes:
        type: Always "train_fasttext"
        text_column: Column containing the text to train on
        label_column: Column containing the labels
        save_path: Path to save the model (supports local or gcs paths)
        hf_repo_id: Optional Hugging Face repo ID to upload the model
        hf_token: Optional Hugging Face token for uploading
        epoch: Number of training epochs
        lr: Learning rate
        word_ngrams: Word N-grams parameter
        min_count: Minimum count of words
    """

    type: Literal["train_fasttext"] = "train_fasttext"
    text_column: str
    save_path: Optional[str] = None
    positive_input_ids: List[str]
    negative_input_ids: List[str]
    hf_repo_id: Optional[str] = None
    dim: int = 256
    epoch: int = 3
    lr: float = 0.1
    word_ngrams: int = 3
    min_count: int = 3
    tmpdir: Optional[str] = "/tmp/"


class TrainFastTextOperator(Operator):
    """
    Operator that trains a FastText model on input data and optionally uploads to HuggingFace.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: TrainFastTextOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the TrainFastTextOperator.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (TrainFastTextOperatorConfig): Specific configuration for the FastText training operator.
            execution_context (ExecutionContext): Execution context for the operator.
        """
        super().__init__(id, input_ids, config, execution_context)
        self.text_column = config.text_column
        self.save_path = config.save_path
        self.hf_repo_id = config.hf_repo_id
        self.positive_input_ids = config.positive_input_ids
        self.negative_input_ids = config.negative_input_ids
        self.training_params = {
            "epoch": config.epoch,
            "lr": config.lr,
            "word_ngrams": config.word_ngrams,
            "min_count": config.min_count,
            "dim": config.dim,
        }
        self.tmpdir = config.tmpdir
        if self.save_path is None and self.hf_repo_id is None:
            raise ValueError("Either save_path or hf_repo_id must be specified")

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Trains FastText model on the input datasets.

        Args:
            inputs (DatasetRefs): Input datasets containing text and labels

        Returns:
            ManyShardRefs: Reference to the trained model path
        """
        positive_input_shards = []

        # The input ID that's passed in the executor is of the form <framework_id>::<op_id>
        # We need to get the shards for the <op_id>.
        op_id_to_full_id = {}
        for id in inputs.keys():
            op_id = id.split("::")[-1]
            if op_id in op_id_to_full_id:
                raise ValueError(
                    f"Duplicate op_id {op_id} found in input IDs {id} and {op_id_to_full_id[op_id]}"
                )
            op_id_to_full_id[op_id] = id

        for input_op_id in self.positive_input_ids:
            full_id = op_id_to_full_id[input_op_id]
            positive_input_shards.extend(inputs[full_id])

        negative_input_shards = []
        for input_op_id in self.negative_input_ids:
            full_id = op_id_to_full_id[input_op_id]
            negative_input_shards.extend(inputs[full_id])

        # Train on all shards combined
        yield self.train_and_save_model.remote(
            positive_input_shards,
            negative_input_shards,
            self.text_column,
            self.save_path,
            self.training_params,
            self.hf_repo_id,
            self.tmpdir,
        )

    @ray.remote
    def train_and_save_model(
        positive_input_shards: List[ray.ObjectRef],
        negative_input_shards: List[ray.ObjectRef],
        text_column: str,
        save_path: str,
        training_params: dict,
        hf_repo_id: Optional[str],
        tmpdir: Optional[str],
    ) -> str:
        """
        Trains FastText model and saves it to the specified path.

        Args:
            input_shards: List of dataset shards
            text_column: Column name containing text
            label_column: Column name containing labels
            save_path: Path to save the model
            training_params: Training parameters
            hf_repo_id: Optional HuggingFace repo ID
            hf_token: Optional HuggingFace token
            tmpdir: Optional temporary directory

        Returns:
            str: Path where the model was saved
        """
        # Combine all shards
        positive = _merge_shards(positive_input_shards)
        negative = _merge_shards(negative_input_shards)

        with tempfile.TemporaryDirectory(dir=tmpdir) as temp_dir:
            train_output_file = os.path.join(temp_dir, "train.txt")
            model_output_file = os.path.join(temp_dir, "model.bin")

            # Write combined dataset to FastText format
            with open(train_output_file, "w", encoding="utf-8") as f:
                for example in positive:
                    label = "__label__QA_doc"
                    single_line_example = example[text_column].replace("\n", " ")
                    f.write(f"{label} {single_line_example}\n")
                for example in negative:
                    label = "__label__Not_QA_doc"
                    single_line_example = example[text_column].replace("\n", " ")
                    f.write(f"{label} {single_line_example}\n")

            logging.warning(
                f"Combined dataset written to {train_output_file} in FastText format."
            )

            # Train the model
            model = fasttext.train_supervised(
                input=train_output_file,
                dim=training_params["dim"],
                epoch=training_params["epoch"],
                lr=training_params["lr"],
                wordNgrams=training_params["word_ngrams"],
                minCount=training_params["min_count"],
            )
            model.save_model(model_output_file)

            logging.warning(
                f"FastText model trained and saved to temp file {model_output_file}"
            )

            if save_path:
                # Determine filesystem and open function based on path
                if save_path.startswith("gs://"):
                    fs = gcsfs.GCSFileSystem()
                    fs.put(model_output_file, save_path)
                else:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(model_output_file, "rb") as src, open(
                        save_path, "wb"
                    ) as dst:
                        dst.write(src.read())

                logging.warning(f"FastText model trained and saved to {save_path}")

            # Upload to HuggingFace if specified
            if hf_repo_id:
                api = HfApi()
                try:
                    # Create the repo if it doesn't exist
                    api.create_repo(
                        repo_id=hf_repo_id,
                        private=True,  # Assuming we want private repos by default
                        exist_ok=True,  # Won't fail if repo already exists
                    )

                    api.upload_file(
                        path_or_fileobj=model_output_file,
                        path_in_repo="model.bin",
                        repo_id=hf_repo_id,
                    )
                    logging.warning(
                        f"FastText model uploaded to HuggingFace as {hf_repo_id}"
                    )
                except Exception as e:
                    logging.error(f"Failed to upload model to HuggingFace: {str(e)}")
                    # Continue execution even if HF upload fails
                    pass
        return Dataset.from_list(
            [
                {
                    "TRAIN_FASTTEXT_OP_PATH": save_path,
                    "TRAIN_FASTTEXT_OP_HF_REPO_ID": hf_repo_id,
                    "TRAIN_FASTTEXT_OP_TEXT_COLUMN": text_column,
                    "TRAIN_FASTTEXT_OP_EPOCH": training_params["epoch"],
                    "TRAIN_FASTTEXT_OP_LR": training_params["lr"],
                    "TRAIN_FASTTEXT_OP_WORD_NGRAMS": training_params["word_ngrams"],
                    "TRAIN_FASTTEXT_OP_MIN_COUNT": training_params["min_count"],
                    "TRAIN_FASTTEXT_OP_DIM": training_params["dim"],
                }
            ]
        )


def _merge_shards(shards: List[ray.ObjectRef]) -> Dataset:
    combined_data = []
    for shard_ref in shards:
        shard = ray.get(shard_ref)
        combined_data.append(shard)

    return concatenate_datasets(combined_data)
