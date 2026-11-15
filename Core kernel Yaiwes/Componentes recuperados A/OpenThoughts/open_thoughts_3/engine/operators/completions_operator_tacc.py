import importlib
import itertools
import logging
import math
import os
import threading
import time
from itertools import chain
from typing import Callable, List, Literal, Optional, Type

import ray
import torch
from bespokelabs import curator
from datasets import Dataset, concatenate_datasets
from ray.util.placement_group import (
    placement_group,
    placement_group_table,
    remove_placement_group,
)
from ray.util.scheduling_strategies import PlacementGroupSchedulingStrategy

from dcft.data_strategies.commons import repeat_dataset
from engine.data_syncer import _DataSyncer
from engine.maps.map_registry import COMPLETIONS_MAPS
from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
    ShardRef,
)


class CompletionsOperatorTACCConfig(OperatorSpecificConfig):
    """
    Configuration class for CompletionsOperator.

    Attributes:
        type (str): The type of the operator, should be 'completions'.
        materialize_output (bool): Whether to materialize the output of the operator.
        model (str): The name of the model to use for completions.
        map (str): The name of the map to use for completions.
        map_config (dict): The configuration for the map.
        batch (bool): Whether to batch the completions.
        merge_shards (bool): Whether to merge the shards of the output of the operator.
        n_repeat (int): The number of times to repeat the dataset.
    """

    type: Literal["completions_tacc"] = "completions_tacc"

    # Required
    model: str
    map: str
    map_config: Optional[dict] = {}
    num_vllm_instances: Optional[int] = 4
    # Optional and None
    top_p: Optional[float] = None
    temperature: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None

    n_repeat: Optional[int] = None
    max_requests_per_minute: Optional[int] = None
    max_tokens_per_minute: Optional[int] = None

    # Optional and not None
    require_all_responses: Optional[bool] = True
    batch: Optional[bool] = False
    merge_shards: Optional[bool] = True
    batch_size: Optional[int] = 10_000


# Use 1 logical vllm_instance_resource
@ray.remote
class _Completions:
    _instance = None

    def __init__(self):
        self._sync_thread = None
        self._stop_event = threading.Event()

    def _start_sync_loop(self, data_syncer: _DataSyncer, interval: int = 30):
        """Start the sync thread."""

        pass

        # def sync_loop():
        #     while not self._stop_event.is_set():
        #         try:
        #             data_syncer._scan_and_sync()
        #         except Exception as e:
        #             print(f"Error during sync: {e}")
        #         time.sleep(interval)

        #     data_syncer._scan_and_sync()

        # def run_sync_loop():
        #     sync_loop()

        # self._stop_event.clear()
        # self._sync_thread = threading.Thread(target=run_sync_loop, daemon=True)
        # self._sync_thread.start()

    @staticmethod
    def _load_function_or_class(module_path: str) -> Callable | Type:
        try:
            module_name, attr_name = module_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            loaded_attr = getattr(module, attr_name)

            if not callable(loaded_attr):
                raise TypeError(
                    f"Loaded object '{attr_name}' from '{module_name}' is not callable. "
                    f"Expected a function or class, got {type(loaded_attr)}"
                )

            return loaded_attr
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Failed to load from '{module_path}'. "
                f"Make sure the module is in PYTHONPATH and the function/class exists. Error: {str(e)}"
            ) from e

    def completions(
        self,
        dataset: Dataset,
        config: CompletionsOperatorTACCConfig,
        operator_id: str,
        should_sync_with_remote: bool,
    ) -> ShardRef:
        if not should_sync_with_remote:
            logging.info(
                f'Completions operator {operator_id} is using local curator cache since fs_type is not set to "gcs". Will not sync with remote.'
            )

        operator_id = operator_id.replace("::", "__")
        curator_cache_dir = os.path.expanduser(
            f"{os.environ['CURATOR_CACHE_DIR']}/{operator_id}"
        )

        if should_sync_with_remote:
            remote_dir = f"dcft-data-gcp/curator-cache/{operator_id}"
            logging.info(f"=-=-=-=-=-=- REMOTE CURATOR CACHE DIR -=-=-=-=-=-=")
            logging.info(f"downloading from {remote_dir}")
            _data_syncer = _DataSyncer(curator_cache_dir, remote_dir)

            _data_syncer._download_from_remote()

        completions_map_cls = COMPLETIONS_MAPS[config.map]
        completions_map = completions_map_cls(config.map_config)
        prompt_func = completions_map.prompt
        parse_func = completions_map.parse
        response_format = completions_map.response_format

        # Set logger to INFO level so we get logs from curator.
        logger = logging.getLogger("bespokelabs.curator")
        logger.setLevel(logging.INFO)

        # VLLM behaves weirdly if these are set to None
        generation_params = {}
        if config.top_p:
            generation_params["top_p"] = config.top_p
        if config.temperature:
            generation_params["temperature"] = config.temperature
        if config.presence_penalty:
            generation_params["presence_penalty"] = config.presence_penalty
        if config.frequency_penalty:
            generation_params["frequency_penalty"] = config.frequency_penalty

        backend_params = {
            "batch_size": config.batch_size,
            "tensor_parallel_size": 4,
            "require_all_responses": config.require_all_responses,
            "max_retries": 50,
        }
        # Ray sets CUDA_VISIBLE_DEVICES to empty and this affects VLLM, so we unset here
        del os.environ["CUDA_VISIBLE_DEVICES"]
        completion = curator.LLM(
            model_name=config.model,
            prompt_func=prompt_func,
            parse_func=parse_func,
            response_format=response_format,
            batch=config.batch,
            backend="vllm",
            generation_params=generation_params,
            backend_params=backend_params,
        )

        if should_sync_with_remote:
            self._start_sync_loop(data_syncer=_data_syncer)

        if config.n_repeat:
            dataset = repeat_dataset(dataset, config.n_repeat)
        logging.warning("Dataset")
        logging.warning(dataset)
        dataset = completion(dataset, working_dir=curator_cache_dir)
        # if torch.cuda.is_available():
        #     torch.cuda.empty_cache()
        # This assumes the dataset is stored in a single Arrow file, which is the case
        # for the datasets we use.
        return Dataset.from_file(dataset.cache_files[0]["filename"], in_memory=True)


