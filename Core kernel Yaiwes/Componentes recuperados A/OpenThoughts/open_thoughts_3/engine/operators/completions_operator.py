import importlib
import logging
import os
import threading
import time
from typing import Callable, List, Literal, Optional, Type

import ray
from bespokelabs.curator import LLM
from datasets import Dataset, concatenate_datasets

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


class CompletionsOperatorConfig(OperatorSpecificConfig):
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

    type: Literal["completions"] = "completions"

    # Required
    model: str
    map: str
    map_config: Optional[dict] = None

    # Optional and None
    top_p: Optional[float] = None
    temperature: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None

    n_repeat: Optional[int] = None
    max_requests_per_minute: Optional[int] = None
    max_tokens_per_minute: Optional[int] = None
    base_url: Optional[str] = None
    backend: Optional[str] = None
    backend_params: Optional[dict] = {}
    generation_params: Optional[dict] = {}
    max_retries: Optional[int] = 50
    # Optional and not None
    require_all_responses: Optional[bool] = True
    batch: Optional[bool] = False
    merge_shards: Optional[bool] = True
    batch_size: Optional[int] = 10_000


@ray.remote(num_cpus=0.1)
class _Completions:
    _instance = None

    def __init__(self):
        self._sync_thread = None
        self._stop_event = threading.Event()

    def _start_sync_loop(self, data_syncer: _DataSyncer, interval: int = 30):
        """Start the sync thread."""

        def sync_loop():
            while not self._stop_event.is_set():
                try:
                    data_syncer._scan_and_sync()
                except Exception as e:
                    print(f"Error during sync: {e}")
                time.sleep(interval)

            data_syncer._scan_and_sync()

        def run_sync_loop():
            sync_loop()

        self._stop_event.clear()
        self._sync_thread = threading.Thread(target=run_sync_loop, daemon=True)
        self._sync_thread.start()

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
        config: CompletionsOperatorConfig,
        operator_id: str,
        should_sync_with_remote: bool,
    ) -> ShardRef:
        if not should_sync_with_remote:
            logging.info(
                f'Completions operator {operator_id} is using local curator cache since fs_type is not set to "gcs". Will not sync with remote.'
            )

        operator_id = operator_id.replace("::", "__")
        curator_cache_dir = os.path.expanduser(f"~/.cache/curator/{operator_id}")

        if should_sync_with_remote:
            remote_dir = f"dcft-data-gcp/curator-cache/{operator_id}"
            logging.info("=-=-=-=-=-=- REMOTE CURATOR CACHE DIR -=-=-=-=-=-=")
            logging.info(f"downloading from {remote_dir}")
            _data_syncer = _DataSyncer(curator_cache_dir, remote_dir)

            _data_syncer._download_from_remote()

        completions_map_cls = COMPLETIONS_MAPS[config.map]
        completions_map = completions_map_cls(config.map_config)
        prompt_func = completions_map.prompt
        parse_func = completions_map.parse

        # Set logger to INFO level so we get logs from curator.
        logger = logging.getLogger("bespokelabs.curator")
        logger.setLevel(logging.INFO)

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
            "max_retries": config.max_retries,
            "require_all_responses": config.require_all_responses,
        }
        if config.base_url:
            backend_params["base_url"] = config.base_url

        # Set specific backend params depending on batch or not
        if config.batch:
            backend_params["batch_size"] = config.batch_size
        else:
            backend_params["max_requests_per_minute"] = config.max_requests_per_minute
            backend_params["max_tokens_per_minute"] = config.max_tokens_per_minute
        backend_params.update(config.backend_params)
        generation_params.update(config.generation_params)

        class _CustomLLM(LLM):
            response_format = completions_map.response_format
            if hasattr(completions_map, "return_completions_object"):
                return_completions_object = completions_map.return_completions_object
            else:
                return_completions_object = False

            def prompt(self, input):
                return prompt_func(input)

            def parse(self, input, response):
                return parse_func(input, response)

        if config.backend:
            completion = _CustomLLM(
                model_name=config.model,
                batch=config.batch,
                generation_params=generation_params,
                backend_params=backend_params,
                backend=config.backend,
            )
        else:
            completion = _CustomLLM(
                model_name=config.model,
                batch=config.batch,
                generation_params=generation_params,
                backend_params=backend_params,
            )
        if should_sync_with_remote:
            self._start_sync_loop(data_syncer=_data_syncer)

        if config.n_repeat:
            dataset = repeat_dataset(dataset, config.n_repeat)
        dataset = completion(dataset, working_dir=curator_cache_dir)
        if should_sync_with_remote:
            self._stop_event.set()
            self._sync_thread.join(timeout=120)

        is_remote = os.environ.get("IS_REMOTE", "0") == "1"

        # This assumes the dataset is stored in a single Arrow file, which is the case
        # for the datasets we use.
        return Dataset.from_file(
            dataset.cache_files[0]["filename"], in_memory=is_remote
        )


class CompletionsOperator(Operator):
    """
        Operator for handling completions.

    Attributes:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (CompletionsOperatorConfig): Specific configuration for the completions operator.
    """

    _completions_singleton = None

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: CompletionsOperatorConfig,
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
        if self.config.merge_shards:
            logging.info(f"Merging shards for {self.__class__.__name__} {self.id}")
            shard_refs = [
                shard_ref
                for (_, shard_refs) in inputs.items()
                for shard_ref in shard_refs
            ]
            waitable = self.merge_shards.remote(shard_refs)
            actor = self._get_completions_actor(self.config.batch)
            yield actor.completions.options(name=f"completions__{self.id}").remote(
                waitable, self.config, self._id, should_sync_with_remote
            )
            return

        for _, shard_refs in inputs.items():
            for shard_ref in shard_refs:
                actor = self._get_completions_actor(self.config.batch)
                waitable = actor.completions.options(
                    name=f"completions__{self.id}"
                ).remote(shard_ref, self.config, self._id, should_sync_with_remote)
                yield waitable

    @staticmethod
    @ray.remote
    def merge_shards(shard_refs: List[ShardRef]) -> ShardRef:
        dataset_shards = []
        for shard_ref in shard_refs:
            dataset_shards.append(ray.get(shard_ref))
        return concatenate_datasets(dataset_shards)

    def _get_completions_actor(self, batch: bool):
        # If we're batching, spin up a new actor for each operator since
        # we don't need to share QPS limit across operators.
        if batch:
            return _Completions.remote()

        # If we're not batching, we need a singleton since we need to share
        # QPS limit across all operators.
        if self._completions_singleton is None:
            self._completions_singleton = _Completions.options(
                name="CompletionsSingleton", get_if_exists=True
            ).remote()
        return self._completions_singleton

    def cleanup(self):
        """Clean up resources when the operator is being shut down."""
        ray.get(self._completions_singleton.shutdown.remote())
