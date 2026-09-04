from typing import Any, Callable, Dict, List, Literal, Optional

from datasets import Dataset
from pydantic import Field

from engine.operators.function_operator import FunctionOperator, FunctionOperatorConfig
from engine.operators.operator import ExecutionContext, OperatorSpecificConfig


class HFFilterOperatorConfig(OperatorSpecificConfig):
    """Configuration for HF filter operator."""

    type: Literal["hf_filter"] = "hf_filter"
    filter_fn: str  # Name of the filter function
    sharded: bool = False
    num_shards: int = 15
    filter_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class HFFilterOperator(FunctionOperator):
    """Operator that filters a HuggingFace dataset using a provided filter function."""

    def __init__(
        self,
        id: str,
        input_ids: List[str],
        config: HFFilterOperatorConfig,
        execution_context: ExecutionContext,
    ):
        def create_filter_function(
            filter_fn: str, filter_config: Dict[str, Any]
        ) -> Callable[[Dataset], Dataset]:
            """Creates a function that applies the filter to a dataset."""
            filter_func = self._load_function(filter_fn)

            def filter_dataset(dataset: Dataset) -> Dataset:
                return dataset.filter(lambda x: filter_func(x, **filter_config))

            return filter_dataset

        # Create config for parent class
        function = create_filter_function(config.filter_fn, config.filter_config)
        parent_config = FunctionOperatorConfig(
            type="function",
            function="data_strategies.commons.repeat_dataset",
            function_config=config.filter_config,
            sharded=config.sharded,
            num_shards=config.num_shards,
        )

        super().__init__(id, input_ids, parent_config, execution_context)
        self.function = function
