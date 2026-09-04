import importlib
import inspect
import itertools
import logging
import time
from itertools import chain
from typing import Any, Callable, Dict, List, Literal

import ray
from datasets import Dataset, concatenate_datasets
from pydantic import Field

from engine.operators.operator import (
    DatasetRefs,
    ExecutionContext,
    ManyShardRefsGenerator,
    Operator,
    OperatorSpecificConfig,
    ShardRef,
)


class FunctionOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for function operators.

    Attributes:
        type (Literal["function"]): The type of the operator, always set to "function".
        function (str): The name or identifier of the function.
        function_config (Dict[str, Any]): Additional configuration for the function.
        sharded (bool): Indicates whether the function can operate across only a shard
        num_shards (int): The number of shards if the function is sharded.
        input_dataset_map (Dict[str, str]): Mapping of function argument names to input datasets from previous operators
    """

    type: Literal["function"] = "function"
    function: str
    function_config: Dict[str, Any] = Field(default_factory=dict)
    sharded: bool = False
    num_shards: int = 15
    input_dataset_map: Dict[str, str] = Field(default_factory=dict)


class GenericResourceFunctionOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for function operators.

    Attributes:
        type (Literal["function"]): The type of the operator, always set to "function".
        function (str): The name or identifier of the function.
        function_config (Dict[str, Any]): Additional configuration for the function.
        sharded (bool): Indicates whether the function can operate across only a shard
        num_shards (int): The number of shards if the function is sharded.
        input_dataset_map (Dict[str, str]): Mapping of function argument names to input datasets from previous operators
    """

    type: Literal["generic_resource_function"] = "generic_resource_function"
    function: str
    function_config: Dict[str, Any] = Field(default_factory=dict)
    sharded: bool = False
    num_shards: int = 15
    input_dataset_map: Dict[str, str] = Field(default_factory=dict)
    num_cpus: float = 1.0
    memory: int = 200


class GPUFunctionOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for GPUfunction operators.

    Attributes:
        type (Literal["gpu_function"]): The type of the operator, always set to "gpu_function".
        function (str): The name or identifier of the function.
        function_config (Dict[str, Any]): Additional configuration for the function.
        sharded (bool): Indicates whether the function can operate across only a shard
        num_shards (int): The number of shards if the function is sharded.
        input_dataset_map (Dict[str, str]): Mapping of function argument names to input datasets from previous operators
    """

    type: Literal["gpu_function"] = "gpu_function"
    function: str
    function_config: Dict[str, Any] = Field(default_factory=dict)
    sharded: bool = False
    num_shards: int = 15
    num_gpus: float = 1.0
    num_cpus: float = 1.0
    input_dataset_map: Dict[str, str] = Field(default_factory=dict)


class HighMemoryFunctionOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for High Memory Function Operators

    Attributes:
        type (Literal["high_memory_function"]): The type of the operator, always set to "high_memory_function".
        function (str): The name or identifier of the function.
        function_config (Dict[str, Any]): Additional configuration for the function.
        sharded (bool): Indicates whether the function can operate across only a shard
        num_shards (int): The number of shards if the function is sharded.
        num_cpus (float): Number of CPUs to allocate for this function.
        input_dataset_map (Dict[str, str]): Mapping of function argument names to input datasets from previous operators
    """

    type: Literal["high_memory_function"] = "high_memory_function"
    function: str
    function_config: Dict[str, Any] = Field(default_factory=dict)
    sharded: bool = False
    num_shards: int = 15
    memory: int = 200
    input_dataset_map: Dict[str, str] = Field(default_factory=dict)


class CPUFunctionOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for CPU function operators.

    Attributes:
        type (Literal["cpu_function"]): The type of the operator, always set to "cpu_function".
        function (str): The name or identifier of the function.
        function_config (Dict[str, Any]): Additional configuration for the function.
        sharded (bool): Indicates whether the function can operate across only a shard
        num_shards (int): The number of shards if the function is sharded.
        num_cpus (float): Number of CPUs to allocate for this function.
        input_dataset_map (Dict[str, str]): Mapping of function argument names to input datasets from previous operators
    """

    type: Literal["cpu_function"] = "cpu_function"
    function: str
    function_config: Dict[str, Any] = Field(default_factory=dict)
    sharded: bool = False
    num_shards: int = 15
    num_cpus: float = 1.0
    input_dataset_map: Dict[str, str] = Field(default_factory=dict)


class AsyncFunctionOperatorConfig(OperatorSpecificConfig):
    """
    Configuration class for async function operators.

    Attributes:
        type (Literal["async_function"]): The type of the operator, always set to "async_function".
        function (str): The name or identifier of the function.
        function_config (Dict[str, Any]): Additional configuration for the function.
        sharded (bool): Indicates whether the function can operate across only a shard
        num_shards (int): The number of shards if the function is sharded.
        input_dataset_map (Dict[str, str]): Mapping of function argument names to input datasets from previous operators
    """

    type: Literal["async_function"] = "async_function"
    function: str
    function_config: Dict[str, Any] = Field(default_factory=dict)
    sharded: bool = False
    num_shards: int = 15
    input_dataset_map: Dict[str, str] = Field(default_factory=dict)


class FunctionOperator(Operator):
    """
    Operator that applies a function to the input dataset or shard.

    Attributes:
        function (Callable[[Dataset], Dataset]): The function to apply to the dataset or shard (shard of a dataset is a dataset).
        function_config (Dict[str, Any]): Additional configuration for the function.
        num_shards (int): Number of shards to split the dataset into if the function can operate across individual shards
        sharded (bool): If the function can be applied to individual shards of a dataset rather than the whole, set this to true to utilize parallelism
    """

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: FunctionOperatorConfig,
        execution_context: ExecutionContext,
        remote_kwargs: Dict = {},
    ):
        """
        Initialize the FunctionOperator.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (FunctionOperatorConfig): Specific configuration for the function operator.
            execution_context (ExecutionContext): Execution context for the operator.
            remote_kwargs (Dict): Keyword argument to be passed into ray remote call
        """
        super().__init__(id, input_ids, config, execution_context)
        self.function = self._load_function(config.function)
        self.function_config = config.function_config
        self.num_shards = config.num_shards
        self.sharded = config.sharded
        self.input_dataset_map = config.input_dataset_map
        self.remote_kwargs = remote_kwargs

    def _load_function(self, function_path: str) -> Callable[[Dataset], Dataset]:
        """
        Load the function from the given path.

        Args:
            function_path (str): Path to the function.

        Returns:
            Callable[[Dataset], Dataset]: The loaded function.
        """
        module_name, function_name = function_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, function_name)

    def compute(self, inputs: DatasetRefs) -> ManyShardRefsGenerator:
        """
        Execute the function operator on the input datasets.

        Args:
            inputs (DatasetRefs): Map of input datasets to apply function on

        Returns:
            ManyShardRefsGenerator: Generator of shards outputted by the function
        """
        sig = inspect.signature(self.function)
        parameters = list(sig.parameters.values())

        # Count the number of Dataset parameters in the function signature
        expected_datasets = [
            param for param in parameters if param.annotation == Dataset
        ]
        if len(expected_datasets) == 1:
            # Single dataset case
            if len(inputs) > 1:
                logging.info(
                    f"Operator {self.id}: Expects 1 dataset, but more than one input_ids were provided. "
                    f"Will run function over all the shards from input datasets."
                )
            elif len(inputs) == 0:
                raise ValueError(
                    f"Operator {self.id}: Expects 1 dataset, but no input_ids were provided."
                )

            arg_name = expected_datasets[0].name
            input_dataset = itertools.chain(
                *[iter(input_dataset) for input_dataset in inputs.values()]
            )

            is_dataset_sharded = False
            first_element = next(input_dataset, None)

            if first_element is None:
                raise ValueError(
                    f"Operator {self.id}: No shards found in input dataset."
                )

            second_element = next(input_dataset, None)
            # If there's a second shard, then the dataset is sharded
            is_dataset_sharded = second_element is not None

            input_shards = (
                chain([first_element, second_element], input_dataset)
                if is_dataset_sharded
                else [first_element]
            )

            if self.sharded and not is_dataset_sharded:
                shards_to_process = self.shard_dataset.options(
                    name=f"sharding::{self.function.__name__}"
                ).remote(first_element, self.num_shards)
            elif not self.sharded and is_dataset_sharded:
                shards_to_process = [
                    self.merge_shards.options(
                        name=f"merging::{self.function.__name__}"
                    ).remote(list(input_shards))
                ]
            else:
                shards_to_process = input_shards

            for shard in shards_to_process:
                processed_dataset = self.process_with_dataset.options(
                    **self.remote_kwargs, name=self.function.__name__
                ).remote({arg_name: shard}, self.function, self.function_config)
                yield processed_dataset

        elif len(expected_datasets) > 1:
            # Multiple datasets case.
            # First argument must be the main dataset that can be sharded
            # Other Dataset arguments must not be sharded
            if len(inputs) != len(expected_datasets):
                raise ValueError(
                    f"Operator {self.id}: Function expects {len(expected_datasets)} datasets, but {len(inputs)} were provided."
                )

            if len(self.input_dataset_map) == 0:
                raise ValueError(
                    f"Operator {self.id}: More than one dataset needed in function, but 'input_dataset_map' is not set!"
                )

            if len(self.input_dataset_map) != len(expected_datasets):
                raise ValueError(
                    f"Operator {self.id}: Length of input_dataset_map does not match the number of datasets needed."
                )

            # Get ordered parameter names and verify first parameter is Dataset
            ordered_params = list(sig.parameters.keys())
            if not ordered_params:
                raise ValueError(f"Operator {self.id}: Function has no parameters")

            first_param = ordered_params[0]
            if sig.parameters[first_param].annotation != Dataset:
                raise ValueError(
                    f"Operator {self.id}: First parameter '{first_param}' must be a Dataset, "
                    f"got {sig.parameters[first_param].annotation}"
                )

            main_dataset_param = (
                first_param  # First parameter is always the main dataset
            )

            # Process each input and verify secondary datasets are not sharded
            mapped_inputs = {}
            main_dataset_shards = None
            for arg, key in self.input_dataset_map.items():
                if arg not in sig.parameters:
                    continue
                input_dataset = iter(inputs[key])
                first_shard = next(input_dataset, None)
                if first_shard is None:
                    raise ValueError(
                        f"Operator {self.id}: No shards found in input dataset for argument {arg}"
                    )

                second_shard = next(input_dataset, None)

                is_dataset_sharded = second_shard is not None
                # For all arguments except the first Dataset parameter, ensure they're not sharded
                if arg != main_dataset_param and second_shard is not None:
                    raise ValueError(
                        f"Operator {self.id}: Secondary dataset argument '{arg}' must not be sharded. "
                        "Only the first dataset argument can be sharded."
                    )

                # For secondary datasets, use the first (and only) shard
                if arg != main_dataset_param:
                    mapped_inputs[arg] = first_shard
                else:
                    # For the main dataset, merge all shards if config is set to not sharded.
                    if not self.sharded:
                        shards = [first_shard]
                        if second_shard is not None:
                            shards.append(second_shard)
                        shards.extend(input_dataset)
                        main_dataset_shards = [self.merge_shards.remote(shards)]
                    else:
                        if second_shard is not None:
                            input_shards = (
                                chain([first_shard, second_shard], input_dataset)
                                if is_dataset_sharded
                                else [first_shard]
                            )
                        else:
                            input_shards = self.shard_dataset.options(
                                name=f"sharding::{self.function.__name__}"
                            ).remote(first_shard, self.num_shards)
                        main_dataset_shards = input_shards

            for shard in main_dataset_shards:
                mapped_inputs[main_dataset_param] = shard
                yield self.process_with_dataset.options(
                    name=self.function.__name__
                ).remote(mapped_inputs, self.function, self.function_config)

        elif len(expected_datasets) == 0:
            # No datasets case (source function)
            result = self.process_without_dataset.options(
                **self.remote_kwargs, name=self.function.__name__
            ).remote(self.function, self.function_config)
            yield result
        else:
            raise ValueError(
                f"Operator {self.id}: Unexpected number of Dataset parameters: {len(expected_datasets)}"
            )

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
        split_size = max(total_size // num_shards, 1)

        start = 0
        while start < total_size:
            end = start + split_size
            split = dataset.select(range(start, min(end, total_size)))
            start = end
            yield split

    @staticmethod
    @ray.remote
    def merge_shards(shards: List[ShardRef]) -> Dataset:
        """
        Merge multiple dataset shards into a single dataset if function requires all data at once.

        Args:
            shards (List[ShardRef]): List of dataset shard references.

        Returns:
            Dataset: Merged dataset.
        """
        dataset = concatenate_datasets([ray.get(shard) for shard in shards])
        logging.warning(f"Merged dataset. Total length: {len(dataset)}")
        return dataset

    @staticmethod
    @ray.remote
    def process_without_dataset(
        function: Callable, function_config: Dict[str, Any]
    ) -> Any:
        """
        Process using the configured function without passing a dataset.
        """
        logging.info(f"Processing with function: {function.__name__}")
        return function(**function_config)

    @staticmethod
    @ray.remote
    def process_with_dataset(
        mapped_inputs: Dict[str, ShardRef],
        function: Callable,
        function_config: Dict[str, Any],
    ) -> Dataset:
        """
        Process datasets using the configured function.

        Args:
            mapped_inputs (Dict[str, ShardRef]): A dictionary mapping parameter names to shard references (merged in previous step)
            function (Callable): The function to apply to the datasets
            function_config (Dict[str, Any]): Additional configuration for the function

        Returns:
            Dataset: The result of applying the function to the input datasets.
        """
        processed_mapped_inputs = {k: ray.get(v) for k, v in mapped_inputs.items()}
        all_inputs = {**function_config, **processed_mapped_inputs}

        logging.info(
            f"Processing {len(processed_mapped_inputs)} input datasets with function: {function.__name__}"
        )

        return function(**all_inputs)


class GPUFunctionOperator(FunctionOperator):
    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: GPUFunctionOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the GPUFunctionOperator, which is the same as a FunctionOperator but the ray remote calls are assigned a GPU.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (FunctionOperatorConfig): Specific configuration for the function operator.
            execution_context (ExecutionContext): Execution context for the operator.
            remote_kwargs (Dict): Keyword argument to be passed into ray remote call
        """
        super().__init__(
            id,
            input_ids,
            config,
            execution_context,
            {"num_gpus": config.num_gpus, "num_cpus": 11 * config.num_cpus},
        )

    @staticmethod
    @ray.remote
    def process_with_dataset(
        mapped_inputs: Dict[str, ShardRef],
        function: Callable,
        function_config: Dict[str, Any],
    ) -> Dataset:
        """
        Process datasets using the configured function. For GPU, we retrying more aggressively
        when we hit OOM errors.

        Args:
            mapped_inputs (Dict[str, ShardRef]): A dictionary mapping parameter names to shard references (merged in previous step)
            function (Callable): The function to apply to the datasets
            function_config (Dict[str, Any]): Additional configuration for the function

        Returns:
            Dataset: The result of applying the function to the input datasets.
        """

        import torch

        processed_mapped_inputs = {k: ray.get(v) for k, v in mapped_inputs.items()}
        all_inputs = {**function_config, **processed_mapped_inputs}

        logging.info(
            f"Processing {len(processed_mapped_inputs)} input datasets with function: {function.__name__}"
        )

        max_retries = 10
        for attempt in range(max_retries):
            try:
                return function(**all_inputs)
            except torch.OutOfMemoryError:
                logging.warning(
                    f"OutOfMemoryError on attempt {attempt + 1} of {max_retries} for function {function.__name__}"
                )
            time.sleep(10)

        raise RuntimeError(
            f"Failed to process datasets with function {function.__name__} after {max_retries} attempts"
        )


