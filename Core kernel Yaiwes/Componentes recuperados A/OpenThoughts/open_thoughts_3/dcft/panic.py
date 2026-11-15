import argparse
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

from google.cloud import storage
from openai import OpenAI

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "dcft/service_account_credentials.json"

# TODO make this run based off a framework so you can do `python -m dcft.panic --framework <framework> --dev/--remote`


# PANIC! You submitted too many batches. No worries, just cancel them. Include a `framework__operatorid` pattern to narrow down the search.
# usage: python dcft/panic.py --path gs://dcft-data-gcp/curator-cache/ --pattern alpaca_gpt-4o-mini__
def parse_args():
    parser = argparse.ArgumentParser(
        description="Cancel OpenAI batches from a local JSONL file or GCS path"
    )
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Path to batch_objects.jsonl file or GCS directory containing batch_objects.jsonl files",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Optional pattern to filter paths (only process files containing this pattern)",
    )
    return parser.parse_args()


def is_gcs_path(path: str) -> bool:
    return path.startswith("gs://")


def parse_gcs_path(path: str) -> Tuple[str, str]:
    # Remove gs:// prefix and split into bucket and path
    path = path.replace("gs://", "")
    bucket_name = path.split("/")[0]
    prefix = "/".join(path.split("/")[1:])
    return bucket_name, prefix


def find_batch_objects_files(
    bucket_name: str, folder_prefix: str, pattern: Optional[str] = None
) -> List[str]:
    """Find all batch_objects.jsonl files in the specified GCS folder"""
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)

    if not folder_prefix.endswith("/"):
        folder_prefix += "/"

    blobs = bucket.list_blobs(prefix=folder_prefix)

    matching_files = []
    for blob in blobs:
        filename = blob.name.split("/")[-1]
        if filename == "batch_objects.jsonl":
            full_path = f"gs://{bucket_name}/{blob.name}"
            if pattern is None or pattern in full_path:
                matching_files.append(full_path)

    return matching_files


def download_gcs_file(gcs_path: str) -> str:
    """Download a GCS file to a temporary location and return the local path"""
    client = storage.Client()
    bucket_name, blob_path = parse_gcs_path(gcs_path)
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
    temp_path = temp_file.name
    temp_file.close()

    # Download to temporary file
    blob.download_to_filename(temp_path)
    return temp_path


def cancel_single_batch(client: OpenAI, batch_id: str) -> Tuple[str, Optional[str]]:
    """Cancel a single batch and return the result"""
    try:
        client.batches.cancel(batch_id)
        print(f"Successfully cancelled batch: {batch_id}")
        return (batch_id, None)  # None indicates success
    except Exception as e:
        error_msg = str(e)
        print(f"Failed to cancel batch {batch_id}: {error_msg}")
        return (batch_id, error_msg)


def cancel_batches(batch_objects_file: str) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Cancel batches from a local JSONL file using parallel execution"""
    client = OpenAI()
    cancelled = []
    failed = []

    # Read all batch IDs first
    batch_ids = []
    with open(batch_objects_file, "r") as f:
        for line in f:
            batch_obj = json.loads(line.strip())
            batch_ids.append(batch_obj["id"])

    # Use ThreadPoolExecutor to cancel batches in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_batch = {
            executor.submit(cancel_single_batch, client, batch_id): batch_id
            for batch_id in batch_ids
        }

        # Process results as they complete
        for future in as_completed(future_to_batch):
            batch_id, error = future.result()
            if error is None:
                cancelled.append(batch_id)
            else:
                failed.append((batch_id, error))

    return cancelled, failed


def process_path(path: str, pattern: Optional[str] = None) -> None:
    """Process either a local file or GCS path"""
    temp_files = []
    all_cancelled = []
    all_failed = []

    try:
        if is_gcs_path(path):
            # If it's a directory, find all batch_objects.jsonl files
            if not path.endswith("batch_objects.jsonl"):
                bucket_name, prefix = parse_gcs_path(path)
                print(f"Searching for batch_objects.jsonl files in {path}")
                gcs_files = find_batch_objects_files(bucket_name, prefix, pattern)
                if not gcs_files:
                    print(
                        f"No matching batch_objects.jsonl files found in {path} based on pattern: {pattern}"
                    )
                    return

                for gcs_file in gcs_files:
                    print(f"\nProcessing {gcs_file}...")
                    temp_path = download_gcs_file(gcs_file)
                    temp_files.append(temp_path)
                    cancelled, failed = cancel_batches(temp_path)
                    all_cancelled.extend(cancelled)
                    all_failed.extend(failed)
            else:
                # Single GCS file
                if pattern is None or pattern in path:
                    temp_path = download_gcs_file(path)
                    temp_files.append(temp_path)
                    all_cancelled, all_failed = cancel_batches(temp_path)
                else:
                    print(f"Skipping {path} as it doesn't match pattern: {pattern}")
        else:
            # Local file
            if pattern is None or pattern in path:
                all_cancelled, all_failed = cancel_batches(path)
            else:
                print(f"Skipping {path} as it doesn't match pattern: {pattern}")

    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass

    # Print final summary
    print(f"\nFinal Summary:")
    print(f"Successfully cancelled: {len(all_cancelled)} batches")
    print(f"Failed to cancel: {len(all_failed)} batches")
    if all_failed:
        print("\nFailed batches:")
        for batch_id, error in all_failed:
            print(f"- {batch_id}: {error}")


def main():
    args = parse_args()
    process_path(args.path, args.pattern)


if __name__ == "__main__":
    main()
