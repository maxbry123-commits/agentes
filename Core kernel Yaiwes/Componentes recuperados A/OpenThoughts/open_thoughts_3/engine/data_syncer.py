import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import gcsfs
from google.cloud import storage


class _DataSyncer:
    def __init__(self, local_dir: str, remote_dir: str):
        self._local_dir = local_dir
        self._remote_dir = remote_dir.replace("gs://", "")  # Remove gs:// prefix
        self._bucket_name = self._remote_dir.split("/")[0]
        self._remote_prefix = "/".join(self._remote_dir.split("/")[1:])
        self._local_mtimes = {}
        self._remote_mtimes = {}
        self._gcs_fs = gcsfs.GCSFileSystem()
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _download_from_remote(self):
        """
        Perform initial sync by scanning both directories and downloading newer files
        from remote to local.
        """
        # Get remote files recursively using find
        remote_files = self._get_remote_files()
        local_files = self._get_local_files()

        if len(remote_files) != 0:
            # Count files per subdirectory and pattern
            subdir_counts = {}
            pattern_counts = {
                "responses": [],
                "requests": [],
                "batch_objects": [],
                "arrow_files": [],
                "metadata": [],
                "other": [],
            }

            for remote_file in remote_files:
                # Directory counting
                parent_dir = os.path.dirname(remote_file)
                if parent_dir:
                    subdir_counts[parent_dir] = subdir_counts.get(parent_dir, 0) + 1

                # Pattern matching
                filename = os.path.basename(remote_file)
                if filename.startswith("responses") and filename.endswith(".jsonl"):
                    pattern_counts["responses"].append(remote_file)
                elif filename.startswith("requests") and filename.endswith(".jsonl"):
                    pattern_counts["requests"].append(remote_file)
                elif filename.startswith("batch_objects") and filename.endswith(
                    ".jsonl"
                ):
                    pattern_counts["batch_objects"].append(remote_file)
                elif filename.endswith(".arrow"):
                    pattern_counts["arrow_files"].append(remote_file)
                elif filename.startswith("metadata"):
                    pattern_counts["metadata"].append(remote_file)
                else:
                    pattern_counts["other"].append(remote_file)

            logging.info(
                f"=-=-=-=-=-=- EXISTING FILES IN REMOTE CURATOR CACHE -=-=-=-=-=-= found {len(remote_files)}"
            )
            for subdir, count in subdir_counts.items():
                # Count patterns for this specific directory
                dir_patterns = {
                    "responses": len(
                        [f for f in pattern_counts["responses"] if f.startswith(subdir)]
                    ),
                    "requests": len(
                        [f for f in pattern_counts["requests"] if f.startswith(subdir)]
                    ),
                    "batch_objects": len(
                        [
                            f
                            for f in pattern_counts["batch_objects"]
                            if f.startswith(subdir)
                        ]
                    ),
                    "arrow_files": len(
                        [
                            f
                            for f in pattern_counts["arrow_files"]
                            if f.startswith(subdir)
                        ]
                    ),
                    "metadata": len(
                        [f for f in pattern_counts["metadata"] if f.startswith(subdir)]
                    ),
                    "other": len(
                        [f for f in pattern_counts["other"] if f.startswith(subdir)]
                    ),
                }
                # Create pattern breakdown string (only including non-zero counts)
                pattern_breakdown = ", ".join(
                    f"{pattern}: {count}"
                    for pattern, count in dir_patterns.items()
                    if count > 0
                )
                logging.info(f"  {subdir}: {count} files ({pattern_breakdown})")
        all_files = remote_files.union(local_files)

        def download_single_file(path: str):
            remote_mtime = self._get_remote_mtime(path)
            local_mtime = self._get_local_mtime(path)

            # Download remote file if it's newer or local doesn't exist
            if remote_mtime and (not local_mtime or remote_mtime > local_mtime):
                local_path = os.path.join(self._local_dir, path)
                remote_path = os.path.join(self._remote_dir, path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                self._gcs_fs.get(remote_path, local_path)
                local_mtime = self._get_local_mtime(path)

            if local_mtime:
                self._local_mtimes[path] = local_mtime

            if remote_mtime:
                self._remote_mtimes[path] = remote_mtime

        # Process files in parallel using ThreadPoolExecutor
        list(self._executor.map(download_single_file, all_files))

    def _get_remote_mtime(self, path: str) -> Optional[int]:
        """Get remote file modification time or None if file doesn't exist."""
        try:
            client = storage.Client()
            bucket = client.bucket(self._bucket_name)
            remote_path = os.path.join(self._remote_dir, path)
            blob_path = str(Path(remote_path).relative_to(self._bucket_name))
            blob = bucket.blob(blob_path)
            if not blob.exists():
                return None
            blob.reload()
            if blob.updated:
                return blob.updated.timestamp()
            else:
                return None
        except FileNotFoundError:
            return None

    def _get_local_mtime(self, path: str) -> Optional[float]:
        """Get local file modification time or None if file doesn't exist."""
        try:
            local_path = os.path.join(self._local_dir, path)
            return os.path.getmtime(local_path)
        except FileNotFoundError:
            return None

    def _sync_file(self, path: str) -> None:
        """Sync a single file between local and remote storage."""
        remote_mtime = self._get_remote_mtime(path)
        local_mtime = self._get_local_mtime(path)
        prev_local_mtime = self._local_mtimes.get(path, None)
        prev_remote_mtime = self._remote_mtimes.get(path, None)

        local_file_changed = (
            local_mtime and prev_local_mtime and local_mtime > prev_local_mtime
        ) or (local_mtime and not prev_local_mtime)
        remote_file_changed = (
            remote_mtime and prev_remote_mtime and remote_mtime > prev_remote_mtime
        ) or (remote_mtime and not prev_remote_mtime)

        if local_file_changed:
            if remote_file_changed:
                logging.warning(
                    f"Potential concurrent modification detected for file {path} since the remote file has changed without our modification. "
                    f"Local file was modified at {local_mtime} and remote file was modified at {remote_mtime}. Will not overwrite remote file."
                )
                return

            local_path = os.path.join(self._local_dir, path)
            remote_path = os.path.join(self._remote_dir, path)

            client = storage.Client()
            bucket = client.bucket(self._bucket_name)
            blob_path = str(Path(remote_path).relative_to(self._bucket_name))
            blob = bucket.blob(blob_path)

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    blob.upload_from_filename(local_path)
                    self._remote_mtimes[path] = self._get_remote_mtime(path)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        logging.error(
                            f"Failed to sync {local_path} after {max_retries} attempts: {e}"
                        )
                        raise
                    time.sleep(1)  # Exponential backoff

        self._local_mtimes[path] = self._get_local_mtime(path)
        self._remote_mtimes[path] = self._get_remote_mtime(path)

    def _scan_and_sync(self):
        """Scan both directories and sync all files."""
        remote_files = self._get_remote_files()
        local_files = self._get_local_files()

        all_files = remote_files.union(local_files)

        # Process files in parallel using ThreadPoolExecutor
        list(self._executor.map(self._sync_file, all_files))

    def _get_local_files(self):
        local_files = set()
        for root, _, files in os.walk(self._local_dir):
            for file in files:
                if file == "metadata.db":
                    continue
                full_path = os.path.join(root, file)
                local_files.add(str(Path(full_path).relative_to(self._local_dir)))
        return local_files

    def _get_remote_files(self):
        gs_paths = self._gcs_fs.find(self._remote_dir)
        return set(
            [
                str(Path(path).relative_to(self._remote_dir))
                for path in gs_paths
                if "metadata.db" not in path
            ]
        )