class CPUFunctionOperator(FunctionOperator):
    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: CPUFunctionOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the CPUFunctionOperator, which is the same as a FunctionOperator but with explicit CPU allocation.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (CPUFunctionOperatorConfig): Specific configuration for the function operator.
            execution_context (ExecutionContext): Execution context for the operator.
            remote_kwargs (Dict): Keyword argument to be passed into ray remote call
        """
        super().__init__(
            id, input_ids, config, execution_context, {"num_cpus": config.num_cpus}
        )


class GenericResourceFunctionOperator(FunctionOperator):
    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: GenericResourceFunctionOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the CPUFunctionOperator, which is the same as a FunctionOperator but with explicit CPU allocation.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (CPUFunctionOperatorConfig): Specific configuration for the function operator.
            execution_context (ExecutionContext): Execution context for the operator.
            remote_kwargs (Dict): Keyword argument to be passed into ray remote call
        """
        super().__init__(
            id,
            input_ids,
            config,
            execution_context,
            {"num_cpus": config.num_cpus, "memory": config.memory * 1024 * 1024 * 1024},
        )


class HighMemoryFunctionOperator(FunctionOperator):
    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: HighMemoryFunctionOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the HighMemoryFunctionOperator, which is the same as a FunctionOperator but with explicit memory.

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (HighMemoryFunctionOperatorConfig): Specific configuration for the function operator.
            execution_context (ExecutionContext): Execution context for the operator.
            remote_kwargs (Dict): Keyword argument to be passed into ray remote call
        """
        super().__init__(
            id,
            input_ids,
            config,
            execution_context,
            {"memory": config.memory * 1024 * 1024 * 1024},
        )


class AsyncFunctionOperator(FunctionOperator):
    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: AsyncFunctionOperatorConfig,
        execution_context: ExecutionContext,
    ):
        """
        Initialize the AsyncFunctionOperator, which is the same as a FunctionOperator but the ray remote calls are told they need 0 CPU's
        https://docs.ray.io/en/latest/ray-core/scheduling/resources.html#fractional-resource-requirements

        Args:
            id (str): Unique identifier for the operator.
            input_ids (List[str]): List of input identifiers for the operator.
            config (FunctionOperatorConfig): Specific configuration for the function operator.
            execution_context (ExecutionContext): Execution context for the operator.
        """
        super().__init__(id, input_ids, config, execution_context, {"num_cpus": 0.01})
