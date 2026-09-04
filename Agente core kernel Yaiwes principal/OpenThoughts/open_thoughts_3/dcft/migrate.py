import argparse
import logging
import os
from collections import defaultdict
from enum import Enum
from typing import Optional, Tuple

import gcsfs
import psycopg
from psycopg.types.json import Jsonb
from tqdm import tqdm

from dcft.data_strategies.synthetic_data_manager import (
    HashCodeHelper,
    SyntheticDataManager,
)


def setup_logger(log_level: str = "INFO"):
    """
    Configure logger with formatting

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Prevent duplicate logging by disabling propagation to root logger
    logger = logging.getLogger(__name__)
    logger.propagate = False

    formatter = logging.Formatter(fmt="%(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove any existing handlers to avoid duplicate logs
    for old_handler in logger.handlers[:-1]:
        logger.removeHandler(old_handler)

    return logger


logger = setup_logger("INFO")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "dcft/service_account_credentials.json"
output_dir = f"gs://dcft-data-gcp/datasets-cache"
db_connection_string = (
    "postgresql://postgres:t%7DLQ7ZL%5D3%24x~I8ye@35.225.163.235:5432/postgres"
)
fs = gcsfs.GCSFileSystem(project="bespokelabs")

old_table_name = "datasets_backup_20241118"
new_table_name = "datasets"


class MigrationStatus(Enum):
    SUCCESS = "SUCCESS"  # Successfully migrated
    ALREADY_VALID = (
        "ALREADY_VALID"  # Hash already valid in both filesystem and database
    )
    DATASET_NAME_NOT_FOUND = (
        "DATASET_NAME_NOT_FOUND"  # Couldn't find dataset name in DB
    )
    NO_COMPLETED_VERSION = "NO_COMPLETED_VERSION"  # No completed version found in DB
    OLD_HASH_INVALID = "OLD_HASH_INVALID"  # Old hash exists in DB but not in GCS
    DB_ERROR = "DB_ERROR"  # Database connection/query error
    COPY_ERROR = "COPY_ERROR"  # Error copying directory from old hash to new hash


def get_dataset_name_by_hash(
    db_connection_string: str, hash_id: str
) -> Tuple[Optional[str], Optional[MigrationStatus]]:
    """
    Query the database to get the dataset name matching a generation hash.

    Returns:
        Tuple[Optional[str], Optional[MigrationStatus]]: (dataset_name, status) pair
    """
    try:
        with psycopg.connect(db_connection_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT name
                    FROM public.{new_table_name}
                    WHERE data_generation_hash LIKE %s
                        AND data_generation_hash IS NOT NULL
                    LIMIT 1
                    """,
                    (f"%{hash_id}%",),
                )
                result = cursor.fetchone()
                if result:
                    return result[0], None
                return None, MigrationStatus.DATASET_NAME_NOT_FOUND

    except Exception as e:
        logger.error(f"Database error while querying hash {hash_id}: {e}")
        return None, MigrationStatus.DB_ERROR


def get_latest_completed_dataset_matching_name(
    db_connection_string: str, dataset_name: str, new_hash_id: str
) -> Tuple[Optional[str], Optional[MigrationStatus]]:
    """
    Query both old and new database tables to get the latest completed dataset hash matching a name.

    Returns:
        Tuple[Optional[str], Optional[MigrationStatus]]: (hash_id, status) pair
    """
    try:
        with psycopg.connect(db_connection_string) as conn:
            with conn.cursor() as cursor:
                # Query both tables and union the results
                cursor.execute(
                    f"""
                    SELECT data_generation_hash, generation_end, 'new' as source
                    FROM public.{new_table_name}
                    WHERE name = %s
                        AND generation_status = 'COMPLETED'
                        AND data_generation_hash IS NOT NULL
                        AND data_generation_hash != %s
                    UNION ALL
                    SELECT data_generation_hash, generation_end, 'old' as source
                    FROM public.{old_table_name}
                    WHERE name = %s
                        AND generation_status = 'COMPLETED'
                        AND data_generation_hash IS NOT NULL
                        AND data_generation_hash != %s
                    ORDER BY generation_end DESC
                    LIMIT 1
                    """,
                    (dataset_name, new_hash_id, dataset_name, new_hash_id),
                )
                result = cursor.fetchone()
                if result:
                    hash_id, _, source = result
                    logger.debug(
                        f"Found hash {hash_id} in {source} table for {dataset_name}"
                    )
                    if hash_id is None:
                        return None, MigrationStatus.NO_COMPLETED_VERSION
                    return hash_id, None
                return None, MigrationStatus.NO_COMPLETED_VERSION

    except Exception as e:
        logger.error(f"Database error while querying dataset {dataset_name}: {e}")
        return None, MigrationStatus.DB_ERROR


