import fcntl
import hashlib
import logging
import math
import os
import tempfile
import time
from typing import Literal, Optional

import fasttext
import fsspec
import gcsfs
import numpy as np
import ray
import requests
from datasets import Dataset
from huggingface_hub import hf_hub_download
from pydantic import DirectoryPath, Field, model_validator
from tqdm import tqdm

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
)

logger = logging.getLogger(__name__)


class FastTextOperatorConfig(OperatorSpecificConfig):
    type: Literal["fasttext"] = "fasttext"
    hf_repo_id: Optional[str] = None  # HuggingFace repo ID to download from
    fasttext_path: Optional[str] = None  # Local or GCS path
    input_column: str
    filter_threshold: float = Field(default=0.5, ge=0, le=1)
    top_percentage_ranking: Optional[float] = None
    cache_dir: Optional[DirectoryPath] = None
    batch_size: int = Field(default=500, ge=1)
    target_label: str
    just_add_scores: bool = False
    num_cpus: float = Field(default=1, gt=0)

    @model_validator(mode="after")
    def check_source_path(self):
        if self.hf_repo_id is None and self.fasttext_path is None:
            raise ValueError("Either hf_repo_id or fasttext_path must be specified")
        if self.hf_repo_id is not None and self.fasttext_path is not None:
            raise ValueError("Only one of hf_repo_id or fasttext_path can be specified")
        return self

    class Config:
        extra = "forbid"


