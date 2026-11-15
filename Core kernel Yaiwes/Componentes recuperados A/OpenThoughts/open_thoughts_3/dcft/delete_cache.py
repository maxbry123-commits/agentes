import argparse
import os
from typing import Dict, List

import gcsfs

from dcft.data_strategies.synthetic_data_manager import (
    HashCodeHelper,
    SyntheticDataManager,
)

# Constants for remote access
REMOTE_OUTPUT_DIR = "gs://dcft-data-gcp/datasets-cache"
GCS_PROJECT = "bespokelabs"
GCS_CREDENTIALS = "dcft/service_account_credentials.json"


def get_filesystem():
    """Get the GCS filesystem"""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCS_CREDENTIALS
    return gcsfs.GCSFileSystem(project=GCS_PROJECT)


def delete_cache_directory(hash_id: str) -> bool:
    """Delete a specific cache directory"""
    fs = get_filesystem()
    full_path = os.path.join(REMOTE_OUTPUT_DIR, hash_id).replace("gs://", "")

    try:
        if fs.exists(full_path):
            fs.rm(full_path, recursive=True)
            print(f"Successfully deleted cache directory: {hash_id}")
            return True
        else:
            print(f"Cache directory not found: {hash_id}")
            return False
    except Exception as e:
        print(f"Error deleting directory {hash_id}: {e}")
        return False


def get_framework_hashes(framework: str) -> dict:
    """Get all hashes associated with a framework"""
    manager = SyntheticDataManager()
    manager.parsed_yamls = set()
    framework_path = manager.frameworks.get(framework, None)
    if framework_path is None:
        raise ValueError(f"Framework '{framework}' not found.")

    manager.from_config(framework_path)
    sorted_ops = manager.dag.topological_sort()
    hasher = HashCodeHelper()
    return manager.dag.calculate_operator_hashes(sorted_ops, hasher)


def display_menu(op_id_to_hash: Dict[str, str], selected: set) -> None:
    """Display the interactive menu"""
    print("\nSelect cache directories to delete:")
    print("Enter numbers (comma-separated) to toggle selection")
    print(
        "Commands: 'd' to delete selected, 'a' to select all, 'n' to select none, 'q' to quit\n"
    )

    for i, (op_id, hash_id) in enumerate(op_id_to_hash.items(), 1):
        mark = "X" if i in selected else " "
        print(f"[{mark}] {i}. {op_id}: {hash_id}")


def interactive_delete(op_id_to_hash: Dict[str, str]) -> None:
    """Interactive menu for selecting which caches to delete"""
    # Start with everything selected
    selected = set(range(1, len(op_id_to_hash) + 1))

    while True:
        display_menu(op_id_to_hash, selected)
        choice = input("\nEnter choice: ").lower().strip()

        if choice == "q":
            print("Operation cancelled")
            return

        elif choice == "d":
            if not selected:
                print("No items selected")
                continue

            # Convert to list for stable ordering
            items = list(op_id_to_hash.items())
            selected_ops = [items[i - 1][0] for i in selected]
            selected_hashes = [items[i - 1][1] for i in selected]

            print("\nYou selected the following operations for deletion:")
            for op_id in selected_ops:
                print(f"- {op_id}")

            # Double confirmation for deletion
            confirm = input(
                "\nAre you sure you want to delete these cache directories? Type 'yes' to confirm: "
            )
            if confirm.lower() == "yes":
                for i, (op_id, hash_id) in enumerate(
                    zip(selected_ops, selected_hashes)
                ):
                    print(f"\nDeleting cache for {op_id} ({i+1}/{len(selected_ops)}):")
                    delete_cache_directory(hash_id)
                print("\nSelected cache directories have been deleted")
            else:
                print("Deletion cancelled. Returning to menu...")
                continue
            return

        elif choice == "a":
            selected = set(range(1, len(op_id_to_hash) + 1))

        elif choice == "n":
            selected.clear()

        else:
            # Handle comma-separated list of numbers
            try:
                numbers = [int(x.strip()) for x in choice.split(",")]
                valid_numbers = [n for n in numbers if 1 <= n <= len(op_id_to_hash)]

                if not valid_numbers:
                    print("No valid numbers entered")
                    continue

                # Toggle each number in the list
                for num in valid_numbers:
                    if num in selected:
                        selected.remove(num)
                    else:
                        selected.add(num)

            except ValueError:
                print(
                    "Invalid input. Enter numbers separated by commas or a command (d/a/n/q)"
                )


def main():
    parser = argparse.ArgumentParser(
        description="Delete cache directories for a framework"
    )
    parser.add_argument(
        "--framework", help="Framework name whose cache directories should be deleted"
    )
    args = parser.parse_args()

    try:
        op_id_to_hash = get_framework_hashes(args.framework)
        print(
            f"\nFound {len(op_id_to_hash)} cache directories for framework '{args.framework}'"
        )
        interactive_delete(op_id_to_hash)
    except ValueError as e:
        print(str(e))


if __name__ == "__main__":
    main()
