import copy
import datetime
import json
import logging
import os
import subprocess
import time
import uuid
from itertools import tee
from pathlib import Path
from queue import Queue
from typing import Any, Dict, Iterator, List, Optional

import fsspec
import gcsfs
import huggingface_hub
import psycopg
import ray
from datasets import (
    Dataset,
    concatenate_datasets,
    disable_caching,
    load_dataset,
    load_from_disk,
)
from psycopg.types.json import Jsonb
from pydantic import ValidationError
from ray.job_submission import JobSubmissionClient

from dcft.data_strategies.yaml_utils import remove_prefix, walk_directory
from engine.dag import DAG, Operator
from engine.operators.function_operator import (
    FunctionOperator,
    FunctionOperatorConfig,
    AsyncFunctionOperatorConfig,
    GPUFunctionOperatorConfig,
    CPUFunctionOperatorConfig,
    GenericResourceFunctionOperatorConfig,
    HighMemoryFunctionOperatorConfig,
)
from engine.operators.hashing_utils import HashCodeHelper
from engine.operators.hf_upload_operator import HFUploadOperator, HFUploadOperatorConfig
from engine.operators.operator import (
    ExecutionContext,
    ManyShardRefsGenerator,
    OperatorConfig,
    ShardRef,
    create_operator,
    parse_specific_config,
    parse_yaml_config,
)

# Disable HF caching for remote runs. Otherwise, datasets will be unserializable for Ray
# and cause bugs when they're passed as refs.
if os.environ.get("IS_REMOTE", "0") == "1":
    disable_caching()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def flatten(nested_list: List[Any]) -> List[Any]:
    """
    Flatten a nested list structure.

    Args:
        nested_list (List[Any]): A list that may contain nested lists.

    Returns:
        List[Any]: A flattened version of the input list.
    """
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten(item))
        else:
            flat_list.append(item)
    return flat_list


def get_git_commit_hash():
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("ascii")
            .strip()
        )
    except subprocess.CalledProcessError:
        return None


def get_git_diff():
    try:
        staged_diff = subprocess.check_output(["git", "diff", "--staged"]).decode(
            "utf-8"
        )
        unstaged_diff = subprocess.check_output(["git", "diff"]).decode("utf-8")
        diff = f"===Staged changes===\n{staged_diff}\n===Unstaged changes===\n{unstaged_diff}"
    except subprocess.CalledProcessError:
        return None
    return diff


def _to_generator(iter: Iterator[ShardRef]) -> ManyShardRefsGenerator:
    """
    Convert an iterator to a generator.
    """
    yield from iter