class FastTextOperator(Operator):
    def __init__(
        self,
        id: str,
        input_ids: list[str],
        config: FastTextOperatorConfig,
        execution_context: ExecutionContext,
    ):
        super().__init__(id, input_ids, config, execution_context)
        self.hf_repo_id = config.hf_repo_id
        self.fasttext_path = config.fasttext_path
        self.input_column = config.input_column
        self.filter_threshold = config.filter_threshold
        self.top_percentage_ranking = config.top_percentage_ranking
        self.cache_dir = (
            os.path.join(os.getcwd(), ".cache", "fasttext")
            if config.cache_dir is None
            else config.cache_dir
        )
        self.batch_size = config.batch_size
        self.target_label = config.target_label
        self.num_cpus = config.num_cpus
        self.just_add_scores = config.just_add_scores

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        for input in inputs.values():
            for shard in input:
                logger.warning(f"Processing shard: {shard}")
                yield FastTextOperator._fasttext_filter.options(
                    num_cpus=self.num_cpus
                ).remote(
                    self.hf_repo_id,
                    self.fasttext_path,
                    self.input_column,
                    self.filter_threshold,
                    self.top_percentage_ranking,
                    self.cache_dir,
                    self.target_label,
                    shard,
                    self.batch_size,
                    self.just_add_scores,
                )

    @staticmethod
    @ray.remote
    def _fasttext_filter(
        hf_repo_id: Optional[str],
        fasttext_path: Optional[str],
        input_column: str,
        filter_threshold: float,
        top_percentage_ranking: float,
        cache_dir: str,
        target_label: str,
        data: Dataset,
        batch_size: int = 100,
        just_add_scores: bool = False,
    ) -> Dataset:
        model = FastTextOperator._load_model(hf_repo_id, fasttext_path, cache_dir)
        if model is None:
            logger.warning(f"Failed to load model. Returning all data.")
            return data

        texts = data[input_column]
        texts = [" ".join(text.strip().split("\n")) for text in texts]

        # Process in batches
        all_scores = []
        for i in tqdm(
            range(0, len(texts), batch_size),
            desc="Running fasttext filter",
            unit="batches",
            total=math.ceil(len(texts) / batch_size),
        ):
            batch_texts = texts[i : i + batch_size]
            labels, probs = model.predict(batch_texts, k=10)

            # Extract probabilities for the target label for this batch
            batch_target_probs = []
            for label_list, prob_list in zip(labels, probs):
                try:
                    target_index = label_list.index(target_label)
                    batch_target_probs.append(prob_list[target_index])
                except ValueError:
                    batch_target_probs.append(0.0)

            all_scores.extend(batch_target_probs)

        scores = np.array(all_scores)
        if just_add_scores:
            data = data.add_column("_fasttext_score", scores)
            return data
        if top_percentage_ranking:
            # Calculate the threshold value for the top percentage
            threshold = np.percentile(scores, 100 - top_percentage_ranking)
            # Create mask for scores above the threshold
            mask = scores >= threshold
        else:
            mask = scores > filter_threshold

        filtered_data = data.filter(lambda _, idx: mask[idx], with_indices=True)
        logger.info(f"Filtered {len(texts)} records to {len(filtered_data)} records")
        return filtered_data

    @staticmethod
    def _download_from_path(source: str, destination: str, is_hf: bool = False) -> bool:
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)

            if is_hf:
                # Download from HuggingFace
                dest = os.path.dirname(destination)
                hf_hub_download(
                    repo_id=source,
                    filename="model.bin",
                    local_dir=dest,
                    local_dir_use_symlinks=False,
                )
                # Rename the downloaded file to our cache filename
                os.rename(os.path.join(dest, "model.bin"), destination)
            elif source.startswith("gs://"):
                fs = gcsfs.GCSFileSystem()
                fs.get(source, destination)
            else:
                # Assume local file
                with open(source, "rb") as src, open(destination, "wb") as dst:
                    dst.write(src.read())

            logger.info(
                f"Successfully downloaded/copied model from {source} to {destination}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to download/copy model from {source}: {str(e)}")
            return False

    @staticmethod
    def _load_model(
        hf_repo_id: Optional[str], fasttext_path: Optional[str], cache_dir: str
    ):
        source = hf_repo_id or fasttext_path
        is_hf = hf_repo_id is not None
        cache_key = hashlib.md5(source.encode()).hexdigest()

        model_dir = os.path.join(cache_dir, cache_key)

        success_file = os.path.join(model_dir, f"SUCCESS")
        model_file = os.path.join(model_dir, f"model.bin")

        if os.path.exists(model_dir):
            logger.warning(
                f"Cache directory {cache_dir} already exists so will try to load model from cache."
            )
            model = FastTextOperator._wait_for_cache_or_download_model(
                model_file, success_file, source, is_hf
            )
            return model

        # Use a lock to prevent multiple processes from downloading the model at the same time.
        logger.warning(f"Acquiring lock on {cache_dir} to download model from {source}")
        os.makedirs(model_dir, exist_ok=True)
        lock_path = os.path.join(cache_dir, f"model.lock")
        fd = _acquire_lock(lock_path)

        if fd is not None:
            try:
                logger.warning(
                    f"First process downloading model from {source} to {model_dir}"
                )
                os.makedirs(model_dir, exist_ok=True)

                if FastTextOperator._download_from_path(source, model_file, is_hf):
                    with open(success_file, "w") as f:
                        f.write("Success.")
                    return fasttext.load_model(model_file)
                return None
            finally:
                _release_lock(fd, lock_path)

        # If we get here, we failed to acquire the lock, so we need to wait for the model to be downloaded to
        # cache by another process or download it ourselves.
        return FastTextOperator._wait_for_cache_or_download_model(
            model_file, success_file, source, is_hf
        )

    @staticmethod
    def _wait_for_cache_or_download_model(
        model_file: str,
        success_file: str,
        source: str,
        is_hf: bool,
        timeout_threshold: int = 5,
    ) -> Optional[fasttext.FastText._FastText]:
        total_sleep = 0
        while not os.path.exists(success_file) and total_sleep <= timeout_threshold:
            time.sleep(1)
            logger.warning(f"Waiting for model to download. Total sleep: {total_sleep}")
            total_sleep += 1

        if os.path.exists(success_file):
            return fasttext.load_model(model_file)

        logger.warning(
            f"Failed waiting for model to be downloaded to cache. Will download to temp file."
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_model_file = os.path.join(temp_dir, "model.bin")
            if FastTextOperator._download_from_path(source, temp_model_file, is_hf):
                return fasttext.load_model(temp_model_file)
            return None


def _acquire_lock(lock_file):
    fd = os.open(lock_file, os.O_WRONLY | os.O_CREAT)

    try:
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print(f"Lock acquired on {lock_file}")
        return fd
    except IOError:
        # Another process has the lock
        print(f"Unable to acquire lock on {lock_file}. Another process has it.")
        os.close(fd)
        return None


def _release_lock(fd, lock_file):
    fcntl.lockf(fd, fcntl.LOCK_UN)
    os.close(fd)
    print(f"Lock released on {lock_file}")


def download_file(url, filename):
    response = requests.get(url)
    response.raise_for_status()

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "wb") as file:
        file.write(response.content)
    print(f"File '{filename}' has been downloaded successfully.")
