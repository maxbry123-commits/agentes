import logging
import os
import random
from typing import Generator

import fsspec
import gcsfs
import ray
from datasets import load_from_disk


def load_dataset_from_fs(
    output_dir: str,
    dataset_id: str,
    fs: fsspec.AbstractFileSystem,
    seed: int = 42,
    max_shard: int = 0,
    shuffle: bool = False,
) -> Generator[ray.ObjectRef, None, None]:
    """Load a dataset from the filesystem.

    Args:
        output_dir (str): The directory containing the dataset
        dataset_id (str): The ID of the dataset to load
        fs (fsspec.AbstractFileSystem): The filesystem to use
        seed (int): Random seed for reproducibility
        max_shard (int): The maximum number of shards to load. If 0, all shards are loaded.

    Yields:
        ray.ObjectRef: References to loaded dataset shards
    """
    path = f"{output_dir}/{dataset_id}"
    print(f"Loading dataset from {path}")

    # List all files/directories in the path
    contents = fs.listdir(path)

    # Extract shard indices and sort
    shard_paths = []
    for item in contents:
        if item["name"].endswith("info.json"):
            continue
        full_path = (
            f"gs://{item['name']}"
            if isinstance(fs, gcsfs.GCSFileSystem)
            else item["name"]
        )
        shard_idx = int(full_path.split("/")[-1])
        shard_paths.append((shard_idx, full_path))

    # Sort by shard index
    shard_paths.sort(key=lambda x: x[0])

    if shuffle:
        random.seed(seed)
        random.shuffle(shard_paths)

    if max_shard > 0:
        shard_paths = shard_paths[:max_shard]

    # Load and yield datasets in sorted order
    for _, dataset_path in shard_paths:
        logging.warning(f"Attempt to load from {dataset_path}")
        dataset = (
            ray.remote(load_from_disk)
            .options(num_cpus=0.1)
            .remote(
                dataset_path,
                storage_options={"open": fs.open},
                keep_in_memory=(os.environ.get("IS_REMOTE", "0") == "1"),
            )
        )
        yield dataset
