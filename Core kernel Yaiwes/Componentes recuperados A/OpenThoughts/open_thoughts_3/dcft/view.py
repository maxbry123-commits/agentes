import argparse
import json
import os
import random

import gcsfs
from datasets import load_from_disk

from dcft.data_strategies.synthetic_data_manager import (
    HashCodeHelper,
    SyntheticDataManager,
)

# Constants for remote access
REMOTE_OUTPUT_DIR = "gs://dcft-data-gcp/datasets-cache"
GCS_PROJECT = "bespokelabs"
GCS_CREDENTIALS = "dcft/service_account_credentials.json"


def get_filesystem(remote: bool = False):
    """Get the appropriate filesystem based on whether we're accessing remote or local data"""
    if remote:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCS_CREDENTIALS
        return gcsfs.GCSFileSystem(project=GCS_PROJECT)
    return None


def print_first_n_rows(dataset, n=5):
    """
    Pretty-print the first n rows from a dataset.

    Args:
        dataset: Hugging Face dataset
        n (int): Number of rows to print
    """
    if len(dataset) == 0:
        return
    if len(dataset) < n:
        n = len(dataset)
    if n == 1:
        print(json.dumps(dataset[0], indent=2))
        return

    print(f"\nRandom consecutive {n} rows of the dataset:")
    random.seed(42)
    i = random.randint(0, len(dataset) - n - 1)
    for i in range(i, i + n):
        print(f"\nRow {i+1}:")
        print(json.dumps(dataset[i], indent=2))


def load_dataset(output_dir, hash_id, num_rows, remote: bool = False):
    """
    Load a dataset from either local filesystem or GCS.

    Args:
        output_dir: Base directory containing the dataset
        hash_id: Hash ID of the dataset to load
        num_rows: Number of rows to print
        remote: Whether to load from remote GCS storage
    """
    # Look for the first shard
    dataset_path = os.path.join(output_dir, hash_id, "0")
    fs = get_filesystem(remote)

    try:
        print(f"Loading dataset from {dataset_path}")

        if remote:
            # Check if the dataset exists in GCS
            if not fs.exists(dataset_path):
                print(f"Dataset not found at {dataset_path}")
                return

            # Load from GCS using the GCS filesystem
            dataset = load_from_disk(dataset_path, storage_options={"open": fs.open})
        else:
            # Load from local filesystem
            dataset = load_from_disk(dataset_path)

        print(f"Dataset has {len(dataset)} rows")
        print_first_n_rows(dataset, int(num_rows))

    except Exception as e:
        print(f"Error loading dataset: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="View rows from a Hugging Face dataset"
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        help="Base directory containing the dataset",
        default="./datasets",
    )
    parser.add_argument("-n", "--num_rows", help="Number of rows to print", default=5)
    parser.add_argument("--hash", help="Hash ID of the dataset")
    parser.add_argument(
        "--framework", help="View each step in a framework", default=None
    )
    parser.add_argument(
        "--remote", action="store_true", help="Load from remote GCS storage"
    )
    parser.add_argument(
        "--dev", help="View the development dataset", action="store_true"
    )
    parser.add_argument(
        "--links-only",
        help="Only show links to the datasets with --remote",
        action="store_true",
    )

    args = parser.parse_args()

    # If remote flag is set, use the remote output directory
    output_dir = REMOTE_OUTPUT_DIR if args.remote else args.output_dir

    if args.hash:
        load_dataset(output_dir, args.hash, args.num_rows, remote=args.remote)

    elif args.framework:
        print("Mapping of op_id to operator_hash:")
        manager = SyntheticDataManager()
        manager.parsed_yamls = set()
        framework_path = manager.frameworks.get(args.framework, None)
        if framework_path is None:
            raise ValueError(f"Framework '{args.framework}' not found.")
        manager.from_config(framework_path)
        sorted_ops = manager.dag.topological_sort()
        hasher = HashCodeHelper()
        map_op_id_to_dag_hash = manager.dag.calculate_operator_hashes(
            sorted_ops, hasher
        )
        for op_id, dag_hash in map_op_id_to_dag_hash.items():
            print(f"{op_id} -> {dag_hash}")
            if args.links_only and args.remote:
                print(
                    f"https://console.cloud.google.com/storage/browser/{REMOTE_OUTPUT_DIR[5:]}/{dag_hash}"
                )
            else:
                load_dataset(output_dir, dag_hash, args.num_rows, remote=args.remote)


if __name__ == "__main__":
    main()