class CompletionsOperatorTACC(Operator):
    """
    Operator for handling completions.

    Attributes:
        id (str): Unique identifier for the operator.
        input_ids (List[str]): List of input identifiers for the operator.
        config (CompletionsOperatorConfig): Specific configuration for the completions operator.
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: CompletionsOperatorTACCConfig,
        execution_context: ExecutionContext,
    ):
        super().__init__(id, input_ids, config, execution_context)

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Compute the completions operator on the given inputs.

        Args:
            inputs (DatasetRefs): Dictionary of inputs mapping identifiers to a list of shard references.

        Returns:
            ManyShardRefsGenerator: Generator of processed output shard references for each input shard.
        """
        # If we're using GCS cache as output dir, we need to sync our local cache with remote.
        # If using file system, we don't need to do this sync and only use remote cache.
        should_sync_with_remote = self.execution_context.fs_type == "gcs"

        input_dataset = itertools.chain(
            *[iter(input_dataset) for input_dataset in inputs.values()]
        )

        is_dataset_sharded = False
        first_element = next(input_dataset, None)
        if first_element is None:
            raise ValueError(f"Operator {self.id}: No shards found in input dataset.")

        second_element = next(input_dataset, None)
        is_dataset_sharded = second_element is not None
        input_shards = (
            chain([first_element, second_element], input_dataset)
            if is_dataset_sharded
            else [first_element]
        )

        if is_dataset_sharded:
            merged_shard = self.concatenate.remote(input_shards, False)
            shards_to_process = self.shard_dataset.options(
                name=f"sharding::completions"
            ).remote(merged_shard, self.config.num_vllm_instances)
        else:
            shards_to_process = self.shard_dataset.options(
                name=f"sharding::completions"
            ).remote(first_element, self.config.num_vllm_instances)
        for i, shard_ref in enumerate(shards_to_process):
            actor = self._get_completions_actor(f"vllm_placement_{i:02d}")
            waitable = actor.completions.options(name=f"completions__{self.id}").remote(
                shard_ref, self.config, self._id, should_sync_with_remote
            )
            yield waitable

    @staticmethod
    @ray.remote
    def concatenate(shards: List[ShardRef], add_shard_id_column: bool) -> Dataset:
        """
        Concatenate the input shards.

        Args:
            shards (List[ShardRef]): List of dataset shard references.

        Returns:
            Dataset: Concatenateed and shuffled dataset.
        """
        datasets = []
        for shard_id, shards in shards.items():
            for shard in shards:
                dataset_shard = ray.get(shard)
                if add_shard_id_column:
                    dataset_shard = dataset_shard.add_column(
                        "shard_id", [shard_id] * len(dataset_shard)
                    )
                datasets.append(dataset_shard)
        combined_dataset = concatenate_datasets(datasets)
        return combined_dataset

    @staticmethod
    @ray.remote
    def shard_dataset(dataset: Dataset, num_shards: int) -> ray.ObjectRefGenerator:
        """
        Shard the input dataset into multiple parts to utilize parallelism.

        Args:
            dataset (Dataset): The input dataset to be sharded.
            num_shards (int): The number of shards to create.


        Returns:
            ray.ObjectRefGenerator: Generator of dataset shards.
        """
        total_size = len(dataset)
        split_size = max(int(math.ceil(total_size / num_shards)), 1)

        start = 0
        while start < total_size:
            end = start + split_size
            split = dataset.select(range(start, min(end, total_size)))
            start = end
            yield split

    @staticmethod
    @ray.remote
    def cleanup_actor(dataset: Dataset, placement_group) -> ShardRef:
        remove_placement_group(placement_group)
        return dataset

    @staticmethod
    @ray.remote
    def merge_shards(shard_refs: List[ShardRef]) -> ShardRef:
        dataset_shards = []
        for shard_ref in shard_refs:
            dataset_shards.append(ray.get(shard_ref))
        return concatenate_datasets(dataset_shards)

    def _get_completions_actor(self, pg_name: str):
        # If we're batching, spin up a new actor for each operator since
        # we don't need to share QPS limit across operators.
        try:
            pg = ray.util.get_placement_group(pg_name)
        except ValueError:
            pg = placement_group(
                [{"CPU": 1}, {"vllm_instance": 1}] + [{"GPU": 1}] * 4, name=pg_name
            )
            ray.get(pg.ready(), timeout=3600)
        return _Completions.options(
            scheduling_strategy=PlacementGroupSchedulingStrategy(placement_group=pg)
        ).remote()