def check_hash_validity(hash_id: str) -> Tuple[bool, Optional[MigrationStatus]]:
    """
    Check if a hash is valid by verifying both filesystem and database state.

    Returns:
        Tuple[bool, Optional[MigrationStatus]]: (is_valid, status) pair
    """
    # Check filesystem
    operator_cache_directory = os.path.join(output_dir, hash_id)
    success_file_path = os.path.join(operator_cache_directory, "SUCCESS_FLAG")

    if not fs.exists(success_file_path):
        return False, None  # Not a failure, just needs migration

    # Check both database tables
    try:
        with psycopg.connect(db_connection_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT generation_status
                    FROM public.{new_table_name}
                    WHERE data_generation_hash = %s
                    LIMIT 1
                    """,
                    (hash_id,),
                )
                result = cursor.fetchone()
                if result:
                    (status,) = result
                    if status == "COMPLETED":
                        logger.debug(
                            f"Found completed status in new table for hash {hash_id}"
                        )
                        return True, None

                return False, None  # Not a failure, just needs migration

    except Exception as e:
        logger.error(f"Database error while checking hash validity: {e}")
        return False, MigrationStatus.DB_ERROR


def copy_dataset_entry(
    old_hash: str, new_hash: str
) -> Tuple[bool, Optional[MigrationStatus]]:
    """
    Copy dataset entry from old hash to new hash in the database.
    Looks in both old and new tables for the source data.

    Returns:
        Tuple[bool, Optional[MigrationStatus]]: (success, status) pair
    """
    try:
        with psycopg.connect(db_connection_string) as conn:
            with conn.cursor() as cursor:
                # First, check both tables for the old hash
                cursor.execute(
                    f"""
                    SELECT 
                        name, generation_parameters, generation_status,
                        row_count, hf_link, hf_fingerprint, hf_commit_hash,
                        created_by, creation_location, dataset_type, 
                        is_external, git_commit_hash, git_diff, is_final,
                        'new' as source
                    FROM public.{new_table_name}
                    WHERE data_generation_hash = %s
                        AND generation_status = 'COMPLETED'
                    UNION ALL
                    SELECT 
                        name, generation_parameters, generation_status,
                        row_count, hf_link, hf_fingerprint, hf_commit_hash,
                        created_by, creation_location, dataset_type,
                        is_external, git_commit_hash, git_diff, is_final,
                        'old' as source
                    FROM public.{old_table_name}
                    WHERE data_generation_hash = %s
                        AND generation_status = 'COMPLETED'
                    ORDER BY source ASC  -- Prefer new table over old
                    LIMIT 1
                    """,
                    (old_hash, old_hash),
                )
                result = cursor.fetchone()
                if not result:
                    return False, MigrationStatus.NO_COMPLETED_VERSION

                (
                    name,
                    gen_params,
                    _,
                    row_count,
                    hf_link,
                    hf_fingerprint,
                    hf_commit_hash,
                    created_by,
                    creation_location,
                    dataset_type,
                    is_external,
                    git_commit_hash,
                    git_diff,
                    is_final,
                    source,
                ) = result

                logger.debug(f"Found source data in {source} table for hash {old_hash}")

                # Insert new entry with updated hash
                cursor.execute(
                    f"""
                    INSERT INTO public.{new_table_name} (
                        id, name, generation_parameters, generation_status,
                        data_generation_hash, row_count, hf_link, hf_fingerprint,
                        hf_commit_hash, creation_time, last_modified,
                        created_by, creation_location, dataset_type,
                        is_external, git_commit_hash, git_diff, is_final
                    )
                    VALUES (
                        gen_random_uuid(), %s, %s, 'COMPLETED',
                        %s, %s, %s, %s, %s,
                        NOW(), NOW(),
                        %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    """,
                    (
                        name,
                        Jsonb(gen_params),
                        new_hash,
                        row_count,
                        hf_link,
                        hf_fingerprint,
                        hf_commit_hash,
                        created_by,
                        creation_location,
                        dataset_type,
                        is_external,
                        git_commit_hash,
                        git_diff,
                        is_final,
                    ),
                )
                conn.commit()
                return True, None

    except Exception as e:
        logger.error(f"Database error while copying dataset entry: {e}")
        return False, MigrationStatus.DB_ERROR


def migrate_old_to_new(
    new_hash_id: str, old_hash_id: str, dataset_name: str, apply: bool = False
) -> Tuple[bool, Optional[MigrationStatus]]:
    """
    Migrate dataset from old hash to new hash, including both filesystem and database.

    Args:
        new_hash_id: Hash to migrate to
        old_hash_id: Hash to migrate from
        dataset_name: Name of the dataset
        apply: Whether to actually perform the migration or just simulate
    """
    old_hash_directory = os.path.join(output_dir, old_hash_id)
    success_file_path = os.path.join(old_hash_directory, "SUCCESS_FLAG")

    # Is the old hash valid?
    if not fs.exists(success_file_path):
        logger.error(f"[FAIL] {dataset_name}: Old hash invalid or missing success flag")
        return False, MigrationStatus.OLD_HASH_INVALID

    logger.info(f"[{'MIGRATE' if apply else 'DRY-RUN'}] {dataset_name}:")
    logger.info(f"         From: {old_hash_id}")
    logger.info(f"         To:   {new_hash_id}")

    if not apply:
        return True, MigrationStatus.SUCCESS

    # Copy filesystem data
    new_hash_directory = os.path.join(output_dir, new_hash_id)
    try:
        fs.rm(new_hash_directory, recursive=True)
        fs.copy(
            os.path.join(old_hash_directory, "*"), new_hash_directory, recursive=True
        )
    except Exception as e:
        logger.error(f"[FAIL] {dataset_name}: Error copying directory: {e}")
        return False, MigrationStatus.COPY_ERROR

    # Copy database entry
    success, failure_reason = copy_dataset_entry(old_hash_id, new_hash_id)
    if not success:
        logger.error(f"[FAIL] {dataset_name}: Error copying database entry")
        return False, failure_reason

    logger.info(f"[SUCCESS] {dataset_name}: Migration completed")
    return True, MigrationStatus.SUCCESS


def migrate_dataset(
    new_hash_id: str, op_id: str, apply: bool = False
) -> Tuple[bool, Optional[MigrationStatus]]:
    """
    Attempt to migrate a dataset.

    Args:
        new_hash_id: Hash to migrate to
        op_id: Operator ID
        apply: Whether to actually perform the migration or just simulate

    Returns:
        Tuple[bool, Optional[MigrationStatus]]: (success, status) pair
    """
    # Check if new hash is already valid
    is_valid, failure_reason = check_hash_validity(new_hash_id)
    if failure_reason:
        return False, failure_reason
    if is_valid:
        logger.debug(f"[SKIP] {op_id}: Hash already valid")
        return True, MigrationStatus.ALREADY_VALID

    logger.debug(f"[{'MIGRATE' if apply else 'DRY-RUN'}] {op_id}: Hash needs migration")

    # Get old hash
    old_hash_id, failure_reason = get_latest_completed_dataset_matching_name(
        db_connection_string, op_id, new_hash_id
    )
    if old_hash_id is None:
        logger.debug(f"[FAIL] {op_id}: {failure_reason.value}")
        return False, failure_reason

    return migrate_old_to_new(new_hash_id, old_hash_id, op_id, apply)


def print_summary(failures_by_reason: dict, success_count: int, total_count: int):
    """Pretty print the migration summary"""
    separator = "=" * 80

    logger.info(f"\n{separator}")
    logger.info(f"{'Migration Summary':^80}")
    logger.info(separator)

    success_percentage = (success_count / total_count) * 100 if total_count > 0 else 0
    logger.info(
        f"\nSuccessfully migrated: {success_count}/{total_count} ({success_percentage:.1f}%)"
    )

    if total_count - success_count > 0:
        logger.info("\nStatus breakdown:")
        for status, affected_ids in failures_by_reason.items():
            if status != MigrationStatus.SUCCESS:
                count = len(affected_ids)
                percentage = (count / total_count) * 100
                logger.info(f"\n{status.value} ({count} datasets - {percentage:.1f}%):")
                for affected_id in sorted(affected_ids):  # Sort for consistent output
                    logger.info(f"  • {affected_id}")

    logger.info(f"\n{separator}\n")


def main():
    parser = argparse.ArgumentParser(description="Migrate a dataset")
    parser.add_argument("--hash", help="Hash ID of the dataset")
    parser.add_argument(
        "--framework", help="View each step in a framework", default=None
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually perform the migration (default is dry-run)",
    )

    args = parser.parse_args()

    # Print mode banner
    mode_str = "MIGRATION MODE" if args.apply else "DRY-RUN MODE"
    separator = "=" * 80
    logger.info(f"\n{separator}")
    logger.info(f"{mode_str:^80}")
    logger.info(f"{separator}\n")

    if not args.apply:
        logger.info(
            "Running in dry-run mode. Use --apply to actually perform the migrations.\n"
        )

    if args.hash:
        success, status = migrate_dataset(
            args.hash, "single_hash_migration", apply=args.apply
        )
        if not success:
            logger.error(f"Migration failed with status: {status.value}")
        else:
            logger.info(f"Migration completed with status: {status.value}")

    elif args.framework:
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

        # Track status counts
        status_by_id = defaultdict(set)
        success_count = 0
        total_count = 0

        logger.info(f"Starting migration for framework: {args.framework}")
        for op_id, dag_hash in tqdm(
            map_op_id_to_dag_hash.items(),
            total=len(map_op_id_to_dag_hash),
            desc=f"{'Migrating' if args.apply else 'Checking'} datasets",
            unit="dataset",
        ):
            success, status = migrate_dataset(dag_hash, op_id, apply=args.apply)
            if success:
                success_count += 1
                status_by_id[status].add(op_id)
            else:
                status_by_id[status].add(op_id)
            total_count += 1

        print_summary(status_by_id, success_count, total_count)


if __name__ == "__main__":
    main()
