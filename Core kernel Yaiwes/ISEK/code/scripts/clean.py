import os
import shutil


def remove_directory(path):
    """Remove a directory if it exists."""
    if os.path.exists(path):
        print(f"Removing directory: {path}")
        shutil.rmtree(path, ignore_errors=True)


def remove_file(path):
    """Remove a file if it exists."""
    if os.path.exists(path):
        print(f"Removing file: {path}")
        os.remove(path)


def main(root="."):
    unwanted_dirs = []

    # Walk the directory tree
    for dirpath, dirnames, filenames in os.walk(root):
        # Identify __pycache__ directories and directories ending with .egg-info
        for dirname in dirnames:
            full_path = os.path.join(dirpath, dirname)
            if dirname == "__pycache__" or dirname.endswith(".egg-info"):
                unwanted_dirs.append(full_path)

        # Remove any .pyc files
        for filename in filenames:
            if filename.endswith(".pyc"):
                file_path = os.path.join(dirpath, filename)
                remove_file(file_path)

    # Additionally, target top-level directories often created during builds
    for extra in ["build", "dist", "interfaces", "reports", "contracts"]:
        extra_path = os.path.join(root, extra)
        unwanted_dirs.append(extra_path)

    # Remove the collected directories
    for directory in unwanted_dirs:
        remove_directory(directory)


if __name__ == "__main__":
    main()