class SyntheticDataManager:
    """
    A manager class for handling data frameworks or dataset handlers, outside of the data generation process itself.

    This class is responsible for loading, managing, and running various
    synthetic data generation frameworks based on YAML configurations.
    """

    def __init__(
        self,
        hf_account: str = None,
        output_dir: Optional[str] = None,
        fs_type: str = "file",
        hf_private: bool = True,
        ray_address: Optional[str] = None,
        no_return: bool = False,
        max_pending_waitables: int = 100,
        db_connection_string: Optional[str] = None,
        enable_cache: bool = False,
        log_level: str = "INFO",
        resume_from_partial: bool = False,
        wait_for_job_completion: bool = False,
    ):
        """
        Initialize the SyntheticDataManager.

        Args:
            hf_account (str): The Hugging Face account name.
            fs_type (str, optional): The filesystem type to use. Defaults to "file".
            ray_address (Optional[str], optional): The address of the Ray cluster. Defaults to None.
            no_return (bool, optional): Whether to not return data to the local machine. Defaults to False.
            max_pending_waitables (int, optional): The maximum number of waitables to wait on at once. Defaults to 100.
            db_connection_string (Optional[str], optional): The connection string for the PostgreSQL database. Defaults to None.
            enable_cache (bool, optional): Whether to enable caching. Defaults to False.
            log_level (str, optional): The log level to use. Defaults to "INFO".
            resume_from_partial (bool, optional): Whether to use existing shards in a partially completed operator's cache even if not fully finished
        """
        self.hf_account = hf_account
        self.hf_private = hf_private
        self.no_return = no_return
        self.fs_type = fs_type
        if fs_type != "gcs":
            self.fs = fsspec.filesystem(fs_type)
        else:
            self.fs = gcsfs.GCSFileSystem(project="bespokelabs")
        self.strategies_dir = os.path.dirname(os.path.abspath(__file__))
        self.frameworks = self._load_frameworks()
        self.ray_address = ray_address
        self.max_pending_waitables = max_pending_waitables
        self.output_dir = output_dir
        self.enable_cache = enable_cache

        self.db_connection_string = db_connection_string
        if self.db_connection_string:
            self.db_connection = psycopg.connect(self.db_connection_string)
        else:
            self.db_connection = None
        self.created_dataset_ids = []
        self.log_level = log_level
        self.resume_from_partial = resume_from_partial
        self.generation_start = datetime.datetime.now(datetime.timezone.utc)
        self.final_operator_loaded_from_cache = False
        self.wait_for_job_completion = wait_for_job_completion

    def list_frameworks(self) -> List[str]:
        """
        List all available framework names.

        Returns:
            List[str]: A list of all loaded framework names.
        """
        return list(self.frameworks.keys())

    def run_framework(self, framework_name: str, remote: bool = False) -> None:
        """
        Run a specific framework and push the generated dataset to Hugging Face Hub.

        Args:
            framework_name (str): The name of the framework to run.
            remote (bool, optional): Whether to run the framework on a remote Ray cluster. Defaults to False.
        """
        log_level = getattr(logging, self.log_level)

        framework_path = self.frameworks.get(framework_name, None)
        self.framework_name = framework_name
        self.parsed_yamls = set()
        if framework_path is None:
            raise ValueError(f"Framework '{framework_name}' not found.")

        logger.info(f"Running framework: {framework_name}")

        if remote:
            self.run_remote(framework_name)
        else:
            # https://docs.ray.io/en/latest/ray-observability/user-guides/configure-logging.html#customizing-worker-process-loggers
            def logger_setup_func():
                logging.basicConfig(level=logging.WARNING)
                logging.getLogger("httpx").setLevel(
                    logging.WARNING
                )  # INFO to see response codes
                logging.getLogger("LiteLLM").setLevel(logging.WARNING)
                logging.getLogger("bespokelabs-curator").setLevel(logging.INFO)

            # log_level is used for ray, not for worker libraries
            ray.init(
                logging_level=log_level,
                runtime_env={"worker_process_setup_hook": logger_setup_func},
            )
            logger_setup_func()
            self.from_config(framework_path)
            try:
                self.run()
            finally:
                ray.shutdown()

        # running python -m dcft.main --framework ... on something that is a subframework of another framework, will load from cache and just assign a UUID, upload to HF, and mark as `is_final` (if these things have not already been done).
        if self.final_operator_loaded_from_cache:
            logger.info(
                ">>> FRAMEWORK CACHE BONANZA <<< Final step loaded from cache! Will upload to HF (which detects if nothing has changed and will skip empty commits) and update the database with the HF link if it doesn't already exist."
            )

        self.cleanup()

    def _load_frameworks(self) -> Dict[str, str]:
        """
        Load all synthetic data frameworks from YAML configurations.
        Uses utility function to recursively search through all subdirectories.

        Returns:
            Dict[str, str]: A dictionary mapping framework names to their config file paths.

        Raises:
            ValueError: If a duplicate framework name is encountered.
        """
        return walk_directory(
            directory=self.strategies_dir,
            file_extensions=(".yaml", ".yml"),
            skip_dirs=("__pycache__",),
        )

    def from_config(self, config_path: str) -> None:
        """
        Create a DAG from a configuration file.

        Args:
            config_path (str): Path to the configuration file.
        """
        self.deduped_sub_dags = {}
        self.dag = self.parse_dag(config_path)

    def get_operator_cache_directory(self, operator_hash: str) -> str:
        return os.path.join(self.output_dir, operator_hash)

    def get_waitables(self) -> List[ManyShardRefsGenerator]:
        """
        Execute the operators in the DAG and return a list of waitables representing the output shards.

        Returns:
            List[ManyShardRefsGenerator]: References to the output shards of the data generation process.
        """
        datas: Dict[str, ManyShardRefsGenerator] = {}

        sorted_ops = self.dag.topological_sort()
        out_degree_map = self.dag.get_out_degree_map()
        waitables = []

        hasher = HashCodeHelper()
        self.map_op_id_to_dag_hash = self.dag.calculate_operator_hashes(
            sorted_ops, hasher
        )

        dag_dict = self.dag.to_dict()
        waitables = []
        self.save_shard_waitables = {}

        successfully_loaded_from_cache = False
        for operator in sorted_ops:
            # Prepare input data for the operator
            input_datas = {}
            for input_id in operator.input_ids:
                if out_degree_map[input_id] > 1:
                    # Since the input_ids is still needed by more than one operator, we need to
                    # tee the generator so that the output operators can independently consume the shards.
                    iter1, iter2 = tee(datas[input_id])
                    input_datas[input_id] = _to_generator(iter1)
                    datas[input_id] = _to_generator(iter2)
                else:
                    input_datas[input_id] = datas[input_id]

                # Decrement the out-degree of the input operator
                out_degree_map[input_id] -= 1

            operator_hash = self.map_op_id_to_dag_hash[operator.id]
            if self.output_dir:
                operator_cache_directory = self.get_operator_cache_directory(
                    operator_hash
                )
                success_file_path = os.path.join(
                    operator_cache_directory, "SUCCESS_FLAG"
                )

            # Execute the operator, load from cache if possible
            successfully_loaded_from_cache = False
            if (
                self.output_dir
                and self.fs
                and self.enable_cache
                and self.fs.exists(operator_cache_directory)
            ):
                if self.resume_from_partial or self.fs.exists(success_file_path):
                    # CACHE HIT! Cache directory present and (resume from partial or success flag present)

                    # List shard directories in the operator hash directory
                    shard_paths = []
                    for shard_path in self.fs.listdir(operator_cache_directory):
                        if shard_path["type"] == "directory":
                            if self.fs_type == "gcs":
                                shard_path["name"] = f"gs://{shard_path['name']}"
                            shard_paths.append(shard_path)

                    # If there are no shards, cache is invalid
                    if self.fs_type == "gcs":
                        browse_message = f"You can browse these shards at https://console.cloud.google.com/storage/browser/{operator_cache_directory[len('gs://'):]}"
                    else:
                        browse_message = (
                            f"You can browse these shards at {operator_cache_directory}"
                        )
                    if len(shard_paths) == 0:
                        if self.fs.exists(success_file_path):
                            self.fs.delete(success_file_path)
                        logger.warning(
                            f">>> FRAMEWORK CACHE INVALID <<< Found no shards for {operator_hash} in {operator_cache_directory} for operator {operator.id}. Removing success flag if one is present. {browse_message}"
                        )
                    else:
                        if not self.fs.exists(success_file_path):
                            # If there are shards, but no success flag, we're resuming from a partial operator output
                            logger.info(
                                f">>> FRAMEWORK CACHE PARTIAL HIT <<< Found {len(shard_paths)} shards for {operator_hash} in {operator_cache_directory} for operator {operator.id}, but no success flag and resume_from_partial is True. {browse_message}"
                            )
                        else:
                            # Otherwise, we're resuming from a completed operator output
                            logger.info(
                                f">>> FRAMEWORK CACHE HIT <<< Found {len(shard_paths)} shards for {operator_hash} in {operator_cache_directory} for operator {operator.id}. {browse_message}"
                            )

                        # Load the cached dataset
                        curr_op_output = self._load_dataset_from_fs_generator(
                            operator.id, shard_paths, self.fs
                        )
                        successfully_loaded_from_cache = True
                else:
                    # Cache dir present but we are going to overwrite it
                    if self.fs_type == "gcs":
                        browse_message = f"You can browse these shards at https://console.cloud.google.com/storage/browser/{operator_cache_directory[len('gs://'):]}"
                    else:
                        browse_message = (
                            f"You can browse these shards at {operator_cache_directory}"
                        )
                    logger.warning(
                        f">>> FRAMEWORK CACHE INVALID <<< Found cache directory {operator_hash} in {operator_cache_directory} for operator {operator.id}. But resume_from_partial is False and no success flag present. If other operators depend on this and are not cached, then this will run and overwrite the cache. {browse_message}"
                    )

            if not successfully_loaded_from_cache:
                logger.info(f"Adding operator {operator.id} waitables for execution")
                # execute returns a generator of shard references
                curr_op_output = operator.execute(input_datas)

            # not loaded from cache and materializing output
            should_materialize_output = (
                operator.config.materialize_output
                and not successfully_loaded_from_cache
                and self.output_dir
                and not isinstance(operator, HFUploadOperator)
            )
            if should_materialize_output:
                generation_parameters = dag_dict.copy()
                generation_parameters["op_id"] = operator.id
                dataset_id = str(uuid.uuid4())
                generation_start = datetime.datetime.now(datetime.timezone.utc)

                # Here we check to see if a row with the operator hash exists in the DB
                # if it doesn't we add name, UUID, generation_parameters, generation_start, data_location
                # if it does, we update the start time. (even though this isn't actually started yet, the waitables have just been created)
                # NOTE(Ryan) if a later operator is cached, the the waitables won't even be waited on by ray (won't be executed)

                self._create_or_update_dataset_start_in_db(
                    operator_id=operator.id,
                    operator_hash=operator_hash,
                    generation_parameters=generation_parameters,
                    generation_start=generation_start,
                    data_location=operator_cache_directory,
                )
                self.fs.makedirs(operator_cache_directory, exist_ok=True)

                # Writes an empty file so humans can understand what framework + operator made this operator_cache_directory
                self.fs.touch(
                    os.path.join(
                        operator_cache_directory, operator.id.replace("::", "--")
                    )
                )
            if not isinstance(operator, HFUploadOperator):
                curr_op_output = self._wrap_generator_with_saving_shard_and_throttling(
                    curr_op_output,
                    operator_hash,
                    operator_cache_directory,
                    should_materialize_output,
                )

            # this is why if a loader cache gets loaded, we don't wait for the earlier operators to finish
            if operator.id in self.dag.output_ids:
                waitables.append(curr_op_output)

            datas[operator.id] = curr_op_output

        # Assumes one output id
        self.final_operator_loaded_from_cache = successfully_loaded_from_cache

        # only reaching this once for the last operator, the last operator doesn't wait for it's input operators to finish if it is cached
        logger.info(f"Generated {len(waitables)} waitables")
        return waitables

    def wait_for_results(
        self, waitables: List[ManyShardRefsGenerator], no_return: bool = False
    ) -> List[Dataset]:
        """
        Wait for the waitables and return the results.

        The goal is to generate the data in a way that doesn't overwhelm the
        system's distributed memory. We do this by controlling how many waitables
        are in-flight at the same time (if the number of waitables is too high, we
        wait for some of them to finish before adding more). Note that this is
        only possible if the waitables are generators and we can control when
        new shards are generated.

        Args:
            waitables (List[ManyShardRefsGenerator]): List of waitables to process.
            no_return (bool, optional): Whether to not return data to the local machine. Defaults to False.

        Returns:
            List[Dataset]: The results obtained from the waitables as a list of Dataset objects.
        """
        i = 0
        pending_waitables = []
        results = []
        remaining_save_shard_waitables = True
        while (
            i < len(waitables)
            or len(pending_waitables) > 0
            or remaining_save_shard_waitables
        ):
            if i < len(waitables):
                try:
                    shard = next(waitables[i])
                    pending_waitables.append(shard)
                except StopIteration:
                    i += 1

            # Some waitables are actually done, but if we don't ray.wait them and garbage collect their
            # references, they'll keep accumulating in the object store. In order to avoid this, we
            # periodically ray.wait on the pending_waitables.
            # i >= len(waitables) means we have yielded all waitables
            if len(pending_waitables) > self.max_pending_waitables or i >= len(
                waitables
            ):
                ready_waitables, pending_waitables = ray.wait(
                    pending_waitables, fetch_local=False, timeout=30
                )
                for ready_waitable in ready_waitables:
                    if not no_return:
                        dataset = ray.get(ready_waitable)
                        results.append(dataset)

            # Save shards
            remaining_save_shard_waitables = True
            all_shards_saved_successfully_map = {}

            if remaining_save_shard_waitables:
                remaining_save_shard_waitables = False
                for operator_hash in self.save_shard_waitables:
                    operator_cache_directory = self.get_operator_cache_directory(
                        operator_hash
                    )

                    lst = self.save_shard_waitables[operator_hash]
                    ready_waitables, pending_save_shard_waitables = ray.wait(
                        lst, timeout=0.1
                    )
                    logger.info(
                        f"{len(pending_save_shard_waitables)} save shard waitables remainings for op hash {operator_hash}."
                    )
                    shards_saved_successfully = all_shards_saved_successfully_map.get(
                        operator_hash, True
                    )
                    for ready_waitable in ready_waitables:
                        shard_saved_successfully = ray.get(ready_waitable)
                        shards_saved_successfully = (
                            shards_saved_successfully and shard_saved_successfully
                        )
                    all_shards_saved_successfully_map[operator_hash] = (
                        shards_saved_successfully
                    )

                    if pending_save_shard_waitables:
                        self.save_shard_waitables[operator_hash] = (
                            pending_save_shard_waitables
                        )
                        remaining_save_shard_waitables = True
                    elif shards_saved_successfully:
                        self.fs.touch(
                            os.path.join(operator_cache_directory, "SUCCESS_FLAG")
                        )
                        if self.fs_type == "gcs":
                            browse_message = f"You can browse these shards at https://console.cloud.google.com/storage/browser/{operator_cache_directory[len('gs://'):]}"
                        else:
                            browse_message = f"You can browse these shards at {operator_cache_directory}"
                        logger.info(
                            f"All shards successfully saved. Planted success flag for operator hash {operator_hash}. {browse_message}"
                        )
                        # HERE we could update with everything
                        self._update_dataset_end_in_db(operator_hash)
                    else:
                        logger.warning(
                            f"Not all shards were saved successfully for operator hash {operator_hash}, no success flag planted."
                        )

        logger.info(f"Finished waiting for waitables")
        return results

    def run(self) -> None:
        """
        Modified run method to add HF upload operator to the DAG.
        """
        self.run_id = str(uuid.uuid4())
        logger.info(f"Run ID: {self.run_id}")

        self._initialize_git_info()

        # Get original DAG waitables
        self.dag_without_hf = copy.deepcopy(self.dag)

        # Create and add HF upload operator if HF account is specified
        if self.hf_account and not self.no_return:
            # Create HF upload operator config
            upload_config = HFUploadOperatorConfig(
                repo_id=f"{self.hf_account}/{self.framework_name}",
                private=self.hf_private,
                config_paths=list(self.parsed_yamls) if self.parsed_yamls else None,
            )

            # Create operator instance
            upload_operator = HFUploadOperator(
                id=f"{self.framework_name}::hf_upload",
                input_ids=self.dag_without_hf.output_ids,
                config=upload_config,
                execution_context=ExecutionContext(fs_type=self.fs_type),
            )

            # Add upload operator to DAG
            self.dag.add_operator(upload_operator)
            self.dag.output_ids = [upload_operator.id]

        # Get waitables and process results
        waitables = self.get_waitables()
        results = self.wait_for_results(waitables, no_return=False)[0]
        if not self.no_return and self.hf_account:
            # Update database with upload information
            if self.db_connection:
                sorted_ops = self.dag.topological_sort()
                operator_hash = self.map_op_id_to_dag_hash[sorted_ops[-2].id]

                hf_link = f"https://huggingface.co/datasets/{results['repo_id']}"

                self._update_dataset_as_final_in_db(
                    hf_link=hf_link,
                    hf_commit_hash=results["commit_hash"],
                    hf_fingerprint=results["fingerprint"],
                    row_count=results["length"],
                    operator_hash=operator_hash,
                )

            logger.info(f"Dataset uploaded successfully with {results['length']} rows")
            logger.info(
                f"Dataset available at: https://huggingface.co/datasets/{results['repo_id']}"
            )

    def run_remote(self, framework_name: str) -> None:
        """
        Run the entire data generation process on a remote Ray cluster.

        Args:
            framework_name (str): The name of the framework to run.
        """
        self.client = JobSubmissionClient(self.ray_address)
        cmd_args = [
            f"--framework {framework_name}",
        ]

        if self.hf_account:
            cmd_args.append(f"--hf-account {self.hf_account}")
        if self.no_return:
            cmd_args.append("--no-return")
        if self.fs_type:
            cmd_args.append(f"--fs-type {self.fs_type}")
        if self.enable_cache:
            cmd_args.append("--enable-cache")
        if self.max_pending_waitables:
            cmd_args.append(f"--max-pending-waitables {self.max_pending_waitables}")
        if self.output_dir:
            cmd_args.append(f"--output-dir {self.output_dir}")
        if self.db_connection_string:
            cmd_args.append(f"--db-connection-string {self.db_connection_string}")

        # Run uv pip compile to generate remote_requirements.txt
        subprocess.run(
            [
                "uv",
                "pip",
                "compile",
                "requirements.txt",
                "--universal",
                "--output-file",
                "remote_requirements.txt",
            ],
            check=True,
        )

        requirements = []
        with open("remote_requirements.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("."):
                    # Replace the relative path with the absolute path based
                    # on the working directory for the Ray worker.
                    # (see https://docs.ray.io/en/latest/ray-core/handling-dependencies.html#using-local-files)
                    line = line.replace("./", "${RAY_RUNTIME_ENV_CREATE_WORKING_DIR}/")
                    requirements.append(line)
                    continue
                if line and not line.startswith("#"):
                    requirements.append(line.strip())

        job_id = self.client.submit_job(
            entrypoint=f"python -m dcft.generate {' '.join(cmd_args)}",
            runtime_env={
                "working_dir": "./",
                "conda": {
                    "dependencies": [
                        "pip",
                        "libffi=3.4",
                        {"pip": requirements},
                    ],
                },
                "py_modules": [
                    # "prebuilt_wheels/fast_bleu-0.0.90-cp310-cp310-linux_x86_64.whl",
                    # "prebuilt_wheels/fast_jl-0.1.3-cp310-cp310-linux_x86_64.whl",
                    "https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.0.post2/flash_attn-2.7.0.post2+cu12torch2.5cxx11abiFALSE-cp310-cp310-linux_x86_64.whl",
                ],
                "config": {"setup_timeout_seconds": 1200},
                # Exclude potentially large files and directories
                # NOTE(Ryan) removed .jsonl since we need it as seed data for Alpaca
                # do `ls **/*.jsonl` to see what potentially getting sent.
                # Note that /eval and /datasets are excluded already elsewhere
                # TODO(Ryan): Get the largest files and have a threshold at X00 MB and print out a warning and auto exclude anything over that size
                "excludes": [
                    "**/.gitignore",
                    "**/.DS_Store",
                    "**/.git",
                    "**/.venv",
                    "/datasets",
                    "/eval",
                    "/dcft/train",
                    "/database",
                    "/cluster",
                    "/dcft/external_repositories/code2flow/tests/",
                    "**/*.csv",
                    "**/*.bin",
                    "**/*.gif",
                    "**/*.png",
                    "**/*.jpg",
                    "**/*.jpeg",
                    "github_issues_data/*",
                ],
                "env_vars": {
                    "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", ""),
                    "HF_TOKEN": os.environ.get("HF_TOKEN", ""),
                    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
                    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
                    "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
                    "SAMBANOVA_API_KEY": os.environ.get("SAMBANOVA_API_KEY", ""),
                    "TOGETHER_API_KEY": os.environ.get("TOGETHER_API_KEY", ""),
                    "FIREWORKS_API_KEY": os.environ.get("FIREWORKS_API_KEY", ""),
                    "DEEPINFRA_API_KEY": os.environ.get("DEEPINFRA_API_KEY", ""),
                    "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY", ""),
                    "OPENAI_LOG": "warning",
                    "CURATOR_DISABLE_RICH_DISPLAY": "1",
                    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", ""),
                    "AWS_SECRET_ACCESS_KEY": os.environ.get(
                        "AWS_SECRET_ACCESS_KEY", ""
                    ),
                    "AWS_SESSION_TOKEN": os.environ.get("AWS_SESSION_TOKEN", ""),
                    "RAY_DEDUP_LOGS": "0",
                    "RAY_TASK_MAX_RETRIES": "-1",
                    "SYNTHETIC_DATA_MANAGER_CREATION_LOCATION": self.ray_address,
                    "GIT_COMMIT_HASH": get_git_commit_hash(),
                    "GIT_DIFF": get_git_diff(),
                    "IS_REMOTE": "1",
                    "SUBMISSION_USER": os.environ.get(
                        "USER", os.environ.get("USERNAME", "unknown")
                    ),
                    "RAY_record_ref_creation_sites": "1",
                },
            },
        )

        logger.info(f"Submitted job with ID: {job_id}")
        if self.wait_for_job_completion:
            logger.info(
                "Waiting for job to complete... "
                f"You can press Ctrl+C to stop and still check the status with the job ID {job_id} "
                f"at {self.ray_address}."
            )
            self._wait_until_status(job_id, ["SUCCEEDED", "FAILED"])
            logger.info(
                f"Job {job_id} completed with status: {self.client.get_job_status(job_id)}"
            )
            logger.info(
                f"Check (if SUCCEEDED) https://huggingface.co/datasets/{self.hf_account}/{framework_name}"
            )

    def cleanup(self) -> None:
        """
        Clean up and save the generated datasets to cache.
        """
        if self.db_connection:
            self.db_connection.close()

    def _look_up_dataset_id_in_db(self, hash_id: str) -> str:
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id FROM datasets
                    WHERE data_generation_hash = %s
                    AND generation_status = 'COMPLETED'
                    ORDER BY generation_end DESC
                    LIMIT 1
                    """,
                    (hash_id,),
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error looking up dataset ID: {e}")
            return None

    def _save_dataset_info_to_file(
        self,
        dataset_id: str,
        name: str,
        generation_parameters: dict,
        op_id: str,
        generation_start: datetime.datetime,
    ):
        info = {
            "dataset_id": dataset_id,
            "run_id": self.run_id,
            "name": name,
            "generation_parameters": generation_parameters,
            "op_id": op_id,
            "generation_start": generation_start.isoformat(),
        }
        cache_parent_dir = SyntheticDataManager._get_cache_parent_dir(
            self.output_dir, op_id, dataset_id, self.fs_type
        )
        file_path = os.path.join(cache_parent_dir, "info.json")

        if self.fs_type == "file" and not self.fs.exists(cache_parent_dir):
            self.fs.makedirs(cache_parent_dir, exist_ok=True)

        with self.fs.open(file_path, "w") as f:
            json.dump(info, f, indent=2)

        logger.info(f"Saved generation parameters to {file_path}")

    def _save_dataset_info_to_db(
        self,
        dataset_id: str,
        name: str,
        generation_parameters: dict,
        generation_start: datetime.datetime,
        generation_end: Optional[datetime.datetime] = None,
        data_location: Optional[str] = None,
        generation_status: Optional[str] = "QUEUED",
        hf_fingerprint: Optional[str] = None,
        hf_link: Optional[str] = None,
        hf_commit_hash: Optional[str] = None,
        row_count: Optional[int] = None,
        is_final: bool = False,
    ):
        if not self.db_connection:
            logger.warning("Database connection not available. Skipping database save.")
            return
        try:
            data_generation_hash = None
            if self.map_op_id_to_dag_hash and (name in self.map_op_id_to_dag_hash):
                data_generation_hash = self.map_op_id_to_dag_hash[name]

            with self.db_connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO datasets (
                        id, run_id, name, created_by, creation_location, creation_time, 
                        generation_start, generation_end, data_location, generation_parameters, 
                        generation_status, dataset_type, is_external, 
                        data_generation_hash, git_commit_hash, git_diff, hf_fingerprint, hf_link, hf_commit_hash, is_final, last_modified,
                        row_count
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        dataset_id,
                        self.run_id,  # This contains UUID of the run - only updated if a future run sees this wasn't successful and re-runs and updates start and end times
                        name,
                        os.environ.get("SUBMISSION_USER", "unknown"),
                        os.environ.get(
                            "SYNTHETIC_DATA_MANAGER_CREATION_LOCATION", "unknown"
                        ),
                        datetime.datetime.now(datetime.timezone.utc),
                        generation_start,
                        generation_end,
                        data_location,
                        Jsonb(generation_parameters),
                        generation_status,
                        "SFT",
                        False,
                        data_generation_hash,
                        self.git_commit_hash,
                        self.git_diff,
                        hf_fingerprint,
                        hf_link,
                        hf_commit_hash,
                        is_final,
                        datetime.datetime.now(datetime.timezone.utc),
                        row_count,
                    ),
                )
            self.db_connection.commit()
            self.created_dataset_ids.append(
                dataset_id
            )  # Add the dataset ID to our list
            logger.info(f"Saved dataset info to database for dataset_id: {dataset_id}")
        except Exception as e:
            self.db_connection.rollback()
            logger.error(f"Error saving to database: {e}")

    def _create_or_update_dataset_start_in_db(
        self,
        operator_id: str,
        generation_parameters: dict,
        generation_start: datetime.datetime,
        data_location: str,
        operator_hash: str,
    ):
        """
        Create or update a dataset row in the database when starting operator execution.

        Args:
            operator_id: The ID of the operator
            generation_parameters: Dictionary of generation parameters
            generation_start: Start time of generation
            data_location: Location where data will be stored
            operator_hash: Hash of the operator for tracking
        """
        if not self.db_connection:
            return

        try:
            with self.db_connection.cursor() as cursor:
                # Check if row exists
                cursor.execute(
                    """
                    SELECT id, generation_status 
                    FROM datasets 
                    WHERE data_generation_hash = %s
                    """,
                    (operator_hash,),
                )
                rows = cursor.fetchall()

                if len(rows) == 0:
                    # Create new row - this is the only time we create a UUID - when we create a row. Then we prevent duplicates happening.
                    # There should be one UUID for each operator hash - kinda a duplicate key but allows us to change things later if we need
                    dataset_id = str(uuid.uuid4())
                    self._save_dataset_info_to_db(
                        dataset_id=dataset_id,
                        name=operator_id,
                        generation_parameters=generation_parameters,
                        generation_start=generation_start,
                        data_location=data_location,
                    )
                    logger.info(
                        f"Created DB record in datasets table for operator {operator_id} and operator hash {operator_hash} with ID {dataset_id}"
                    )
                else:
                    assert (
                        len(rows) == 1
                    ), f"Expected exactly one row for operator_hash {operator_hash}, found {len(rows)}"
                    # Update existing row
                    dataset_id, status = rows[0]
                    if status == "COMPLETED":
                        raise ValueError(
                            f"Cannot update completed dataset with ID {dataset_id}, if completed then the cache should be valid. Something went wrong."
                        )

                    cursor.execute(
                        """
                        UPDATE datasets 
                        SET name = %s,
                            generation_parameters = %s,
                            generation_start = %s,
                            data_location = %s,
                            generation_status = 'QUEUED',
                            run_id = %s,
                            last_modified = %s
                        WHERE data_generation_hash = %s
                        """,
                        (
                            operator_id,
                            Jsonb(generation_parameters),
                            generation_start,
                            data_location,
                            self.run_id,
                            datetime.datetime.now(datetime.timezone.utc),
                            operator_hash,
                        ),
                    )
                    logger.info(
                        f"Updated existing dataset row for operator {operator_id} and operator hash {operator_hash} with ID {dataset_id}"
                    )

                self.db_connection.commit()

        except Exception as e:
            self.db_connection.rollback()
            logger.error(f"Error creating/updating dataset row: {e}")

    def _update_dataset_end_in_db(self, operator_hash: str):
        if not self.db_connection:
            return
        try:
            with self.db_connection.cursor() as cursor:
                generation_end = datetime.datetime.now(datetime.timezone.utc)
                cursor.execute(
                    """
                    UPDATE datasets
                    SET generation_end = %s, generation_status = 'COMPLETED', run_id = %s, last_modified = %s
                    WHERE data_generation_hash = %s
                """,
                    (
                        generation_end,
                        self.run_id,
                        datetime.datetime.now(datetime.timezone.utc),
                        operator_hash,
                    ),
                )
            self.db_connection.commit()
            logger.info(f"Updated end times for operator hash {operator_hash}")
        except Exception as e:
            self.db_connection.rollback()
            logger.error(f"Error updating dataset end times: {e}")

    def _update_dataset_as_final_in_db(
        self,
        hf_link: str,
        hf_commit_hash: str,
        hf_fingerprint: str,
        row_count: int,
        operator_hash: str,
    ):
        if not self.db_connection:
            return False

        try:
            with self.db_connection.cursor() as cursor:
                # Get the existing row and verify there is only one
                cursor.execute(
                    """
                    SELECT hf_link, hf_fingerprint, hf_commit_hash, row_count
                    FROM datasets 
                    WHERE data_generation_hash = %s
                    """,
                    (operator_hash,),
                )
                rows = cursor.fetchall()
                assert (
                    len(rows) == 1
                ), f"Expected exactly one row for operator_hash {operator_hash}, found {len(rows)}"

                row = rows[0]
                # If any fields exist, verify they match
                if row[0]:  # hf_link
                    assert (
                        row[0] == hf_link
                    ), f"Existing hf_link {row[0]} does not match new link {hf_link}"
                if row[1]:  # hf_fingerprint
                    assert (
                        row[1] == hf_fingerprint
                    ), f"Existing fingerprint {row[1]} does not match new fingerprint {hf_fingerprint}"
                if row[2]:  # hf_commit_hash
                    assert (
                        row[2] == hf_commit_hash
                    ), f"Existing commit hash {row[2]} does not match new hash {hf_commit_hash}"
                if row[3]:  # row_count
                    assert (
                        row[3] == row_count
                    ), f"Existing row_count {row[3]} does not match new row_count {row_count}"

                # Update the row with the final information
                cursor.execute(
                    """
                    UPDATE datasets
                    SET hf_link = %s,
                        hf_fingerprint = %s,
                        hf_commit_hash = %s,
                        row_count = %s,
                        is_final = TRUE,
                        last_modified = %s
                    WHERE data_generation_hash = %s
                    """,
                    (
                        hf_link,
                        hf_fingerprint,
                        hf_commit_hash,
                        row_count,
                        datetime.datetime.now(datetime.timezone.utc),
                        operator_hash,
                    ),
                )

            self.db_connection.commit()
            logger.info(f"Updated final information for operator hash {operator_hash}")
            return True
        except Exception as e:
            self.db_connection.rollback()
            logger.error(f"Error updating dataset as final: {e}")
            return False

    def _wrap_generator_with_saving_shard_and_throttling(
        self,
        generator,
        operator_hash,
        operator_cache_directory,
        should_materialize_output,
    ):
        pending_shards = []

        for i, item in enumerate(generator):
            pending_shards.append(item)
            # Throttle the number of pending shards for a given operator to avoid memory issues
            while len(pending_shards) >= self.max_pending_waitables:
                _, pending_shards = ray.wait(pending_shards, fetch_local=False)

            if should_materialize_output:
                waitables = self.save_shard_waitables.get(operator_hash, [])
                waitables.append(
                    self._save_shard.options(num_cpus=0.1).remote(
                        item,
                        i,
                        operator_cache_directory,
                        self.fs.open,
                    )
                )
                self.save_shard_waitables[operator_hash] = waitables
            yield item

    @staticmethod
    @ray.remote
    def _save_shard(dataset, idx, operator_cache_directory, custom_open):
        # Create directory for the shard and save the shard
        shard_directory = os.path.join(operator_cache_directory, f"{idx}")
        logger.info(f"Saving shard {idx} to {shard_directory}")
        # Skip saving if dataset has no features or examples
        if not dataset.features or len(dataset) == 0:
            logger.warning(
                f"Skipping save of shard {idx} - dataset has no features or examples"
            )
            return True
        try:
            dataset.save_to_disk(
                shard_directory,
                max_shard_size="2GB",
                storage_options={"open": custom_open},
            )
            return True
        except:
            pass

        num_shards = 64
        max_attempts = 50
        attempt = 0
        success = False
        while not success and attempt < max_attempts:
            try:
                dataset.save_to_disk(
                    shard_directory,
                    storage_options={"open": custom_open},
                    num_shards=num_shards,
                )
                success = True
            except Exception as e:
                attempt += 1
                num_shards *= 2
                logger.warning(
                    f"Failed to save shard with {num_shards//2} shards, trying with {num_shards} shards. Attempt {attempt}/{max_attempts}"
                )
                if attempt == max_attempts:
                    raise e

        return True  # success

    @staticmethod
    @ray.remote
    def load_from_disk(dataset_path, fs, keep_in_memory):
        try:
            dataset = load_from_disk(
                dataset_path,
                storage_options={"open": fs.open},
                keep_in_memory=keep_in_memory,
            )
            # saving and loading from disk changes the fingerprint in a deterministic way
            # the fingerprint prior to saving is saved in the state.json file
            # we overwrite to the old fingerprint to ensure the fingerprint is the same as the source dataset
            # this way the curator cache is valid
            old_fingerprint = json.load(fs.open(f"{dataset_path}/state.json"))[
                "_fingerprint"
            ]
            dataset._fingerprint = old_fingerprint
            return dataset
        except Exception as e:
            logger.error(f"Error loading dataset from disk: {e}")
            return Dataset.from_dict({})

    @staticmethod
    def _load_dataset_from_fs_generator(operator_id, shard_paths, fs):
        assert shard_paths

        # Load the shards in order
        shard_paths_with_indices = []
        for shard_path in shard_paths:
            # assuming all directories in the cache folder contain shards
            full_path = shard_path["name"]
            shard_idx = int(full_path.split("/")[-1])
            shard_paths_with_indices.append((shard_idx, full_path))
        # Sort by shard index
        shard_paths_with_indices.sort(key=lambda x: x[0])

        # Load and yield datasets in sorted order
        for _, dataset_path in shard_paths_with_indices:
            logger.info(f"Loading shard from {dataset_path}")
            yield SyntheticDataManager.load_from_disk.options(name=f"load_from_cache_{operator_id}", memory=50 * 1024 * 1024 * 1024).remote(
                dataset_path,
                fs,
                (os.environ.get("IS_REMOTE", "0") == "1"),
            )

    def _wait_until_status(
        self, job_id: str, status_to_wait_for: List[str], timeout_seconds: int = 36000
    ) -> None:
        """
        Wait until the job reaches a specified status.

        Args:
            job_id (str): The ID of the job to wait for.
            status_to_wait_for (List[str]): List of statuses to wait for.
            timeout_seconds (int, optional): Timeout in seconds. Defaults to 36000.
        """
        start = time.time()
        while time.time() - start <= timeout_seconds:
            status = self.client.get_job_status(job_id)
            logger.info(f"status: {status}")
            if status in status_to_wait_for:
                break
            time.sleep(30)

        logger.info(f"Job {job_id} completed with status: {status}")

    def parse_dag(self, config_path: str) -> DAG:
        """
        Parse the configuration and create a DAG.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            DAG: The created DAG.

        Raises:
            ValueError: If there are duplicate operator IDs, invalid configurations, or invalid DAG structure.
        """
        dag = DAG()

        seen_ids = set()
        self.parsed_yamls.add(config_path)
        queue_config_paths: Queue = Queue()
        queue_config_paths.put((None, config_path))

        renaming_map: Dict[str, List[str]] = {}
        config = parse_yaml_config(config_path)
        config["name"] = Path(config_path).stem
        renaming_map = {}

        for op_config in config["operators"]:
            op_id = f"{config['name']}::{op_config['id']}"
            if op_id in seen_ids:
                raise ValueError(f"Duplicate operator ID found: {op_id}")
            seen_ids.add(op_id)

            if op_config["config"]["type"] == "load_preexisting":
                framework_name = op_config["config"]["framework_name"]
                # We only parse the sub-dag and add it to the DAG once
                # This is to avoid duplicating operators from existing sub-dags.
                # Note that we still do the remapping of operator IDs to the
                # output IDs of the sub-dag so that we can correctly connect the
                # sub-dag to the rest of the DAG.
                if framework_name in self.deduped_sub_dags:
                    sub_dag = self.deduped_sub_dags[framework_name]
                else:
                    sub_dag = self.parse_dag(self.frameworks[framework_name])
                    self.deduped_sub_dags[framework_name] = sub_dag
                    dag.extend(sub_dag)
                renaming_map[op_id] = sub_dag.output_ids
            else:
                try:
                    specific_config = parse_specific_config(op_config["config"])
                    if "input_ids" in op_config:
                        inpid = [
                            f"{config['name']}::{input_id}"
                            for input_id in op_config["input_ids"]
                        ]
                    else:
                        inpid = []

                    if (
                        isinstance(specific_config, FunctionOperatorConfig)
                        or isinstance(specific_config, HighMemoryFunctionOperatorConfig)
                        or isinstance(specific_config, GPUFunctionOperatorConfig)
                        or isinstance(specific_config, CPUFunctionOperatorConfig)
                        or isinstance(specific_config, AsyncFunctionOperatorConfig)
                        or isinstance(
                            specific_config, GenericResourceFunctionOperatorConfig
                        )
                    ):
                        if len(specific_config.input_dataset_map.keys()) > 0:
                            for key, value in specific_config.input_dataset_map.items():
                                specific_config.input_dataset_map[key] = (
                                    f"{config['name']}::{value}"
                                )

                    operator_config = OperatorConfig(
                        id=op_id, input_ids=inpid, config=specific_config
                    )

                    operator = create_operator(
                        operator_config, ExecutionContext(fs_type=self.fs_type)
                    )
                    dag.add_operator(operator)

                except ValidationError as e:
                    raise ValueError(
                        f"Invalid configuration for operator {op_id}: {str(e)}"
                    )

        # If output_ids is not specified, use the last operator's ID
        if "output_ids" not in config:
            if dag.operators:
                output_of_sub_dag = [dag.operators[-1].id]
        else:
            output_of_sub_dag = [
                f"{config['name']}::{item}" for item in config["output_ids"]
            ]

        dag.set_output_ids(output_of_sub_dag)

        for operator in dag.operators:
            operator.set_input_ids(
                flatten([renaming_map.get(item, item) for item in operator.input_ids])
            )
            if (
                isinstance(operator, FunctionOperator)
                and operator.config.input_dataset_map
            ):
                keys = list(operator.config.input_dataset_map.keys())
                for k in keys:
                    value = operator.config.input_dataset_map[k]
                    operator.config.input_dataset_map[k] = renaming_map.get(
                        value, [value]
                    )[0]
        try:
            dag.validate()
        except ValueError as e:
            raise ValueError(f"Invalid DAG structure: {str(e)}")

        return dag

    def _initialize_git_info(self):
        if os.environ.get("GIT_COMMIT_HASH"):
            self.git_commit_hash = os.environ.get("GIT_COMMIT_HASH")
        else:
            self.git_commit_hash = get_git_commit_hash()

        if os.environ.get("GIT_DIFF"):
            self.git_diff = os.environ.get("GIT_DIFF")
        else:
            self.git_diff = get_git_diff()
